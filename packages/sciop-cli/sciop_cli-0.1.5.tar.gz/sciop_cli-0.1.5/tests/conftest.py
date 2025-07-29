from pathlib import Path

import pytest
from sciop.testing.fixtures.config import set_config as sciop_set_config  # noqa: F401
from sciop.testing.fixtures.db import *  # noqa: F401
from sciop.testing.fixtures.server import *  # noqa: F401

from sciop_cli.config import Config

from .fixtures import *

DATA_DIR = Path(__file__).parent / "data"

pytest_plugins = ("sciop.testing.plugin",)


@pytest.fixture(autouse=True, scope="session")
def session_monkeypatch_config(
    monkeypatch_session: pytest.MonkeyPatch, tmp_path_factory: pytest.TempPathFactory
) -> None:
    """sessionwide baseline for our config..."""
    from sciop_cli import config
    from sciop_cli.config import Config, set_config

    session_dir = tmp_path_factory.mktemp("sciop_cli_session")
    monkeypatch_session.setattr(config, "_global_config", session_dir / "sciop_cli_test.yaml")

    new_config = Config(
        username=None,
        password=None,
        token=None,
        instance_url="http://127.0.0.1:8080",
        request_timeout=10,
    )
    set_config(new_config)


@pytest.fixture()
def fresh_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Config:
    from sciop_cli import config
    from sciop_cli.config import Config, set_config

    monkeypatch.setattr(config, "_global_config", tmp_path / "sciop_cli_test.yaml")

    new_config = Config(
        username=None, password=None, token=None, instance_url="http://127.0.0.1:8080"
    )
    set_config(new_config)
    return new_config
