#!/usr/bin/env python3

from pathlib import Path
import os
import shutil


REPO = Path(__file__).resolve().parents[1]
PAYLOAD = REPO / "scripts/jerkgram_v12g_build118_storage1_payload/JerkgramRetention.swift"
ROOT = Path(
    os.environ.get(
        "JERKGRAM_SOURCE_ROOT",
        os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())),
    )
).resolve()
DESTINATION = ROOT / "submodules/JerkgramCore/Sources/JerkgramRetention.swift"


HISTORY_DAYS = {"disabled": 0, "days7": 7, "days30": 30, "days90": 90}
MEDIA_BYTES = {
    "disabled": 0,
    "megabytes250": 250 * 1_048_576,
    "megabytes500": 500 * 1_048_576,
    "gigabytes1": 1_073_741_824,
    "gigabytes2": 2 * 1_073_741_824,
    "gigabytes5": 5 * 1_073_741_824,
}


def require(value, message):
    if not value:
        raise RuntimeError("[Build118 storage] " + message)


def history_cutoff_ms(duration, now_ms):
    if duration == "forever":
        return None
    require(duration in HISTORY_DAYS, "unknown history duration: " + duration)
    return int(now_ms) - HISTORY_DAYS[duration] * 86_400_000


def media_budget_bytes(limit):
    if limit == "unlimited":
        return None
    require(limit in MEDIA_BYTES, "unknown media limit: " + limit)
    return MEDIA_BYTES[limit]


def media_eviction_plan(records, budget):
    if budget is None:
        return []
    total = sum(max(0, int(record["byteCount"])) for record in records)
    result = []
    for record in sorted(records, key=lambda item: (int(item["observedAtMs"]), str(item["eventId"]))):
        if total <= budget:
            break
        result.append(str(record["eventId"]))
        total -= max(0, int(record["byteCount"]))
    return result


def should_capture(duration, is_secret_chat, archive_secret_chats):
    if duration == "disabled":
        return False
    if is_secret_chat and not archive_secret_chats:
        return False
    return True


def main():
    require(PAYLOAD.is_file(), "retention payload missing")
    require(DESTINATION.parent.is_dir(), "JerkgramCore must be materialized first")
    require(not DESTINATION.exists(), "retention owner already exists")
    shutil.copy2(PAYLOAD, DESTINATION)
    print("[Build118 storage] account/chat retention and cleanup policy materialized")


if __name__ == "__main__":
    main()
