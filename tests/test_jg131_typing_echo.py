"""One-event composer self-echo policy and exact-stage integration.

The Swift fixture executes the production generic policy on hosts with swiftc.
UIKit/IME integration still requires the full native composer harness.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PANEL = 'submodules/TelegramUI/Components/Chat/ChatTextInputPanelNode/Sources/ChatTextInputPanelNode.swift'
SOURCE = Path(os.environ.get('JG_TYPING_SOURCE', ROOT / 'work/swiftgram-src'))
BEGIN = '// BEGIN JerkgramSynchronousInputEchoPolicy'
END = '// END JerkgramSynchronousInputEchoPolicy'
FIXTURE = r'''
struct Content: Equatable { let text: String; let attributes: [String] }
struct Configuration: Equatable { let theme: Int; let font: Int; let spoiler: Bool; let emojis: Set<String> }
let node = NSObject()
let otherNode = NSObject()
let plain = Content(text: "hello", attributes: [])
let rich = Content(text: "hello", attributes: ["bold", "mention:7"])
let config = Configuration(theme: 1, font: 17, spoiler: false, emojis: ["😀"])
let caret = NSRange(location: 5, length: 0)
func token(_ value: Content = plain) -> JerkgramSynchronousInputEcho<Content, Configuration> {
    return JerkgramSynchronousInputEcho(node: node, content: value, selection: caret, configuration: config, literalText: value.text, displayText: NSAttributedString(string: value.text))
}
var echo = token()
var reads = 0
precondition(echo.consume(node: node, content: plain, selection: caret, configuration: config, literalText: { plain.text }, currentDisplayText: { NSAttributedString(string: plain.text) }, currentContent: { reads += 1; return plain }))
precondition(reads == 1)
precondition(!echo.consume(node: node, content: plain, selection: caret, configuration: config, literalText: { plain.text }, currentDisplayText: { NSAttributedString(string: plain.text) }, currentContent: { reads += 1; return plain }), "event was reused")
precondition(reads == 1, "consumed token re-read editor")
// Matching plain strings must not suppress changed rich attributes.
echo = token()
precondition(!echo.consume(node: node, content: rich, selection: caret, configuration: config, literalText: { plain.text }, currentDisplayText: { NSAttributedString(string: plain.text) }, currentContent: { fatalError("must reject cheap mismatch first") }))
echo = token(rich)
precondition(echo.consume(node: node, content: rich, selection: caret, configuration: config, literalText: { plain.text }, currentDisplayText: { NSAttributedString(string: plain.text) }, currentContent: { rich }))
echo = token()
precondition(!echo.consume(node: otherNode, content: plain, selection: caret, configuration: config, literalText: { plain.text }, currentDisplayText: { NSAttributedString(string: plain.text) }, currentContent: { fatalError("wrong node read") }))
precondition(!echo.consume(node: node, content: plain, selection: caret, configuration: config, literalText: { plain.text }, currentDisplayText: { NSAttributedString(string: plain.text) }, currentContent: { plain }), "mismatch did not consume event")
// Live mutation during a reentrant state callback invalidates the old observation.
echo = token()
precondition(!echo.consume(node: node, content: plain, selection: caret, configuration: config, literalText: { plain.text }, currentDisplayText: { NSAttributedString(string: plain.text) }, currentContent: { rich }))
// Selection changes, including a marked/selected UTF-16 range, always take normal set handling.
echo = token()
precondition(!echo.consume(node: node, content: plain, selection: NSRange(location: 1, length: 3), configuration: config, literalText: { plain.text }, currentDisplayText: { NSAttributedString(string: plain.text) }, currentContent: { plain }))
for changed in [Configuration(theme: 2, font: 17, spoiler: false, emojis: ["😀"]),
                Configuration(theme: 1, font: 20, spoiler: false, emojis: ["😀"]),
                Configuration(theme: 1, font: 17, spoiler: true, emojis: ["😀"]),
                Configuration(theme: 1, font: 17, spoiler: false, emojis: ["😀", "👍"])] {
    echo = token()
    precondition(!echo.consume(node: node, content: plain, selection: caret, configuration: changed, literalText: { plain.text }, currentDisplayText: { NSAttributedString(string: plain.text) }, currentContent: { plain }))
}
for text in ["e\u{301}", "é", "👨‍👩‍👧‍👦", "🇷🇺", "👍🏽", "正在输入"] {
    let content = Content(text: text, attributes: ["marked-or-rich"])
    let range = NSRange(location: 0, length: (text as NSString).length)
    var unicode = JerkgramSynchronousInputEcho(node: node, content: content, selection: range, configuration: config, literalText: text, displayText: NSAttributedString(string: text))
    precondition(unicode.consume(node: node, content: content, selection: range, configuration: config, literalText: { text }, currentDisplayText: { NSAttributedString(string: text) }, currentContent: { content }))
}
let precomposed = Content(text: "é", attributes: [])
let decomposed = Content(text: "e\u{301}", attributes: [])
precondition(precomposed == decomposed) // Swift equality alone is insufficient.
var normalization = JerkgramSynchronousInputEcho(node: node, content: precomposed,
    selection: NSRange(location: 0, length: 0), configuration: config, literalText: "é", displayText: NSAttributedString(string: "é"))
precondition(!normalization.consume(node: node, content: decomposed,
    selection: NSRange(location: 0, length: 0), configuration: config,
    literalText: { "e\u{301}" }, currentDisplayText: { NSAttributedString(string: "e\u{301}") }, currentContent: { decomposed }))
// A display-only reentrant change must still take the full setter path.
echo = token()
precondition(!echo.consume(node: node, content: plain, selection: caret, configuration: config,
    literalText: { plain.text }, currentDisplayText: {
        NSAttributedString(string: "hello", attributes: [NSAttributedString.Key("fixture.style"): "changed"])
    }, currentContent: { plain }))
// The scoped guard owns only a weak identity, never the editor itself.
weak var released: NSObject?
var lifetime: JerkgramSynchronousInputEcho<Content, Configuration>?
do {
    let temporary = NSObject(); released = temporary
    lifetime = JerkgramSynchronousInputEcho(node: temporary, content: plain, selection: caret, configuration: config, literalText: plain.text, displayText: NSAttributedString(string: plain.text))
}
precondition(released == nil)
withExtendedLifetime(lifetime) {}
print("PASS: one-shot identity, rich semantics, live reentrancy, selection, config, Unicode and lifetime")
'''

class TypingEchoTests(unittest.TestCase):
    def text(self):
        return (SOURCE / PANEL).read_text()

    def test_stage_owns_and_restores_the_original_panel(self):
        # This local regression fails before the new owner is registered.
        import json
        manifest = json.loads((ROOT / 'patches/jg131-performance-followup.sha256.json').read_text())
        self.assertIn(PANEL, manifest['owners'], 'panel self-echo optimization is absent from exact stage')
        import sys
        sys.path.insert(0, str(ROOT / 'scripts'))
        import materialize_jg131_performance_followup as stage
        import hashlib
        after = self.text().encode()
        before = stage.parent_bytes(PANEL, after)
        self.assertEqual(hashlib.sha256(before).hexdigest(), 'b024bb02f020dd0a63e45838212d7219e466f0ffb773ab2199751238c2bddb2c', 'panel parent is not the effective Build173 source')
        self.assertEqual(stage.parent_bytes(PANEL, before), before)

    def test_provenance_is_scoped_and_bypass_keeps_noncontent_updates(self):
        text = self.text()
        callback = text.split('    public func chatInputTextNodeDidUpdateText() {', 1)[1].split('    @objc public func editableTextNodeDidUpdateText', 1)[0]
        self.assertIn('defer { self.jerkgramSynchronousInputEcho = nil }', callback)
        self.assertIn('JerkgramSynchronousInputEcho(', callback)
        self.assertLess(callback.index('self.jerkgramSynchronousInputEcho = JerkgramSynchronousInputEcho('), callback.index('self.interfaceInteraction?.updateTextInputStateAndMode'))
        self.assertLess(callback.index('self.jerkgramSynchronousInputEcho = nil\n            }'), callback.index('self.interfaceInteraction?.updateInputLanguage'))
        # Both overloads must retain their layout/spoiler/accessory tail when content is skipped.
        for block in text.split('    public func updateInputTextState(')[1:3]:
            block = block.split('\n    public func ', 1)[0]
            self.assertIn('if !self.consumeJerkgramSynchronousInputEcho(state, node: richTextInputNode)', block)
            self.assertIn('self.updateTextNodeText(animated:', block)
            self.assertIn('self.updateSpoiler()', block)
            self.assertIn('self.updatingInputState = false', block)
        helper = text.split('    private func consumeJerkgramSynchronousInputEcho(', 1)[1].split('\n    public func ', 1)[0]
        self.assertIn('!node.usesNativeRichTextEngine', helper)
        self.assertIn('node.currentInputContent().content', helper)
        self.assertIn('node.selectedRange ==', helper)
        self.assertNotIn('inputText.string', helper)
        self.assertIn('textView.markedTextRange == nil', helper)
        self.assertIn('(echo.literalText as NSString).isEqual(to: node.text)', helper)
        self.assertIn('literalText: { attributedString(from: state.content).string }', helper)
        self.assertIn('currentDisplayText: { node.attributedText', helper)

    @unittest.skipUnless(shutil.which('swiftc'), 'Swift unavailable: production policy behavior executes in macOS CI')
    def test_actual_production_policy(self):
        text = self.text()
        self.assertIn(BEGIN, text)
        policy = text.split(BEGIN, 1)[1].split(END, 1)[0]
        # Widen file-private visibility for top-level fixture bindings; leave the implementation intact.
        policy = policy.replace('private struct JerkgramSynchronousInputEcho', 'struct JerkgramSynchronousInputEcho', 1)
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'main.swift'
            executable = Path(directory) / 'typing-echo'
            p.write_text('import Foundation\n' + policy + '\n' + FIXTURE)
            subprocess.run(['swiftc', '-swift-version', '5', '-warnings-as-errors', str(p), '-o', str(executable)], check=True)
            subprocess.run([str(executable)], check=True, timeout=15)

if __name__ == '__main__':
    unittest.main()
