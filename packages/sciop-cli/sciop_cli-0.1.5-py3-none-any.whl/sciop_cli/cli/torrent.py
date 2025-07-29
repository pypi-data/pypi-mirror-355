from pathlib import Path
from typing import Literal as L
from typing import cast

import click
import humanize
from rich import print
from rich.console import Group
from rich.panel import Panel
from rich.table import Table

from sciop_cli.const import DEFAULT_TORRENT_CREATOR
from sciop_cli.data import get_default_trackers
from sciop_cli.torrent import (
    calculate_overhead,
    calculate_total_pieces,
    create_torrent,
    find_optimal_piece_size,
    iter_files,
)
from sciop_cli.types import PieceSize


@click.group()
def torrent() -> None:
    """
    Create and manage torrents
    """


@torrent.command()
def pack() -> None:
    """
    Pack a directory to prepare it for torrent creation

    - Generate a manifest for the directory
    - Archive small files
    - Emit a .packmap.json description of the packing operation
    """
    raise NotImplementedError()


@torrent.command()
@click.option(
    "-p",
    "--path",
    required=True,
    help="Path to a directory or file to create .torrent from",
    type=click.Path(exists=True),
)
@click.option(
    "-t",
    "--tracker",
    required=False,
    default=None,
    multiple=True,
    help="Trackers to add to the torrent. can be used multiple times for multiple trackers. "
    "If not present, use the default trackers from https://sciop.net/docs/uploading/default_trackers.txt",
)
@click.option(
    "--default-trackers/--no-default-trackers",
    is_flag=True,
    default=None,
    help="If trackers are specified with --tracker, "
    "--default-trackers appends the default trackers to that list, "
    "otherwise just use the supplied trackers (--no-default-trackers has no effect). "
    "If no trackers are specified, "
    "--no-default-trackers prevents adding the default tracker list,"
    "which is done by default (--default-trackers has no effect).",
)
@click.option(
    "-s",
    "--piece-size",
    default=None,
    help="Piece size, in bytes. If not given, calculate piece size automatically."
    "Use `sciop-cli torrent piece-size` to preview the ",
    show_default=True,
)
@click.option(
    "--comment",
    default=None,
    required=False,
    help="Optional comment field for torrent",
)
@click.option(
    "--creator",
    default=DEFAULT_TORRENT_CREATOR,
    show_default=True,
    required=False,
    help="Optional creator field for torrent",
)
@click.option(
    "-w",
    "--webseed",
    required=False,
    default=None,
    multiple=True,
    help="Add HTTP webseeds as additional sources for torrent. Can be used multiple times. "
    "See https://www.bittorrent.org/beps/bep_0019.html",
)
@click.option(
    "--similar",
    required=False,
    default=None,
    multiple=True,
    help="Add infohash of a similar torrent. "
    "Similar torrents are torrents who have files in common with this torrent, "
    "clients are able to reuse files from the other torrents if they already have them downloaded.",
)
@click.option(
    "-2",
    "--v2",
    is_flag=True,
    default=False,
    help="Make a v2-only torrent (otherwise, hybrid v1/v2)",
)
@click.option("--progress/--no-progress", default=True, help="Enable progress bar (default True)")
@click.option(
    "-o",
    "--output",
    required=False,
    default=None,
    type=click.Path(exists=False),
    help=".torrent file to write to. Otherwise to stdout",
)
def create(
    path: Path,
    tracker: list[str] | tuple[str] | None = None,
    default_trackers: bool | None = None,
    piece_size: PieceSize | None = None,
    comment: str | None = None,
    creator: str = DEFAULT_TORRENT_CREATOR,
    webseed: list[str] | None = None,
    similar: list[str] | None = None,
    v2: bool = False,
    progress: bool = True,
    output: Path | None = None,
) -> None:
    """
    Create a torrent from a file or directory.

    Uses libtorrent to create standard torrent files.
    Will create a hybrid v1/v2 torrent file.

    See https://www.libtorrent.org/reference-Create_Torrents.html
    form details on fields, all input here is passed through to
    libtorrent's creation methods.
    """
    # recast tuple to list or none rather than tuple or empty tuple
    tracker = list(tracker) if tracker else None
    version = "v2" if v2 else "hybrid"
    version = cast(L["v2", "hybrid"], version)

    if piece_size is None:
        click.echo("No piece size specified, estimating optimal piece size")
        piece_size = find_optimal_piece_size(path=Path(path).absolute(), version=version)

        click.echo(f"Piece size estimated as {humanize.naturalsize(piece_size, binary=True)}")
    if not tracker and (default_trackers is None or default_trackers):
        click.echo(
            "No trackers specified, using default trackers from "
            "sciop.net/docs/uploading/default_trackers.txt"
        )
        tracker = get_default_trackers()
    elif tracker and default_trackers:
        default_tracker_list = get_default_trackers()
        tracker.extend(default_tracker_list)

    result = create_torrent(
        path,
        trackers=tracker,
        piece_size=piece_size,
        comment=comment,
        creator=creator,
        webseeds=webseed,
        similar=similar,
        version=version,
        pbar=progress,
        bencode=True,
    )
    result = cast(bytes, result)
    if output:
        with open(output, "wb") as f:
            f.write(result)
    else:
        click.echo(result)


@torrent.command("piece-size")
@click.option(
    "-p",
    "--path",
    required=True,
    help="Path to a directory or file to create .torrent from",
    type=click.Path(exists=True),
)
def piece_size(path: Path) -> None:
    """
    Show the optimal piece sizes calculated for each torrent version
    for a given file or directory.
    """
    path = Path(path)
    paths = [path] if path.is_file() else list(iter_files(path))

    sizes = [p.stat().st_size for p in paths]
    versions = ("v1", "v2", "hybrid")
    piece_sizes = {v: find_optimal_piece_size(path=paths, sizes=sizes, version=v) for v in versions}
    n_pieces = {v: calculate_total_pieces(sizes, piece_sizes[v], v) for v in versions}
    hybrid_overhead = sum(calculate_overhead(sizes, piece_sizes["hybrid"]))

    summary = Table(show_header=False)
    summary.add_column("", style="bold magenta")
    summary.add_column("")
    summary.add_row("N Files", humanize.number.intcomma(len(paths)))
    summary.add_row("Total size", humanize.naturalsize(sum(sizes), binary=True))

    pieces = Table(title="Piece sizes")
    pieces.add_column("Version")
    pieces.add_column("Piece Size")
    pieces.add_column("N Pieces")
    pieces.add_column("Padding Overhead")
    for v in ("v1", "v2", "hybrid"):
        row = [v, str(piece_sizes[v]), humanize.number.intcomma(n_pieces[v])]

        if v == "hybrid":
            row.append(humanize.naturalsize(hybrid_overhead, binary=True))
        pieces.add_row(*row)

    panel = Panel(Group(summary, pieces), title=str(path))
    print(panel)
