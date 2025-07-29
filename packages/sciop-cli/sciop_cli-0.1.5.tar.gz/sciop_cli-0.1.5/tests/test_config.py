from pathlib import Path

import keyring
import pytest
import yaml

from sciop_cli import config
from sciop_cli.config import Config, set_config


def test_instantiation_defaults(monkeypatch, tmp_path):
    """We should be able to instantiate config without setting any values"""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config, "_global_config", Path(tmp_path) / "sciop_cli_test.yaml")
    _ = Config()


def test_password_from_keychain(request: pytest.FixtureRequest):
    """We can get a password from the keychain automatically"""
    username = f"__test__{request.node.name}"
    expected = "__testpassword__"
    keyring.set_password("sciop_cli", username, expected)

    cfg = Config(username=username)
    assert cfg.password
    assert cfg.password.get_secret_value() == expected


def test_set_config_no_password(monkeypatch, tmp_path: Path, request: pytest.FixtureRequest):
    """
    When we dump the config, and we have a password, and we can access a keyring,
    we should remove the password from the dump, save it in the keyring.
    """
    username = f"__test__{request.node.name}"
    expected = "__testpassword__"
    cfg_path = Path(tmp_path) / "sciop_cli_test.yaml"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config, "_global_config", cfg_path)
    if keyring.get_password("sciop_cli", username):
        keyring.delete_password("sciop_cli", username)

    assert not keyring.get_password("sciop_cli", username)
    cfg = Config(username=username, password=expected)
    cfg = set_config(cfg)

    with open(cfg_path) as f:
        dumped = yaml.safe_load(f)
    assert dumped["username"] == username
    assert "password" not in dumped
    assert keyring.get_password("sciop_cli", username) == expected

    # and we should get it again when we instantiate
    loaded = Config()
    assert loaded.username == username
    assert loaded.password.get_secret_value() == expected
