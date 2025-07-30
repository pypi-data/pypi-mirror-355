# bean-sort

`bean-sort` is a naive sorting utility for Beancount files.  It is naive in that it makes no attempt to parse the file, simply splitting on date fields.

Specifically, `bean-sort` splits on any date at the beginning of a line.  All text between this and the next date are regarded as part of that record.  This is particularly important for any pragmas which follow any actual directive.

Any test before the first date in the file is regarded as header.

The sortng is stable, that is, records already in date order are left undisturbed.

Output is written to standard output.

## Installation

Either from PyPI or from the Nix flake in this repo.

## Usage

```
> bean-sort --help
usage: bean-sort [-h] file [file ...]

Sort one or more Beancount files to standard output.

positional arguments:
  file        Beancount file(s) to sort

options:
  -h, --help  show this help message and exit
```
