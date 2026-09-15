#!/usr/bin/env python3
"""Reject a Display allocating-initializer call that lacks Swift swiftself."""

import argparse
import pathlib
import re


def swiftself_call_line(source):
    calls = re.findall(r"^.*\bcall\s+swiftcc\s+ptr\b.*$", source, re.MULTILINE)
    second_argument_is_swiftself = re.compile(
        r"\(\s*ptr\b[^,]*,\s*ptr\b(?=[^)]*\bswiftself\b)[^)]*\)"
    )
    return next((line.strip() for line in calls if second_argument_is_swiftself.search(line)), None)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("llvm_ir")
    args = parser.parse_args()
    source = pathlib.Path(args.llvm_ir).read_text(encoding="utf-8")

    call_line = swiftself_call_line(source)
    if call_line is None:
        raise SystemExit("RED: generated LLVM IR has no swiftcc call with swiftself on its second argument")

    print("GREEN: Swift allocating initializer call carries swiftself as its second argument")
    print(call_line)


if __name__ == "__main__":
    main()
