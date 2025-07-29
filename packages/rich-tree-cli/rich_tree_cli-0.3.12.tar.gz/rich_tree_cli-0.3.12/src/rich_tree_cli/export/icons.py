"""Helper functions for managing SVG and icon mappings."""

from enum import Enum, auto
from pathlib import Path
from typing import ClassVar

from ._common import ICON_DIR


class IconMode(Enum):
    """Enum for icon modes."""

    SVG_ICONS = auto()
    GLYPHS_ICONS = auto()
    EMOJI_ICONS = auto()
    PLAIN_ICONS = auto()


class BaseIcons:

    FILE = ""
    FOLDER = ""

    @classmethod
    def get_icon(cls, name: str, is_dir: bool = False) -> str:
        """Get icon based on file type."""
        if hasattr(cls, name.upper()):
            return getattr(cls, name.upper())
        return cls.FILE if not is_dir else cls.FOLDER


class GlyphsIcons(BaseIcons):
    """Class for terminal icons."""

    FILE: str = "\uf15b"
    FOLDER: str = "\uf07b"
    PYTHON: str = "\ue73c"
    GIT: str = "\ue702"
    GIT_FOLDER: str = "\ue5fb"
    VSCODE: str = "\ue8da"
    HTML: str = "\ue736"
    SETTINGS: str = "\ueb51"
    NIX: str = "\uf313"
    SVG: str = "\uf03e"
    MARKDOWN: str = "\ueb1d"
    TOML: str = "\ue6b2"
    DB: str = "\ue706"


class EmojiIcons(BaseIcons):
    """Class for emoji icons."""

    FILE: str = "📄"
    FOLDER: str = "📁"
    PYTHON: str = "🐍"
    GIT: str = "🗃️"
    GIT_FOLDER: str = "🗂️"
    VSCODE: str = "💻"
    HTML: str = "🌐"
    ENV: str = "🌱"
    SETTINGS: str = "⚙️"
    NIX: str = "❄️"
    SVG: str = "🖼️"
    DB: str = "🛢️"


class SVGIcons(BaseIcons): ...


def _load_svg_icon(path: Path) -> str:
    """Return the contents of an SVG file."""
    return path.read_text(encoding="utf-8").strip()


def get_svg_icons() -> SVGIcons:
    """Generate a namespace with SVG icons loaded from the icon directory."""
    svg_files = SVGIcons()
    for file in ICON_DIR.glob("*.svg"):
        setattr(SVGIcons, file.stem.upper(), _load_svg_icon(file))
    return svg_files


class IconManager:

    EXT_TO_NAME: ClassVar[dict[str, str]] = {
        ".py": "PYTHON",
        ".html": "HTML",
        ".jinja2": "HTML",
        ".json": "JSON",
        ".md": "MARKDOWN",
        ".css": "CSS",
        ".svg": "SVG",
        ".cfg": "SETTINGS",
        ".txt": "TXT",
        ".nix": "NIX",
        ".js": "JAVASCRIPT",
        ".log": "LOG",
        ".toml": "TOML",
        ".db": "DB",
    }

    def __repr__(self) -> str:
        """Return a string representation of the IconManager."""
        return f"IconManager(mode={self.mode}, fallback_mode={self.fallback_mode})"

    def __init__(self, mode: IconMode = IconMode.SVG_ICONS, fallback_mode: IconMode = IconMode.EMOJI_ICONS) -> None:
        """Initialize the IconManager with a specific icon mode."""
        self.mode: IconMode = mode
        self.fallback_mode: IconMode = fallback_mode
        self.svg_icons: SVGIcons = get_svg_icons()

        self.current_icon: SVGIcons | type[GlyphsIcons] | type[EmojiIcons] = (
            self.svg_icons
            if self.mode == IconMode.SVG_ICONS
            else GlyphsIcons if self.mode == IconMode.GLYPHS_ICONS else EmojiIcons
        )

    def set_mode(self, mode: IconMode) -> None:
        """Set the icon mode."""
        self.mode = mode

    @property
    def file_default(self) -> str:
        """Return the default icon for files based on the current mode."""
        return self.current_icon.FILE

    @property
    def folder_default(self) -> str:
        """Return the default icon for folders based on the current mode."""
        return self.current_icon.FOLDER

    def handle_dir(self, name: str) -> str:
        if name == "tests":
            return "TESTS"
        if name.startswith(".git"):
            return "GIT"
        if name == "db" or name == "database":
            return "DB"
        if name == "src":
            return "SRC"
        if name == ".vscode":
            return "VSCODE"
        if name == ".env":
            return "ENV"
        if name == "html":
            return "HTML"
        return self.folder_default

    def get(self, path: Path) -> str:
        name: str = path.name.lower()
        ext: str = path.suffix.lower()
        no_ext: bool = not ext
        is_dir: bool = path.is_dir()
        result: str = self.file_default

        if is_dir:
            result = self.handle_dir(name)

        if no_ext and not is_dir:
            if name.startswith(".git"):
                result = "GIT"
            if name == ".python-version":
                result = "PYTHON"

        if ext in self.EXT_TO_NAME and not is_dir:
            result = f"{self.EXT_TO_NAME[ext]}"

        match self.mode:
            case IconMode.GLYPHS_ICONS | IconMode.EMOJI_ICONS | IconMode.SVG_ICONS:
                return self.current_icon.get_icon(result, is_dir)
        return result
