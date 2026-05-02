# iso6346-check

A clean, operator-grade Python implementation of the **ISO 6346** container
check-digit algorithm. Pure standard library. Zero dependencies.
Drop-in CLI or import as a module.

```
$ python iso6346_check.py MSKU8492509
MSKU 849250 9  VALID

$ python iso6346_check.py "MSKU 849250 9" -v
MSKU 849250 9
  prefix    MSK
  category  U
  serial    849250
  expected  9
  actual    9
  status    VALID
```

[Full walkthrough, in-browser bulk validator, and downloadable Windows
operator edition at **prefixcheck.com**](https://prefixcheck.com/guide/iso-6346-check-digit/).

---

## What it does

Validates 11-character ISO 6346 shipping container identification numbers
against the standard's mod-11 check-digit math. Catches transposition errors,
OCR confusions, and manual-entry typos before they reach inventory systems.

The algorithm:

```
For each character in positions 0..9:
    value = letter-table-lookup OR digit
    weighted = value * (2 ^ position)

sum = total of all 10 weighted values
check digit = sum mod 11   (a remainder of 10 is written as 0)
```

Letter values are the public ISO 6346:2022 table — values skip multiples of 11
so a single transposed character cannot collide with the original at the
check-digit step.

## Install

There is no install. The implementation is a single ~170-line file with no
third-party dependencies. Either:

```sh
# Use as a CLI
curl -O https://raw.githubusercontent.com/xultrax-web/iso6346-check/main/iso6346_check.py
chmod +x iso6346_check.py
./iso6346_check.py MSKU8492509
```

Or copy `iso6346_check.py` into your own project and `import` from it.

## CLI usage

```
iso6346_check.py CSQU3054383            # validate one
iso6346_check.py "MSKU 849250 9"        # spaces are tolerated
iso6346_check.py < codes.txt            # batch via stdin
iso6346_check.py --next MSKU849250      # compute the 11th digit
iso6346_check.py -v MSKU8492509         # show full breakdown
```

### Exit codes

| Code | Meaning                                                             |
|------|---------------------------------------------------------------------|
| `0`  | All numbers valid (or check digit successfully computed for `--next`) |
| `1`  | One or more numbers were invalid                                    |
| `2`  | Bad input format                                                    |

Useful in pipelines:

```sh
if iso6346_check.py < manifest.csv > /dev/null; then
    echo "all numbers valid"
fi
```

## Library usage

```python
from iso6346_check import check, compute_check_digit, normalize, Result

# Validate a complete 11-char number
r = check("MSKU 849250 9")
print(r.code, r.valid)
# MSKU8492509 True

# Compute the check digit for a 10-char payload
print(compute_check_digit("MSKU849250"))
# 9

# Normalize without validation (strip whitespace, uppercase)
print(normalize("msku 849250 9"))
# MSKU8492509
```

`Result` is a `NamedTuple`:

```python
Result(
    code     = "MSKU8492509",   # normalized 11-char identifier
    expected = 9,                # check digit the math says should be there
    actual   = 9,                # the check digit on the input
    valid    = True,             # expected == actual
)
```

`check()` raises `ValueError` if the input doesn't match the
`4 letters + 7 digits` shape. `compute_check_digit()` raises `ValueError`
on bad payload shape (not `4 letters + 6 digits`).

## Worked example

```
MSKU 849250 9

M = 24    K = 21    8 ×16   2 ×128
S = 30    U = 32    4 ×32   5 ×256
                    9 ×64   0 ×512

position weights: 1, 2, 4, 8, 16, 32, 64, 128, 256, 512

24 + 60 + 84 + 256 + 128 + 128 + 576 + 256 + 1280 + 0
= 2,792

2,792 mod 11 = 9   <- the printed check digit
```

## Performance

The whole calculation is ten table lookups and ten bit-shifted adds. A
single validation runs in microseconds. Bulk validation of 100,000 numbers
completes in well under a second on a typical laptop.

## What this library does NOT do

- **Owner-prefix lookup.** Returning the registered owner of a 3-letter prefix
  requires a curated registry, which lives in the iOS PrefixCheck app
  ([prefixcheck.com](https://prefixcheck.com/)). This library is pure math.
- **OCR.** Converting a photo of a container number into 11 characters is a
  separate problem (camera frame aggregation, character voting, confidence
  scoring) handled in the iOS app.
- **Format detection** beyond ISO 6346. Shipper-owned containers, military
  conex variants, and other off-standard identifiers will fail
  `check()` with `ValueError` — that's a feature, not a bug.

## Compatibility

Python 3.10+ recommended (uses `from __future__ import annotations` and
modern typing syntax). Tested on CPython 3.10 through 3.14. No Python 2,
no third-party dependencies, no native compilation, no runtime side
effects.

## License

MIT. See [LICENSE](./LICENSE).

## Disclaimer

PrefixCheck is an independent operator-grade tool. Not affiliated with or
endorsed by the Bureau International des Containers et du Transport
Intermodal. Not a BIC-approved product. The mod-11 check-digit algorithm
itself is part of the public ISO 6346 standard.
