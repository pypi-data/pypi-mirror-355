from typing import TYPE_CHECKING

import httpx
import pytest
from pydantic import TypeAdapter

from sciop_cli.api import claim_next, create_upload, get_token, login, upload_torrent
from sciop_cli.config import Config, get_config
from sciop_cli.models.sciop import TorrentFile, Upload

if TYPE_CHECKING:
    from sciop.models import Account
    from torf import Torrent


@pytest.mark.asyncio
async def test_login(fresh_config: Config, run_server_sync):
    """
    The login command logs us in!
    """
    username = "testuser"
    password = "testuser12345"
    async with httpx.AsyncClient() as client:
        account = await client.post(
            "http://127.0.0.1:8080/api/v1/register",
            data={"username": username, "password": password},
            timeout=10,
        )
        assert account.status_code == 200

        token = login(username, password)
        assert isinstance(token, str)

        res = await client.get(
            "http://localhost:8080/self/", headers={"Authorization": f"Bearer {token}"}
        )
        assert res.status_code == 200


@pytest.mark.asyncio
async def test_get_token(config_logged_in: Config, run_server_sync):
    """
    get_token gets a token and sets it in the config
    """
    cfg = config_logged_in
    assert cfg.token is None
    assert get_config().token is None

    # then we should get a token and set it in the config
    token = get_token()
    assert token is not None
    assert get_config().token.get_secret_value() == token


@pytest.mark.asyncio
async def test_get_next_claim(as_admin: "Account", run_server_sync, claims_setup):
    """
    Should be able to call get next claim!
    """
    responses = [claim_next("default") for _ in range(3)]
    for letter, response in zip(("a", "b", "c"), responses):
        assert response["dataset_part"] == letter
        assert response["status"] == "in_progress"

    assert claim_next("default") is None


@pytest.mark.asyncio
async def test_upload_torrent(as_admin: "Account", run_server_sync, torrent, tmp_path):
    """
    We can upload a torrent!
    """
    torrent: Torrent = torrent()
    path = tmp_path / "test.torrent"
    torrent.write(path)
    res = upload_torrent(path)

    adapter = TypeAdapter(TorrentFile)
    adapter.validate_python(res)
    assert res["v1_infohash"] == torrent.infohash
    assert res["file_name"] == "test.torrent"


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["infohash", "path"])
async def test_create_upload(
    as_admin: "Account",
    dataset,
    run_server_sync,
    torrent,
    tmp_path,
    mode: str,
):
    """
    We can create an upload item, either by passing an infohash or a path
    """
    slug = "default"
    path = tmp_path / "test.torrent"

    dataset(slug=slug)
    torrent: Torrent = torrent()
    torrent.write(path)

    if mode == "infohash":
        upload_torrent(path)
        ul = create_upload(dataset=slug, infohash=torrent.infohash)
    elif mode == "path":
        ul = create_upload(dataset=slug, torrent_path=path)
    else:
        raise ValueError()

    adapter = TypeAdapter(Upload)
    adapter.validate_python(ul)


@pytest.mark.asyncio
@pytest.mark.parametrize("parts", [["part-1"], ["part-1", "part-2"]])
async def test_create_upload_part(
    as_admin: "Account", dataset, run_server_sync, torrent, tmp_path, parts: list[str]
):
    """
    We can upload to a dataset part
    """
    slug = "default"
    path = tmp_path / "test.torrent"

    dataset(slug=slug, parts=[{"part_slug": p} for p in parts])
    torrent: Torrent = torrent()
    torrent.write(path)

    ul = create_upload(dataset=slug, dataset_parts=parts, torrent_path=path)
    assert ul["dataset_parts"] == parts
