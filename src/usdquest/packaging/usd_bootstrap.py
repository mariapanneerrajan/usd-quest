"""Wire up the OpenUSD runtime before any `from pxr import ...` happens.

Dev mode: points at the local C:\\code\\open_usd\\USDinst tree.
Packaged mode: points at the bundled USDinst inside the PyInstaller dist.

Must be imported *before* anything that touches pxr.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_BOOTSTRAPPED = False


def _dev_usd_root() -> Path | None:
    # Honor an explicit override first.
    override = os.environ.get("USDQUEST_USD_ROOT")
    if override:
        p = Path(override)
        if p.exists():
            return p

    # Known-good local install on this machine.
    candidate = Path(r"C:\code\open_usd\USDinst")
    if candidate.exists():
        return candidate

    return None


def _packaged_usd_root() -> Path | None:
    # When frozen by PyInstaller, the USDinst tree is bundled next to the exe.
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS) if hasattr(sys, "_MEIPASS") else Path(sys.executable).parent
        candidate = base / "USDinst"
        if candidate.exists():
            return candidate
    return None


def bootstrap() -> Path:
    """Configure env vars and sys.path so `from pxr import ...` works.

    Returns the resolved USDinst root. Idempotent.
    """
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        # Return whatever we chose last time.
        return Path(os.environ["USDQUEST_USD_ROOT"])

    root = _packaged_usd_root() or _dev_usd_root()
    if root is None:
        raise RuntimeError(
            "Could not locate an OpenUSD install. Set USDQUEST_USD_ROOT to the "
            "USDinst directory, or install USD at C:\\code\\open_usd\\USDinst."
        )

    bin_dir = root / "bin"
    lib_dir = root / "lib"
    py_dir = lib_dir / "python"
    plugin_dir = root / "plugin" / "usd"

    # Windows DLL search + tools on PATH.
    path_entries = [str(bin_dir), str(lib_dir)]
    os.environ["PATH"] = os.pathsep.join(path_entries + [os.environ.get("PATH", "")])

    # Python 3.8+ on Windows needs explicit DLL directories.
    if sys.platform == "win32" and hasattr(os, "add_dll_directory"):
        for d in (bin_dir, lib_dir):
            if d.exists():
                os.add_dll_directory(str(d))

    # Python bindings.
    if str(py_dir) not in sys.path:
        sys.path.insert(0, str(py_dir))

    # USD plugin discovery.
    existing_plug = os.environ.get("PXR_PLUGINPATH_NAME", "")
    if plugin_dir.exists() and str(plugin_dir) not in existing_plug:
        os.environ["PXR_PLUGINPATH_NAME"] = os.pathsep.join(
            [str(plugin_dir)] + ([existing_plug] if existing_plug else [])
        )

    os.environ["USDQUEST_USD_ROOT"] = str(root)
    _BOOTSTRAPPED = True
    return root


def resolved_root() -> Path:
    return Path(os.environ["USDQUEST_USD_ROOT"])
