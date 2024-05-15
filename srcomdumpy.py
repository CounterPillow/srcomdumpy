#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import argparse
import csv
import json
import re
import sys

from urllib.parse import urlparse

import apireq


class Leaderboard:
    game_id = None
    category_ids = None

    def __init__(self, game_id, category_ids):
        self.game_id = game_id
        self.category_ids = category_ids

    def __repr__(self):
        return f"Leaderboard(game_id={self.game_id}, category_ids=[{", ".join(self.category_ids)}])"


API_URL = "https://www.speedrun.com/api/v1"
RQR = apireq.APIRequestor(100, "CounterPillow/srcomdumpy")


def lb_from_url(url):
    u = urlparse(url)
    abbrev = u.path.split('/')[1]

    rf = RQR.submit(f"{API_URL}/games?name={abbrev}")
    r = rf.result()
    if r.status != 200:
        raise Exception(f"Failed fetching games list, HTTP error {r.status}")
    j = json.loads(r.data.decode('utf-8'))

    game_id = None
    for game in j["data"]:
        if url.startswith(game["weblink"]):
            game_id = game["id"]
            break

    if not game_id:
        raise Exception("Can't find the game for this")

    rf = RQR.submit(f"{API_URL}/games/{game_id}/categories")
    r = rf.result()
    if r.status != 200:
        raise Exception(f"Failed fetching game categories, HTTP error {r.status}")
    j = json.loads(r.data.decode('utf-8'))

    category_ids = []
    for category in j["data"]:
        category_ids.append(category["id"])

    if len(category_ids) == 0:
        raise Exception(f"Can't find the categories for game ID {game_id}")

    lb = Leaderboard(game_id, category_ids)
    return lb


def get_leaderboard(url):
    lb = lb_from_url(url)
    runs = []
    for category_id in lb.category_ids:
        # Filter by run status to work around API limits
        for run_status in ["verified", "new", "rejected"]:
            url = f"{API_URL}/runs?category={category_id}&status={run_status}&max=200&orderby=submitted&direction=asc"
            descending = False
            seen_ids = dict()
            running = True
            while running:
                rf = RQR.submit(url)
                r = rf.result()
                if r.status != 200:
                    raise Exception(f"Request failed for {url} with status {r.status}")

                j = json.loads(r.data.decode('utf-8'))

                for run in j["data"]:
                    if not run["id"] in seen_ids:
                        seen_ids[run["id"]] = True
                        runs.append(run)
                    else:
                        running = False
                        break

                print(f"Fetched {len(runs)} runs so far...", file=sys.stderr)

                if j["pagination"]["max"] > j["pagination"]["size"]:
                    break

                for link in j["pagination"]["links"]:
                    if link["rel"] == "next":
                        # Partial workaround for srcom cringe.
                        # See https://github.com/speedruncomorg/api/issues/125
                        if "offset=10000" in link["uri"]:
                            if not descending:
                                print("Switching to desc", file=sys.stderr)
                                url = f"{API_URL}/runs?category={category_id}&status={run_status}&max=200&orderby=submitted&direction=desc"
                                descending = True
                            else:
                                print("Couldn't fetch the entire leaderboard for "
                                      f"category {category_id} (>20k runs)",
                                      file=sys.stderr)
                                running = False
                                break
                        else:
                            url = link["uri"]
                        break
                else:
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
