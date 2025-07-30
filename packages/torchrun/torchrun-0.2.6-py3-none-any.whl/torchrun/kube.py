import sys
import time
import yaml
from .compat import get_rocm_image_for_torch_version
import os
import subprocess
from urllib.parse import urlparse
import typer

def safe_clone(url: str, target_dir: str):
    if os.path.exists(target_dir):
        typer.echo(f"❌ Target directory '{target_dir}' already exists. Remove it or choose a different one.")
        raise typer.Exit(code=1)
    typer.echo(f"📥 Cloning into {target_dir}...")
    subprocess.run(["git", "clone", url, target_dir], check=True)

def parse_space_type(space_dir: str) -> str:
    space_yaml_path = os.path.join(space_dir, "space.yaml")
    if os.path.exists(space_yaml_path):
        with open(space_yaml_path) as f:
            config = yaml.safe_load(f)
        space_type = config.get("sdk", "").lower()
        typer.echo(f"[torchrun] Detected space type: {space_type}")
        return space_type
    return "unknown"

def deploy_hf_space(space_url: str):
    if not space_url.startswith("https://"):
        space_url = f"https://{space_url}"

    parsed = urlparse(space_url)
    if "/spaces/" not in parsed.path:
        raise typer.BadParameter("Not a valid Hugging Face Space URL.")

    org_repo = parsed.path.split("/spaces/")[-1]
    repo_url = f"https://huggingface.co/spaces/{org_repo}"
    local_dir = f"./hf_space_{org_repo.replace('/', '_')}"

    safe_clone(repo_url, local_dir)
    typer.echo(f"✅ Cloned Hugging Face Space to {local_dir}")

    parse_space_type(local_dir)
    deploy_pod_for_requirements(os.path.join(local_dir, "requirements.txt"), local_dir)

def deploy_hf_model(model_id: str):
    if "huggingface.co" in model_id:
        model_id = model_id.split("huggingface.co/")[-1]

    repo_url = f"https://huggingface.co/{model_id}"
    local_dir = f"./hf_model_{model_id.replace('/', '_')}"

    safe_clone(repo_url, local_dir)
    typer.echo(f"✅ Cloned Hugging Face Model to {local_dir}")

    req_path = os.path.join(local_dir, "requirements.txt")
    if not os.path.exists(req_path):
        typer.echo("[torchrun] No requirements.txt found. Generating minimal app.")
        generate_default_model_app(local_dir, model_id)

    deploy_pod_for_requirements(req_path, local_dir)

def get_torch_version_from_requirements(path: str) -> str:
    print(f"[torchrun] Reading torch version from {path}")
    if os.path.isdir(path):
        path = os.path.join(path, "requirements.txt")
        if not os.path.isfile(path):
            print("[torchrun] No requirements.txt found in directory. Using default torch version: 2.2.2")
            return "2.2.2"
    if not os.path.exists(path):
        print("[torchrun] File does not exist. Using default torch version: 2.2.2")
        return "2.2.2"
    with open(path) as f:
        for line in f:
            if line.startswith("torch"):
                parts = line.strip().split("==")
                if len(parts) == 2:
                    print(f"[torchrun] Found torch version: {parts[1]}")
                    return parts[1]
    print("[torchrun] No torch version specified. Using default: 2.2.2")
    return "2.2.2"

def generate_default_model_app(path: str, model_id: str):
    dockerfile = f"""FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install torch transformers
CMD [\"python\", \"main.py\"]
"""
    main_py = f"""from transformers import pipeline
import os

model = pipeline(\"text-generation\", model=\"{model_id}\")
out = model(\"Hello world\", max_length=30)
print(\"Model output:\", out)
"""
    with open(os.path.join(path, "Dockerfile"), "w") as f:
        f.write(dockerfile)

    with open(os.path.join(path, "main.py"), "w") as f:
        f.write(main_py)

    with open(os.path.join(path, "requirements.txt"), "w") as f:
        f.write("torch\ntransformers\n")

def deploy_pod_for_requirements(requirements_path: str, copy_dir: str = "."):
    print(f"[torchrun] Deploying pod for requirements: {requirements_path}")

    try:
        torch_version = get_torch_version_from_requirements(requirements_path)
    except Exception as e:
        print(f"[torchrun][error] Failed to get torch version: {e}")
        sys.exit(1)

    image = get_rocm_image_for_torch_version(torch_version)
    pod_name = f"torchrun-{torch_version.replace('.', '-')}-pod"
    yaml_path = "torchrun_pod.yaml"

    pod_spec = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": pod_name,
            "namespace": "default"
        },
        "spec": {
            "volumes": [
                {"name": "kfd", "hostPath": {"path": "/dev/kfd", "type": "CharDevice"}},
                {"name": "dri", "hostPath": {"path": "/dev/dri", "type": "Directory"}},
                {"name": "workspace", "emptyDir": {}}
            ],
            "containers": [
                {
                    "name": "torch-container",
                    "image": image,
                    "command": ["/bin/bash", "-c", "sleep infinity"],
                    "stdin": True,
                    "tty": True,
                    "volumeMounts": [
                        {"name": "kfd", "mountPath": "/dev/kfd"},
                        {"name": "dri", "mountPath": "/dev/dri"},
                        {"name": "workspace", "mountPath": "/workspace"}
                    ],
                    "ports": [
                        {"containerPort": 7860, "name": "gradio"},
                        {"containerPort": 8000, "name": "fastapi"}
                    ],
                    "securityContext": {
                        "privileged": True,
                        "runAsUser": 0,
                        "runAsGroup": 0,
                        "capabilities": {"add": ["SYS_PTRACE"]}
                    }
                }
            ],
            "restartPolicy": "Always",
            "imagePullSecrets": [
                {"name": "gcp-docker-virtual"},
                {"name": "gcr-json-key"}
            ],
            "tolerations": [
                {
                    "key": "node.kubernetes.io/not-ready",
                    "operator": "Exists",
                    "effect": "NoExecute",
                    "tolerationSeconds": 300
                },
                {
                    "key": "node.kubernetes.io/unreachable",
                    "operator": "Exists",
                    "effect": "NoExecute",
                    "tolerationSeconds": 300
                }
            ]
        }
    }

    print(f"[torchrun] Writing pod spec to {yaml_path}")
    with open(yaml_path, "w") as f:
        pyyaml.safe_dump(pod_spec, f)

    print(f"[torchrun] Deleting existing pod (if any): {pod_name}")
    subprocess.run(["kubectl", "delete", "pod", pod_name], capture_output=True)

    print(f"[torchrun] Applying pod spec with kubectl...")
    try:
        result = subprocess.run(["kubectl", "apply", "-f", yaml_path], capture_output=True, text=True, check=True)
        print(f"[torchrun][kubectl apply] stdout:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"[torchrun][error] Failed to apply pod spec:\n{e.stderr}")
        sys.exit(e.returncode)

    print(f"[torchrun] Waiting for pod to reach Running state...")
    while True:
        result = subprocess.run(
            ["kubectl", "get", "pod", pod_name, "-o", "jsonpath={.status.phase}"],
            capture_output=True, text=True
        )
        if result.stdout.strip() == "Running":
            break
        elif "Error" in result.stdout or "Failed" in result.stdout:
            print(f"[torchrun][error] Pod entered failure state: {result.stdout.strip()}")
            sys.exit(1)
        time.sleep(1)

    print(f"[torchrun] Copying {copy_dir} into /workspace ...")
    try:
        result = subprocess.run(["kubectl", "cp", copy_dir, f"{pod_name}:/workspace", "-c", "torch-container"],
                                capture_output=True, text=True, check=True)
        print(f"[torchrun][kubectl cp] stdout:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"[torchrun][error] Failed to copy files into pod:\n{e.stderr}")
        sys.exit(e.returncode)

    print(f"[torchrun] Installing Python requirements inside pod ...")
    try:
        result = subprocess.run(["kubectl", "exec", "-it", pod_name, "-c", "torch-container",
                                 "--", "pip", "install", "-r", "/workspace/requirements.txt"],
                                check=True)
    except subprocess.CalledProcessError as e:
        print(f"[torchrun][error] pip install failed:\n{e.stderr}")
        sys.exit(e.returncode)

    print(f"[torchrun] Pod {pod_name} is ready. Run: kubectl exec -it {pod_name} -- bash")