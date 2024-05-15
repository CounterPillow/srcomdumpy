#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import argparse
import csv
import json
import re
import sys

from time import sleep
from urllib.parse import urlparse

import requests


class Leaderboard:
    game_id = None
    category_ids = None

    def __init__(self, game_id, category_ids):
        self.game_id = game_id
        self.category_ids = category_ids

    def __repr__(self):
        return f"Leaderboard(game_id={self.game_id}, category_ids=[{", ".join(self.category_ids)}])"


API_URL = "https://www.speedrun.com/api/v1"


def lb_from_url(url):
    u = urlparse(url)
    abbrev = u.path.split('/')[1]

    r = requests.get(API_URL + "/games", params={"name": abbrev})
    r.raise_for_status()
    j = r.json()

    game_id = None
    for game in j["data"]:
        if url.startswith(game["weblink"]):
            game_id = game["id"]
            break

    if not game_id:
        raise Exception("Can't find the game for this")

    r = requests.get(API_URL + f"/games/{game_id}/categories")
    r.raise_for_status()
    j = r.json()

    category_ids = []
    for category in j["data"]:
        category_ids.append(category["id"])

    if not category_ids:
        raise Exception(f"Can't find the categories for game ID {game_id}")

    lb = Leaderboard(game_id, category_ids)
    return lb


def get_leaderboard(url):
    lb = lb_from_url(url)
    runs = []
    s = requests.Session()
    tries = 0
    for category_id in lb.category_ids:
        url = f"{API_URL}/runs?category={category_id}&max=200"
        while True:
            try:
                r = s.get(url)
                r.raise_for_status()
            except Exception as e:
                if tries == 10:
                    raise Exception("Too many errors fetching runs")
                else:
                    tries += 1
                    print(f"Received {str(e)}, sleeping for 10 seconds", file=sys.stderr)
                    sleep(10)
                    continue

            j = r.json()
            tries = 0

            runs.extend(j["data"])
            print(f"Fetched {len(runs)} runs so far...", file=sys.stderr)

            for link in j["pagination"]["links"]:
                if link["rel"] == "next":
                    url = link["uri"]
                    break
            else:
                break

            if j["pagination"]["max"] > j["pagination"]["size"]:
                break

    return runs


def csv_fieldname_helper(key, value, prefix=""):
    fieldnames = {}
    if type(value) is dict:
        for k, v in value.items():
            fieldnames.update(csv_fieldname_helper(k, v,
                                                   key if prefix == "" else f"{prefix}_{key}"))
    elif type(value) is not list:
        if prefix != "":
            fieldnames.update({f"{prefix}_{key}": value})
        else:
            fieldnames.update({key: value})
    else:
        for i, entry in enumerate(value):
            fieldnames.update(csv_fieldname_helper(str(i), entry,
                                                   key if prefix == "" else f"{prefix}_{key}"))

    return fieldnames


def dump_csv(lb, outf):
    if len(lb) == 0:
        return

    fieldnames = {}
    for run in lb:
        fieldnames.update(csv_fieldname_helper("", run))
    print("Writing a CSV with headers " + ", ".join(sorted(fieldnames.keys())))

    dw = csv.DictWriter(outf, sorted(fieldnames.keys()))
    dw.writeheader()

    for run in lb:
        dw.writerow(csv_fieldname_helper("", run))


def dump_json(lb, outf):
    outf.write(json.dumps(lb, sort_keys=True, indent=4))
    print("", file=outf)


def main():
    parser = argparse.ArgumentParser(
        prog="srcomdumpy.py",
        description="Dump all runs of a speedrun.com leaderboard")
    parser.add_argument("url", metavar="URL", help="URL of the game to dump")
    parser.add_argument("-o", "--output", metavar="FILENAME", default="-",
                        help="Path to output file, or - for stdout (default)")
    parser.add_argument("-f", "--output-format", default="JSON", choices=["CSV", "JSON"],
                        help="Which format to use as the output")
    args = parser.parse_args()

    imgay = re.fullmatch(r"https://www\.speedrun\.com/(?P<abbrev>\w+)/?.*", args.url)
    if not imgay or not imgay.group("abbrev"):
        print(f"'{args.url}' is not a valid URL", file=sys.stderr)
        sys.exit(1)

    lb = get_leaderboard(args.url)

    dump_cmd = {"CSV": dump_csv, "JSON": dump_json}[args.output_format]

    if args.output == '-':
        dump_cmd(lb, sys.stdout)
    else:
        with open(args.output, 'w') as outf:
            dump_cmd(lb, outf)


if __name__ == "__main__":
    main()
