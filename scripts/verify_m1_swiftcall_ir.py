#!/usr/bin/env python3
"""Reject a Display allocating-initializer call that lacks Swift swiftself."""

import argparse
import pathlib
import re


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("llvm_ir")
    args = parser.parse_args()
    source = pathlib.Path(args.llvm_ir).read_text(encoding="utf-8")

    calls = re.findall(r"call\s+swiftcc\s+ptr\s+[^\n]+", source)
    allocating_calls = [line for line in calls if "swiftself" in line]
    if not allocating_calls:
        raise SystemExit("RED: generated LLVM IR has no swiftcc call carrying a swiftself argument")
    if not any(re.search(r"ptr\s+swiftself\s+[^,)]+\)", line) for line in allocating_calls):
        raise SystemExit("RED: swiftself is not the final class-metatype argument")

    print("GREEN: Swift allocating initializer call carries final swiftself class metatype")
    print(allocating_calls[0].strip())


if __name__ == "__main__":
    main()
