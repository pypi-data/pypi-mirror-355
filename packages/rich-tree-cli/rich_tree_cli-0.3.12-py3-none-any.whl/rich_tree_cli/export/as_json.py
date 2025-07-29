from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..main import RichTreeCLI


def build_json(cli: "RichTreeCLI", path: Path) -> dict:
    """Build a dictionary representation of the directory structure."""

    if path == cli.root:
        tree_data: dict[str, str] = build_tree_dict(cli, path)
        return {
            "metadata": {
                "total_dirs": cli.dir_count,
                "total_files": cli.file_count,
                "root_path": str(path),
            },
            "tree": tree_data,
        }
    else:
        return build_tree_dict(cli, path)


def build_tree_dict(cli: "RichTreeCLI", path: Path) -> dict[str, str]:
    """Build just the tree part without metadata wrapper."""
    result = {"name": path.name, "type": "directory", "children": []}
    for item in cli.get_items(path):
        if cli.ignore_handler.should_ignore(item):
            continue
        if item.is_dir():
            result["children"].append(build_tree_dict(cli=cli, path=item))
        else:
            try:
                file_info = {
                    "name": item.name,
                    "type": "file",
                    "size": item.stat().st_size,
                    "lines": len(item.read_text(encoding="utf-8").splitlines()),
                }
            except UnicodeDecodeError:
                file_info = {
                    "name": item.name,
                    "type": "file",
                    "size": item.stat().st_size,
                    "lines": 0,  # Binary file
                }
            result["children"].append(file_info)
    return result
