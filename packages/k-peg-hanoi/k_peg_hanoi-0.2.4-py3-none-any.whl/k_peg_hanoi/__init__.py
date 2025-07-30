from collections.abc import Iterable
from functools import cache
from importlib.metadata import metadata

import fire

if __package__:
    _package_metadata = metadata(__package__)
    __version__ = _package_metadata["Version"]
    __author__ = _package_metadata.get("Author-email", "")


def main():
    fire.Fire(show_hanoi)


@cache
def nmove(m: int, n: int) -> float:
    """Minimum number of moves

    :param m: number of disks
    :param n: number of rods
    :return: minimum number of moves
    """
    n = min(m + 1, n)
    if n == 2:
        return 1 if m == 1 else float("inf")
    if n == 3:
        return 2**m - 1
    if n == m + 1:
        return 2 * m - 1
    return min(nmove(i, n) * 2 + nmove(m - i, n - 1) for i in range(1, m))


def hanoi(md: int, pos: list[int]) -> Iterable[tuple[int, int]]:
    """Moves of Tower of Hanoi

    :param md: number of disks
    :param pos: position of rods
    :return: from, to
    """
    if md == 1:
        yield pos[0], pos[-1]
        return
    n = len(pos)
    if n <= 2:
        msg = "Too few len(pos)"
        raise ValueError(msg)
    mn = min((nmove(i, n) * 2 + nmove(md - i, n - 1), i) for i in range(1, md))[1]
    yield from hanoi(mn, [pos[0], *pos[2:], pos[1]])
    yield from hanoi(md - mn, [pos[0], *pos[2:-1], pos[-1]])
    yield from hanoi(mn, [*pos[1:-1], pos[0], pos[-1]])


def _show(towers, count):
    height = max(len(tower) for tower in towers)
    width = max(max(tower, default=0) for tower in towers)
    for i in range(height - 1, -1, -1):
        for tower in towers:
            n = tower[i] if i < len(tower) else 0
            s = "=" * (n * 2 - 1)
            print(f"{s:^{width * 2 - 1}}", end=" ")
        print()
    print(f"{count:-<{width * 2 * len(towers) - 1}}\n")


def show_hanoi(m: int, n: int = 3, *, text: bool = False):
    """Show move of Tower of Hanoi

    :param m: number of disks
    :param n: number of rods, default 3
    :param text: show with text, default False
    """
    towers = [list(range(m, 0, -1))] + [[] for _ in range(n - 1)]
    if not text:
        _show(towers, 0)
    for i, (fr, to) in enumerate(hanoi(m, list(range(n))), 1):
        towers[to].append(towers[fr].pop())
        if text:
            print(f"#{i} disk {towers[to][-1]} from {fr} to {to}")
        else:
            _show(towers, i)
