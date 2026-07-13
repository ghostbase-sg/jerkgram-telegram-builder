from pathlib import Path

root = Path(__file__).resolve().parents[1]

voice = root / (
    "work/swiftgram-src/submodules/TelegramUI/Sources/Chat/"
    "ChatControllerMediaRecording.swift"
)

text = voice.read_text()

marker = "// MARK: GhostBase v1.0V scheduled voice native cleanup"
marker_pos = text.find(marker)

if marker_pos < 0:
    raise RuntimeError("[preflight] voice cleanup marker missing")

declaration = text.rfind(
    "let ghostBaseVoiceWasScheduled =",
    0,
    marker_pos
)

if declaration < 0:
    raise RuntimeError(
        "[preflight] voice scheduled declaration missing before cleanup"
    )

distance = marker_pos - declaration

if distance > 1800:
    raise RuntimeError(
        "[preflight] voice declaration is too far from cleanup"
    )

closure_start = text.rfind(
    "startStandalone(next:",
    0,
    marker_pos
)

if closure_start < 0 or declaration < closure_start:
    raise RuntimeError(
        "[preflight] voice declaration is outside enqueue completion"
    )

print("[preflight] v1.0V voice scope OK")
