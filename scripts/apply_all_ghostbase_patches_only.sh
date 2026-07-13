#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="$ROOT/work/swiftgram-src"

cd "$SOURCE"

git reset --hard HEAD

rm -rf \
submodules/SettingsUI/Sources/GhostBase

rm -f \
submodules/TelegramCore/Sources/SyncCore/GhostBaseMessageAttribute.swift

python3 "$ROOT/scripts/apply_ghostbase_v10q_sh2_ot2_combined.py"
python3 "$ROOT/scripts/apply_ghostbase_v10r_menu.py"
python3 "$ROOT/scripts/apply_ghostbase_v10s_public_controls.py"
python3 "$ROOT/scripts/apply_ghostbase_v10s_post_share_fix.py"
python3 "$ROOT/scripts/apply_ghostbase_v10t.py"
python3 "$ROOT/scripts/apply_ghostbase_v10t_style_settings.py"
python3 "$ROOT/scripts/apply_ghostbase_v10t_style_menu.py"
python3 "$ROOT/scripts/apply_ghostbase_v10t_style_runtime.py"
python3 "$ROOT/scripts/apply_ghostbase_v10u.py"
python3 "$ROOT/scripts/apply_ghostbase_v10u_style_preview.py"
python3 "$ROOT/scripts/apply_ghostbase_v10u_appearance.py"
python3 "$ROOT/scripts/apply_ghostbase_v10w_voice_cleanup.py"
python3 "$ROOT/scripts/apply_ghostbase_v10w_forward_without_author.py"
python3 "$ROOT/scripts/apply_ghostbase_v10w_native_style_page.py"

echo "[patch-only] GhostBase through v1.0W applied"
