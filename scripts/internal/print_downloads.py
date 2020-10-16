#!/usr/bin/env python3

# Copyright (c) 2009 Giampaolo Rodola'. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""
Print PYPI statistics in MarkDown format.
Useful sites:
* https://pepy.tech/project/psutil
* https://pypistats.org/packages/psutil
* https://hugovk.github.io/top-pypi-packages/
"""

from __future__ import print_function
import json
import os
import subprocess
import sys

import pypinfo  # NOQA

from psutil._common import memoize


AUTH_FILE = os.path.expanduser("~/.pypinfo.json")
PKGNAME = 'psutil'
DAYS = 30
LIMIT = 100
GITHUB_SCRIPT_URL = "https://github.com/giampaolo/psutil/blob/master/" \
                    "scripts/internal/pypistats.py"
bytes_billed = 0


# --- get

@memoize
def sh(cmd):
    assert os.path.exists(AUTH_FILE)
    env = os.environ.copy()
    env['GOOGLE_APPLICATION_CREDENTIALS'] = AUTH_FILE
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = p.communicate()
    if p.returncode != 0:
        raise RuntimeError(stderr)
    assert not stderr, stderr
    return stdout.strip()


@memoize
def query(cmd):
    global bytes_billed
    ret = json.loads(sh(cmd))
    bytes_billed += ret['query']['bytes_billed']
    return ret


def top_packages():
    return query(
        f"pypinfo --all --json --days {DAYS} --limit {LIMIT} '' project")


def ranking():
    data = top_packages()
    for i, line in enumerate(data['rows'], 1):
        if line['project'] == PKGNAME:
            return i
    raise ValueError(f"can't find {PKGNAME}")


def downloads():
    data = top_packages()
    for line in data['rows']:
        if line['project'] == PKGNAME:
            return line['download_count']
    raise ValueError(f"can't find {PKGNAME}")


def downloads_pyver():
    return query(f"pypinfo --json --days {DAYS} {PKGNAME} pyversion")


def downloads_by_country():
    return query(f"pypinfo --json --days {DAYS} {PKGNAME} country")


def downloads_by_system():
    return query(f"pypinfo --json --days {DAYS} {PKGNAME} system")


def downloads_by_distro():
    return query(f"pypinfo --json --days {DAYS} {PKGNAME} distro")


# --- print


templ = "| %-30s | %15s |"


def print_row(left, right):
    if isinstance(right, int):
        right = '{0:,}'.format(right)
    print(templ % (left, right))


def print_header(left, right="Downloads"):
    print_row(left, right)
    s = templ % ("-" * 30, "-" * 15)
    print("|:" + s[2:-2] + ":|")


def print_markdown_table(title, left, rows):
    pleft = left.replace('_', ' ').capitalize()
    print("### " + title)
    print()
    print_header(pleft)
    for row in rows:
        lval = row[left]
        print_row(lval, row['download_count'])
    print()


def main():
    last_update = top_packages()['last_update']
    print("# Download stats")
    print("")
    s = f"psutil download statistics of the last {DAYS} days (last update "
    s += f"*{last_update}*).\n"
    s += f"Generated via [pypistats.py]({GITHUB_SCRIPT_URL}) script.\n"
    print(s)

    data = [
        {'what': 'Per month', 'download_count': downloads()},
        {'what': 'Per day', 'download_count': int(downloads() / 30)},
        {'what': 'PYPI ranking', 'download_count': ranking()}
    ]
    print_markdown_table('Overview', 'what', data)
    print_markdown_table('Operating systems', 'system_name',
                         downloads_by_system()['rows'])
    print_markdown_table('Distros', 'distro_name',
                         downloads_by_distro()['rows'])
    print_markdown_table('Python versions', 'python_version',
                         downloads_pyver()['rows'])
    print_markdown_table('Countries', 'country',
                         downloads_by_country()['rows'])


if __name__ == '__main__':
    try:
        main()
    finally:
        print("bytes billed: %s" % bytes_billed, file=sys.stderr)