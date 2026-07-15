#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src"
))

path = root / (
    "submodules/SettingsUI/Sources/GhostBase/"
    "GhostBaseSettingsController.swift"
)

if not path.is_file():
    raise SystemExit(f"missing generated settings source: {path}")

text = path.read_text(encoding="utf-8")

def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(
            f"[v1.0ZA gifts send verifier] {message}"
        )

for proof in [
    "GhostBase v1.0ZA Hidden Gifts real send",
    "Hidden Gifts Send — реальное списание",
    "New Year Bear · ID 5956217000635139069",
    "Christmas Tree · ID 5922558454332916696",
    "Valentine Bear · ID 5800655655995968830",
    "March 8 Bear · ID 5866352046986232958",
    "Valentine Card · ID 5801108895304779062",
    "Leprechaun Bear · ID 5893356958802511476",
    "April 1 Bear · ID 5935895822435615975",
    "Easter Bear · ID 5969796561943660080",
    "Builder Bear · ID 6026193266406327981",
    "hiddenGiftSendConfirm",
    "hiddenGiftSendPay",
    "2. СПИСАТЬ 50 STARS И ОТПРАВИТЬ",
    "includeUpgrade: false",
    'form.invoice.currency == "XTR"',
    "guard total == 50",
    "guard !form.invoice.isTest",
    "fetchBotPaymentForm(",
    "sendStarsPaymentForm(",
    "ghostBaseHiddenGiftSendErrorText",
    "ghostBaseHiddenGiftSendResultText"
]:
    require(proof in text, f"missing proof: {proof}")

require(
    text.count("sendStarsPaymentForm(") == 1,
    "sendStarsPaymentForm must appear exactly once"
)

require(
    "retryRequest" not in text[
        text.index(
            "// MARK: GhostBase v1.0ZA Hidden Gifts real send"
        ):
    ],
    "payment implementation must not retry automatically"
)

deep_start = text.index(
    "// MARK: GhostBase v1.0Z Hidden Gifts direct catalog deep probe"
)
deep_end = text.index(
    "private func ghostBaseSettingsEntries(",
    deep_start
)

require(
    "sendStarsPaymentForm" not in text[deep_start:deep_end],
    "Deep Probe must remain no-spend"
)

require(
    text.index("hiddenGiftSendConfirm")
    < text.index("hiddenGiftSendPay"),
    "first confirmation must precede payment action"
)

print("[v1.0ZA gifts send verifier] nine selections OK")
print("[v1.0ZA gifts send verifier] Deep Probe remains no-spend")
print("[v1.0ZA gifts send verifier] double confirmation OK")
print("[v1.0ZA gifts send verifier] exact 50 XTR guard OK")
print("[v1.0ZA gifts send verifier] one no-retry payment RPC OK")
