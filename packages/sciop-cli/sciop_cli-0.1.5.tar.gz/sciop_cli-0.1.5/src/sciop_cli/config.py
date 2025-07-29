from logging import getLogger
from pathlib import Path
from typing import Optional, Self

import keyring
import yaml
from platformdirs import PlatformDirs
from pydantic import SecretStr, model_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

_dirs = PlatformDirs("sciop_cli", "sciop", ensure_exists=True)
_global_config = Path(_dirs.user_config_dir) / "sciop_cli.yaml"
_config: Optional["Config"] = None


def get_config() -> "Config":
    global _config
    if _config is None:
        _config = Config()
    return _config


def set_config(cfg: "Config") -> "Config":
    """
    Set config, dumping to the global config yaml file.

    If a password is present, first try to save it in the keychain
    and exclude it from the dump.

    if we can't for some reason, dump it with a warning
    """
    global _config
    _config = cfg

    logger = getLogger("sciop_cli.config")
    if cfg.password and cfg.username:
        try:
            keyring.set_password("sciop_cli", cfg.username, cfg.password.get_secret_value())
            dumped = cfg.model_dump(exclude={"password"})
        except Exception as e:
            logger.warning(
                "Password present, but could not save in keyring. "
                "Dumping in plaintext, which is insecure!\n"
                f"Got exception: {e}"
            )
            dumped = cfg.model_dump()
            dumped["password"] = dumped["password"].get_secret_value()
    else:
        dumped = cfg.model_dump()

    if dumped.get("token") and isinstance(dumped["token"], SecretStr):
        dumped["token"] = dumped["token"].get_secret_value()

    with open(_global_config, "w") as f:
        yaml.safe_dump(dumped, f)
    logger.debug(f"Dumped config to {_global_config}")
    return cfg


class Config(BaseSettings):
    """
    Environmental config for cli commands.

    Keep this light - just what we need to run cli commands,
    don't want this to be a major point of interaction.

    Values can be set in a .env file with a SCIOP_CLI_ prefix,
    a `sciop_cli.yaml` file in cwd,
    or the `sciop_cli` user config dir provided by
    [platformdirs](https://github.com/tox-dev/platformdirs)
    (e.g. `~/.config/sciop_cli/sciop_cli.yaml`)
    """

    instance_url: str = "https://sciop.net"
    username: str | None = None
    password: SecretStr | None = None
    request_timeout: float = 5
    """Default timeout to use in API requests."""
    token: SecretStr | None = None
    """Expiring jwt, stored in config to reuse between cli calls"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="sciop_cli_",
        env_nested_delimiter="__",
        extra="ignore",
        nested_model_default_partial_update=True,
        yaml_file="sciop_cli.yaml",
        validate_assignment=True,
    )

    @model_validator(mode="before")
    @classmethod
    def password_from_keychain(cls, value: dict | Self) -> dict | Self:
        """Try to get a password from keychain, if not provided"""
        try:
            if isinstance(value, dict) and value.get("username") and not value.get("password"):
                maybe_password = keyring.get_password("sciop_cli", value["username"])
                if maybe_password:
                    value["password"] = SecretStr(maybe_password)
            elif isinstance(value, cls) and value.username and value.password is None:
                maybe_password = keyring.get_password("sciop_cli", value.username)
                if maybe_password:
                    value.password = SecretStr(maybe_password)
        except Exception:
            # e.g. no supported keyring backends available
            return value
        return value

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """
        Read from the following sources,
        in order such that later sources in the list override earlier sources

        - `{config_dir}/sciop_cli.yaml`
        - `sciop_cli.yaml` (in cwd)
        - `.env` (in cwd)
        - environment variables prefixed with `SCIOP_`
        - arguments passed on config object initialization

        See [pydantic settings docs](https://docs.pydantic.dev/latest/concepts/pydantic_settings/#customise-settings-sources)
        """
        global_source = YamlConfigSettingsSource(settings_cls, yaml_file=_global_config)
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YamlConfigSettingsSource(settings_cls),
            global_source,
        )
