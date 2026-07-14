#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src"
))
dry_run = os.environ.get("GHOSTBASE_DRY_RUN") == "1"

pc_path = root / "submodules/AuthorizationUI/Sources/AuthorizationSequencePasswordEntryController.swift"
pn_path = root / "submodules/AuthorizationUI/Sources/AuthorizationSequencePasswordEntryControllerNode.swift"
fc_path = root / "submodules/AuthorizationUI/Sources/AuthorizationSequencePhoneEntryController.swift"
fn_path = root / "submodules/AuthorizationUI/Sources/AuthorizationSequencePhoneEntryControllerNode.swift"

for path in (pc_path, pn_path, fc_path, fn_path):
    if not path.is_file():
        raise SystemExit(f"missing source: {path}")

def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f"anchor not found: {label}")
    return text.replace(old, new, 1)

def save(path: Path, text: str) -> None:
    if dry_run:
        print(f"[DRY RUN] would update {path}")
    else:
        path.write_text(text, encoding="utf-8")

pc = pc_path.read_text(encoding="utf-8")

pc = replace_once(
    pc,
    "final class AuthorizationSequencePasswordEntryController: ViewController {",
    """// MARK: GhostBase v1.0Y Bot Login UI
enum AuthorizationSequencePasswordEntryMode: Equatable {
    case password
    case ghostBaseBotToken
}

final class AuthorizationSequencePasswordEntryController: ViewController {""",
    "password entry mode"
)

pc = replace_once(
    pc,
    """    private let sharedContext: SharedAccountContext
    private let presentationData: PresentationData
""",
    """    private let sharedContext: SharedAccountContext
    private let presentationData: PresentationData
    private let mode: AuthorizationSequencePasswordEntryMode
""",
    "password controller mode property"
)

pc = replace_once(
    pc,
    """    init(sharedContext: SharedAccountContext, presentationData: PresentationData, back: @escaping () -> Void) {
        self.sharedContext = sharedContext
        self.presentationData = presentationData
""",
    """    init(sharedContext: SharedAccountContext, presentationData: PresentationData, back: @escaping () -> Void, mode: AuthorizationSequencePasswordEntryMode = .password) {
        self.sharedContext = sharedContext
        self.presentationData = presentationData
        self.mode = mode
""",
    "password controller initializer"
)

pc = replace_once(
    pc,
    """        self.displayNode = AuthorizationSequencePasswordEntryControllerNode(strings: self.presentationData.strings, theme: self.presentationData.theme)
""",
    """        self.displayNode = AuthorizationSequencePasswordEntryControllerNode(strings: self.presentationData.strings, theme: self.presentationData.theme, mode: self.mode)
""",
    "password node creation"
)

pc = replace_once(
    pc,
    """    @objc func nextPressed() {
        if self.controllerNode.currentPassword.isEmpty {
            self.hapticFeedback.error()
            self.controllerNode.animateError()
        } else {
            self.loginWithPassword?(self.controllerNode.currentPassword)
        }
    }
""",
    """    @objc func nextPressed() {
        let value = self.controllerNode.currentPassword
        if value.isEmpty {
            self.hapticFeedback.error()
            self.controllerNode.animateError()
        } else {
            if self.mode == .ghostBaseBotToken {
                self.controllerNode.clearInput()
            }
            self.loginWithPassword?(value)
        }
    }
""",
    "secure token capture"
)

pn = pn_path.read_text(encoding="utf-8")

pn = replace_once(
    pn,
    """    private let strings: PresentationStrings
    private let theme: PresentationTheme
""",
    """    private let strings: PresentationStrings
    private let theme: PresentationTheme
    private let mode: AuthorizationSequencePasswordEntryMode
""",
    "password node mode property"
)

pn = replace_once(
    pn,
    """    init(strings: PresentationStrings, theme: PresentationTheme) {
        self.strings = strings
        self.theme = theme
""",
    """    init(strings: PresentationStrings, theme: PresentationTheme, mode: AuthorizationSequencePasswordEntryMode = .password) {
        self.strings = strings
        self.theme = theme
        self.mode = mode
""",
    "password node initializer"
)

pn = replace_once(
    pn,
    """        self.titleNode.attributedText = NSAttributedString(string: strings.LoginPassword_Title, font: Font.semibold(28.0), textColor: self.theme.list.itemPrimaryTextColor)
""",
    """        self.titleNode.attributedText = NSAttributedString(string: mode == .ghostBaseBotToken ? "Вход как бот" : strings.LoginPassword_Title, font: Font.semibold(28.0), textColor: self.theme.list.itemPrimaryTextColor)
""",
    "bot login title"
)

pn = replace_once(
    pn,
    """        self.noticeNode.attributedText = NSAttributedString(string: strings.TwoStepAuth_EnterPasswordHelp, font: Font.regular(17.0), textColor: self.theme.list.itemPrimaryTextColor, paragraphAlignment: .center)
""",
    """        self.noticeNode.attributedText = NSAttributedString(string: mode == .ghostBaseBotToken ? "Введите токен, выданный BotFather. Токен не сохраняется." : strings.TwoStepAuth_EnterPasswordHelp, font: Font.regular(17.0), textColor: self.theme.list.itemPrimaryTextColor, paragraphAlignment: .center)
""",
    "bot login notice"
)

pn = replace_once(
    pn,
    """        self.codeField.textField.accessibilityHint = self.strings.Login_VoiceOver_Password
""",
    """        self.codeField.textField.accessibilityHint = self.strings.Login_VoiceOver_Password
        if mode == .ghostBaseBotToken {
            self.codeField.textField.attributedPlaceholder = NSAttributedString(string: "123456789:AA…", font: Font.regular(20.0), textColor: self.theme.list.itemPlaceholderTextColor)
            self.codeField.textField.textContentType = nil
            self.codeField.textField.autocorrectionType = .no
            self.codeField.textField.autocapitalizationType = .none
            self.codeField.textField.spellCheckingType = .no
            self.codeField.textField.smartQuotesType = .no
            self.codeField.textField.smartDashesType = .no
        }
""",
    "bot token text field policy"
)

pn = replace_once(
    pn,
    """        self.titleNode.attributedText = NSAttributedString(string: self.strings.LoginPassword_Title, font: Font.semibold(28.0), textColor: self.theme.list.itemPrimaryTextColor)
""",
    """        self.titleNode.attributedText = NSAttributedString(string: self.mode == .ghostBaseBotToken ? "Вход как бот" : self.strings.LoginPassword_Title, font: Font.semibold(28.0), textColor: self.theme.list.itemPrimaryTextColor)
""",
    "bot title layout"
)

pn = replace_once(
    pn,
    """        items.append(AuthorizationLayoutItem(node: self.forgotNode, size: forgotSize, spacingBefore: AuthorizationLayoutItemSpacing(weight: 48.0, maxValue: 100.0), spacingAfter: AuthorizationLayoutItemSpacing(weight: 0.0, maxValue: 0.0)))
        
        if self.didForgotWithNoRecovery || self.suggestReset {
            self.resetNode.isHidden = false
            items.append(AuthorizationLayoutItem(node: self.resetNode, size: resetSize, spacingBefore: AuthorizationLayoutItemSpacing(weight: 10.0, maxValue: 10.0), spacingAfter: AuthorizationLayoutItemSpacing(weight: 0.0, maxValue: 0.0)))
        } else {
            self.resetNode.isHidden = true
        }
""",
    """        if self.mode == .password {
            self.forgotNode.isHidden = false
            items.append(AuthorizationLayoutItem(node: self.forgotNode, size: forgotSize, spacingBefore: AuthorizationLayoutItemSpacing(weight: 48.0, maxValue: 100.0), spacingAfter: AuthorizationLayoutItemSpacing(weight: 0.0, maxValue: 0.0)))
            
            if self.didForgotWithNoRecovery || self.suggestReset {
                self.resetNode.isHidden = false
                items.append(AuthorizationLayoutItem(node: self.resetNode, size: resetSize, spacingBefore: AuthorizationLayoutItemSpacing(weight: 10.0, maxValue: 10.0), spacingAfter: AuthorizationLayoutItemSpacing(weight: 0.0, maxValue: 0.0)))
            } else {
                self.resetNode.isHidden = true
            }
        } else {
            self.forgotNode.isHidden = true
            self.resetNode.isHidden = true
        }
""",
    "hide password recovery"
)

pn = replace_once(
    pn,
    """        self.codeField.textField.attributedPlaceholder = NSAttributedString(string: hint, font: Font.regular(20.0), textColor: self.theme.list.itemPlaceholderTextColor)
""",
    """        if self.mode == .password {
            self.codeField.textField.attributedPlaceholder = NSAttributedString(string: hint, font: Font.regular(20.0), textColor: self.theme.list.itemPlaceholderTextColor)
        }
""",
    "preserve bot token placeholder"
)

pn = replace_once(
    pn,
    """    func animateError() {
        self.codeField.layer.addShakeAnimation()
    }
""",
    """    func clearInput() {
        self.codeField.textField.text = ""
        self.proceedNode.isEnabled = false
    }
    
    func animateError() {
        self.codeField.layer.addShakeAnimation()
    }
""",
    "clear bot token input"
)

fn = fn_path.read_text(encoding="utf-8")

fn = replace_once(
    fn,
    """    private let proceedNode: SolidRoundedButtonNode
""",
    """    private let proceedNode: SolidRoundedButtonNode
    private let ghostBaseBotLoginNode: HighlightableButtonNode
""",
    "bot login button property"
)

# Remove the old accidental placement inside PhoneAndCountryNode.
wrong_callback_location = """    var selectCountryCode: (() -> Void)?
    var checkPhone: (() -> Void)?
    var loginAsBot: (() -> Void)?
    var hasNumberUpdated: ((Bool) -> Void)?
"""

correct_phone_callback_block = """    var selectCountryCode: (() -> Void)?
    var checkPhone: (() -> Void)?
    var hasNumberUpdated: ((Bool) -> Void)?
"""

if wrong_callback_location in fn:
    fn = fn.replace(
        wrong_callback_location,
        correct_phone_callback_block,
        1
    )

node_class_anchor = (
    "final class AuthorizationSequencePhoneEntryControllerNode: "
    "ASDisplayNode {"
)

node_class_start = fn.find(node_class_anchor)

if node_class_start == -1:
    raise SystemExit(
        "anchor not found: phone entry controller node class"
    )

node_class_source = fn[node_class_start:]

if "    var loginAsBot: (() -> Void)?\n" not in node_class_source:
    callback_anchor = "    var retryPasskey: (() -> Void)?\n"
    callback_position = fn.find(
        callback_anchor,
        node_class_start
    )

    if callback_position == -1:
        raise SystemExit(
            "anchor not found: controller node retryPasskey"
        )

    callback_end = callback_position + len(callback_anchor)

    fn = (
        fn[:callback_end]
        + "\n"
        + "    var loginAsBot: (() -> Void)?\n"
        + fn[callback_end:]
    )

fn = replace_once(
    fn,
    """            self.phoneAndCountryNode.countryButton.isEnabled = !self.inProgress
""",
    """            self.phoneAndCountryNode.countryButton.isEnabled = !self.inProgress
            self.ghostBaseBotLoginNode.isEnabled = !self.inProgress
            self.ghostBaseBotLoginNode.alpha = self.inProgress ? 0.5 : 1.0
""",
    "bot button progress state"
)

fn = replace_once(
    fn,
    """        self.proceedNode.accessibilityIdentifier = "Auth.PhoneEntry.ContinueButton"
""",
    """        self.proceedNode.accessibilityIdentifier = "Auth.PhoneEntry.ContinueButton"

        self.ghostBaseBotLoginNode = HighlightableButtonNode()
        self.ghostBaseBotLoginNode.setAttributedTitle(NSAttributedString(string: "Войти как бот — Экспериментально", font: Font.regular(16.0), textColor: self.theme.list.itemAccentColor, paragraphAlignment: .center), for: [])
        self.ghostBaseBotLoginNode.accessibilityLabel = "Войти как бот"
        self.ghostBaseBotLoginNode.accessibilityTraits = [.button]
        self.ghostBaseBotLoginNode.isHidden = !hasOtherAccounts
""",
    "create bot login button"
)

fn = replace_once(
    fn,
    """        self.addSubnode(self.proceedNode)
""",
    """        self.addSubnode(self.proceedNode)
        self.addSubnode(self.ghostBaseBotLoginNode)
""",
    "add bot login button"
)

fn = replace_once(
    fn,
    """        self.proceedNode.pressed = { [weak self] in
            self?.checkPhone?()
        }
""",
    """        self.proceedNode.pressed = { [weak self] in
            self?.checkPhone?()
        }
        self.ghostBaseBotLoginNode.addTarget(self, action: #selector(self.ghostBaseBotLoginPressed), forControlEvents: .touchUpInside)
""",
    "bot button action"
)

fn = replace_once(
    fn,
    """    deinit {
        self.exportTokenDisposable.dispose()
""",
    """    @objc private func ghostBaseBotLoginPressed() {
        self.loginAsBot?()
    }
    
    deinit {
        self.exportTokenDisposable.dispose()
""",
    "bot button selector"
)

if "let botLoginReservedHeight: CGFloat" not in fn:
    layout_start = """        let buttonFrame: CGRect
"""

    layout_start_replacement = """        let botLoginSize = self.ghostBaseBotLoginNode.measure(
            CGSize(
                width: maximumWidth - inset * 2.0,
                height: 44.0
            )
        )
        let botLoginReservedHeight: CGFloat =
            self.hasOtherAccounts ? 40.0 : 0.0

        let buttonFrame: CGRect
"""

    if layout_start not in fn:
        raise SystemExit(
            "anchor not found: bot layout declaration"
        )

    fn = fn.replace(
        layout_start,
        layout_start_replacement,
        1
    )

    old_button_frame = """            buttonFrame = CGRect(origin: CGPoint(x: floorToScreenPixels((layout.size.width - proceedSize.width) / 2.0), y: layout.size.height - insets.bottom - proceedSize.height - inset), size: proceedSize)
"""

    new_button_frame = """            buttonFrame = CGRect(
                origin: CGPoint(
                    x: floorToScreenPixels(
                        (layout.size.width - proceedSize.width) / 2.0
                    ),
                    y: layout.size.height
                        - insets.bottom
                        - proceedSize.height
                        - inset
                        - botLoginReservedHeight
                ),
                size: proceedSize
            )
"""

    if old_button_frame not in fn:
        raise SystemExit(
            "anchor not found: bot layout button frame"
        )

    fn = fn.replace(
        old_button_frame,
        new_button_frame,
        1
    )

    proceed_frame = """        transition.updateFrame(node: self.proceedNode, frame: buttonFrame)
"""

    proceed_frame_replacement = """        transition.updateFrame(
            node: self.proceedNode,
            frame: buttonFrame
        )

        if self.hasOtherAccounts {
            self.ghostBaseBotLoginNode.isHidden = false
            transition.updateFrame(
                node: self.ghostBaseBotLoginNode,
                frame: CGRect(
                    x: floorToScreenPixels(
                        (layout.size.width - botLoginSize.width) / 2.0
                    ),
                    y: buttonFrame.maxY + 4.0,
                    width: botLoginSize.width,
                    height: 36.0
                )
            )
        } else {
            self.ghostBaseBotLoginNode.isHidden = true
        }
"""

    if proceed_frame not in fn:
        raise SystemExit(
            "anchor not found: bot layout proceed frame"
        )

    fn = fn.replace(
        proceed_frame,
        proceed_frame_replacement,
        1
    )

fc = fc_path.read_text(encoding="utf-8")

fc = replace_once(
    fc,
    """    private let termsDisposable = MetaDisposable()
""",
    """    private let termsDisposable = MetaDisposable()
    private let ghostBaseBotAuthorizationDisposable = MetaDisposable()
""",
    "bot authorization disposable"
)

fc = replace_once(
    fc,
    """    deinit {
        self.termsDisposable.dispose()
    }
""",
    """    deinit {
        self.termsDisposable.dispose()
        self.ghostBaseBotAuthorizationDisposable.dispose()
    }
""",
    "dispose bot authorization"
)

fc = replace_once(
    fc,
    """        self.controllerNode.retryPasskey = { [weak self] in
            guard let self else {
                return
            }
            self.loadAndPresentPasskey(force: true)
        }
""",
    """        self.controllerNode.retryPasskey = { [weak self] in
            guard let self else {
                return
            }
            self.loadAndPresentPasskey(force: true)
        }
        self.controllerNode.loginAsBot = { [weak self] in
            self?.openGhostBaseBotLogin()
        }
""",
    "connect bot login button"
)

method_anchor = """    private func loadAndPresentPasskey(force: Bool) {
"""

method = """    private func openGhostBaseBotLogin() {
        guard self.otherAccountPhoneNumbers.0 != nil, let account = self.account else {
            return
        }
        
        let controller = AuthorizationSequencePasswordEntryController(
            sharedContext: self.sharedContext,
            presentationData: self.presentationData,
            back: { [weak self] in
                self?.navigationController?.popViewController(animated: true)
            },
            mode: .ghostBaseBotToken
        )
        
        controller.loginWithPassword = { [weak self, weak controller] rawToken in
            guard let self, let controller else {
                return
            }
            
            let token = rawToken.trimmingCharacters(in: .whitespacesAndNewlines)
            guard !token.isEmpty else {
                controller.passwordIsInvalid()
                return
            }
            
            controller.inProgress = true
            
            self.ghostBaseBotAuthorizationDisposable.set((
                ghostBaseAuthorizeBot(
                    accountManager: self.sharedContext.accountManager,
                    account: account,
                    apiId: self.apiId,
                    apiHash: self.apiHash,
                    botAuthToken: token
                )
                |> deliverOnMainQueue
            ).start(error: { [weak self, weak controller] error in
                guard let self, let controller else {
                    return
                }
                
                controller.inProgress = false
                
                let text: String
                switch error {
                case .invalidToken:
                    controller.passwordIsInvalid()
                    text = "Токен бота недействителен."
                case .floodWait:
                    text = "Слишком много попыток. Попробуйте позже."
                case .apiIdInvalid:
                    text = "Telegram отклонил API ID клиента."
                case .botMethodInvalid:
                    text = "Сервер не разрешил авторизацию бота."
                case .signUpRequired:
                    text = "Сервер запросил регистрацию вместо входа."
                case .generic:
                    text = "Не удалось войти в аккаунт бота."
                }
                
                controller.present(
                    textAlertController(
                        sharedContext: self.sharedContext,
                        title: "Вход как бот",
                        text: text,
                        actions: [
                            TextAlertAction(
                                type: .defaultAction,
                                title: self.presentationData.strings.Common_OK,
                                action: {}
                            )
                        ]
                    ),
                    in: .window(.root)
                )
            }, completed: { [weak controller] in
                controller?.inProgress = false
            }))
        }
        
        self.push(controller)
    }
    
"""

if method not in fc:
    if method_anchor not in fc:
        raise SystemExit("anchor not found: bot login method")
    fc = fc.replace(method_anchor, method + method_anchor, 1)

save(pc_path, pc)
save(pn_path, pn)
save(fc_path, fc)
save(fn_path, fn)

required = [
    "GhostBase v1.0Y Bot Login UI",
    "ghostBaseBotLoginNode",
    "openGhostBaseBotLogin",
    "ghostBaseAuthorizeBot(",
    "mode: .ghostBaseBotToken",
    "func clearInput()"
]

combined = pc + pn + fc + fn

for value in required:
    if value not in combined:
        raise SystemExit(f"missing generated proof: {value}")

print("[v1.0Y] Bot Login UI anchors OK")
print("[v1.0Y] secure token screen connected")
