#include "cuMatfuse.h"
#include <cuda_runtime.h>
#include <iostream>

__global__ void gemm_relu_kernel(const float* A, const float* B, float* C, int M, int N, int K) {
    int row = blockIdx.y * blockDim.y + threadIdx.y;
    int col = blockIdx.x * blockDim.x + threadIdx.x;
    if (row < M && col < N) {
        float val = 0.0f;
        for (int i = 0; i < K; ++i)
            val += A[row * K + i] * B[i * N + col];
        C[row * N + col] = val > 0.0f ? val : 0.0f;
    }
}

void cuMatfuse_gemm_relu(const float* d_A, const float* d_B, float* d_C, int M, int N, int K) {
    dim3 threads(16, 16);
    dim3 blocks((N + 15) / 16, (M + 15) / 16);
    gemm_relu_kernel<<<blocks, threads>>>(d_A, d_B, d_C, M, N, K);
    cudaDeviceSynchronize();
}
