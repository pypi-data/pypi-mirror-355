# 🚀 cuMatfuse

cuMatfuse is a minimal CUDA library for fused matrix multiplication with ReLU activation: C = ReLU(A × B)

## ✨ Features

- CUDA-accelerated fused GEMM with ReLU
- Lightweight and portable
- Easy to extend and integrate into ML inference pipelines

## 🛠 Requirements

- NVIDIA GPU (Compute Capability 7.0+)
- CUDA Toolkit ≥ 11.8
- CMake ≥ 3.18
- Linux or Windows

## 🔧 Build Instructions

```bash
git clone https://github.com/divakar-yadav/cuMatfuse.git
cd cuMatfuse
mkdir build && cd build
cmake ..
make
```

## 🧪 Run Example

```bash
./cuMatfuse_demo
```

Expected Output:
```
C = ReLU(A × B):
22 28
49 64
76 100
6 8
```

## 📦 License

MIT
