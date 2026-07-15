#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src"
))

star_gifts = (
    root
    / "submodules/TelegramCore/Sources/TelegramEngine/Payments/"
      "StarGifts.swift"
).read_text(encoding="utf-8")

payments = (
    root
    / "submodules/TelegramCore/Sources/TelegramEngine/Payments/"
      "TelegramEnginePayments.swift"
).read_text(encoding="utf-8")

settings = (
    root
    / "submodules/SettingsUI/Sources/GhostBase/"
      "GhostBaseSettingsController.swift"
).read_text(encoding="utf-8")

def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"[v1.0Z verifier] {message}")

for proof in (
    "GhostBaseStarGiftsCatalogResult",
    "getStarGifts(hash: 0)",
    "StarGift(apiStarGift:",
    "ghostBaseFetchStarGiftsCatalogDirect"
):
    require(
        proof in star_gifts + payments,
        f"missing direct catalog proof: {proof}"
    )

for proof in (
    "GhostBase v1.0Z Hidden Gifts direct catalog deep probe",
    "DIRECT_CATALOG",
    "catalog: absent",
    "catalogIndex",
    "fileId",
    "price:",
    "convertStars",
    "availability:",
    "soldOut:",
    "upgradeStars",
    "upgradeVariantsCount",
    "perUserLimit",
    "lockedUntilDate",
    "auctionSlug",
    "let plainForm = formProbe(false)",
    "let upgradedForm = formProbe(true)",
    "upgradeDelta"
):
    require(
        proof in settings,
        f"missing deep probe proof: {proof}"
    )

for gift_id in (
    "5956217000635139069",
    "5922558454332916696",
    "5800655655995968830",
    "5866352046986232958",
    "5801108895304779062",
    "5893356958802511476",
    "5935895822435615975",
    "5969796561943660080",
    "6026193266406327981"
):
    require(gift_id in settings, f"missing gift id: {gift_id}")

start = settings.index(
    "// MARK: GhostBase v1.0Z Hidden Gifts direct catalog deep probe"
)
end = settings.index(
    "private func ghostBaseSettingsEntries(",
    start
)
probe = settings[start:end]

for forbidden in (
    "sendStarsPaymentForm",
    "sendPaymentForm",
    "sendStarsForm"
):
    require(
        forbidden not in probe,
        f"forbidden payment method present: {forbidden}"
    )

print("[v1.0Z verifier] direct catalog hash=0 OK")
print("[v1.0Z verifier] full gift metadata OK")
print("[v1.0Z verifier] plain/upgrade form matrix OK")
print("[v1.0Z verifier] no-spend boundary OK")
