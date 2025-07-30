#!/usr/bin/env python

# Copyright (C) 2025  Simon Guest

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import argparse
import datetime
import re
import sys


class Sorter:
    _DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})", re.MULTILINE)

    def __init__(self):
        self._headers = []
        self._by_date = {}

    def _add_header(self, header: str):
        self._headers.append(header)

    def _add_dated_text(self, date: str, body: str):
        ordinal = datetime.date.fromisoformat(date).toordinal()
        if ordinal in self._by_date:
            self._by_date[ordinal].append(body)
        else:
            self._by_date[ordinal] = [body]

    def add_from_file(self, path: str):
        with open(path) as f:
            content = f.read()
            records = self.__class__._DATE_RE.split(content)

            if not records:
                return

            # handle header if any
            header = records[0].strip()
            if header:
                self._add_header(header)

            for i in range(len(records) // 2):
                date_str = records[2 * i + 1]
                remainder = records[2 * i + 2]
                self._add_dated_text(date_str, (date_str + remainder).strip())

    def print(self, file=sys.stdout):
        for header in self._headers:
            file.write("%s\n\n" % header)

        for ordinal in sorted(self._by_date.keys()):
            for body in self._by_date[ordinal]:
                file.write("%s\n\n" % body)


def main():
    parser = argparse.ArgumentParser(
        description="""
        Sort one or more Beancount files to standard output.
    """
    )
    parser.add_argument("file", nargs="+", help="Beancount file(s) to sort")
    args = parser.parse_args()

    sorter = Sorter()
    for path in args.file:
        sorter.add_from_file(path)

    sorter.print()


if __name__ == "__main__":
    main()
