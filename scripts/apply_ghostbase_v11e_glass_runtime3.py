#!/usr/bin/env python3
import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
path = root / "submodules/Display/Source/GhostBaseGlass.swift"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(r'''import Foundation
import UIKit

// MARK: GhostBase v1.1E GLASSRUNTIME3 audit-driven runtime
public extension Notification.Name {
    static let ghostBaseGlassDidChange = Notification.Name("GhostBase.Glass.DidChange")
    static let ghostBaseProfilePaletteDidChange = Notification.Name("GhostBase.ProfilePalette.DidChange")
}

public enum GhostBaseGlassStyle {
    public static let enabledKey = "GhostBase.Glass.Enabled"

    public static var isEnabled: Bool {
        if let value = UserDefaults.standard.object(forKey: self.enabledKey) as? Bool {
            return value
        }
        return true
    }

    public static var usesReducedEffects: Bool {
        return UIAccessibility.isReduceTransparencyEnabled || ProcessInfo.processInfo.isLowPowerModeEnabled
    }

    public static func setEnabled(_ value: Bool) {
        UserDefaults.standard.set(value, forKey: self.enabledKey)
        NotificationCenter.default.post(name: .ghostBaseGlassDidChange, object: nil)
    }
}

// Palette is deliberately process-local. A peer can never inherit a stale tint
// from another profile and there is no hard-coded GhostBase accent color.
public enum GhostBaseProfilePalette {
    private static let lock = NSLock()
    private static var peerColors: [Int64: UIColor] = [:]
    private static var globalColor: UIColor?

    public static func setColor(_ color: UIColor, peerId: Int64?) {
        self.lock.lock()
        if let peerId {
            self.peerColors[peerId] = color
        } else {
            self.globalColor = color
        }
        self.lock.unlock()
        NotificationCenter.default.post(name: .ghostBaseProfilePaletteDidChange, object: peerId)
    }

    public static func color(peerId: Int64?, fallback: UIColor) -> UIColor {
        self.lock.lock()
        defer { self.lock.unlock() }
        if let peerId, let color = self.peerColors[peerId] {
            return color
        }
        return self.globalColor ?? fallback
    }

    public static func clear(peerId: Int64?) {
        self.lock.lock()
        if let peerId {
            self.peerColors.removeValue(forKey: peerId)
        } else {
            self.globalColor = nil
        }
        self.lock.unlock()
    }
}
''', encoding="utf-8")
print("[V11E] GLASSRUNTIME3 installed: no persisted tint, no hard-coded purple")
