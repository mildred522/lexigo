from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
from _pytest.compat import get_user_id
from _pytest.pathlib import make_numbered_dir, rm_rf
from _pytest.tmpdir import TempPathFactory, get_user

PYTEST_TEMP_ROOT = Path(__file__).resolve().parents[1] / "pytest_temp_root"


def _ensure_repo_dirs() -> None:
    PYTEST_TEMP_ROOT.mkdir(parents=True, exist_ok=True)


class WindowsTempPathFactory(TempPathFactory):
    def mktemp(self, basename: str, numbered: bool = True) -> Path:
        basename = self._ensure_relative_to_basetemp(basename)
        if not numbered:
            p = self.getbasetemp().joinpath(basename)
            p.mkdir(parents=True, exist_ok=True)
        else:
            p = make_numbered_dir(root=self.getbasetemp(), prefix=basename, mode=0o777)
            self._trace("mktemp", p)
        return p

    def getbasetemp(self) -> Path:
        if self._basetemp is not None:
            return self._basetemp

        if self._given_basetemp is not None:
            basetemp = self._given_basetemp
            if basetemp.exists():
                rm_rf(basetemp)
            basetemp.mkdir(mode=0o777)
            basetemp = basetemp.resolve()
        else:
            from_env = os.environ.get("PYTEST_DEBUG_TEMPROOT")
            temproot = Path(from_env or tempfile.gettempdir()).resolve()
            user = get_user() or "unknown"
            rootdir = temproot.joinpath(f"pytest-of-{user}")
            try:
                rootdir.mkdir(mode=0o777, exist_ok=True)
            except OSError:
                rootdir = temproot.joinpath("pytest-of-unknown")
                rootdir.mkdir(mode=0o777, exist_ok=True)
            uid = get_user_id()
            if uid is not None:
                rootdir_stat = rootdir.stat()
                if rootdir_stat.st_uid != uid:
                    raise OSError(
                        f"The temporary directory {rootdir} is not owned by the current user. "
                        "Fix this and try again."
                    )
                if (rootdir_stat.st_mode & 0o077) != 0:
                    os.chmod(rootdir, rootdir_stat.st_mode & ~0o077)
            basetemp = make_numbered_dir(root=rootdir, prefix="pytest-", mode=0o777)
        assert basetemp is not None, basetemp
        self._basetemp = basetemp
        self._trace("new basetemp", basetemp)
        return basetemp


if os.name == "nt":
    _ensure_repo_dirs()
    os.environ.setdefault("PYTEST_DEBUG_TEMPROOT", str(PYTEST_TEMP_ROOT))


@pytest.fixture(scope="session")
def tmp_path_factory(pytestconfig) -> WindowsTempPathFactory:
    if os.name != "nt":
        return pytestconfig._tmp_path_factory

    return WindowsTempPathFactory.from_config(pytestconfig, _ispytest=True)
