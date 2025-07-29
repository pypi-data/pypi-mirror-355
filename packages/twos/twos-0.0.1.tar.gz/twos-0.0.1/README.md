# twos

Converting between [two's complement](https://en.wikipedia.org/wiki/Two%27s_complement) and unsigned integer interpretation (i.e. sum of powers of two) of integer bit patterns.

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/twos?style=flat-square)
![PyPI](https://img.shields.io/pypi/v/twos?style=flat-square)

## Installation
`twos` is available on pypi:
```bash
pip install twos
```

## Example
Basic usage example (can be found in [examples/convert.py](examples/convert.py)):

```python
from twos import to_signed, to_unsigned

bit_width = 8
x = 170 # 0b10101010
pattern = f"{x:b}"

y = to_signed(value=x, bit_width=bit_width)
print(f"Interpreting {pattern} as {bit_width}-bit two's complement: {y}")

z = to_unsigned(value=y, bit_width=bit_width)
print(f"Interpreting {pattern} as {bit_width}-bit unsigned integer: {z}")
```

Output:

```
Interpreting 10101010 as 8-bit two's complement: -86
Interpreting 10101010 as 8-bit unsigned integer: 170
```
