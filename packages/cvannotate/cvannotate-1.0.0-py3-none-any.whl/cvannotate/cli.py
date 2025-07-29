import json
from pathlib import Path
from typing import Optional

import typer

from .convert import read_annotation, write_annotation

app = typer.Typer(add_completion=False)


@app.callback()
def main_callback():
    """cvannotate command line interface."""
    pass


def load_classes(path_or_list: str):
    if Path(path_or_list).exists():
        return [
            c.strip() for c in Path(path_or_list).read_text().splitlines() if c.strip()
        ]
    return [c.strip() for c in path_or_list.split(",") if c.strip()]


@app.command()
def convert(
    input: str = typer.Option(..., "-i", help="Input annotation file"),
    output: str = typer.Option(..., "-o", help="Output directory"),
    from_format: str = typer.Option(..., "--from-format", help="Input format"),
    to_format: str = typer.Option(..., "-f", "--to-format", help="Output format"),
    width: Optional[int] = typer.Option(None, "-w", help="Image width for YOLO"),
    height: Optional[int] = typer.Option(
        None, "--height", help="Image height for YOLO"
    ),
    classes: str = typer.Option(
        ..., "-c", help="Path to classes file or comma separated list"
    ),
    verbose: bool = typer.Option(False, "--verbose", help="Verbose output"),
    force: bool = typer.Option(False, "--force", help="Overwrite output files"),
):
    input_path = Path(input)
    out_dir = Path(output)
    class_map = load_classes(classes)
    anns = read_annotation(input_path, from_format, width=width, height=height)
    for ann in anns:
        out_file = out_dir / (
            ann.filename + {"yolo": ".txt", "voc": ".xml"}.get(to_format, "")
        )
        if out_file.exists() and not force:
            skipped_path = out_dir / "skipped.txt"
            skipped_path.parent.mkdir(parents=True, exist_ok=True)
            with skipped_path.open("a") as f:
                f.write(str(out_file) + "\n")
            if verbose:
                typer.echo(f"Skipping {out_file}")
            continue
    write_annotation(anns, out_dir, to_format, class_map)
    if verbose:
        typer.echo("Conversion complete")


def main():
    app()


if __name__ == "__main__":
    main()
