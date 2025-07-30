import typer
from .kube import deploy_pod_for_requirements, deploy_hf_space, deploy_hf_model

app = typer.Typer()

def normalize_space_url(raw: str) -> str:
    if "huggingface.co" in raw:
        if "/spaces/" in raw:
            return raw.strip()
        raise typer.BadParameter("That appears to be a model URL. Use `hf_model` instead.")
    if "/" in raw:
        return f"https://huggingface.co/spaces/{raw.strip()}"
    raise typer.BadParameter("Invalid space format.")

def normalize_model_id(raw: str) -> str:
    if "huggingface.co" in raw:
        return raw.strip().split("huggingface.co/")[-1]
    return raw.strip()


@app.command()
def deploy():
    choice = typer.prompt("Deploy from [local/hf_space/hf_model]").strip().lower()

    if choice == "local":
        path = typer.prompt("Path to requirements.txt", default="requirements.txt")
        deploy_pod_for_requirements(path)

    elif choice == "hf_space":
        raw = typer.prompt("Enter HF Space URL or space ID (e.g. black-forest-labs/FLUX.1-dev)")
        space_url = normalize_space_url(raw)
        deploy_hf_space(space_url)

    elif choice == "hf_model":
        raw = typer.prompt("Enter HF Model URL or model ID (e.g. EleutherAI/gpt-j-6B)")
        model_id = normalize_model_id(raw)
        deploy_hf_model(model_id)

    else:
        typer.echo("Invalid option. Choose: local, hf_space, or hf_model.")

if __name__ == "__main__":
    app()