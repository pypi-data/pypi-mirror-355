import json
from pathlib import Path

from typer.testing import CliRunner

from cvannotate import convert
from cvannotate.cli import app

DATA = Path(__file__).parent / "data"


def test_yolo_to_voc(tmp_path):
    ann = convert.read_annotation(DATA / "sample.txt", "yolo", width=640, height=480)[0]
    out_dir = tmp_path
    convert.write_annotation([ann], out_dir, "voc", ["person"])
    xml_file = out_dir / "sample.xml"
    assert xml_file.exists()
    ann2 = convert.read_annotation(xml_file, "voc")[0]
    assert ann2.boxes[0].xmin == 240
    assert ann2.boxes[0].ymax == 300


def test_cli(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "convert",
            "-i",
            str(DATA / "sample.txt"),
            "-o",
            str(tmp_path),
            "--from-format",
            "yolo",
            "-f",
            "voc",
            "-w",
            "640",
            "--height",
            "480",
            "-c",
            str(DATA / "classes.txt"),
        ],
    )
    assert result.exit_code == 0
    assert (tmp_path / "sample.xml").exists()
