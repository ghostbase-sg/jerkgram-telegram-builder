#!/usr/bin/env python3
import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
path = root / "submodules/Display/Source/GhostBaseGlass.swift"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(r'''import Foundation
import UIKit

// MARK: GhostBase v1.1D GLASSCORE2 global runtime
public extension Notification.Name {
    static let ghostBaseGlassDidChange = Notification.Name("GhostBase.Glass.DidChange")
    static let ghostBaseGlassTintDidChange = Notification.Name("GhostBase.Glass.TintDidChange")
}

public enum GhostBaseGlassStyle {
    public static let enabledKey = "GhostBase.Glass.Enabled"
    private static let activeTintKey = "GhostBase.Glass.ActiveTint"
    private static let peerTintPrefix = "GhostBase.Glass.PeerTint."

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

    private static func packedColor(_ color: UIColor) -> UInt32? {
        var red: CGFloat = 0.0
        var green: CGFloat = 0.0
        var blue: CGFloat = 0.0
        var alpha: CGFloat = 0.0
        guard color.getRed(&red, green: &green, blue: &blue, alpha: &alpha) else {
            return nil
        }
        return (UInt32(max(0.0, min(1.0, red)) * 255.0) << 16)
            | (UInt32(max(0.0, min(1.0, green)) * 255.0) << 8)
            | UInt32(max(0.0, min(1.0, blue)) * 255.0)
    }

    private static func unpackedColor(_ value: UInt32) -> UIColor {
        return UIColor(
            red: CGFloat((value >> 16) & 0xff) / 255.0,
            green: CGFloat((value >> 8) & 0xff) / 255.0,
            blue: CGFloat(value & 0xff) / 255.0,
            alpha: 1.0
        )
    }

    public static func setActiveTintColor(_ color: UIColor, peerId: Int64?) {
        guard let packed = self.packedColor(color) else {
            return
        }
        let value = Int64(packed)
        let defaults = UserDefaults.standard
        var changed = defaults.object(forKey: self.activeTintKey) == nil || defaults.integer(forKey: self.activeTintKey) != Int(value)
        defaults.set(value, forKey: self.activeTintKey)
        if let peerId {
            let key = self.peerTintPrefix + String(peerId)
            if defaults.object(forKey: key) == nil || defaults.integer(forKey: key) != Int(value) {
                changed = true
            }
            defaults.set(value, forKey: key)
        }
        if changed {
            NotificationCenter.default.post(name: .ghostBaseGlassTintDidChange, object: nil)
        }
    }

    public static func activeTintColor(fallback: UIColor) -> UIColor {
        guard UserDefaults.standard.object(forKey: self.activeTintKey) != nil else {
            return fallback
        }
        return self.unpackedColor(UInt32(truncatingIfNeeded: UserDefaults.standard.integer(forKey: self.activeTintKey)))
    }

    public static func tintColor(peerId: Int64, fallback: UIColor) -> UIColor {
        let key = self.peerTintPrefix + String(peerId)
        guard UserDefaults.standard.object(forKey: key) != nil else {
            return self.activeTintColor(fallback: fallback)
        }
        return self.unpackedColor(UInt32(truncatingIfNeeded: UserDefaults.standard.integer(forKey: key)))
    }

    public static func coldTintColor(_ color: UIColor) -> UIColor {
        guard self.isEnabled else {
            return color
        }
        return color.withAlphaComponent(self.usesReducedEffects ? 0.88 : 0.34)
    }

    public static func lightweightTintColor(_ color: UIColor) -> UIColor {
        guard self.isEnabled else {
            return color
        }
        return color.withAlphaComponent(self.usesReducedEffects ? 0.94 : 0.18)
    }

    public static func borderColor(_ color: UIColor) -> UIColor {
        guard self.isEnabled else {
            return .clear
        }
        return color.withAlphaComponent(self.usesReducedEffects ? 0.10 : 0.24)
    }

    public static let compactCornerRadius: CGFloat = 18.0
    public static let cardCornerRadius: CGFloat = 24.0
}
''', encoding="utf-8")
print("[V11D] GLASSCORE2 global runtime installed")
