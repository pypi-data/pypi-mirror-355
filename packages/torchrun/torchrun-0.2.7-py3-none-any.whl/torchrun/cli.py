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
def deploy(
    mode: str = typer.Option(
        None,
        "--mode",
        "-m",
        prompt="Select deploy source: [l]ocal / [s]pace / [m]odel",
        help="Choose deployment type: l for local, s for space, m for model",
    )
):
    mode = mode.lower().strip()

    if mode == "l":
        path = typer.prompt("Path to requirements.txt", default="requirements.txt")
        deploy_pod_for_requirements(path)

    elif mode == "s":
        raw = typer.prompt("Enter HF Space URL or ID (e.g. black-forest-labs/FLUX.1-dev)")
        space_url = normalize_space_url(raw)
        deploy_hf_space(space_url)

    elif mode == "m":
        raw = typer.prompt("Enter HF Model URL or ID (e.g. EleutherAI/gpt-j-6B)")
        model_id = normalize_model_id(raw)
        deploy_hf_model(model_id)

    else:
        typer.echo("Invalid mode. Use -m l (local), -m s (space), or -m m (model).")

if __name__ == "__main__":
    app()