from pathlib import Path
import importlib.util
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts/apply_jerkgram_v12m_build124_auth_keyboard1.py"


class Build124AuthKeyboardTests(unittest.TestCase):
    def load_patch(self):
        spec = importlib.util.spec_from_file_location("build124_auth_keyboard", PATCH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def fixture(self) -> str:
        return '''        let additionalBottomInset: CGFloat = layout.size.width > 320.0 ? 80.0 : 10.0
        
        var items: [AuthorizationLayoutItem] = [
            AuthorizationLayoutItem(node: self.titleNode, size: titleSize, spacingBefore: AuthorizationLayoutItemSpacing(weight: titleInset, maxValue: titleInset), spacingAfter: AuthorizationLayoutItemSpacing(weight: 0.0, maxValue: 0.0)),
            AuthorizationLayoutItem(node: self.noticeNode, size: noticeSize, spacingBefore: AuthorizationLayoutItemSpacing(weight: 18.0, maxValue: 18.0), spacingAfter: AuthorizationLayoutItemSpacing(weight: 0.0, maxValue: 0.0)),
            AuthorizationLayoutItem(node: self.phoneAndCountryNode, size: CGSize(width: maximumWidth, height: 115.0), spacingBefore: AuthorizationLayoutItemSpacing(weight: 30.0, maxValue: 30.0), spacingAfter: AuthorizationLayoutItemSpacing(weight: 0.0, maxValue: 0.0)),
        ]
        
        if layout.size.width > 320.0 {
            items.insert(AuthorizationLayoutItem(node: self.animationNode, size: animationSize, spacingBefore: AuthorizationLayoutItemSpacing(weight: 10.0, maxValue: 10.0), spacingAfter: AuthorizationLayoutItemSpacing(weight: 0.0, maxValue: 0.0)), at: 0)
            self.proceedNode.isHidden = false
            self.animationNode.isHidden = false
            self.animationNode.visibility = true
        } else {
            insets.top = navigationBarHeight
            self.proceedNode.isHidden = true
            self.animationNode.isHidden = true
            self.managedAnimationNode.isHidden = true
        }
        
        let contactSyncSize = self.contactSyncNode.updateLayout(width: maximumWidth)
        if self.hasOtherAccounts {
            self.contactSyncNode.isHidden = false
            items.append(AuthorizationLayoutItem(node: self.contactSyncNode, size: contactSyncSize, spacingBefore: AuthorizationLayoutItemSpacing(weight: 14.0, maxValue: 14.0), spacingAfter: AuthorizationLayoutItemSpacing(weight: 0.0, maxValue: 0.0)))
        } else {
            self.contactSyncNode.isHidden = true
        }
        
        transition.updateFrame(node: self.proceedNode, frame: buttonFrame)

        // MARK: GhostBase v0.8H Safe Login layout
        let ghostBaseSafeLoginButtonFrame = CGRect(origin: CGPoint(x: buttonFrame.minX, y: buttonFrame.minY - 10.0 - ghostBaseSafeLoginHeight), size: CGSize(width: proceedSize.width, height: ghostBaseSafeLoginHeight))
        let ghostBaseSafeLoginInfoFrame = CGRect(origin: CGPoint(x: buttonFrame.minX, y: ghostBaseSafeLoginButtonFrame.minY - 6.0 - ghostBaseSafeLoginInfoSize.height), size: ghostBaseSafeLoginInfoSize)
        transition.updateFrame(node: self.ghostBaseSafeLoginNode, frame: ghostBaseSafeLoginButtonFrame)
        transition.updateFrame(node: self.ghostBaseSafeLoginInfoNode, frame: ghostBaseSafeLoginInfoFrame)
        self.ghostBaseSafeLoginNode.isHidden = self.proceedNode.isHidden
        self.ghostBaseSafeLoginInfoNode.isHidden = self.proceedNode.isHidden
        
        self.animationNode.updateLayout(size: animationSize)
        
        let _ = layoutAuthorizationItems(bounds: CGRect(origin: CGPoint(x: 0.0, y: insets.top), size: CGSize(width: layout.size.width, height: layout.size.height - insets.top - insets.bottom - additionalBottomInset)), items: items, transition: transition, failIfDoesNotFit: false)
'''

    def test_keyboard_mode_removes_nonessential_items(self):
        module = self.load_patch()
        result = module.patch_phone_layout(self.fixture())
        self.assertIn("BUILD124_AUTH_KEYBOARD1", result)
        self.assertIn("BUILD124_AUTH_RUNTIME_LAYOUT1", result)
        self.assertIn("let jerkgramKeyboardVisible = (layout.inputHeight ?? 0.0) > 0.0", result)
        self.assertIn("if !jerkgramKeyboardVisible {", result)
        self.assertIn("self.animationNode.isHidden = true", result)
        self.assertIn("self.hasOtherAccounts && !jerkgramKeyboardVisible", result)

    def test_keyboard_content_stops_above_ghost_stack(self):
        module = self.load_patch()
        result = module.patch_phone_layout(self.fixture())
        self.assertIn("let jerkgramAuthorizationBottomY: CGFloat", result)
        self.assertIn("ghostBaseSafeLoginInfoFrame.minY - 10.0", result)
        self.assertIn("max(0.0, jerkgramAuthorizationBottomY - insets.top)", result)

    def test_normal_layout_keeps_official_bottom_formula(self):
        module = self.load_patch()
        result = module.patch_phone_layout(self.fixture())
        self.assertIn("layout.size.height - insets.bottom - additionalBottomInset", result)

    def test_prepatched_materialized_auth_owner_is_left_intact(self):
        module = self.load_patch()
        source = "// MARK: GhostBase v0.8H Safe Login layout\nlet ghostBaseSafeLoginInfoFrame = CGRect.zero\n"
        result = module.patch_phone_layout(source)
        self.assertIn("BUILD124_AUTH_KEYBOARD1", result)
        self.assertIn("ghostBaseSafeLoginInfoFrame", result)

    def test_patch_is_idempotent(self):
        module = self.load_patch()
        once = module.patch_phone_layout(self.fixture())
        self.assertEqual(once, module.patch_phone_layout(once))


if __name__ == "__main__":
    unittest.main()
