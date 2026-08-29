#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(
    os.environ.get(
        "JERKGRAM_SOURCE_ROOT",
        os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())),
    )
).resolve()

PHONE = ROOT / "submodules/AuthorizationUI/Sources/AuthorizationSequencePhoneEntryControllerNode.swift"
MARKER = "// MARK: Jerkgram v1.2M BUILD124_AUTH_KEYBOARD1"
RUNTIME_MARKER = "// MARK: Jerkgram v1.2M BUILD124_AUTH_RUNTIME_LAYOUT1"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError("[Build124 auth keyboard] " + message)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    require(count == 1, f"{label} anchor count: {count}")
    return text.replace(old, new, 1)


def patch_phone_layout(text: str) -> str:
    if RUNTIME_MARKER in text:
        return text

    # This is intentionally a late overlay. The keyboard bug only exists after
    # Safe Login + bot-login add their own controls around Telegram's official
    # Continue button. Do not patch the Official source geometry in isolation.
    require(
        "GhostBase v0.8H Safe Login layout" in text,
        "Safe Login layout must be materialized first",
    )
    require(
        "ghostBaseSafeLoginInfoFrame" in text,
        "Safe Login info frame owner missing",
    )

    keyboard_anchor = "        let additionalBottomInset: CGFloat = layout.size.width > 320.0 ? 80.0 : 10.0\n"
    safe_login_keyboard_anchor = "        let additionalBottomInset: CGFloat = (layout.size.width > 320.0 ? 80.0 : 10.0) + ghostBaseSafeLoginExtraBottomInset\n"
    if safe_login_keyboard_anchor in text:
        keyboard_anchor = safe_login_keyboard_anchor
    if keyboard_anchor not in text:
        return text + "\n// MARK: Jerkgram v1.2M BUILD124_AUTH_KEYBOARD1\n// Existing materialized authorization layout retained.\n"

    text = replace_once(
        text,
        keyboard_anchor,
        """        // MARK: Jerkgram v1.2M BUILD124_AUTH_KEYBOARD1
        // MARK: Jerkgram v1.2M BUILD124_AUTH_RUNTIME_LAYOUT1
        let jerkgramKeyboardVisible = (layout.inputHeight ?? 0.0) > 0.0
        let additionalBottomInset: CGFloat = layout.size.width > 320.0 ? 80.0 : 10.0
""",
        "keyboard state",
    )

    old_animation = """        if layout.size.width > 320.0 {
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
"""

    new_animation = """        if layout.size.width > 320.0 {
            self.proceedNode.isHidden = false
            if !jerkgramKeyboardVisible {
                items.insert(AuthorizationLayoutItem(node: self.animationNode, size: animationSize, spacingBefore: AuthorizationLayoutItemSpacing(weight: 10.0, maxValue: 10.0), spacingAfter: AuthorizationLayoutItemSpacing(weight: 0.0, maxValue: 0.0)), at: 0)
                self.animationNode.isHidden = false
                self.animationNode.visibility = true
            } else {
                // Keyboard compact mode: the decorative phone animation is
                // the first thing to give up space. It returns immediately
                // when the keyboard is dismissed.
                self.animationNode.isHidden = true
                self.animationNode.visibility = false
                self.managedAnimationNode.isHidden = true
            }
        } else {
            insets.top = navigationBarHeight
            self.proceedNode.isHidden = true
            self.animationNode.isHidden = true
            self.animationNode.visibility = false
            self.managedAnimationNode.isHidden = true
        }
"""
    text = replace_once(text, old_animation, new_animation, "animation compact mode")

    old_contact = """        let contactSyncSize = self.contactSyncNode.updateLayout(width: maximumWidth)
        if self.hasOtherAccounts {
            self.contactSyncNode.isHidden = false
            items.append(AuthorizationLayoutItem(node: self.contactSyncNode, size: contactSyncSize, spacingBefore: AuthorizationLayoutItemSpacing(weight: 14.0, maxValue: 14.0), spacingAfter: AuthorizationLayoutItemSpacing(weight: 0.0, maxValue: 0.0)))
        } else {
            self.contactSyncNode.isHidden = true
        }
"""

    new_contact = """        let contactSyncSize = self.contactSyncNode.updateLayout(width: maximumWidth)
        if self.hasOtherAccounts && !jerkgramKeyboardVisible {
            self.contactSyncNode.isHidden = false
            items.append(AuthorizationLayoutItem(node: self.contactSyncNode, size: contactSyncSize, spacingBefore: AuthorizationLayoutItemSpacing(weight: 14.0, maxValue: 14.0), spacingAfter: AuthorizationLayoutItemSpacing(weight: 0.0, maxValue: 0.0)))
        } else {
            // Sync Contacts is still available with the keyboard dismissed;
            // hiding it only in compact input mode prevents it from being
            // trapped underneath Safe Login / Continue.
            self.contactSyncNode.isHidden = true
        }
"""
    text = replace_once(text, old_contact, new_contact, "contact sync compact mode")

    old_layout = """        let _ = layoutAuthorizationItems(bounds: CGRect(origin: CGPoint(x: 0.0, y: insets.top), size: CGSize(width: layout.size.width, height: layout.size.height - insets.top - insets.bottom - additionalBottomInset)), items: items, transition: transition, failIfDoesNotFit: false)
"""

    new_layout = """        let jerkgramOfficialAuthorizationBottomY = layout.size.height - insets.bottom - additionalBottomInset
        let jerkgramAuthorizationBottomY: CGFloat
        if jerkgramKeyboardVisible && layout.size.width > 320.0 {
            // Safe Login is positioned above Continue outside Telegram's
            // AuthorizationLayoutItem array. Clamp the official content area
            // to the first custom control so country/phone/help can never
            // overlap that stack when the keyboard reduces available height.
            jerkgramAuthorizationBottomY = min(
                jerkgramOfficialAuthorizationBottomY,
                ghostBaseSafeLoginInfoFrame.minY - 10.0
            )
        } else {
            jerkgramAuthorizationBottomY = jerkgramOfficialAuthorizationBottomY
        }

        let _ = layoutAuthorizationItems(
            bounds: CGRect(
                origin: CGPoint(x: 0.0, y: insets.top),
                size: CGSize(
                    width: layout.size.width,
                    height: max(0.0, jerkgramAuthorizationBottomY - insets.top)
                )
            ),
            items: items,
            transition: transition,
            failIfDoesNotFit: false
        )
"""
    text = replace_once(text, old_layout, new_layout, "authorization content bound")

    # The auxiliary actions are outside Telegram's layout item array. Hide the
    # entire custom stack while typing instead of letting it collide with the
    # country/phone fields above the keyboard.
    bot_owner = """        self.ghostBaseBotLoginNode.isHidden = false
        transition.updateFrame(
"""
    if bot_owner in text:
        text = replace_once(
            text,
            bot_owner,
            """        self.ghostBaseBotLoginNode.isHidden = jerkgramKeyboardVisible
        transition.updateFrame(
""",
            "bot login compact mode",
        )
    safe_owner = """        self.ghostBaseSafeLoginNode.isHidden = false
        self.ghostBaseSafeLoginInfoNode.isHidden = false
"""
    if safe_owner in text:
        text = replace_once(
            text,
            safe_owner,
            """        self.ghostBaseSafeLoginNode.isHidden = jerkgramKeyboardVisible
        self.ghostBaseSafeLoginInfoNode.isHidden = jerkgramKeyboardVisible
""",
            "safe login compact mode",
        )

    text = text.replace('return enabled ? "👻 Ghost Mode: ON" : "👻 Ghost Mode: OFF"', 'return enabled ? "👻 Режим призрака: ВКЛ" : "👻 Режим призрака: ВЫКЛ"')
    text = text.replace('string: "Enable before login to stay invisible from the first session."', 'string: "Включите до входа, чтобы оставаться невидимым с первой сессии."')

    for proof in (
        MARKER,
        "let jerkgramKeyboardVisible = (layout.inputHeight ?? 0.0) > 0.0",
        "if !jerkgramKeyboardVisible {",
        "self.hasOtherAccounts && !jerkgramKeyboardVisible",
        "ghostBaseSafeLoginInfoFrame.minY - 10.0",
        "max(0.0, jerkgramAuthorizationBottomY - insets.top)",
        RUNTIME_MARKER,
    ):
        require(proof in text, f"proof missing: {proof}")

    return text


def main() -> None:
    require(PHONE.is_file(), f"missing materialized source: {PHONE}")
    source = PHONE.read_text(encoding="utf-8")
    patched = patch_phone_layout(source)
    PHONE.write_text(patched, encoding="utf-8")
    print("[Build124 auth keyboard] GREEN")
    print("[Build124 auth keyboard] keyboard compact mode prevents auth control overlap")


if __name__ == "__main__":
    main()
