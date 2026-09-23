# this_file: hatch_build.py
"""Hatch build hook: compile the dohnuts and pcdServer engines into the wheel.

The engines live in the `engines/` git submodules and build with CMake into single static executables,
which the wheel ships as `ornotto/_bin/dohnuts-cli` and `ornotto/_bin/pcd_server`. The wheel is then
tagged for the build platform (`py3-none-<platform>`), because the Python code is version-independent
and only the executables are not.

Environment:
    ORNOTTO_ENGINES=skip        build a pure wheel; ornotto then finds engines on PATH or via
                                ORNOTTO_DOHNUTS_BIN / ORNOTTO_PCD_BIN
    ORNOTTO_PLATFORM_TAG=TAG    wheel platform tag, e.g. manylinux_2_28_x86_64 (CI sets it)
    ORNOTTO_BUILD_DIR=DIR       CMake build directory (default build-engines/), reused between builds
    ORNOTTO_JOBS=N              parallel compile jobs
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

ROOT = Path(__file__).parent
EXE = ".exe" if sys.platform == "win32" else ""
# macOS 11+ wheel tags carry the major version only, so the deployment target is a .0 release.
MACOS_TARGET = "14.0"

# CMake arguments shared by both engines: static, portable (no -march=native), no OpenMP runtime to ship.
COMMON = [
    "-DCMAKE_BUILD_TYPE=Release",
    "-DBUILD_SHARED_LIBS=OFF",
    "-DGGML_NATIVE=OFF",
    "-DGGML_OPENMP=OFF",
    "-DLLAMA_CURL=OFF",
]


def platform_tag() -> str:
    """The wheel platform tag for this build."""
    if tag := os.environ.get("ORNOTTO_PLATFORM_TAG"):
        return tag
    machine = platform.machine().lower()
    if sys.platform == "darwin":
        major = MACOS_TARGET.split(".")[0]
        return f"macosx_{major}_0_{'arm64' if machine == 'arm64' else 'x86_64'}"
    if sys.platform == "win32":
        return "win_arm64" if machine in ("arm64", "aarch64") else "win_amd64"
    return f"linux_{machine}"  # local only; CI sets a manylinux tag


def engine_targets() -> dict[str, tuple[Path, list[str], str]]:
    """Engine name -> (source dir, extra CMake args, target)."""
    dohnuts = ["-DDOHNUTS_STATIC=ON"]
    if sys.platform == "darwin":
        # dohnuts uses std::jthread, which Apple's libc++ before LLVM 20 keeps behind this flag
        dohnuts += ["-DDOHNUTS_METAL=ON", "-DCMAKE_CXX_FLAGS=-fexperimental-library"]
    if sys.platform == "win32":
        # dohnuts builds llama.cpp as C++20, where u8"" literals are char8_t, which llama.cpp rejects
        dohnuts += ["-DCMAKE_CXX_FLAGS=/Zc:char8_t- /utf-8 /EHsc"]
    # cpp-httplib links any TLS or compression library it finds, and resolves names with getaddrinfo_a
    # (libanl on older glibc). The server only binds a loopback port, so it needs none of them.
    pcd = [
        f"-DHTTPLIB_USE_{lib}_IF_AVAILABLE=OFF"
        for lib in ("OPENSSL", "ZLIB", "BROTLI", "ZSTD", "MBEDTLS", "WOLFSSL")
    ]
    pcd += ["-DHTTPLIB_USE_NON_BLOCKING_GETADDRINFO=OFF"]
    if sys.platform == "win32":
        # The same char8_t problem in pcdServer's llama.cpp; nlohmann/json is then told it is on C++17
        # so it does not use the char8_t types the flag removes.
        json17 = "/DJSON_HAS_CPP_17 /DJSON_HAS_CPP_14 /DJSON_HAS_CPP_11"
        pcd += [f"-DCMAKE_CXX_FLAGS=/Zc:char8_t- /utf-8 /EHsc {json17}"]
    return {
        "dohnuts-cli": (ROOT / "engines" / "dohnuts.cpp", dohnuts, "dohnuts-cli"),
        "pcd_server": (ROOT / "engines" / "pcdServer", pcd, "pcd_server"),
    }


def cmake_build(name: str, source: Path, extra: list[str], target: str, build_root: Path) -> Path:
    """Configure and build one engine target; return the executable."""
    build = build_root / name
    args = [*COMMON, *extra]
    if sys.platform == "darwin":
        args += [
            f"-DCMAKE_OSX_DEPLOYMENT_TARGET={MACOS_TARGET}",
            f"-DCMAKE_OSX_ARCHITECTURES={platform.machine()}",
        ]
    if sys.platform == "win32":
        args += ["-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded"]  # no MSVC runtime DLLs to ship
    subprocess.run(["cmake", "-S", str(source), "-B", str(build), *args], check=True)
    jobs = os.environ.get("ORNOTTO_JOBS", str(os.cpu_count() or 2))
    subprocess.run(
        ["cmake", "--build", str(build), "--target", target, "--config", "Release", "-j", jobs], check=True
    )
    for candidate in (
        build / f"{target}{EXE}",
        build / "Release" / f"{target}{EXE}",
        build / "bin" / f"{target}{EXE}",
    ):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"{target}{EXE} not found under {build}")


class EngineBuildHook(BuildHookInterface):
    PLUGIN_NAME = "custom"

    def initialize(self, version: str, build_data: dict) -> None:
        # Editable installs find engines in src/ornotto/_bin (build.sh puts them there), on PATH, or via env.
        if (
            self.target_name != "wheel"
            or version == "editable"
            or os.environ.get("ORNOTTO_ENGINES") == "skip"
        ):
            return
        targets = engine_targets()
        missing = [str(src) for src, _, _ in targets.values() if not (src / "CMakeLists.txt").is_file()]
        if missing:
            self.app.display_warning(f"engine sources missing ({', '.join(missing)}): building a pure wheel")
            return
        if not shutil.which("cmake"):
            raise RuntimeError("cmake is required to build the engines (or set ORNOTTO_ENGINES=skip)")
        build_root = Path(os.environ.get("ORNOTTO_BUILD_DIR", ROOT / "build-engines"))
        for name, (source, extra, target) in targets.items():
            self.app.display_info(f"building {name} from {source.name}")
            exe = cmake_build(name, source, extra, target, build_root)
            build_data["force_include"][str(exe)] = f"ornotto/_bin/{name}{EXE}"
        build_data["pure_python"] = False
        build_data["tag"] = f"py3-none-{platform_tag()}"
