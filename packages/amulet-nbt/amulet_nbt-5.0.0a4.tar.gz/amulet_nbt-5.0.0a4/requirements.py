import os
from packaging.version import Version

import amulet_compiler_version

PYBIND11_REQUIREMENT = "==2.13.6"
AMULET_COMPILER_TARGET_REQUIREMENT = "==1.0"
AMULET_COMPILER_VERSION_REQUIREMENT = "==3.0.0"
AMULET_PYBIND11_EXTENSIONS_REQUIREMENT = "~=1.0"
AMULET_IO_REQUIREMENT = "~=1.0"
AMULET_ZLIB_REQUIREMENT = "~=1.0.0.0a1"
NUMPY_REQUIREMENT = "~=2.0"

if os.environ.get("AMULET_IO_REQUIREMENT", None):
    AMULET_IO_REQUIREMENT = (
        f"{AMULET_IO_REQUIREMENT},{os.environ['AMULET_IO_REQUIREMENT']}"
    )

if os.environ.get("AMULET_ZLIB_REQUIREMENT", None):
    AMULET_ZLIB_REQUIREMENT = (
        f"{AMULET_ZLIB_REQUIREMENT},{os.environ['AMULET_ZLIB_REQUIREMENT']}"
    )


def get_specifier_set(version_str: str) -> str:
    """
    version_str: The PEP 440 version number of the library.
    compiler_suffix_: Only specified if it is a compiled library and the compiler is being frozen.
    """
    version = Version(version_str)
    if version.epoch != 0 or version.is_devrelease or version.is_postrelease:
        raise RuntimeError(f"Unsupported version format. {version_str}")

    return f"~={version.major}.{version.minor}.{version.micro}.0{''.join(map(str, version.pre or ()))}"


if os.environ.get("AMULET_FREEZE_COMPILER", None):
    AMULET_COMPILER_VERSION_REQUIREMENT = f"=={amulet_compiler_version.__version__}"

    try:
        import amulet.io
    except ImportError:
        pass
    else:
        AMULET_IO_REQUIREMENT = get_specifier_set(amulet.io.__version__)

    try:
        import amulet.zlib
    except ImportError:
        pass
    else:
        AMULET_ZLIB_REQUIREMENT = get_specifier_set(amulet.zlib.__version__)


def get_build_dependencies() -> list:
    return [
        f"pybind11{PYBIND11_REQUIREMENT}",
        f"amulet_pybind11_extensions{AMULET_PYBIND11_EXTENSIONS_REQUIREMENT}",
        f"amulet-compiler-version{AMULET_COMPILER_VERSION_REQUIREMENT}",
        f"amulet_io{AMULET_IO_REQUIREMENT}",
        f"amulet_zlib{AMULET_ZLIB_REQUIREMENT}",
    ]


def get_runtime_dependencies() -> list[str]:
    return [
        f"numpy{NUMPY_REQUIREMENT}",
        f"amulet-compiler-target{AMULET_COMPILER_TARGET_REQUIREMENT}",
        f"amulet-compiler-version{AMULET_COMPILER_VERSION_REQUIREMENT}",
        f"amulet-io{AMULET_IO_REQUIREMENT}",
        f"amulet_zlib{AMULET_ZLIB_REQUIREMENT}",
    ]
