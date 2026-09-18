#!/usr/bin/env python3
from pathlib import Path
import sys


ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
SHELL = ROOT / "src/lib/jerkgramNotificationsShell.ts"
MARKER = "// JERKGRAM_NOTIFICATIONS_REPAIR_V06"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"[jerkgram-repair-v06] {label}: expected one anchor, found {count}")
    return text.replace(old, new, 1)


def patch_shell_text(text: str) -> str:
    if MARKER in text:
        if text.count(MARKER) != 1:
            raise RuntimeError("[jerkgram-repair-v06] marker count")
        return text

    text = replace_once(
        text,
        "import rootScope from '@lib/rootScope';\n",
        "import rootScope from '@lib/rootScope';\nimport uiNotificationsManager from '@lib/uiNotificationsManager';\n\n" + MARKER + "\n",
        "notification manager import",
    )

    text = replace_once(
        text,
        "#jg-finish,#jg-manage,#jg-permission{width:100%;",
        "#jg-finish,#jg-manage,#jg-permission,#jg-repair{width:100%;",
        "shared button style",
    )
    text = replace_once(
        text,
        "#jg-permission{margin-top:10px;background:#fff;color:#3390ec}",
        "#jg-permission,#jg-repair{margin-top:10px;background:#fff;color:#3390ec}",
        "repair light style",
    )
    text = replace_once(
        text,
        ".jg-card,#jg-permission{background:#1c1c1e}",
        ".jg-card,#jg-permission,#jg-repair{background:#1c1c1e}",
        "repair dark background",
    )
    text = replace_once(
        text,
        "#jg-permission{color:#64b5f6}",
        "#jg-permission,#jg-repair{color:#64b5f6}",
        "repair dark foreground",
    )

    text = replace_once(
        text,
        "  const permissionButton = make('button', 'Allow Notifications');\n  permissionButton.id = 'jg-permission'; permissionButton.type = 'button'; permissionButton.hidden = true;\n\n  const footnote",
        "  const permissionButton = make('button', 'Allow Notifications');\n  permissionButton.id = 'jg-permission'; permissionButton.type = 'button'; permissionButton.hidden = true;\n\n  const repairButton = make('button', 'Repair Notifications');\n  repairButton.id = 'jg-repair'; repairButton.type = 'button'; repairButton.hidden = true;\n\n  const footnote",
        "repair button creation",
    )

    text = replace_once(
        text,
        "  wrap.append(hero, accountTitle, accountCard, statusTitle, statusCard, finishButton, manage, permissionButton, footnote);",
        "  wrap.append(hero, accountTitle, accountCard, statusTitle, statusCard, finishButton, manage, permissionButton, repairButton, footnote);",
        "repair button append",
    )

    text = replace_once(
        text,
        "    permissionButton.hidden = permission !== 'default';\n  }",
        "    permissionButton.hidden = permission !== 'default';\n    repairButton.hidden = !(permission === 'granted' && subscription === 'missing');\n  }",
        "repair visibility",
    )

    permission_handler = """  permissionButton.addEventListener('click', async() => {\n    if(!('Notification' in window)) return;\n    try { await Notification.requestPermission(); } catch(_) {}\n    await refresh();\n  });\n"""
    repair_handler = permission_handler + """\n  repairButton.addEventListener('click', async(): Promise<void> => {\n    if(repairButton.disabled) return;\n    repairButton.disabled = true;\n    repairButton.textContent = 'Repairing…';\n    try {\n      await uiNotificationsManager.onPushConditionsChange();\n    } catch(_) {}\n    repairButton.textContent = 'Repair Notifications';\n    repairButton.disabled = false;\n    await refresh();\n  });\n"""
    text = replace_once(text, permission_handler, repair_handler, "repair handler")

    for required in (
        "uiNotificationsManager.onPushConditionsChange()",
        "Repair Notifications",
        "Repairing…",
        "subscription === 'missing'",
        "permission === 'granted'",
        MARKER,
    ):
        if required not in text:
            raise RuntimeError("[jerkgram-repair-v06] missing invariant: " + required)

    for forbidden in (
        "pushManager.subscribe(",
        "applicationServerKey",
        "jerkgram://push/register",
        "jerkgram://push/unregister",
    ):
        if forbidden in text:
            raise RuntimeError("[jerkgram-repair-v06] direct/legacy push dependency leaked: " + forbidden)

    return text


def patch_tree(root: Path) -> None:
    target = root / "src/lib/jerkgramNotificationsShell.ts"
    if not target.is_file():
        raise RuntimeError(f"[jerkgram-repair-v06] missing {target}")
    target.write_text(patch_shell_text(target.read_text(encoding="utf-8")), encoding="utf-8")


def main() -> None:
    patch_tree(ROOT)
    print("[jerkgram-repair-v06] OK")
    print("  missing PushSubscription -> Web K notification owner repairs/re-registers it")


if __name__ == "__main__":
    main()
