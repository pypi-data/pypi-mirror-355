from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rich_tree_cli.main import RichTreeCLI
    from rich_tree_cli.output_manager import OutputManager


def output_to_file(output_manager: "OutputManager", cli: "RichTreeCLI"):
    replace_path = cli.replace_path
    if not replace_path or not replace_path.exists():
        output_manager.error(f"Error: The specified replace path '{replace_path}' does not exist.")
        return
    # check if it is either .md or .html file
    if replace_path.suffix in {".md", ".html"}:
        markdown_content = replace_path.read_text(encoding="utf-8")
        new_structure = cli.tree.export_to_markdown()
        updated_content = update_directory_structure(markdown_content, new_structure)
        replace_path.write_text(updated_content, encoding="utf-8")
        output_manager.success(f"Content replaced successfully in {replace_path}.")


def update_directory_structure(markdown_content, new_structure):
    start_tag = "<!-- rTree -->"
    end_tag = "<!-- /rTree -->"
    tag_length = len(start_tag)

    start = markdown_content.find(start_tag)
    end = markdown_content.find(end_tag)

    if start != -1 and end != -1:
        before = markdown_content[: start + tag_length]
        after = markdown_content[end:]

        return f"{before}\n\n{new_structure}\n\n{after}"

    return markdown_content
