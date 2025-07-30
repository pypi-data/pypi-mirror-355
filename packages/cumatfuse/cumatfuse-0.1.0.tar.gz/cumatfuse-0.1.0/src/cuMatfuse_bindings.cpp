#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include "cuMatfuse.h"

namespace py = pybind11;

void cuMatfuse_wrapper(py::array_t<float> A, py::array_t<float> B, py::array_t<float> C, int M, int N, int K) {
    auto bufA = A.request(), bufB = B.request(), bufC = C.request();
    cuMatfuse_gemm_relu(static_cast<float*>(bufA.ptr), static_cast<float*>(bufB.ptr), static_cast<float*>(bufC.ptr), M, N, K);
}

PYBIND11_MODULE(cuMatfuse, m) {
    m.def("gemm_relu", &cuMatfuse_wrapper, "Fused GEMM + ReLU kernel",
          py::arg("A"), py::arg("B"), py::arg("C"),
          py::arg("M"), py::arg("N"), py::arg("K"));
}
