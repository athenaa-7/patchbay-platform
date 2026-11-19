"""Patchbay CLI."""
import json
from pathlib import Path

import typer

from patchbay_core.exceptions import PatchbayError
from patchbay_core.manager import PluginManager

app = typer.Typer(help="Patchbay: connect, extend and create.")
plugin_app = typer.Typer(help="Manage local plugins.")
app.add_typer(plugin_app, name="plugin")


def manager() -> PluginManager:
    return PluginManager(Path("plugins/examples"))


@app.callback()
def main(
    version: bool = typer.Option(False, "--version", help="Show the Patchbay version and exit."),
) -> None:
    if version:
        typer.echo("Patchbay 0.1.0")
        raise typer.Exit()


@plugin_app.command("list")
def list_plugins() -> None:
    """List valid plugins in the local examples directory."""
    items = manager().list_plugins()
    for item in items:
        typer.echo(f"{item['id']}  {item['path']}")
    if not items:
        typer.echo("No valid plugins found.")


@plugin_app.command()
def validate(path: Path = typer.Argument(..., exists=True, file_okay=False)) -> None:
    """Validate a plugin directory."""
    from patchbay_core.validator import load_manifest

    try:
        manifest = load_manifest(path)
        typer.echo(f"Valid: {manifest.id} ({manifest.version})")
    except PatchbayError as exc:
        typer.echo(f"Invalid: {exc}", err=True)
        raise typer.Exit(code=1) from exc


@plugin_app.command()
def inspect(plugin_id: str) -> None:
    """Display a plugin's manifest."""
    try:
        _, manifest = manager().inspect(plugin_id)
        typer.echo(manifest.model_dump_json(indent=2, by_alias=True))
    except PatchbayError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@plugin_app.command()
def run(plugin_id: str, input_json: str = typer.Option("{}", "--input")) -> None:
    """Execute a trusted local plugin."""
    try:
        payload = json.loads(input_json)
        if not isinstance(payload, dict):
            raise ValueError("--input must decode to a JSON object")
        result = manager().run(plugin_id, payload)
        typer.echo(
            json.dumps(
                {
                    "plugin_id": plugin_id,
                    "status": result.status,
                    "data": result.data,
                    "error": result.error,
                },
                indent=2,
            )
        )
    except (PatchbayError, ValueError, json.JSONDecodeError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
