# Copyright (C) 2024 Maxwell G <maxwell@gtmx.me>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import filecmp
import io
import os
import shutil
import sys
import tarfile
from collections.abc import Iterator
from pathlib import Path

import pytest

from zstarfile.extra import _get_opener, open_write_compressed
from zstarfile.tarfile import ZSTarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def iterfiles(dir1: Path, *, _origdir: Path | None = None) -> Iterator[Path]:
    _origdir = _origdir or dir1
    for path in dir1.iterdir():
        if path.is_dir():
            yield from iterfiles(path, _origdir=_origdir)
        else:
            yield path.relative_to(_origdir)


def compare_directories(dir1: Path, dir2: Path) -> None:
    for file in iterfiles(dir2):
        assert filecmp.cmp(dir1 / file, dir2 / file)


@pytest.fixture(params=["zst", "lz4"])
def ext(request: pytest.FixtureRequest) -> str:
    param = request.param
    # 3.14 has broken lz4, for now, so ignore ERROR_FOR_MISSING there
    if os.environ.get("ERROR_FOR_MISSING") and sys.version_info < (3, 14):
        pass
    elif param == "zst":
        # 3.14 has stdlib version
        if sys.version_info < (3, 14):
            pytest.importorskip("pyzstd")
    elif param == "lz4":
        pytest.importorskip("lz4.frame", exc_type=ImportError)
    return param


def test_zstarfile_create(tmp_path_factory: pytest.TempPathFactory, ext: str) -> None:
    tmp_path = tmp_path_factory.mktemp(ext)
    directory = ROOT / "LICENSES"
    test = tmp_path / f"test.tar.{ext}"
    (new := tmp_path / "new").mkdir()
    (new2 := tmp_path / "new2").mkdir()
    with open_write_compressed(test, compression_type=ext, compresslevel=3) as tarobj:
        tarobj.add(directory, "LICENSES/")
    shutil.unpack_archive(test, new, filter="data")
    compare_directories(ROOT, new)
    with ZSTarfile.open(fileobj=io.BytesIO(test.read_bytes())) as tarobj:
        tarobj.extractall(new2)
    compare_directories(ROOT, new2)


def test_zstarfile_fileobj_error(ext: str) -> None:
    with pytest.raises(tarfile.ReadError, match=f"not a {ext}.? file"):
        ZSTarfile.open(mode=f"r:{ext}", fileobj=io.BytesIO(b"fjfjfj"))  # type: ignore


def test_zstarfile_error(ext: str, tmp_path_factory: pytest.TempPathFactory) -> None:
    tmp_path = tmp_path_factory.mktemp(ext)
    func = getattr(ZSTarfile, ZSTarfile.OPEN_METH[ext])
    with pytest.raises(tarfile.ReadError, match=f"not a {ext}.? file"):
        func("README.md", "r")
    with pytest.raises(
        shutil.ReadError,
        match="README.md is not a compressed or uncompressed tar file",
    ):
        ext_name = ext
        if ext_name == "zst":
            ext_name += "d"
        shutil.unpack_archive("README.md", tmp_path, format=ext_name + "tar")


def test_zstarfile_mode_error(ext: str) -> None:
    func = getattr(ZSTarfile, ZSTarfile.OPEN_METH[ext])
    with pytest.raises(ValueError, match="mode must be 'r', 'w' or 'x'"):
        func(None, "invalid")
    if sys.version_info >= (3, 14) and ext == "zst":
        pytest.xfail("The stdlib version zst version behaves differently")
    with pytest.raises(ValueError, match="'name' and 'fileobj' are mutually exclusive"):
        func(name=..., fileobj=...)


@pytest.mark.parametrize(
    "filename, compression_type, expected_meth_name, value_error",
    [
        pytest.param("abc.tar", None, "taropen", None),
        pytest.param("abc.tar.gz", None, "gzopen", None),
        pytest.param("abc.tar.jfjfjf", None, None, "No match found for abc.tar.jfjfj"),
        pytest.param(
            "abc.tar.gz", "invalid1", None, "Invalid compression_type: invalid1"
        ),
    ],
)
def test__get_opener_cases(
    filename: str,
    compression_type: str | None,
    expected_meth_name: str | None,
    value_error: str | None,
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    if value_error:
        with pytest.raises(ValueError, match=value_error):
            _get_opener(filename, compression_type)
    else:
        opener = _get_opener(filename, compression_type)
        assert expected_meth_name == opener.__name__
