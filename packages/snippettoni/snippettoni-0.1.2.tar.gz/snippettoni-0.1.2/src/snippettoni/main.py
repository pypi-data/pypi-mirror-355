import json
import sys
from pathlib import Path
from typing import Annotated

import typer
import yaml

from snippettoni.injector import inject_code_samples
from snippettoni.renderer import SnippetRenderer

app = typer.Typer()


@app.command()
def main(
    spec_path: Path = typer.Argument(..., help="Path to OpenAPI spec YAML or JSON file."),
    base_url: Annotated[
        str | None,
        typer.Option(help="Base URL for code examples."),
    ] = None,
    lang: Annotated[
        list[str] | None,
        typer.Option(
            help=(
                "Languages to generate (e.g. --lang python --lang curl)."
                "Default is all templates in directory."
            ),
        ),
    ] = None,
    template: Annotated[
        list[str] | None,
        typer.Option(help="Override or add templates per language, e.g. --template lang:path"),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option(help="Optional output file path. Defaults to stdout in same format as input."),
    ] = None,
):
    # Determine template paths
    external_templates: dict[str, str] = {}
    if template:
        for entry in template:
            try:
                lang_key, path_val = entry.split(":", 1)
                external_templates[lang_key] = path_val
            except ValueError:
                typer.echo(f"Invalid --template value: {entry}", err=True)
                raise typer.Exit(code=1)

    renderer = SnippetRenderer(lang, external_templates)

    updated_spec = inject_code_samples(spec_path, renderer, base_url=base_url)
    if output:
        with open(output, "w") as f:
            if output.suffix in [".yaml", ".yml"]:
                yaml.dump(updated_spec, f, sort_keys=False)
            else:
                json.dump(updated_spec, f, indent=2)
        typer.echo(f"✅ Updated OpenAPI spec written to: {output}")
    else:
        if spec_path.suffix in [".yaml", ".yml"]:
            yaml.dump(updated_spec, sys.stdout, sort_keys=False)
        else:
            json.dump(updated_spec, sys.stdout, indent=2)


if __name__ == "__main__":
    app()
