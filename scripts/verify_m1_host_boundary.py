#!/usr/bin/env python3
"""Verify the exact production Telegram 12.9.4 Display host boundary."""

import argparse
import hashlib
import struct
import zipfile


FRAMEWORK = "Payload/Telegram.app/Frameworks/TelegramUIFramework.framework/TelegramUIFramework"
INITIALIZER = "_$s7Display14ViewControllerC29navigationBarPresentationDataAcA010NavigationefG0CSg_tcfC"
DISPLAY_CLASS = "_OBJC_CLASS_$__TtC7Display14ViewController"


def read_uleb(data, offset):
    value = 0
    shift = 0
    while True:
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7f) << shift
        if byte < 0x80:
            return value, offset
        shift += 7


def exports(macho):
    if struct.unpack_from("<I", macho, 0)[0] != 0xfeedfacf:
        raise ValueError("TelegramUIFramework is not a thin arm64 Mach-O")
    command_count = struct.unpack_from("<I", macho, 16)[0]
    offset = 32
    export_range = None
    for _ in range(command_count):
        command, size = struct.unpack_from("<II", macho, offset)
        if command in (0x22, 0x80000022):
            fields = struct.unpack_from("<12I", macho, offset)
            export_range = fields[10], fields[11]
        offset += size
    if export_range is None:
        raise ValueError("missing LC_DYLD_INFO export trie")
    start, size = export_range
    trie = macho[start:start + size]
    result = set()

    def walk(node_offset, prefix):
        terminal_size, cursor = read_uleb(trie, node_offset)
        children = cursor + terminal_size
        if terminal_size:
            result.add(prefix)
        cursor = children + 1
        for _ in range(trie[children]):
            end = trie.index(0, cursor)
            edge = trie[cursor:end].decode("utf-8")
            cursor = end + 1
            child_offset, cursor = read_uleb(trie, cursor)
            walk(child_offset, prefix + edge)

    walk(0, "")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("ipa")
    args = parser.parse_args()
    with zipfile.ZipFile(args.ipa) as archive:
        framework = archive.read(FRAMEWORK)
    symbols = exports(framework)
    missing = {INITIALIZER, DISPLAY_CLASS} - symbols
    if missing:
        raise SystemExit("RED: missing production host exports: " + ", ".join(sorted(missing)))
    print("GREEN: production Display host boundary verified")
    print("initializer=" + INITIALIZER)
    print("class=" + DISPLAY_CLASS)
    print("TelegramUIFramework.sha256=" + hashlib.sha256(framework).hexdigest())


if __name__ == "__main__":
    main()
