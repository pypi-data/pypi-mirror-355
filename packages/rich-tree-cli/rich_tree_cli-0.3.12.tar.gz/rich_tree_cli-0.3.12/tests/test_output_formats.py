import json
from pathlib import Path

from rich_tree_cli import OutputManager, RichTreeCLI

OUTPUT_FORMATS = ["text", "markdown", "html", "json", "svg"]


def test_output_formats(tmp_path: Path) -> None:
    output_dir = Path(__file__).parent / "output"
    output_base = output_dir / "test_output"
    try:
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "file.txt").write_text("content")
        (tmp_path / "root.txt").write_text("root")

        cli = RichTreeCLI(
            directory=tmp_path,
            output=output_base,
            output_format=OUTPUT_FORMATS,
            disable_color=True,
            no_console=True,
            metadata="all",
        )
        manager = OutputManager(disable_color=True)
        manager.set_cli(cli)
        result = cli.run()
        manager.output(result, OUTPUT_FORMATS, output_base)

        ext_map = {
            "text": ".txt",
            "markdown": ".md",
            "html": ".html",
            "json": ".json",
            "svg": ".svg",
        }
        for fmt, ext in ext_map.items():
            output_file = output_base.with_suffix(ext)
            assert output_file.exists()
            assert output_file.stat().st_size > 0

        json_data = json.loads(output_base.with_suffix(".json").read_text(encoding="utf-8"))
        assert "tree" in json_data

    finally:
        for subdir in output_dir.iterdir():
            if subdir.is_dir():
                for file in subdir.iterdir():
                    file.unlink(missing_ok=True)
                subdir.rmdir()

        for fmt in ["txt", "md", "html", "svg", "json"]:
            output_file = output_base.with_suffix(f".{fmt}")
            output_file.unlink(missing_ok=True)
