#!/usr/bin/env python3
import argparse
import os
from typing import List

from subsplease_dl.subsplease import BOTS, SubsPleaseXDCC, search_all


def episode_parser(string: str) -> List[int]:
    episodes = []
    for part in string.split(","):
        if "-" in part:
            if part.count("-") >= 2:
                raise TypeError(f"Range {part!r} is not valid")

            a, b = map(int, part.split("-"))
            episodes.extend(range(a, b + 1))
        else:
            episodes.append(int(part))

    return episodes


def main():
    prog_name = os.path.basename(os.path.dirname(__file__)).replace("_", "-")
    parser = argparse.ArgumentParser(prog=prog_name)
    parser.add_argument("anime", help="Name of the anime to download")
    parser.add_argument(
        "-b", "--bot", help="Name of bot to use to download", choices=BOTS
    )
    parser.add_argument(
        "-d", "--download", help="Download all listed anime", action="store_true"
    )
    parser.add_argument(
        "-e",
        "--episodes",
        help="The episodes to download, must be a valid comma separated range",
        type=episode_parser,
        default=[],
    )
    parser.add_argument(
        "-r",
        "--resolution",
        help="The resolution to download with",
        choices=["480p", "540p", "720p", "1080p", "SD"],
    )
    parser.add_argument("-g", "--group", help="The group which subbed the anime")
    parser.add_argument(
        "--cutoff", help="The cutoff of the search algorithm", type=float, default=0.6
    )

    args = parser.parse_args()
    episodes = set(map(str, args.episodes))

    anime = [
        i
        for i in search_all(args.anime, cutoff=args.cutoff)
        if (not episodes or i.episode.lstrip("0") in episodes)
        and (not args.resolution or args.resolution == i.resolution)
        and (not args.group or args.group == i.group)
        and (not args.bot or args.bot == i.bot)
    ]

    for file in anime:
        print(
            f"[{file.group}] {file.title} - {file.episode} ({file.resolution})        (#{file.id} - {file.bot})"
        )

    if args.download:
        for file in anime:
            if (
                os.path.exists(file.filename)
                and abs(os.path.getsize(file.filename) - file.size) < 0x1000
            ):
                print(f"Skipping {file.filename}, already downloaded")
                continue

            with SubsPleaseXDCC(file.bot) as client:
                client.download(file.id)


if __name__ == "__main__":
    main()
