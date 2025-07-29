import tomli_w as toml


def build_toml(json_data: dict) -> str:
    """Convert JSON data to TOML format."""
    toml_str = toml.dumps(json_data)
    return toml_str
