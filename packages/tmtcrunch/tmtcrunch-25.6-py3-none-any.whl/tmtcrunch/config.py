"""TMTCrunch defaults and settings functions."""

__all__ = [
    "load_config",
    "load_default_config",
    "load_phospho_config",
    "format_settings",
]


import os.path
from importlib.resources import files

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


def load_config(fpath: str) -> dict:
    """
    Load configuration from a file.

    :param fpath: Path to config file.
    :return: settings.
    """
    with open(fpath, "rb") as f:
        settings = tomllib.load(f)
    return settings


def load_default_config() -> dict:
    """
    Load default configuration.

    :return: settings.
    """
    config_file = files("tmtcrunch.conf").joinpath("default.toml")
    return load_config(config_file)


def load_phospho_config() -> dict:
    """
    Load default configuration for phospho-proteomics.

    :return: settings.
    """
    config_file = files("tmtcrunch.conf").joinpath("phospho.toml")
    return load_config(config_file)


def format_settings(settings: dict, pretty=True) -> str:
    """
    Return formatted representation of `settings`.

    :param settings: TMTCrunch settings.
    :param pretty: If True, add header and footer.
    :return: Formatted string.
    """
    header = "====  settings  ===="
    footer = "=" * len(header)

    settings_str = ""
    if pretty:
        settings_str += header + "\n"
    for key, value in settings.items():
        if key == "psm_group":
            settings_str += f"{key}: " + "{\n"
            for group, group_cfg in value.items():
                settings_str += f"  {group}: {group_cfg},\n"
            settings_str += "}\n"
        else:
            settings_str += f"{key}: {value}\n"
    if pretty:
        settings_str += footer
    else:
        settings_str = settings_str[:-1]
    return settings_str
