from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext

setup(
    name="cuMatfuse",
    version="0.1.0",
    author="Your Name",
    author_email="your@email.com",
    description="Fused CUDA MatMul + ReLU kernel using PyBind11",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=["cuMatfuse"],
    package_dir={"cuMatfuse": "cuMatfuse"},
    zip_safe=False,
)
