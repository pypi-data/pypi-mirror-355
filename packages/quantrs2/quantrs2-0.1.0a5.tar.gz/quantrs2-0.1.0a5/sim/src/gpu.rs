//! GPU-accelerated quantum simulation module
//!
//! This module provides GPU-accelerated implementations of quantum simulators
//! using WGPU (WebGPU). This implementation is optimized for simulating
//! quantum circuits on GPUs, which significantly speeds up simulations
//! for large qubit counts.

use bytemuck::{Pod, Zeroable};
use num_complex::Complex64;
use quantrs2_circuit::builder::Simulator as CircuitSimulator;
use quantrs2_circuit::prelude::Circuit;
use quantrs2_core::prelude::QubitId;
use std::borrow::Cow;
use std::collections::HashMap;
use std::sync::Arc;
use wgpu::util::DeviceExt;

use crate::simulator::{Simulator, SimulatorResult};

// Define GateType enum for the GPU implementation
#[derive(Debug, Clone)]
pub enum GateType {
    /// Single-qubit gate with matrix representation
    SingleQubit {
        /// Target qubit
        target: QubitId,
        /// 2x2 matrix representation (row-major)
        matrix: ndarray::Array2<num_complex::Complex64>,
    },
    /// Two-qubit gate with matrix representation
    TwoQubit {
        /// Control qubit
        control: QubitId,
        /// Target qubit
        target: QubitId,
        /// 4x4 matrix representation (row-major)
        matrix: ndarray::Array2<num_complex::Complex64>,
    },
}

/// The alignment used for buffers
const BUFFER_ALIGNMENT: u64 = 256;

/// GPU buffer pool for efficient memory management
#[derive(Debug)]
pub struct GpuBufferPool {
    /// Device reference for creating buffers
    device: Arc<wgpu::Device>,
    /// Queue reference for updating buffers
    queue: Arc<wgpu::Queue>,
    /// Pool of reusable state vector buffers by size
    state_buffers: HashMap<u64, Vec<wgpu::Buffer>>,
    /// Pool of reusable result buffers by size
    result_buffers: HashMap<u64, Vec<wgpu::Buffer>>,
    /// Pool of reusable uniform buffers by size
    uniform_buffers: HashMap<u64, Vec<wgpu::Buffer>>,
    /// Maximum number of buffers to keep per size
    max_buffers_per_size: usize,
    /// Current buffer generation (for invalidation)
    generation: u64,
}

impl GpuBufferPool {
    /// Create a new GPU buffer pool
    pub fn new(device: Arc<wgpu::Device>, queue: Arc<wgpu::Queue>) -> Self {
        Self {
            device,
            queue,
            state_buffers: HashMap::new(),
            result_buffers: HashMap::new(),
            uniform_buffers: HashMap::new(),
            max_buffers_per_size: 4, // Keep max 4 buffers per size
            generation: 0,
        }
    }

    /// Get or create a state vector buffer
    pub fn get_state_buffer(&mut self, size: u64) -> wgpu::Buffer {
        let aligned_size = Self::align_buffer_size(size);

        if let Some(buffers) = self.state_buffers.get_mut(&aligned_size) {
            if let Some(buffer) = buffers.pop() {
                return buffer;
            }
        }

        // Create new buffer
        self.device.create_buffer(&wgpu::BufferDescriptor {
            label: Some("Pooled State Vector Buffer"),
            size: aligned_size,
            usage: wgpu::BufferUsages::STORAGE
                | wgpu::BufferUsages::COPY_SRC
                | wgpu::BufferUsages::COPY_DST,
            mapped_at_creation: false,
        })
    }

    /// Get or create a result buffer
    pub fn get_result_buffer(&mut self, size: u64) -> wgpu::Buffer {
        let aligned_size = Self::align_buffer_size(size);

        if let Some(buffers) = self.result_buffers.get_mut(&aligned_size) {
            if let Some(buffer) = buffers.pop() {
                return buffer;
            }
        }

        // Create new buffer
        self.device.create_buffer(&wgpu::BufferDescriptor {
            label: Some("Pooled Result Buffer"),
            size: aligned_size,
            usage: wgpu::BufferUsages::COPY_DST | wgpu::BufferUsages::MAP_READ,
            mapped_at_creation: false,
        })
    }

    /// Get or create a uniform buffer
    pub fn get_uniform_buffer(&mut self, size: u64, data: &[u8]) -> wgpu::Buffer {
        let aligned_size = Self::align_buffer_size(size);

        if let Some(buffers) = self.uniform_buffers.get_mut(&aligned_size) {
            if let Some(buffer) = buffers.pop() {
                // Update buffer data
                self.queue.write_buffer(&buffer, 0, data);
                return buffer;
            }
        }

        // Create new buffer with data
        self.device
            .create_buffer_init(&wgpu::util::BufferInitDescriptor {
                label: Some("Pooled Uniform Buffer"),
                contents: data,
                usage: wgpu::BufferUsages::UNIFORM | wgpu::BufferUsages::COPY_DST,
            })
    }

    /// Return a state buffer to the pool
    pub fn return_state_buffer(&mut self, buffer: wgpu::Buffer, size: u64) {
        let aligned_size = Self::align_buffer_size(size);
        let buffers = self
            .state_buffers
            .entry(aligned_size)
            .or_insert_with(Vec::new);

        if buffers.len() < self.max_buffers_per_size {
            buffers.push(buffer);
        }
        // Otherwise buffer is dropped and deallocated
    }

    /// Return a result buffer to the pool
    pub fn return_result_buffer(&mut self, buffer: wgpu::Buffer, size: u64) {
        let aligned_size = Self::align_buffer_size(size);
        let buffers = self
            .result_buffers
            .entry(aligned_size)
            .or_insert_with(Vec::new);

        if buffers.len() < self.max_buffers_per_size {
            buffers.push(buffer);
        }
        // Otherwise buffer is dropped and deallocated
    }

    /// Return a uniform buffer to the pool
    pub fn return_uniform_buffer(&mut self, buffer: wgpu::Buffer, size: u64) {
        let aligned_size = Self::align_buffer_size(size);
        let buffers = self
            .uniform_buffers
            .entry(aligned_size)
            .or_insert_with(Vec::new);

        if buffers.len() < self.max_buffers_per_size {
            buffers.push(buffer);
        }
        // Otherwise buffer is dropped and deallocated
    }

    /// Align buffer size to GPU requirements
    fn align_buffer_size(size: u64) -> u64 {
        (size + BUFFER_ALIGNMENT - 1) & !(BUFFER_ALIGNMENT - 1)
    }

    /// Clear all buffers (for memory cleanup)
    pub fn clear(&mut self) {
        self.state_buffers.clear();
        self.result_buffers.clear();
        self.uniform_buffers.clear();
        self.generation += 1;
    }

    /// Get memory usage statistics
    pub fn get_stats(&self) -> GpuBufferStats {
        let mut total_state_buffers = 0;
        let mut total_result_buffers = 0;
        let mut total_uniform_buffers = 0;

        for buffers in self.state_buffers.values() {
            total_state_buffers += buffers.len();
        }
        for buffers in self.result_buffers.values() {
            total_result_buffers += buffers.len();
        }
        for buffers in self.uniform_buffers.values() {
            total_uniform_buffers += buffers.len();
        }

        GpuBufferStats {
            state_buffer_pools: self.state_buffers.len(),
            result_buffer_pools: self.result_buffers.len(),
            uniform_buffer_pools: self.uniform_buffers.len(),
            total_state_buffers,
            total_result_buffers,
            total_uniform_buffers,
            generation: self.generation,
        }
    }
}

/// Statistics for GPU buffer usage
#[derive(Debug, Clone)]
pub struct GpuBufferStats {
    pub state_buffer_pools: usize,
    pub result_buffer_pools: usize,
    pub uniform_buffer_pools: usize,
    pub total_state_buffers: usize,
    pub total_result_buffers: usize,
    pub total_uniform_buffers: usize,
    pub generation: u64,
}

/// GPU-accelerated state vector simulator
#[derive(Debug)]
pub struct GpuStateVectorSimulator {
    /// The WGPU device
    #[allow(dead_code)]
    device: Arc<wgpu::Device>,
    /// The WGPU queue
    #[allow(dead_code)]
    queue: Arc<wgpu::Queue>,
    /// The compute pipeline for applying single-qubit gates
    #[allow(dead_code)]
    single_qubit_pipeline: wgpu::ComputePipeline,
    /// The compute pipeline for applying two-qubit gates
    #[allow(dead_code)]
    two_qubit_pipeline: wgpu::ComputePipeline,
    /// GPU buffer pool for efficient memory management
    buffer_pool: std::sync::Mutex<GpuBufferPool>,
}

/// Complex number for GPU computation
#[repr(C)]
#[derive(Copy, Clone, Debug, Pod, Zeroable)]
struct GpuComplex {
    /// Real part
    real: f32,
    /// Imaginary part
    imag: f32,
}

impl From<Complex64> for GpuComplex {
    fn from(c: Complex64) -> Self {
        Self {
            real: c.re as f32,
            imag: c.im as f32,
        }
    }
}

impl From<GpuComplex> for Complex64 {
    fn from(c: GpuComplex) -> Self {
        Complex64::new(c.real as f64, c.imag as f64)
    }
}

/// Uniform buffer for single-qubit gate operations
#[repr(C)]
#[derive(Debug, Copy, Clone, Pod, Zeroable)]
struct SingleQubitGateParams {
    /// Target qubit index
    target_qubit: u32,
    /// Number of qubits
    n_qubits: u32,
    /// Matrix elements (row-major order)
    matrix: [GpuComplex; 4],
}

/// Uniform buffer for two-qubit gate operations
#[repr(C)]
#[derive(Debug, Copy, Clone, Pod, Zeroable)]
struct TwoQubitGateParams {
    /// Control qubit index
    control_qubit: u32,
    /// Target qubit index
    target_qubit: u32,
    /// Number of qubits
    n_qubits: u32,
    /// Matrix elements (row-major order)
    matrix: [GpuComplex; 16],
}

impl GpuStateVectorSimulator {
    /// Create a new GPU-accelerated state vector simulator
    pub async fn new() -> Result<Self, Box<dyn std::error::Error>> {
        // Create WGPU instance
        let instance = wgpu::Instance::default();

        // Request adapter
        let adapter = instance
            .request_adapter(&wgpu::RequestAdapterOptions {
                power_preference: wgpu::PowerPreference::HighPerformance,
                force_fallback_adapter: false,
                compatible_surface: None,
            })
            .await
            .map_err(|_| "Failed to find GPU adapter".to_string())?;

        // Create device and queue
        let (device, queue): (wgpu::Device, wgpu::Queue) = adapter
            .request_device(&wgpu::DeviceDescriptor {
                label: Some("Quantrs GPU Simulator"),
                required_features: wgpu::Features::empty(),
                required_limits: wgpu::Limits::default(),
                memory_hints: wgpu::MemoryHints::default(),
                trace: wgpu::Trace::default(),
            })
            .await?;

        let device = Arc::new(device);
        let queue = Arc::new(queue);

        // Shader for single-qubit gates
        let single_qubit_shader = device.create_shader_module(wgpu::ShaderModuleDescriptor {
            label: Some("Single Qubit Gate Shader"),
            source: wgpu::ShaderSource::Wgsl(Cow::Borrowed(include_str!(
                "shaders/single_qubit_gate.wgsl"
            ))),
        });

        // Shader for two-qubit gates
        let two_qubit_shader = device.create_shader_module(wgpu::ShaderModuleDescriptor {
            label: Some("Two Qubit Gate Shader"),
            source: wgpu::ShaderSource::Wgsl(Cow::Borrowed(include_str!(
                "shaders/two_qubit_gate.wgsl"
            ))),
        });

        // Create compute pipeline layouts
        let single_qubit_pipeline_layout =
            device.create_pipeline_layout(&wgpu::PipelineLayoutDescriptor {
                label: Some("Single Qubit Pipeline Layout"),
                bind_group_layouts: &[&device.create_bind_group_layout(
                    &wgpu::BindGroupLayoutDescriptor {
                        label: Some("Single Qubit Bind Group Layout"),
                        entries: &[
                            // State vector
                            wgpu::BindGroupLayoutEntry {
                                binding: 0,
                                visibility: wgpu::ShaderStages::COMPUTE,
                                ty: wgpu::BindingType::Buffer {
                                    ty: wgpu::BufferBindingType::Storage { read_only: false },
                                    has_dynamic_offset: false,
                                    min_binding_size: None,
                                },
                                count: None,
                            },
                            // Gate parameters
                            wgpu::BindGroupLayoutEntry {
                                binding: 1,
                                visibility: wgpu::ShaderStages::COMPUTE,
                                ty: wgpu::BindingType::Buffer {
                                    ty: wgpu::BufferBindingType::Uniform,
                                    has_dynamic_offset: false,
                                    min_binding_size: None,
                                },
                                count: None,
                            },
                        ],
                    },
                )],
                push_constant_ranges: &[],
            });

        let two_qubit_pipeline_layout =
            device.create_pipeline_layout(&wgpu::PipelineLayoutDescriptor {
                label: Some("Two Qubit Pipeline Layout"),
                bind_group_layouts: &[&device.create_bind_group_layout(
                    &wgpu::BindGroupLayoutDescriptor {
                        label: Some("Two Qubit Bind Group Layout"),
                        entries: &[
                            // State vector
                            wgpu::BindGroupLayoutEntry {
                                binding: 0,
                                visibility: wgpu::ShaderStages::COMPUTE,
                                ty: wgpu::BindingType::Buffer {
                                    ty: wgpu::BufferBindingType::Storage { read_only: false },
                                    has_dynamic_offset: false,
                                    min_binding_size: None,
                                },
                                count: None,
                            },
                            // Gate parameters
                            wgpu::BindGroupLayoutEntry {
                                binding: 1,
                                visibility: wgpu::ShaderStages::COMPUTE,
                                ty: wgpu::BindingType::Buffer {
                                    ty: wgpu::BufferBindingType::Uniform,
                                    has_dynamic_offset: false,
                                    min_binding_size: None,
                                },
                                count: None,
                            },
                        ],
                    },
                )],
                push_constant_ranges: &[],
            });

        // Create compute pipelines
        let single_qubit_pipeline =
            device.create_compute_pipeline(&wgpu::ComputePipelineDescriptor {
                label: Some("Single Qubit Pipeline"),
                layout: Some(&single_qubit_pipeline_layout),
                module: &single_qubit_shader,
                entry_point: Some("main"),
                compilation_options: wgpu::PipelineCompilationOptions::default(),
                cache: None,
            });

        let two_qubit_pipeline = device.create_compute_pipeline(&wgpu::ComputePipelineDescriptor {
            label: Some("Two Qubit Pipeline"),
            layout: Some(&two_qubit_pipeline_layout),
            module: &two_qubit_shader,
            entry_point: Some("main"),
            compilation_options: wgpu::PipelineCompilationOptions::default(),
            cache: None,
        });

        // Create buffer pool for efficient memory management
        let buffer_pool = GpuBufferPool::new(device.clone(), queue.clone());

        Ok(Self {
            device,
            queue,
            single_qubit_pipeline,
            two_qubit_pipeline,
            buffer_pool: std::sync::Mutex::new(buffer_pool),
        })
    }

    /// Create a new GPU-accelerated state vector simulator synchronously
    pub fn new_blocking() -> Result<Self, Box<dyn std::error::Error>> {
        // Create a runtime for async operations
        let rt = tokio::runtime::Builder::new_current_thread()
            .enable_all()
            .build()?;

        // Run the async initialization in the runtime
        rt.block_on(Self::new())
    }

    /// Check if GPU acceleration is available on this system
    pub fn is_available() -> bool {
        // Try to create the simulator
        match std::panic::catch_unwind(|| {
            let rt = tokio::runtime::Builder::new_current_thread()
                .enable_all()
                .build()
                .unwrap();

            rt.block_on(async {
                let instance = wgpu::Instance::default();
                instance
                    .request_adapter(&wgpu::RequestAdapterOptions {
                        power_preference: wgpu::PowerPreference::HighPerformance,
                        force_fallback_adapter: false,
                        compatible_surface: None,
                    })
                    .await
                    .is_ok()
            })
        }) {
            Ok(result) => result,
            Err(_) => false,
        }
    }
}

impl Simulator for GpuStateVectorSimulator {
    fn run<const N: usize>(
        &mut self,
        circuit: &Circuit<N>,
    ) -> crate::error::Result<crate::simulator::SimulatorResult<N>> {
        // We'll extract gate information manually since we're using our own GateType enum

        // Skip GPU simulation for small circuits (less than 4 qubits)
        // CPU is often faster for these small circuits due to overhead
        if N < 4 {
            let cpu_sim = crate::statevector::StateVectorSimulator::new();
            // Use the CPU simulator's implementation through quantrs2_circuit::builder::Simulator trait
            let result = quantrs2_circuit::builder::Simulator::<N>::run(&cpu_sim, circuit)
                .expect("CPU simulation failed");
            return Ok(SimulatorResult {
                amplitudes: result.amplitudes().to_vec(),
                num_qubits: N,
            });
        }

        // Calculate state vector size
        let state_size = 1 << N;
        let buffer_size = (state_size * std::mem::size_of::<GpuComplex>()) as u64;

        // Create initial state |0...0⟩
        let mut initial_state = vec![
            GpuComplex {
                real: 0.0,
                imag: 0.0
            };
            state_size
        ];
        initial_state[0].real = 1.0; // Set |0...0⟩ amplitude to 1

        // Create GPU buffer for state vector
        let state_buffer = self
            .device
            .create_buffer_init(&wgpu::util::BufferInitDescriptor {
                label: Some("State Vector Buffer"),
                contents: bytemuck::cast_slice(&initial_state),
                usage: wgpu::BufferUsages::STORAGE
                    | wgpu::BufferUsages::COPY_SRC
                    | wgpu::BufferUsages::COPY_DST,
            });

        // Create a buffer to read back the results from the GPU
        let result_buffer = self.device.create_buffer(&wgpu::BufferDescriptor {
            label: Some("Result Buffer"),
            size: buffer_size,
            usage: wgpu::BufferUsages::COPY_DST | wgpu::BufferUsages::MAP_READ,
            mapped_at_creation: false,
        });

        // Process each gate in the circuit
        for gate in circuit.gates() {
            let mut encoder = self
                .device
                .create_command_encoder(&wgpu::CommandEncoderDescriptor {
                    label: Some("Gate Execution Encoder"),
                });

            // Convert the gate to our own GateType enum for GPU processing
            let gate_type = match gate.name() {
                // Single qubit gates
                "H" | "X" | "Y" | "Z" | "S" | "T" | "S†" | "T†" | "√X" | "√X†" | "RX" | "RY"
                | "RZ" => {
                    // Get the target qubit and matrix from the gate
                    let target = gate.qubits()[0];
                    let matrix = ndarray::Array2::from_shape_vec(
                        (2, 2),
                        gate.matrix().expect("Failed to get gate matrix").to_vec(),
                    )
                    .expect("Failed to convert matrix to Array2");

                    GateType::SingleQubit { target, matrix }
                }

                // Two qubit gates
                "CNOT" | "CY" | "CZ" | "CH" | "CS" | "CRX" | "CRY" | "CRZ" | "SWAP" => {
                    let qubits = gate.qubits();
                    let control = qubits[0];
                    let target = qubits[1];
                    let matrix = ndarray::Array2::from_shape_vec(
                        (4, 4),
                        gate.matrix().expect("Failed to get gate matrix").to_vec(),
                    )
                    .expect("Failed to convert matrix to Array2");

                    GateType::TwoQubit {
                        control,
                        target,
                        matrix,
                    }
                }

                _ => {
                    // For unsupported gates, use CPU fallback
                    let cpu_sim = crate::statevector::StateVectorSimulator::new();
                    let result = quantrs2_circuit::builder::Simulator::<N>::run(&cpu_sim, circuit)
                        .expect("CPU simulation failed");
                    return Ok(SimulatorResult {
                        amplitudes: result.amplitudes().to_vec(),
                        num_qubits: N,
                    });
                }
            };

            match gate_type {
                GateType::SingleQubit { target, matrix } => {
                    // Convert matrix to GPU format
                    let gpu_matrix = [
                        GpuComplex::from(matrix[(0, 0)]),
                        GpuComplex::from(matrix[(0, 1)]),
                        GpuComplex::from(matrix[(1, 0)]),
                        GpuComplex::from(matrix[(1, 1)]),
                    ];

                    // Prepare gate parameters
                    let params = SingleQubitGateParams {
                        target_qubit: target.id() as u32,
                        n_qubits: N as u32,
                        matrix: gpu_matrix,
                    };

                    // Create parameter buffer
                    let param_buffer =
                        self.device
                            .create_buffer_init(&wgpu::util::BufferInitDescriptor {
                                label: Some("Single Qubit Gate Params Buffer"),
                                contents: bytemuck::bytes_of(&params),
                                usage: wgpu::BufferUsages::UNIFORM,
                            });

                    // Create bind group
                    let bind_group = self.device.create_bind_group(&wgpu::BindGroupDescriptor {
                        label: Some("Single Qubit Gate Bind Group"),
                        layout: &self.single_qubit_pipeline.get_bind_group_layout(0),
                        entries: &[
                            wgpu::BindGroupEntry {
                                binding: 0,
                                resource: state_buffer.as_entire_binding(),
                            },
                            wgpu::BindGroupEntry {
                                binding: 1,
                                resource: param_buffer.as_entire_binding(),
                            },
                        ],
                    });

                    // Compute workgroup count (1 per 256 state vector elements)
                    let workgroup_count = ((state_size + 255) / 256) as u32;

                    // Dispatch compute shader
                    let mut compute_pass =
                        encoder.begin_compute_pass(&wgpu::ComputePassDescriptor {
                            label: Some("Single Qubit Gate Compute Pass"),
                            timestamp_writes: None,
                        });
                    compute_pass.set_pipeline(&self.single_qubit_pipeline);
                    compute_pass.set_bind_group(0, &bind_group, &[]);
                    compute_pass.dispatch_workgroups(workgroup_count, 1, 1);
                    drop(compute_pass);
                }
                GateType::TwoQubit {
                    control,
                    target,
                    matrix,
                } => {
                    // Convert matrix to GPU format (assuming a 4x4 matrix)
                    let mut gpu_matrix = [GpuComplex {
                        real: 0.0,
                        imag: 0.0,
                    }; 16];
                    for i in 0..4 {
                        for j in 0..4 {
                            gpu_matrix[i * 4 + j] = GpuComplex::from(matrix[(i, j)]);
                        }
                    }

                    // Prepare gate parameters
                    let params = TwoQubitGateParams {
                        control_qubit: control.id() as u32,
                        target_qubit: target.id() as u32,
                        n_qubits: N as u32,
                        matrix: gpu_matrix,
                    };

                    // Create parameter buffer
                    let param_buffer =
                        self.device
                            .create_buffer_init(&wgpu::util::BufferInitDescriptor {
                                label: Some("Two Qubit Gate Params Buffer"),
                                contents: bytemuck::bytes_of(&params),
                                usage: wgpu::BufferUsages::UNIFORM,
                            });

                    // Create bind group
                    let bind_group = self.device.create_bind_group(&wgpu::BindGroupDescriptor {
                        label: Some("Two Qubit Gate Bind Group"),
                        layout: &self.two_qubit_pipeline.get_bind_group_layout(0),
                        entries: &[
                            wgpu::BindGroupEntry {
                                binding: 0,
                                resource: state_buffer.as_entire_binding(),
                            },
                            wgpu::BindGroupEntry {
                                binding: 1,
                                resource: param_buffer.as_entire_binding(),
                            },
                        ],
                    });

                    // Compute workgroup count (1 per 256 state vector elements)
                    let workgroup_count = ((state_size + 255) / 256) as u32;

                    // Dispatch compute shader
                    let mut compute_pass =
                        encoder.begin_compute_pass(&wgpu::ComputePassDescriptor {
                            label: Some("Two Qubit Gate Compute Pass"),
                            timestamp_writes: None,
                        });
                    compute_pass.set_pipeline(&self.two_qubit_pipeline);
                    compute_pass.set_bind_group(0, &bind_group, &[]);
                    compute_pass.dispatch_workgroups(workgroup_count, 1, 1);
                    drop(compute_pass);
                }
            }

            // Submit command encoder to GPU
            self.queue.submit(std::iter::once(encoder.finish()));
        }

        // After all gates, copy the state vector back from the GPU
        let mut encoder = self
            .device
            .create_command_encoder(&wgpu::CommandEncoderDescriptor {
                label: Some("Result Copy Encoder"),
            });

        encoder.copy_buffer_to_buffer(&state_buffer, 0, &result_buffer, 0, buffer_size);
        self.queue.submit(std::iter::once(encoder.finish()));

        // Map the buffer to read the results
        let buffer_slice = result_buffer.slice(..);
        let (tx, rx) = std::sync::mpsc::channel();

        buffer_slice.map_async(wgpu::MapMode::Read, move |result| {
            tx.send(result).unwrap();
        });

        // Wait for the buffer to be mapped
        let _ = self.device.poll(wgpu::MaintainBase::Wait);
        if rx.recv().unwrap().is_err() {
            panic!("Failed to map buffer for reading");
        }

        // Read the data
        let data = buffer_slice.get_mapped_range();
        let result_data: Vec<GpuComplex> = bytemuck::cast_slice(&data).to_vec();
        drop(data); // Unmap the buffer

        // Convert GPU results to complex amplitudes
        let amplitudes: Vec<Complex64> = result_data.into_iter().map(|c| c.into()).collect();

        // Return simulation result
        Ok(SimulatorResult {
            amplitudes,
            num_qubits: N,
        })
    }
}

// This module now uses the WGSL shaders in the "shaders" directory:
// - shaders/single_qubit_gate.wgsl: Handles single-qubit gate operations
// - shaders/two_qubit_gate.wgsl: Handles two-qubit gate operations
