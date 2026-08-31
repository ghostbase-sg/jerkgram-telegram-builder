#!/usr/bin/env python3

"""Retired Build126 forwarding overlay.

It introduced a second ordinary Telegram "Forward" row and removed the
existing Jerkgram "Forward without author" action. The source owner is now
intentionally left untouched.
"""


def patch_text(text: str) -> str:
    return text


def main() -> None:
    print("[Build126 forward menu] retired; source owner unchanged")


if __name__ == "__main__":
    main()
