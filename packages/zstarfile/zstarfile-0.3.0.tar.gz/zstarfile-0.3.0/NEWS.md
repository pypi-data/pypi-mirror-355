<!--
Copyright (C) 2024 Maxwell G <maxwell@gtmx.me>
SPDX-License-Identifier: MIT
-->

# NEWS

## 0.3.0 - 2025-06-16 <a id='0.3.0'></a>

Add initial support for Python 3.14.

## 0.2.0 - 2024-04-07 <a id='0.2.0'></a>

### Changed

- zstandard: switch from `zstandard` to `pyzstd` library.
  The `zstandard` library has a complicated API and doesn't support the
  seekable protocol. The latter causes issues with tarfile which expects
  seekable IO objects.

### Fixed

- lz4: properly handle `fileobj` argument

## 0.0.1 - 2024-04-06 <a id='0.0.1'></a>

Initial release
