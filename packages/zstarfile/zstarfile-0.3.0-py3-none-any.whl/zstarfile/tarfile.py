# Copyright (C) 2024 Maxwell G <maxwell@gtmx.me>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import shutil
import tarfile as _tarfile
from typing import IO, TYPE_CHECKING, Any, Callable, Literal, TypeVar, cast

if TYPE_CHECKING:
    from _typeshed import StrOrBytesPath, StrPath

_TarFileT = TypeVar("_TarFileT", bound=_tarfile.TarFile)


class _TarFile(_tarfile.TarFile):
    """
    `tarfile.TarFile` subclass that uses the data_filter (introduced in PEP 706)
    when available
    """

    if hasattr(_tarfile, "data_filter"):
        extraction_filter = staticmethod(_tarfile.data_filter)


class ZSPlainTarfile(_tarfile.TarFile):
    """
    Same as `ZSTarfile` without the data_filter default
    """

    OPEN_METH = {  # noqa: RUF012
        **_tarfile.TarFile.OPEN_METH,
        "zst": "zstopen",
        "lz4": "lz4open",
    }

    @classmethod
    def pyzstopen(
        cls: type[_TarFileT],
        name: StrOrBytesPath | None = None,
        mode: Literal["r", "w", "x"] = "r",
        fileobj: IO[bytes] | None = None,
        compresslevel=3,
        **kwargs,
    ) -> _TarFileT:
        if mode not in {"r", "w", "x"}:
            raise ValueError("mode must be 'r', 'w' or 'x'")
        if name and fileobj:
            raise ValueError("'name' and 'fileobj' are mutually exclusive")

        try:
            import pyzstd
        except ImportError:  # pragma: no cover
            raise _tarfile.CompressionError("pyzstd module is not available") from None

        ckwargs: dict[str, Any] = (
            {"level_or_option": compresslevel} if mode != "r" else {}
        )
        fileobj = pyzstd.ZstdFile(  # type: ignore[assignment]
            name or fileobj,  # type: ignore[arg-type]
            cast(str, mode),
            **ckwargs,
        )
        fileobj = cast("IO[bytes]", fileobj)

        try:
            tarobj = cls.taropen(name, mode, fileobj, **kwargs)
        except pyzstd.ZstdError as exc:
            fileobj.close()
            if mode == "r":
                raise _tarfile.ReadError("not a zstd file") from exc
            raise
        except:  # pragma: no cover
            fileobj.close()
            raise
        tarobj._extfileobj = False  # type: ignore[attr-defined]
        return tarobj

    if not hasattr(_tarfile.TarFile, "zstopen"):
        zstopen = pyzstopen

    @classmethod
    def lz4open(
        cls: type[_TarFileT],
        name: StrOrBytesPath | None = None,
        mode: Literal["r", "w", "x"] = "r",
        fileobj: IO[bytes] | None = None,
        compresslevel: int = 0,
        **kwargs,
    ) -> _TarFileT:
        if mode not in {"r", "w", "x"}:
            raise ValueError("mode must be 'r', 'w' or 'x'")
        if name and fileobj:
            raise ValueError("'name' and 'fileobj' are mutually exclusive")

        try:
            import lz4.frame
        except ImportError:  # pragma: no cover
            raise _tarfile.CompressionError("lz4 module is not available") from None

        fileobj = cast(
            "IO[bytes]",
            lz4.frame.LZ4FrameFile(
                name or fileobj, mode=mode, compression_level=compresslevel
            ),
        )

        try:
            tarobj = cls.taropen(name, mode, fileobj, **kwargs)
        except (RuntimeError, EOFError) as exc:
            fileobj.close()
            if mode == "r":
                raise _tarfile.ReadError("not a lz4 file") from exc
            raise
        except:  # pragma: no cover
            fileobj.close()
            raise
        tarobj._extfileobj = False  # type: ignore[attr-defined]
        return tarobj


class ZSTarfile(ZSPlainTarfile, _TarFile):
    """
    `TarFile` subclass that supports Zstandard and lz4 compression
    and uses the data_filter (introduced in PEP 706) by default.
    """


# Code is considered trivial enough to copy w/o copyright concerns
def _unpack_tarfile(
    filename: StrPath,
    extract_dir: StrPath,
    *,
    filter: Callable | None = None,  # noqa: A002
) -> None:
    """
    Derivation of `_unpack_tarfile()` that uses our TarFile subclass.
    """
    try:
        tarobj = ZSPlainTarfile.open(filename)
    except _tarfile.TarError as exc:
        raise shutil.ReadError(
            f"{filename} is not a compressed or uncompressed tar file"
        ) from exc
    try:
        tarobj.extractall(extract_dir, filter=filter)
    finally:
        tarobj.close()


def _register_unpack_format() -> None:
    formats = shutil.get_unpack_formats()
    names = {f[0] for f in formats}
    if "zstdtar" not in names:
        shutil.register_unpack_format(
            "zstdtar", [".tar.zst", ".tzst"], _unpack_tarfile, [], "zst'ed tar-file"
        )
    if "lz4tar" not in names:
        shutil.register_unpack_format(
            "lz4tar", [".tar.lz4", ".tlz4"], _unpack_tarfile, [], "lz4'ed tar-file"
        )


_register_unpack_format()

# TODO: Support shutil.make_archive()

__all__ = ("ZSPlainTarfile", "ZSTarfile")
