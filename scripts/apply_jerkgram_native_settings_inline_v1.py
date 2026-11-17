#!/usr/bin/env python3
"""Source-native Telegram ItemList inline disclosure.

This development-only overlay changes actual ItemListSwitchItem and
GhostBaseSettingsController. It does not create a SwiftUI clone, a new
navigation stack, or alternative Telegram row geometry.

Stage 1: expand the existing 'Show Profile Information' control without
changing its existing account-scoped setting keys or toggle behavior.
"""
import argparse
from pathlib import Path

SWITCH = "submodules/ItemListUI/Sources/Items/ItemListSwitchItem.swift"
SETTINGS = "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
S_MARK = "// Jerkgram native inline disclosure v1 — ItemListSwitchItem"
G_MARK = "// Jerkgram native inline disclosure v1 — SettingsUI"

def once(src, old, new, label):
    hits = src.count(old)
    if hits != 1:
        raise RuntimeError(f"{label}: expected one exact source anchor, found {hits}")
    return src.replace(old, new, 1)

def switch_patch(src):
    if S_MARK in src:
        raise RuntimeError("Native ItemList switch overlay already present: use --verify")
    src = once(src,
        "    let action: (() -> Void)?\n    public let tag: ItemListItemTag?",
        "    let action: (() -> Void)?\n"
        "    let inlineDisclosureExpanded: Bool\n"
        "    let inlineDisclosureAction: (() -> Void)?\n"
        "    let inlineDisclosureAccessibilityLabel: String?\n"
        "    public let tag: ItemListItemTag?", "switch properties")
    src = once(src,
        "action: (() -> Void)? = nil, tag: ItemListItemTag? = nil)",
        "action: (() -> Void)? = nil, inlineDisclosureExpanded: Bool = false, inlineDisclosureAction: (() -> Void)? = nil, inlineDisclosureAccessibilityLabel: String? = nil, tag: ItemListItemTag? = nil)",
        "switch initializer")
    src = once(src,
        "        self.action = action\n        self.tag = tag",
        "        self.action = action\n"
        "        self.inlineDisclosureExpanded = inlineDisclosureExpanded\n"
        "        self.inlineDisclosureAction = inlineDisclosureAction\n"
        "        self.inlineDisclosureAccessibilityLabel = inlineDisclosureAccessibilityLabel\n"
        "        self.tag = tag", "switch initializer fields")
    src = once(src,
        "    private let switchGestureNode: ASDisplayNode\n    private var disabledOverlayNode:",
        "    private let switchGestureNode: ASDisplayNode\n"
        "    // Jerkgram native inline disclosure v1 — ItemListSwitchItem\n"
        "    private var inlineDisclosureButton: UIButton?\n"
        "    private var disabledOverlayNode:", "native button declaration")
    src = once(src,
        "        self.switchGestureNode.view.addGestureRecognizer(UITapGestureRecognizer(target: self, action: #selector(self.tapGesture(_:))))",
        """        self.switchGestureNode.view.addGestureRecognizer(UITapGestureRecognizer(target: self, action: #selector(self.tapGesture(_:))))
        // Attached to Telegram's existing item node, above its regular switch
        // hit area. Never replaces row backgrounds, masks or scroll ownership.
        let inlineButton = UIButton(type: .system)
        // Use Telegram's own disclosure resource during item layout.
        inlineButton.addTarget(self, action: #selector(self.jerkgramInlineDisclosurePressed), for: .touchUpInside)
        inlineButton.isAccessibilityElement = true
        inlineButton.isHidden = true
        self.view.addSubview(inlineButton)
        self.inlineDisclosureButton = inlineButton""", "native disclosure button")
    src = once(src,
        "params.width - leftInset - params.rightInset - 64.0, height: CGFloat.greatestFiniteMagnitude",
        "params.width - leftInset - params.rightInset - (item.inlineDisclosureAction == nil ? 64.0 : 112.0), height: CGFloat.greatestFiniteMagnitude",
        "title width reserve")
    src = once(src,
        "params.width - leftInset - params.rightInset - 84.0, height: CGFloat.greatestFiniteMagnitude",
        "params.width - leftInset - params.rightInset - (item.inlineDisclosureAction == nil ? 84.0 : 128.0), height: CGFloat.greatestFiniteMagnitude",
        "secondary text width reserve")
    src = once(src,
        "params.width - params.rightInset - switchSize.width - 15.0, y: floor((contentSize.height - switchSize.height) / 2.0)",
        "params.width - params.rightInset - switchSize.width - (item.inlineDisclosureAction == nil ? 15.0 : 55.0), y: floor((contentSize.height - switchSize.height) / 2.0)",
        "switch frame controls")
    src = once(src,
        "                    strongSelf.switchGestureNode.isHidden = item.enableInteractiveChanges && item.enabled",
        """                    strongSelf.switchGestureNode.isHidden = item.enableInteractiveChanges && item.enabled
                    if let button = strongSelf.inlineDisclosureButton {
                        button.isHidden = item.inlineDisclosureAction == nil
                        if item.inlineDisclosureAction != nil {
                            button.frame = CGRect(
                                x: params.width - params.rightInset - 44.0,
                                y: floor((contentSize.height - 36.0) / 2.0),
                                width: 36.0, height: 36.0
                            )
                            button.setImage(PresentationResourcesItemList.disclosureArrowImage(item.presentationData.theme), for: .normal)
                            button.tintColor = item.presentationData.theme.list.itemSecondaryTextColor
                            button.accessibilityLabel = item.inlineDisclosureAccessibilityLabel
                            // Telegram's native right arrow: down when closed, up when open.
                            let rotation = CGAffineTransform(rotationAngle: item.inlineDisclosureExpanded ? -CGFloat.pi / 2.0 : CGFloat.pi / 2.0)
                            if animated && currentItem?.inlineDisclosureExpanded != item.inlineDisclosureExpanded {
                                UIView.animate(withDuration: 0.28, delay: 0.0, options: [.curveEaseInOut]) {
                                    button.transform = rotation
                                }
                            } else {
                                button.transform = rotation
                            }
                        }
                    }""",
        "inline disclosure layout")
    src = once(src,
        "    @objc private func switchValueChanged(_ switchView: UISwitch) {",
        """    @objc private func jerkgramInlineDisclosurePressed() {
        self.item?.inlineDisclosureAction?()
    }

    @objc private func switchValueChanged(_ switchView: UISwitch) {""",
        "inline button action")
    return src

def settings_patch(src):
    if G_MARK in src:
        raise RuntimeError("Native Settings overlay already present: use --verify")
    src = once(src,
        "    let openSendTextStyle: () -> Void\n",
        "    let openSendTextStyle: () -> Void\n"
        "    // Jerkgram native inline disclosure v1 — SettingsUI\n"
        "    let toggleInlineDisclosure: (String) -> Void\n",
        "settings arguments property")
    src = once(src,
        "        openSendTextStyle: @escaping () -> Void\n    ) {",
        "        openSendTextStyle: @escaping () -> Void,\n"
        "        toggleInlineDisclosure: @escaping (String) -> Void\n"
        "    ) {",
        "settings arguments initializer")
    src = once(src,
        "        self.openSendTextStyle = openSendTextStyle\n",
        "        self.openSendTextStyle = openSendTextStyle\n"
        "        self.toggleInlineDisclosure = toggleInlineDisclosure\n",
        "settings args assignment")
    src = once(src,
        "    case toggle(Int32, Int32, String, String, Bool, enabled: Bool = true)\n",
        "    case toggle(Int32, Int32, String, String, Bool, enabled: Bool = true)\n"
        "    case inlineToggle(Int32, Int32, String, String, Bool, Bool)\n",
        "entry case")
    src = once(src,
        "        case let .toggle(section, _, _, _, _, _):\n            return section",
        "        case let .toggle(section, _, _, _, _, _):\n            return section\n"
        "        case let .inlineToggle(section, _, _, _, _, _):\n            return section",
        "entry section")
    src = once(src,
        "        case let .toggle(section, index, _, _, _, _):\n            return section * 1000 + index",
        "        case let .toggle(section, index, _, _, _, _):\n            return section * 1000 + index\n"
        "        case let .inlineToggle(section, index, _, _, _, _):\n            return section * 1000 + index",
        "entry stable ID")
    src = once(src,
        "        case let .toggle(ls, li, lk, lt, lv, le):",
        """        case let .inlineToggle(ls, li, lk, lt, lv, lx):
            if case let .inlineToggle(rs, ri, rk, rt, rv, rx) = rhs {
                return ls == rs && li == ri && lk == rk && lt == rt && lv == rv && lx == rx
            }
            return false
        case let .toggle(ls, li, lk, lt, lv, le):""",
        "entry identity")
    src = once(src,
        "        case let .toggle(_, _, key, title, value, enabled):",
        """        case let .inlineToggle(_, _, key, title, value, expanded):
            let isRussian = presentationData.strings.jerkgram.languageCode.hasPrefix("ru")
            return ItemListSwitchItem(
                presentationData: presentationData,
                systemStyle: .glass,
                title: title,
                value: value,
                sectionId: self.section,
                style: .blocks,
                updated: { newValue in arguments.updateBool(key, newValue) },
                inlineDisclosureExpanded: expanded,
                inlineDisclosureAction: { arguments.toggleInlineDisclosure(key) },
                inlineDisclosureAccessibilityLabel: expanded
                    ? (isRussian ? "Свернуть параметры" : "Collapse options")
                    : (isRussian ? "Раскрыть параметры" : "Expand options")
            )
        case let .toggle(_, _, key, title, value, enabled):""",
        "entry native ItemList row")
    src = once(src,
        "    aboutCommunityState: JerkgramAboutChannelState\n) -> [GhostBaseSettingsEntry] {",
        "    aboutCommunityState: JerkgramAboutChannelState,\n"
        "    inlineExpanded: Set<String>\n"
        ") -> [GhostBaseSettingsEntry] {",
        "entries transient expanded argument")
    original_home='''        return [
            .header(0, strings.profileInformation),
            .toggle(0, 1, GhostBaseKey.profileEnabled, strings.showProfileInformation, state.profileEnabled),
            .toggle(0, 2, GhostBaseKey.showIds, strings.telegramId, state.showIds),
            .toggle(0, 3, GhostBaseKey.showDCs, "DC", state.showDCs),
            .toggle(0, 4, GhostBaseKey.showRegistration, strings.registrationDate, state.showRegistration),
            .header(1, strings.basicFunctions),
            .valueDisclosure(1, 50, strings.starsBalance, strings.starsOverrideSummary(state.localStarsEnabled, balance), nil, .stars),
            .valueDisclosure(1, 51, strings.gramBalance, strings.gramOverrideSummary(state.localGramEnabled, state.localGramAmount), "Item List/Icons/Gram", .gram),
            .header(2, strings.backup),
            .disclosure(2, 1, strings.dataAndBackup, "Item List/Icons/Stories", .dataAndBackup),
            .disclosure(2, 2, strings.localPremium, "Item List/Icons/Gram", .localPremium)
        ]'''
    native_home='''        var entries: [GhostBaseSettingsEntry] = [
            .header(0, strings.profileInformation),
            .inlineToggle(0, 1, GhostBaseKey.profileEnabled, strings.showProfileInformation, state.profileEnabled, inlineExpanded.contains(GhostBaseKey.profileEnabled))
        ]
        if inlineExpanded.contains(GhostBaseKey.profileEnabled) {
            entries.append(contentsOf: [
                .toggle(0, 2, GhostBaseKey.showIds, strings.telegramId, state.showIds),
                .toggle(0, 3, GhostBaseKey.showDCs, "DC", state.showDCs),
                .toggle(0, 4, GhostBaseKey.showRegistration, strings.registrationDate, state.showRegistration)
            ])
        }
        entries.append(contentsOf: [
            .header(1, strings.basicFunctions),
            .valueDisclosure(1, 50, strings.starsBalance, strings.starsOverrideSummary(state.localStarsEnabled, balance), nil, .stars),
            .valueDisclosure(1, 51, strings.gramBalance, strings.gramOverrideSummary(state.localGramEnabled, state.localGramAmount), "Item List/Icons/Gram", .gram),
            .header(2, strings.backup),
            .disclosure(2, 1, strings.dataAndBackup, "Item List/Icons/Stories", .dataAndBackup),
            .disclosure(2, 2, strings.localPremium, "Item List/Icons/Gram", .localPremium)
        ])
        return entries'''
    src=once(src,original_home,native_home,"profile information native inline group")
    src = once(src,
        "    let statePromise = ValuePromise(initialState, ignoreRepeated: false)\n",
        "    let statePromise = ValuePromise(initialState, ignoreRepeated: false)\n"
        "    // Transient per-screen UI state: no account storage or runtime policy changes.\n"
        "    let inlineExpandedValue = Atomic(value: Set<String>())\n"
        "    let inlineExpandedPromise = ValuePromise(Set<String>(), ignoreRepeated: true)\n",
        "UI disclosure state")
    src = once(src,
        "    }, openSendTextStyle: {\n        openSendTextStyleImpl?()\n    })",
        """    }, openSendTextStyle: {
        openSendTextStyleImpl?()
    }, toggleInlineDisclosure: { key in
        let next = inlineExpandedValue.modify { current -> Set<String> in
            var updated = current
            if updated.contains(key) { updated.remove(key) }
            else { updated.insert(key) }
            return updated
        }
        inlineExpandedPromise.set(next)
    })""",
        "native disclosure action binding")
    src = once(src,
        "    let signal = combineLatest(\n        context.sharedContext.presentationData,\n        jerkgramImportRefreshStateSignal,\n        aboutChannelSignal,",
        "    let stateAndDisclosure = combineLatest(jerkgramImportRefreshStateSignal, inlineExpandedPromise.get())\n"
        "    let signal = combineLatest(\n"
        "        context.sharedContext.presentationData,\n"
        "        stateAndDisclosure,\n"
        "        aboutChannelSignal,",
        "combineLatest with transient view state")
    src = once(src,
        "    |> map { presentationData, state, aboutChannelState, aboutCommunityState, _, ownPeer\n        -> (ItemListControllerState, (ItemListNodeState, Any)) in",
        "    |> map { presentationData, stateAndInline, aboutChannelState, aboutCommunityState, _, ownPeer\n"
        "        -> (ItemListControllerState, (ItemListNodeState, Any)) in\n"
        "        let state = stateAndInline.0\n"
        "        let inlineExpanded = stateAndInline.1",
        "map state projection")
    src = once(src,
        "                aboutCommunityState: aboutCommunityState\n            ),",
        "                aboutCommunityState: aboutCommunityState,\n"
        "                inlineExpanded: inlineExpanded\n"
        "            ),",
        "entries projection")
    src = once(src,
        "            style: .blocks,\n            animateChanges: false\n        )\n\n        return (controllerState, (listState, arguments))",
        "            style: .blocks,\n"
        "            animateChanges: page == .home\n"
        "        )\n\n        return (controllerState, (listState, arguments))",
        "native in-list animations")
    return src

def verify_source(sw, st):
    for mark, name, src in [(S_MARK, "ItemListSwitchItem", sw), (G_MARK, "SettingsUI", st)]:
        if src.count(mark) != 1:
            raise RuntimeError(f"{name}: wrong marker count")
    if "inlineDisclosureAction: { arguments.toggleInlineDisclosure(key) }" not in st:
        raise RuntimeError("Inline action is not bound to SettingsUI")
    if "animateChanges: page == .home" not in st:
        raise RuntimeError("In-list transition is not enabled")
    for key in ("GhostBaseKey.profileEnabled", "GhostBaseKey.showIds", "GhostBaseKey.showDCs", "GhostBaseKey.showRegistration"):
        if key not in st:
            raise RuntimeError(f"Original settings key missing: {key}")
    if "case let .toggle(_, _, key, title, value, enabled):" not in st:
        raise RuntimeError("Stock Telegram toggle owner changed")
    if "item.inlineDisclosureAction == nil ? 15.0 : 55.0" not in sw:
        raise RuntimeError("Native switch geometry was not reserved")
    print("SOURCE VERIFIED: native Telegram item/blocks/glass preserved; inline view state only")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--apply", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    root = args.source_root.resolve()
    a,b=root/SWITCH,root/SETTINGS
    if not a.is_file() or not b.is_file():
        raise RuntimeError("Expected exact Telegram ItemListUI and Jerkgram SettingsUI owners")
    original_sw,original_st=a.read_text(),b.read_text()
    if args.verify:
        verify_source(original_sw,original_st)
        return
    changed_sw=switch_patch(original_sw)
    changed_st=settings_patch(original_st)
    verify_source(changed_sw,changed_st)
    # All anchors checked and both replacements calculated before any write.
    a.write_text(changed_sw)
    b.write_text(changed_st)
    print("SOURCE PATCHED: real Telegram ItemListSwitchItem + Jerkgram settings")

if __name__ == "__main__":
    main()
