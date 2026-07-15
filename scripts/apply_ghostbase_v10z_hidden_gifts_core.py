#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src"
))
dry_run = os.environ.get("GHOSTBASE_DRY_RUN") == "1"

star_gifts_path = root / (
    "submodules/TelegramCore/Sources/TelegramEngine/"
    "Payments/StarGifts.swift"
)
payments_path = root / (
    "submodules/TelegramCore/Sources/TelegramEngine/"
    "Payments/TelegramEnginePayments.swift"
)

for path in (star_gifts_path, payments_path):
    if not path.is_file():
        raise SystemExit(f"missing generated source: {path}")

star_gifts = star_gifts_path.read_text(encoding="utf-8")
payments = payments_path.read_text(encoding="utf-8")

core_marker = (
    "// MARK: GhostBase v1.0Z Hidden Gifts direct catalog"
)

core_anchor = (
    "func _internal_cachedStarGifts("
    "postbox: Postbox"
    ") -> Signal<StarGiftsList?, NoError> {"
)

core_block = r'''
// MARK: GhostBase v1.0Z Hidden Gifts direct catalog

public enum GhostBaseStarGiftsCatalogResult {
    case catalog(StarGiftsList)
    case notModified
    case failed(String)
}

func _internal_ghostBaseFetchStarGiftsCatalogDirect(
    network: Network
) -> Signal<GhostBaseStarGiftsCatalogResult, NoError> {
    return network.request(
        Api.functions.payments.getStarGifts(hash: 0)
    )
    |> map { result -> GhostBaseStarGiftsCatalogResult in
        switch result {
        case let .starGifts(starGiftsData):
            let list = StarGiftsList(
                items: starGiftsData.gifts.compactMap {
                    StarGift(apiStarGift: $0)
                },
                hashValue: starGiftsData.hash
            )
            return .catalog(list)

        case .starGiftsNotModified:
            return .notModified
        }
    }
    |> `catch` {
        error -> Signal<GhostBaseStarGiftsCatalogResult, NoError> in

        return .single(.failed(
            error.errorDescription ?? "UNKNOWN_RPC_ERROR"
        ))
    }
}

'''

if core_marker not in star_gifts:
    if core_anchor not in star_gifts:
        raise SystemExit("direct catalog core anchor not found")
    star_gifts = star_gifts.replace(
        core_anchor,
        core_block + core_anchor,
        1
    )

method_marker = (
    "public func ghostBaseFetchStarGiftsCatalogDirect()"
)

method_anchor = """        public func cachedStarGifts() -> Signal<[StarGift]?, NoError> {
"""

method_block = """        // MARK: GhostBase v1.0Z Hidden Gifts direct catalog

        public func ghostBaseFetchStarGiftsCatalogDirect()
        -> Signal<GhostBaseStarGiftsCatalogResult, NoError> {
            return _internal_ghostBaseFetchStarGiftsCatalogDirect(
                network: self.account.network
            )
        }

"""

if method_marker not in payments:
    if method_anchor not in payments:
        raise SystemExit("TelegramEngine Payments anchor not found")
    payments = payments.replace(
        method_anchor,
        method_block + method_anchor,
        1
    )

for proof in (
    "getStarGifts(hash: 0)",
    "GhostBaseStarGiftsCatalogResult",
    "ghostBaseFetchStarGiftsCatalogDirect"
):
    if proof not in star_gifts + payments:
        raise SystemExit(f"missing direct catalog proof: {proof}")

if dry_run:
    print(f"[DRY RUN] would update {star_gifts_path}")
    print(f"[DRY RUN] would update {payments_path}")
else:
    star_gifts_path.write_text(star_gifts, encoding="utf-8")
    payments_path.write_text(payments, encoding="utf-8")

print("[v1.0Z] Hidden Gifts direct catalog core OK")
