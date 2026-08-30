#!/usr/bin/env python3
"""Package the audited sideload keychain compatibility library into Build126.

The app is deliberately left resign-ready: this script changes its main Mach-O
load commands and therefore does not pretend to produce an Apple signature.
The final installer (ESign) must sign the app bundle afterwards.
"""

import hashlib
import os
from pathlib import Path
import plistlib
import struct
import sys
import tempfile
import zipfile


ASSET = Path(__file__).resolve().parents[1] / "assets" / "sideloadKeychainFix.dylib"
EXPECTED_SHA256 = "f8d81929c4de5799c9f5cb5b3e7d7410a7374224bef63afe88128f66fc351d79"
INSTALL_NAME = "@executable_path/Frameworks/sideloadKeychainFix.dylib"
LC_LOAD_DYLIB = 0xC
LC_SEGMENT_64 = 0x19
LC_SYMTAB = 0x2
MACHO_64_LE = 0xFEEDFACF
FAT_MAGIC = 0xCAFEBABE
FAT_MAGIC_64 = 0xCAFEBABF


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build126 keychain package] " + message)


def dylib_command(path: str) -> bytes:
    raw_path = path.encode("utf-8") + b"\0"
    size = (24 + len(raw_path) + 7) & ~7
    return struct.pack("<IIIIII", LC_LOAD_DYLIB, size, 24, 0, 0, 0) + raw_path + b"\0" * (size - 24 - len(raw_path))


def _thin_load_commands(data: bytes | bytearray, start: int = 0, size: int | None = None):
    limit = len(data) if size is None else start + size
    require(start + 32 <= limit, "truncated 64-bit Mach-O header")
    magic = struct.unpack_from("<I", data, start)[0]
    require(magic == MACHO_64_LE, "only little-endian 64-bit Mach-O is supported")
    ncmds = struct.unpack_from("<I", data, start + 16)[0]
    sizeofcmds = struct.unpack_from("<I", data, start + 20)[0]
    commands_start = start + 32
    commands_end = commands_start + sizeofcmds
    require(commands_end <= limit, "load commands exceed Mach-O slice")
    result = []
    offset = commands_start
    for _ in range(ncmds):
        require(offset + 8 <= commands_end, "truncated Mach-O load command")
        command, command_size = struct.unpack_from("<II", data, offset)
        require(command_size >= 8 and offset + command_size <= commands_end, "invalid Mach-O load command")
        result.append((command, offset, command_size))
        offset += command_size
    require(offset == commands_end, "Mach-O load-command size mismatch")
    return result, commands_end, limit


def _slice_starts(data: bytes | bytearray):
    magic_be = struct.unpack_from(">I", data, 0)[0]
    if magic_be not in (FAT_MAGIC, FAT_MAGIC_64):
        return [(0, len(data))]
    require(len(data) >= 8, "truncated fat Mach-O header")
    count = struct.unpack_from(">I", data, 4)[0]
    entry_size = 32 if magic_be == FAT_MAGIC_64 else 20
    require(8 + count * entry_size <= len(data), "truncated fat architecture table")
    slices = []
    for index in range(count):
        offset = 8 + index * entry_size
        if magic_be == FAT_MAGIC_64:
            slice_offset, slice_size = struct.unpack_from(">QQ", data, offset + 8)
        else:
            slice_offset, slice_size = struct.unpack_from(">II", data, offset + 8)
        require(slice_offset + slice_size <= len(data), "fat Mach-O slice is outside binary")
        slices.append((slice_offset, slice_size))
    return slices


def _headerpad_limit(data: bytes | bytearray, start: int, slice_size: int, commands_end: int, commands) -> int:
    candidates = []
    for command, offset, command_size in commands:
        if command == LC_SEGMENT_64 and command_size >= 72:
            nsects = struct.unpack_from("<I", data, offset + 64)[0]
            require(72 + nsects * 80 <= command_size, "truncated LC_SEGMENT_64 sections")
            for index in range(nsects):
                section_offset = struct.unpack_from("<I", data, offset + 72 + index * 80 + 48)[0]
                if section_offset > commands_end - start:
                    candidates.append(start + section_offset)
        elif command == LC_SYMTAB and command_size >= 24:
            for relative in (8, 16):
                value = struct.unpack_from("<I", data, offset + relative)[0]
                if value > commands_end - start:
                    candidates.append(start + value)
    return min(candidates) if candidates else start + slice_size


def _loaded_dylib_paths_in_slice(data: bytes | bytearray, start: int, slice_size: int) -> list[str]:
    commands, _, _ = _thin_load_commands(data, start, slice_size)
    paths = []
    for command, offset, command_size in commands:
        if command != LC_LOAD_DYLIB:
            continue
        require(command_size >= 24, "short LC_LOAD_DYLIB")
        name_offset = struct.unpack_from("<I", data, offset + 8)[0]
        require(24 <= name_offset < command_size, "invalid LC_LOAD_DYLIB name offset")
        raw = bytes(data[offset + name_offset:offset + command_size]).split(b"\0", 1)[0]
        paths.append(raw.decode("utf-8"))
    return paths


def loaded_dylib_paths(data: bytes | bytearray) -> list[str]:
    paths = []
    for start, slice_size in _slice_starts(data):
        paths.extend(_loaded_dylib_paths_in_slice(data, start, slice_size))
    return paths


def inject_load_dylib(executable: bytes, install_name: str = INSTALL_NAME) -> bytes:
    mutable = bytearray(executable)
    for start, slice_size in _slice_starts(mutable):
        existing = _loaded_dylib_paths_in_slice(mutable, start, slice_size)
        if install_name in existing:
            continue
        commands, commands_end, _ = _thin_load_commands(mutable, start, slice_size)
        command = dylib_command(install_name)
        headerpad_end = _headerpad_limit(mutable, start, slice_size, commands_end, commands)
        require(commands_end + len(command) <= headerpad_end, "insufficient Mach-O headerpad for Build126 dylib")
        mutable[commands_end:commands_end + len(command)] = command
        ncmds = struct.unpack_from("<I", mutable, start + 16)[0]
        sizeofcmds = struct.unpack_from("<I", mutable, start + 20)[0]
        struct.pack_into("<I", mutable, start + 16, ncmds + 1)
        struct.pack_into("<I", mutable, start + 20, sizeofcmds + len(command))
    return bytes(mutable)


def approved_dylib(path: Path) -> bytes:
    require(path.is_file(), "approved dylib asset is missing: " + str(path))
    data = path.read_bytes()
    require(hashlib.sha256(data).hexdigest() == EXPECTED_SHA256, "approved dylib SHA-256 mismatch")
    return data


def package_ipa(ipa: Path, dylib: Path = ASSET) -> None:
    dylib_data = approved_dylib(dylib)
    require(ipa.is_file(), "IPA missing: " + str(ipa))
    with tempfile.TemporaryDirectory(prefix="jerkgram-build126-keychain-") as directory:
        root = Path(directory)
        with zipfile.ZipFile(ipa, "r") as archive:
            infos = archive.infolist()
            archive.extractall(root)
        apps = list((root / "Payload").glob("*.app"))
        require(len(apps) == 1, "expected exactly one main app")
        app = apps[0]
        info = plistlib.loads((app / "Info.plist").read_bytes())
        executable_name = info.get("CFBundleExecutable")
        require(isinstance(executable_name, str) and executable_name, "main executable key missing")
        executable_path = app / executable_name
        require(executable_path.is_file(), "main executable missing")
        frameworks = app / "Frameworks"
        frameworks.mkdir(exist_ok=True)
        embedded = frameworks / "sideloadKeychainFix.dylib"
        executable_path.write_bytes(inject_load_dylib(executable_path.read_bytes()))
        embedded.write_bytes(dylib_data)
        fd, temporary_name = tempfile.mkstemp(prefix=ipa.name + ".build126.", suffix=".tmp", dir=str(ipa.parent))
        os.close(fd)
        temporary = Path(temporary_name)
        try:
            with zipfile.ZipFile(temporary, "w") as output:
                for info in infos:
                    source = root / info.filename
                    if source.exists():
                        output.writestr(info, b"" if info.is_dir() else source.read_bytes())
                extra = embedded.relative_to(root).as_posix()
                if extra not in {info.filename for info in infos}:
                    output.writestr(extra, embedded.read_bytes())
            os.replace(temporary, ipa)
        finally:
            if temporary.exists():
                temporary.unlink()


def main() -> None:
    ipa = Path(sys.argv[1] if len(sys.argv) > 1 else "work/swiftgram-src/ghostbase-final/GhostBase.ipa").resolve()
    package_ipa(ipa)
    print("[Build126 keychain package] GREEN")
    print("[Build126 keychain package] main app only; ESign must sign the final IPA")


if __name__ == "__main__":
    main()
