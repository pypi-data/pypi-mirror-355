def get_rocm_image_for_torch_version(torch_version: str) -> str:
    compatibility = {
        "2.6.0": "rocm/pytorch:rocm6.4.1_ubuntu24.04_py3.12_pytorch_release_2.6.0",
        "2.5.1": "rocm/pytorch:rocm6.4.1_ubuntu24.04_py3.12_pytorch_release_2.5.1",
        "2.4.1": "rocm/pytorch:rocm6.4.1_ubuntu24.04_py3.12_pytorch_release_2.4.1",
        "2.4.0": "rocm/pytorch:rocm6.3.4_ubuntu24.04_py3.12_pytorch_release_2.4.0",
        "2.3.0": "rocm/pytorch:rocm6.4.1_ubuntu24.04_py3.12_pytorch_release_2.3.0",
        "2.2.1": "rocm/pytorch:rocm6.3.3_ubuntu22.04_py3.10_pytorch_release_2.2.1",
        "2.1.2": "rocm/pytorch:rocm6.2.2_ubuntu22.04_py3.10_pytorch_release_2.1.2",
        "2.1.1": "rocm/pytorch:rocm6.0_ubuntu20.04_py3.9_pytorch_2.1.1",
        "1.13.1": "rocm/pytorch:rocm6.3.3_ubuntu22.04_py3.9_pytorch_release_1.13.1",
        "1.12.1": "rocm/pytorch:rocm5.7_ubuntu20.04_py3.9_pytorch_1.12.1",
        "1.11.0": "rocm/pytorch:rocm5.5_ubuntu20.04_py3.8_pytorch_1.11.0"
    }
    return compatibility.get(torch_version, "rocm/pytorch:latest")

