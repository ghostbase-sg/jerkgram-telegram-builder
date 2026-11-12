"""Focused source-bound checks; UIKit rendering remains a native/device gate.

Numerical checks execute the actual scalar Swift expressions after replacing
their input names. Structural checks cover ownership/lifecycle boundaries only.
"""
from pathlib import Path
import re
import os
import unittest

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT.parent / 'jerkgram-next/beta3'
SOURCE_ROOT = Path(os.environ.get('JG_BETA3_SOURCE', DRAFT / 'target-source'))
BEFORE_ROOT = Path(os.environ.get('JG_BETA3_BEFORE', DRAFT / 'target-baseline'))
OWNER = Path("submodules/TelegramUI/Components/Wallet/WalletScreen/Sources/WalletScreen.swift")
SOURCE = (SOURCE_ROOT / OWNER).read_text()


def scalar(expression, values):
    for name, value in sorted(values.items(), key=lambda pair: -len(pair[0])):
        expression = expression.replace(name, str(value))
    if not re.fullmatch(r"[\d. +*/()\-]+", expression):
        raise ValueError(expression)
    return eval(expression, {"__builtins__": {}}, {})


def contrast(foreground, background):
    def luminance(rgb):
        channels = [((rgb >> shift) & 255) / 255 for shift in (16, 8, 0)]
        channels = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in channels]
        return sum(c * weight for c, weight in zip(channels, (.2126, .7152, .0722)))
    first, second = sorted([luminance(foreground), luminance(background)])
    return (second + .05) / (first + .05)


class WalletEmptySurfaceTests(unittest.TestCase):
    def test_surface_follows_actual_inherited_admission_and_empty_selection(self):
        # Disabling glass, Reduce Transparency, absent backdrop, and navigation
        # outside Settings all reach inheritedSurface == false upstream.
        expression = re.search(r"let hasEmptyTransactionsSurface = (.+)", SOURCE)
        self.assertIsNotNone(expression, "empty Wallet has no scoped surface admission")
        expression = expression[1].replace("(environment.controller()?.jerkgramSettingsSurfaceActive ?? false)", "inheritedSurface")
        expression = expression.replace("&&", "and")
        for empty, inherited, wanted in [(False, False, False), (False, True, False), (True, False, False), (True, True, True)]:
            self.assertEqual(eval(expression, {"__builtins__": {}}, {"hasEmptyTransactions": empty, "inheritedSurface": inherited}), wanted)
        self.assertIn("self.emptyTransactionsSurfaceView.removeFromSuperview()", SOURCE)
        self.assertRegex(SOURCE, r"if !hasEmptyTransactionsSurface \{\s*self.emptyTransactionsSurfaceView.removeFromSuperview\(\)")
        self.assertIn("self.scrollView.insertSubview(self.emptyTransactionsSurfaceView, at: 0)", SOURCE)
        self.assertIn("self.emptyTransactionsSurfaceView.isUserInteractionEnabled = false", SOURCE)
        self.assertIn("self.emptyTransactionsSurfaceView.superview == nil ? .immediate : contentLayoutTransition", SOURCE)

    def test_opaque_panel_palette_has_readable_body_title_and_legal_links(self):
        background = re.search(r"emptyTransactionsSurfaceView, color: UIColor\(rgb: (0x[0-9a-f]+)\)\)", SOURCE)
        self.assertIsNotNone(background, "surface must darken actual imagery, not only text")
        for role in ["titleColor", "textColor", "accentColor"]:
            match = re.search(rf"let {role} = hasEmptyTransactionsSurface \? UIColor\(rgb: (0x[0-9a-f]+)\) : environment.theme\.", SOURCE)
            self.assertIsNotNone(match, f"missing scoped {role} / native theme fallback")
            self.assertGreaterEqual(contrast(int(match[1], 16), int(background[1], 16)), 4.5)
        self.assertIn("containerSize: CGSize(width: max(0.0, cardWidth - (hasEmptyTransactionsSurface ? 32.0 : 0.0)), height: 10000.0)", SOURCE)

    def test_panel_contains_benefits_and_legal_at_narrow_and_long_layouts(self):
        match = re.search(r"// Wallet empty surface frame\n.*?frame: CGRect\(\s*x: ([^\n]+),\s*y: ([^\n]+),\s*width: ([^\n]+),\s*height: ([^\n]+)\s*\)", SOURCE, re.S)
        self.assertIsNotNone(match, "missing panel geometry")
        expressions = [part.strip() for part in match.groups()]
        for width, left, right, info_y, info_h, footer_y, footer_h in [
            (320, 0, 0, 310, 240, 574, 64),
            (393, 0, 0, 330, 180, 738, 44),
            (700, 34, 20, 340, 420, 784, 100),
        ]:
            card_width = width - left - right - 32
            footer_max_y = footer_y + footer_h
            values = {"environment.safeInsets.left": left, "sideInset": 16, "cardWidth": card_width,
                      "emptyTransactionsOriginY": info_y, "contentHeight": footer_max_y}
            x, y, w, h = [scalar(part, values) for part in expressions]
            self.assertEqual(x, left + 16)
            self.assertEqual(w, card_width)
            self.assertLessEqual(y, info_y - 16)
            self.assertGreaterEqual(y + h, footer_max_y + 16)
            self.assertLessEqual(info_y + info_h, footer_y)
            self.assertLessEqual(x + w, width - right)

    def test_terms_interaction_and_existing_scroll_rules_survive(self):
        self.assertIn("self?.openTerms(url: url)", SOURCE)
        self.assertIn("availableSize.height - environment.safeInsets.bottom - emptyTransactionsFooterSize.height - 16.0", SOURCE)
        self.assertIn("contentHeight > availableSize.height + UIScreenPixel", SOURCE)
        self.assertIn("self.navigationItem.setLeftBarButton(backButtonInSideColumn ? nil", SOURCE)
        before = (BEFORE_ROOT / OWNER).read_text()
        for token in ["NotificationCenter.default.addObserver", "Timer(", "UIVisualEffectView(", "CADisplayLink("]:
            self.assertEqual(SOURCE.count(token), before.count(token))


if __name__ == "__main__":
    unittest.main()
