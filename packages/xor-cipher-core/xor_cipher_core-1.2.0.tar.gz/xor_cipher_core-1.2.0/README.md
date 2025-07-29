# `xor-cipher-core`

[![License][License Badge]][License]
[![Version][Version Badge]][Package]
[![Downloads][Downloads Badge]][Package]
[![Test][Test Badge]][Actions]

> *Simple, reusable and optimized XOR ciphers in Python (core).*

`xor-cipher-core` is the core of [`xor-cipher`][xor-cipher].

## Installing

**Python 3.9 or above is required.**

### `pip`

Installing the library with `pip` is quite simple:

```console
$ pip install xor-cipher-core
```

Alternatively, the library can be installed from source:

```console
$ pip install git+https://github.com/GDPSApp/xor-cipher-core.git
```

Or via cloning the repository:

```console
$ git clone https://github.com/GDPSApp/xor-cipher-core.git
$ cd xor-cipher-core
$ pip install .
```

### `uv`

You can add `xor-cipher-core` as a dependency with the following command:

```console
$ uv add xor-cipher-core
```

## Examples

### Simple Cipher

Use the `xor` function to perform the simple XOR cipher:

```python
>>> from xor_cipher_core import xor
>>> xor(b"Hello, world!", 0x42)
b"\n'..-nb5-0.&c"
```

### Cyclic Cipher

Use the `cyclic_xor` function to perform the cyclic XOR variation:

```python
>>> from xor_cipher_core import cyclic_xor
>>> cyclic_xor(b"Hello, world!", b"BLOB")
b"\n)#.-`o5->#&c"
```

### In-Place Cipher

There are functions to perform the XOR cipher in-place, on `bytearray` instances:

```python
>>> from xor_cipher_core import xor_in_place
>>> data = bytearray(b"Hello, world!")
>>> xor_in_place(data, 0x42)
>>> data
bytearray(b"\n'..-nb5-0.&c")
```

## Documentation

You can find the documentation [here][Documentation].

## Support

If you need support with the library, you can send an [email][Email] or join the [Discord server][Discord].

## Changelog

You can find the changelog [here][Changelog].

## Security Policy

You can find the Security Policy of `xor-cipher-core` [here][Security].

## Contributing

If you are interested in contributing to `xor-cipher-core`, make sure to take a look at the
[Contributing Guide][Contributing Guide], as well as the [Code of Conduct][Code of Conduct].

## License

`xor-cipher-core` is licensed under the MIT License terms. See [License][License] for details.

[Email]: mailto:dev@gdps.app
[Discord]: https://gdps.app/discord

[Actions]: https://github.com/GDPSApp/xor-cipher-core/actions

[Changelog]: https://github.com/GDPSApp/xor-cipher-core/blob/main/CHANGELOG.md
[Code of Conduct]: https://github.com/GDPSApp/xor-cipher-core/blob/main/CODE_OF_CONDUCT.md
[Contributing Guide]: https://github.com/GDPSApp/xor-cipher-core/blob/main/CONTRIBUTING.md
[Security]: https://github.com/GDPSApp/xor-cipher-core/blob/main/SECURITY.md

[License]: https://github.com/GDPSApp/xor-cipher-core/blob/main/LICENSE

[Package]: https://pypi.org/project/xor-cipher-core
[Documentation]: https://xor-cipher.github.io/xor-cipher

[License Badge]: https://img.shields.io/pypi/l/xor-cipher-core
[Version Badge]: https://img.shields.io/pypi/v/xor-cipher-core
[Downloads Badge]: https://img.shields.io/pypi/dm/xor-cipher-core

[Test Badge]: https://github.com/GDPSApp/xor-cipher-core/workflows/test/badge.svg

[xor-cipher]: https://github.com/GDPSApp/xor-cipher-python
