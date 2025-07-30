import numpy as np
import cuMatfuse  # Import the built module

M, K, N = 4, 3, 2
A = np.array([[1,2,3],[4,5,6],[7,8,9],[1,0,1]], dtype=np.float32)
B = np.array([[1,2],[3,4],[5,6]], dtype=np.float32)
C = np.zeros((M, N), dtype=np.float32)

cuMatfuse.gemm_relu(A, B, C, M, N, K)

print("C = ReLU(A × B):")
print(C)
