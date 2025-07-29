import os
import amulet_compiler_version
from packaging.version import Version

AMULET_COMPILER_TARGET_REQUIREMENT = "==1.0"
AMULET_COMPILER_VERSION_REQUIREMENT = "==3.0.0"

PYBIND11_REQUIREMENT = "==2.13.6"
AMULET_PYBIND11_EXTENSIONS_REQUIREMENT = "~=1.0"


def get_specifier_set(version_str: str) -> str:
    """
    version_str: The PEP 440 version number of the library.
    """
    version = Version(version_str)
    if version.epoch != 0 or version.is_devrelease or version.is_postrelease:
        raise RuntimeError(f"Unsupported version format. {version_str}")

    return f"~={version.major}.{version.minor}.{version.micro}.0{''.join(map(str, version.pre or ()))}"


if os.environ.get("AMULET_FREEZE_COMPILER", None):
    AMULET_COMPILER_VERSION_REQUIREMENT = f"=={amulet_compiler_version.__version__}"


def get_build_dependencies() -> list:
    return [
        f"pybind11{PYBIND11_REQUIREMENT}",
        f"amulet_pybind11_extensions{AMULET_PYBIND11_EXTENSIONS_REQUIREMENT}",
        f"amulet-compiler-version{AMULET_COMPILER_VERSION_REQUIREMENT}",
    ]


def get_runtime_dependencies() -> list[str]:
    return [
        f"pybind11{PYBIND11_REQUIREMENT}",
        f"amulet-compiler-target{AMULET_COMPILER_TARGET_REQUIREMENT}",
        f"amulet-compiler-version{AMULET_COMPILER_VERSION_REQUIREMENT}",
        "platformdirs~=3.1",
    ]
