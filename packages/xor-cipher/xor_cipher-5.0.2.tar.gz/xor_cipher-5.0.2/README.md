# `xor-cipher`

[![License][License Badge]][License]
[![Version][Version Badge]][Package]
[![Downloads][Downloads Badge]][Package]

[![Documentation][Documentation Badge]][Documentation]
[![Check][Check Badge]][Actions]
[![Test][Test Badge]][Actions]
[![Coverage][Coverage Badge]][Coverage]

> *Simple, reusable and optimized XOR ciphers in Python.*

`xor-cipher` is a fast implementation of the XOR cipher written using Rust.
Our tests show that it can be `1000x` faster than pure Python implementations.
It has been optimized to breeze through datasets of any size.

## Installing

**Python 3.9 or above is required.**

### `pip`

Installing the library with `pip` is quite simple:

```console
$ pip install xor-cipher
```

Alternatively, the library can be installed from source:

```console
$ pip install git+https://github.com/GDPSApp/xor-cipher-python.git
```

Or via cloning the repository:

```console
$ git clone https://github.com/GDPSApp/xor-cipher-python.git
$ cd xor-cipher-python
$ pip install .
```

### `uv`

You can add `xor-cipher` as a dependency with the following command:

```console
$ uv add xor-cipher
```

## Examples

### Simple Cipher

Use the `xor` function to perform the simple XOR cipher:

```python
>>> from xor_cipher import xor
>>> xor(b"Hello, world!", 0x42)
b"\n'..-nb5-0.&c"
```

### Cyclic Cipher

Use the `cyclic_xor` function to perform the cyclic XOR variation:

```python
>>> from xor_cipher import cyclic_xor
>>> cyclic_xor(b"Hello, world!", b"BLOB")
b"\n)#.-`o5->#&c"
```

### In-Place Cipher

There are functions to perform the XOR cipher in-place, on `bytearray` instances:

```python
>>> from xor_cipher import xor_in_place
>>> data = bytearray(b"Hello, world!")
>>> xor_in_place(data, 0x42)
>>> data
bytearray(b"\n'..-nb5-0.&c")
```

## Documentation

You can find the documentation [here][Documentation].

## Support

If you need support with the library, you can send an [email][Email].

## Changelog

You can find the changelog [here][Changelog].

## Security Policy

You can find the Security Policy of `xor-cipher` [here][Security].

## Contributing

If you are interested in contributing to `xor-cipher`, make sure to take a look at the
[Contributing Guide][Contributing Guide], as well as the [Code of Conduct][Code of Conduct].

## License

`xor-cipher` is licensed under the MIT License terms. See [License][License] for details.

[Email]: mailto:dev@gdps.app

[Actions]: https://github.com/GDPSApp/xor-cipher-python/actions

[Changelog]: https://github.com/GDPSApp/xor-cipher-python/blob/main/CHANGELOG.md
[Code of Conduct]: https://github.com/GDPSApp/xor-cipher-python/blob/main/CODE_OF_CONDUCT.md
[Contributing Guide]: https://github.com/GDPSApp/xor-cipher-python/blob/main/CONTRIBUTING.md
[Security]: https://github.com/GDPSApp/xor-cipher-python/blob/main/SECURITY.md

[License]: https://github.com/GDPSApp/xor-cipher-python/blob/main/LICENSE

[Package]: https://pypi.org/project/xor-cipher
[Coverage]: https://codecov.io/gh/GDPSApp/xor-cipher-python
[Documentation]: https://xor-cipher.github.io/xor-cipher

[License Badge]: https://img.shields.io/pypi/l/xor-cipher
[Version Badge]: https://img.shields.io/pypi/v/xor-cipher
[Downloads Badge]: https://img.shields.io/pypi/dm/xor-cipher

[Documentation Badge]: https://github.com/GDPSApp/xor-cipher-python/workflows/docs/badge.svg
[Check Badge]: https://github.com/GDPSApp/xor-cipher-python/workflows/check/badge.svg
[Test Badge]: https://github.com/GDPSApp/xor-cipher-python/workflows/test/badge.svg
[Coverage Badge]: https://codecov.io/gh/GDPSApp/xor-cipher-python/branch/main/graph/badge.svg
