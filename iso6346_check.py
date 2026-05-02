#!/usr/bin/env python3
"""iso6346_check.py — ISO 6346 container check-digit validator.

Operator-grade. Pure stdlib. Zero deps. Drop into your tools/ folder,
chmod +x, and use it as a CLI or import the public functions.

Usage:
    iso6346_check.py MSKU8492509            # validate one
    iso6346_check.py "MSKU 849250 9"        # spaces are tolerated
    iso6346_check.py < codes.txt            # batch via stdin
    iso6346_check.py --next MSKU849250      # compute the 11th digit
    iso6346_check.py -v MSKU8492509         # show breakdown

Exit codes:
    0   all numbers valid (or check digit successfully computed)
    1   one or more numbers were invalid
    2   bad input format

Reference: ISO 6346:2022 — Freight containers — Coding, identification
and marking. PrefixCheck is independent. Not affiliated with the BIC.
"""
from __future__ import annotations

import argparse
import re
import sys
from typing import Iterable, NamedTuple

# ISO 6346 letter-to-value table. Values skip multiples of 11
# (no 22, no 33) so a single transposed character can't collide
# with the original at the check-digit step.
_LETTER_VALUES: dict[str, int] = {
    "A": 10, "B": 12, "C": 13, "D": 14, "E": 15, "F": 16, "G": 17,
    "H": 18, "I": 19, "J": 20, "K": 21, "L": 23, "M": 24, "N": 25,
    "O": 26, "P": 27, "Q": 28, "R": 29, "S": 30, "T": 31, "U": 32,
    "V": 34, "W": 35, "X": 36, "Y": 37, "Z": 38,
}

_FULL = re.compile(r"^[A-Z]{4}\d{7}$")     # 11-char identifier
_PAYLOAD = re.compile(r"^[A-Z]{4}\d{6}$")  # 10-char payload, no check digit
# Strip whitespace AND dashes — EIRs and shipping docs commonly print
# the check digit as `XXXX 123456-7` or `XXXX-123456-7`.
_SEP = re.compile(r"[\s\-]+")


class Result(NamedTuple):
    """Outcome of validating one container number."""
    code: str       # normalized 11-char identifier, e.g. "MSKU8492509"
    expected: int   # check digit the math says should be there
    actual: int     # the check digit on the input
    valid: bool     # expected == actual


def normalize(s: str) -> str:
    """Strip whitespace and dashes, uppercase. No format validation."""
    return _SEP.sub("", s).upper()


def compute_check_digit(payload: str) -> int:
    """Return the ISO 6346 check digit for a 10-char payload.

    payload: 4 letters (owner code + category) + 6 serial digits.
    Raises ValueError if the shape is wrong.
    """
    code = normalize(payload)
    if not _PAYLOAD.fullmatch(code):
        raise ValueError(
            f"bad payload {code!r}: expect 4 letters + 6 digits "
            f"(example: MSKU849250)"
        )

    total = 0
    for i, ch in enumerate(code):
        value = _LETTER_VALUES[ch] if ch.isalpha() else int(ch)
        total += value << i  # 2**i via bitshift; cheap and operator-honest

    remainder = total % 11
    # ISO writes a remainder of 10 as 0. The standard recommends owners
    # avoid serials that produce this case, but it shows up in the field.
    return 0 if remainder == 10 else remainder


def check(container_number: str) -> Result:
    """Validate an 11-char ISO 6346 container number.

    Returns a Result. Raises ValueError if the input isn't 4 letters
    followed by 7 digits (whitespace and case are forgiven).
    """
    code = normalize(container_number)
    if not _FULL.fullmatch(code):
        raise ValueError(
            f"bad number {code!r}: expect 4 letters + 7 digits "
            f"(example: MSKU8492509 or 'MSKU 849250 9')"
        )
    expected = compute_check_digit(code[:10])
    actual = int(code[10])
    return Result(code, expected, actual, expected == actual)


def _format(r: Result, *, verbose: bool) -> str:
    head = f"{r.code[:4]} {r.code[4:10]} {r.code[10]}"
    tag = "VALID" if r.valid else f"INVALID (expected {r.expected})"
    if not verbose:
        return f"{head}  {tag}"
    return (
        f"{head}\n"
        f"  prefix    {r.code[:3]}\n"
        f"  category  {r.code[3]}\n"
        f"  serial    {r.code[4:10]}\n"
        f"  expected  {r.expected}\n"
        f"  actual    {r.actual}\n"
        f"  status    {tag}"
    )


def _read_inputs(args: argparse.Namespace) -> Iterable[str]:
    """Yield container numbers from CLI args, stdin pipe, or interactive prompt."""
    if args.numbers:
        yield from args.numbers
        return
    if not sys.stdin.isatty():
        for line in sys.stdin:
            line = line.strip()
            if line:
                yield line
        return
    try:
        yield input("container number: ").strip()
    except (EOFError, KeyboardInterrupt):
        print(file=sys.stderr)
        sys.exit(2)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="iso6346_check",
        description="Validate ISO 6346 container numbers. Stdlib only, offline.",
    )
    p.add_argument("numbers", nargs="*", help="numbers to check (else stdin)")
    p.add_argument("-v", "--verbose", action="store_true",
                   help="show prefix/category/serial/check-digit breakdown")
    p.add_argument("-n", "--next", metavar="PAYLOAD",
                   help="compute the check digit for a 10-char payload")
    args = p.parse_args(argv)

    if args.next is not None:
        try:
            print(compute_check_digit(args.next))
            return 0
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

    any_invalid = False
    for raw in _read_inputs(args):
        try:
            r = check(raw)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            any_invalid = True
            continue
        print(_format(r, verbose=args.verbose))
        if not r.valid:
            any_invalid = True
    return 1 if any_invalid else 0


if __name__ == "__main__":
    sys.exit(main())
