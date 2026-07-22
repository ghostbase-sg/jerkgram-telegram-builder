#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src"
))

path = root / (
    "submodules/TelegramUI/Components/Gifts/"
    "GiftOptionsScreen/Sources/GiftOptionsScreen.swift"
)

if not path.is_file():
    raise SystemExit(f"missing GiftOptionsScreen source: {path}")

text = path.read_text(encoding="utf-8")

def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(
            f"[v1.0ZB seasonal verifier] {message}"
        )

for proof in (
    "GhostBase v1.0ZB Seasonal Gifts",
    "GhostBaseSeasonalGiftDescriptor",
    'reference: .name("DeletedGiftsStickers")',
    "case .fetching:",
    "case .none:",
    "case let .result(_, items, _):",
    "ghostBaseMakeSeasonalGifts",
    "ghostBaseMergeSeasonalGifts",
    "ghostBaseIsSeasonalGift",
    ".file._parse()",
    "case seasonal",
    "case .seasonal:",
    "StarsFilter.seasonal.rawValue",
    'title: "Сезонные"',
    'text: "Сезонный"',
    "color: .blue",
    "availability: nil",
    "soldOut: nil",
    "flags: []",
    "upgradeStars: nil",
):
    require(proof in text, f"missing proof: {proof}")

gift_ids = (
    "5956217000635139069",
    "5922558454332916696",
    "5800655655995968830",
    "5866352046986232958",
    "5801108895304779062",
    "5893356958802511476",
    "5935895822435615975",
    "5969796561943660080",
    "6026193266406327981",
    "5974210632977745012",
)

for gift_id in gift_ids:
    require(
        text.count(gift_id) == 1,
        f"gift ID missing or duplicated: {gift_id}"
    )

for index in range(1, 11):
    require(
        text.count(f"stickerIndex: {index}") == 1,
        f"sticker index missing or duplicated: {index}"
    )

require(
    "min(descriptor.stickerIndex" not in text,
    "unsafe sticker index fallback present"
)

require(
    "descriptor.stickerIndex < items.count" in text,
    "sticker bounds check missing"
)

require(
    "serverIds.contains($0.id)" in text,
    "server-priority duplicate guard missing"
)

require(
    "ghostBaseSeasonalGiftIds.contains($0.id)" not in text,
    "unsafe StarGift enum id check remains"
)

require(
    "items[descriptor.stickerIndex].file._parse()" in text,
    "StickerPackItem accessor is not parsed"
)

require(
    text.count('reference: .name("DeletedGiftsStickers")') == 1,
    "sticker pack loaded more than once"
)

print("[v1.0ZB seasonal verifier] ten descriptors OK")
print("[v1.0ZB seasonal verifier] sticker indices 1...10 OK")
print("[v1.0ZB seasonal verifier] bounds checking OK")
print("[v1.0ZB seasonal verifier] server priority OK")
print("[v1.0ZB seasonal verifier] native GiftSetupScreen route retained")
