#include <iostream>
#include <vector>
#include <cuda_runtime.h>
#include "cuMatfuse.h"

int main() {
    const int M = 4, K = 3, N = 2;
    std::vector<float> h_A = {1,2,3, 4,5,6, 7,8,9, 1,0,1};
    std::vector<float> h_B = {1,2, 3,4, 5,6};
    std::vector<float> h_C(M * N);

    float *d_A, *d_B, *d_C;
    cudaMalloc(&d_A, M*K*sizeof(float));
    cudaMalloc(&d_B, K*N*sizeof(float));
    cudaMalloc(&d_C, M*N*sizeof(float));

    cudaMemcpy(d_A, h_A.data(), M*K*sizeof(float), cudaMemcpyHostToDevice);
    cudaMemcpy(d_B, h_B.data(), K*N*sizeof(float), cudaMemcpyHostToDevice);

    cuMatfuse_gemm_relu(d_A, d_B, d_C, M, N, K);

    cudaMemcpy(h_C.data(), d_C, M*N*sizeof(float), cudaMemcpyDeviceToHost);

    std::cout << "C = ReLU(A × B):\n";
    for (int i = 0; i < M * N; ++i) {
        std::cout << h_C[i] << (i % N == N-1 ? "\n" : " ");
    }

    cudaFree(d_A); cudaFree(d_B); cudaFree(d_C);
    return 0;
}
