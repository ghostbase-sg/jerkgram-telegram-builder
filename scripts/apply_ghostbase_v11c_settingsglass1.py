#!/usr/bin/env python3
import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
path = root / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
text = path.read_text(encoding="utf-8")

if "GhostBase v1.1C SETTINGSGLASS1" in text:
    print("[V11C] SETTINGSGLASS1 already installed")
    raise SystemExit(0)

anchor = '    static let messageSeconds = "GhostBase.Appearance.MessageSeconds"\n'
if anchor not in text:
    raise SystemExit("[V11C SETTINGSGLASS1] key anchor missing")
text = text.replace(
    anchor,
    '    // MARK: GhostBase v1.1C SETTINGSGLASS1\n'
    '    static let glassEnabled = "GhostBase.Glass.Enabled"\n'
    + anchor,
    1,
)

anchor = '    var messageSeconds: Bool\n'
if anchor not in text:
    raise SystemExit("[V11C SETTINGSGLASS1] state anchor missing")
text = text.replace(anchor, '    var glassEnabled: Bool\n' + anchor, 1)

anchor = '            messageSeconds: ghostBaseBool(\n'
if anchor not in text:
    raise SystemExit("[V11C SETTINGSGLASS1] load anchor missing")
text = text.replace(
    anchor,
    '            glassEnabled: ghostBaseBool(\n'
    '                GhostBaseKey.glassEnabled,\n'
    '                defaultValue: true\n'
    '            ),\n'
    + anchor,
    1,
)

anchor = '        UserDefaults.standard.set(\n            self.messageSeconds,\n'
if anchor not in text:
    raise SystemExit("[V11C SETTINGSGLASS1] save anchor missing")
text = text.replace(
    anchor,
    '        UserDefaults.standard.set(\n'
    '            self.glassEnabled,\n'
    '            forKey: GhostBaseKey.glassEnabled\n'
    '        )\n'
    + anchor,
    1,
)

old = '''    if page == .appearance {
        return [
            .header(0, "Внешний вид"),
            .toggle(
                0,
                1,
                GhostBaseKey.messageSeconds,
                "Показывать секунды в сообщениях",
                state.messageSeconds
            ),
            .toggle(
                0,
                2,
                GhostBaseKey.hideOwnPhone,
                "Скрывать мой номер",
                state.hideOwnPhone
            ),
            .info(
                0,
                "Номер скрывается только локально в интерфейсе GhostBase. Экран изменения профиля и смены номера остаётся доступен."
            )
        ]
    }
'''
new = '''    if page == .appearance {
        return [
            .header(0, "Внешний вид"),
            .toggle(
                0,
                1,
                GhostBaseKey.glassEnabled,
                "GhostBase Glass",
                state.glassEnabled
            ),
            .info(
                0,
                "Единая система Glass. При Reduce Transparency и Low Power Mode эффекты автоматически облегчаются."
            ),
            .toggle(
                1,
                2,
                GhostBaseKey.messageSeconds,
                "Показывать секунды в сообщениях",
                state.messageSeconds
            ),
            .toggle(
                1,
                3,
                GhostBaseKey.hideOwnPhone,
                "Скрывать мой номер",
                state.hideOwnPhone
            ),
            .info(
                1,
                "Номер скрывается только локально в интерфейсе GhostBase. Экран изменения профиля и смены номера остаётся доступен."
            )
        ]
    }
'''
if old not in text:
    raise SystemExit("[V11C SETTINGSGLASS1] appearance block anchor missing")
text = text.replace(old, new, 1)

anchor = '            case GhostBaseKey.messageSeconds:\n'
if anchor not in text:
    raise SystemExit("[V11C SETTINGSGLASS1] update switch anchor missing")
text = text.replace(
    anchor,
    '            case GhostBaseKey.glassEnabled:\n'
    '                updated.glassEnabled = value\n'
    '                UserDefaults.standard.set(\n'
    '                    value,\n'
    '                    forKey: GhostBaseKey.glassEnabled\n'
    '                )\n\n'
    + anchor,
    1,
)

path.write_text(text, encoding="utf-8")
print("[V11C] SETTINGSGLASS1 single GhostBase Glass toggle installed")
