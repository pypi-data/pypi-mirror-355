from setuptools import setup, find_packages

setup(
    name="torchrun",
    version="0.2.6",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "kubernetes",
        "typer[all]",
        "pyyaml",
        "transformers",
        "torch",
        "fastapi",
        "uvicorn",
    ],
    entry_points={
        "console_scripts": [
            "torchrun = torchrun.cli:app",
        ],
    },
    author="Ashish T",
    description="Drop-in ROCm-native CLI for PyTorch + Kubernetes inference",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/torchrun",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)