#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / (
    "work/swiftgram-src/submodules/SettingsUI/Sources/"
    "GhostBase/GhostBaseSettingsController.swift"
)

def need(value, message):
    if not value:
        raise RuntimeError(f"[v1.0V style] {message}")

need(FILE.is_file(), f"missing file: {FILE}")

text = FILE.read_text()
marker = "GhostBase v1.0V global-overlay style menu"

if marker in text:
    print("[v1.0V style] already applied")
    raise SystemExit

old = '''    var openSendTextStyleImpl: (() -> Void)?

    let arguments = GhostBaseSettingsArguments('''

new = '''    var openSendTextStyleImpl: (() -> Void)?

    // MARK: GhostBase v1.0V global-overlay style menu
    var presentInGlobalOverlayImpl:
        ((ViewController, Any?) -> Void)?

    let arguments = GhostBaseSettingsArguments('''

need(old in text, "overlay variable anchor missing")
text = text.replace(old, new, 1)

old = '''        controller.present(
            menu,
            in: .window(.root)
        )
'''

new = '''        presentInGlobalOverlayImpl?(
            menu,
            nil
        )
'''

need(old in text, "old root-window presentation missing")
text = text.replace(old, new, 1)

old = '''    pushController = { [weak controller] target in
        controller?.push(target)
    }
'''

new = '''    presentInGlobalOverlayImpl = { [weak controller] c, a in
        controller?.presentInGlobalOverlay(c, with: a)
    }

    pushController = { [weak controller] target in
        controller?.push(target)
    }
'''

need(old in text, "controller binding anchor missing")
text = text.replace(old, new, 1)

FILE.write_text(text)

print("[v1.0V style] global-overlay menu fix applied")
