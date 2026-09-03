#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
AUDIT="$ROOT_DIR/scripts/audit_jerkgram_profile_renderer_runtime1.py"
FIXTURE=$(mktemp -d)
trap 'rm -rf "$FIXTURE"' EXIT

python3 "$AUDIT" --help >/dev/null 2>&1 || true

GHOSTBASE_SOURCE_ROOT="$FIXTURE" python3 "$AUDIT" | grep -Fx \
  'PROFILE_RENDERER_AUDIT: skip (generated background source is absent)'

BG_DIR="$FIXTURE/submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources"
mkdir -p "$BG_DIR"

cat > "$BG_DIR/GhostBaseProfileFullscreenBackground.swift" <<'EOF'
// MARK: GhostBase v1.1P VIDEO_MIRROR1
private var secondaryVideoDisposable: Disposable?
private var desiredVideoIdentity: String?
func refreshAnimatedVideoOwner(_ node: UniversalVideoNode?) {
    let _ = registerSecondaryVideoLayer(
        mirrorVideoView.videoLayer
    )
}
EOF

GHOSTBASE_SOURCE_ROOT="$FIXTURE" python3 "$AUDIT" | grep -Fx \
  'PROFILE_RENDERER_AUDIT: ready (single decoder + secondary renderer)'

printf '\nAVPlayer(\n' >> "$BG_DIR/GhostBaseProfileFullscreenBackground.swift"
GHOSTBASE_SOURCE_ROOT="$FIXTURE" python3 "$AUDIT" | grep -F \
  'PROFILE_RENDERER_AUDIT: hold (forbidden=AVPlayer()'

echo 'audit fixture tests: PASS'
