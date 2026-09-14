import Foundation

@objc(JGRuntimeIntrospection)
public final class JGRuntimeIntrospection: NSObject {
    private static let settingsSectionNames: [String] = [
        "edit", "phone", "accounts", "myProfile", "ghostbase", "proxy",
        "apps", "shortcuts", "advanced", "payment", "extra", "support"
    ]

    private static func directChild(named name: String, in value: Any) -> Any? {
        var mirror: Mirror? = Mirror(reflecting: value)
        while let current = mirror {
            for child in current.children where child.label == name {
                return unwrapOptional(child.value)
            }
            mirror = current.superclassMirror
        }
        return nil
    }

    private static func unwrapOptional(_ value: Any) -> Any? {
        let mirror = Mirror(reflecting: value)
        if mirror.displayStyle == .optional {
            return mirror.children.first.map { $0.value }
        }
        return value
    }

    private static func objectIdentifierIfClass(_ value: Any) -> ObjectIdentifier? {
        let mirror = Mirror(reflecting: value)
        guard mirror.displayStyle == .class else { return nil }
        return ObjectIdentifier(value as AnyObject)
    }

    private static func findClassObject(typeNameContains needle: String, in value: Any, depth: Int, visited: inout Set<ObjectIdentifier>) -> AnyObject? {
        guard depth >= 0 else { return nil }
        guard let unwrapped = unwrapOptional(value) else { return nil }
        let typeName = String(reflecting: Swift.type(of: unwrapped))
        if typeName.contains(needle), Mirror(reflecting: unwrapped).displayStyle == .class {
            return unwrapped as AnyObject
        }

        if let objectId = objectIdentifierIfClass(unwrapped) {
            if visited.contains(objectId) { return nil }
            visited.insert(objectId)
        }

        var mirror: Mirror? = Mirror(reflecting: unwrapped)
        while let current = mirror {
            for child in current.children {
                if let found = findClassObject(typeNameContains: needle, in: child.value, depth: depth - 1, visited: &visited) {
                    return found
                }
            }
            mirror = current.superclassMirror
        }
        return nil
    }

    private static func uint32Value(_ value: Any) -> UInt32? {
        guard let unwrapped = unwrapOptional(value) else { return nil }
        if let v = unwrapped as? UInt32 { return v }
        if let v = unwrapped as? Int32 { return UInt32(bitPattern: v) }
        if let v = unwrapped as? UInt64, v <= UInt64(UInt32.max) { return UInt32(v) }
        if let v = unwrapped as? Int64, v >= 0, v <= Int64(UInt32.max) { return UInt32(v) }
        if let raw = directChild(named: "rawValue", in: unwrapped) { return uint32Value(raw) }
        return nil
    }

    private static func int64Value(_ value: Any) -> Int64? {
        guard let unwrapped = unwrapOptional(value) else { return nil }
        if let v = unwrapped as? Int64 { return v }
        if let v = unwrapped as? Int32 { return Int64(v) }
        if let v = unwrapped as? UInt32 { return Int64(v) }
        if let v = unwrapped as? UInt64, v <= UInt64(Int64.max) { return Int64(v) }
        if let raw = directChild(named: "rawValue", in: unwrapped) { return int64Value(raw) }
        return nil
    }

    // Exact Postbox PeerId._toInt64 packing from the final materialized source.
    private static func packedPeerId(namespace: UInt32, id: Int64) -> Int64? {
        guard (namespace | 0x7) == 0x7 else { return nil }

        let rawId: UInt64
        if id < 0 {
            guard let int32Value = Int32(exactly: id) else { return nil }
            rawId = UInt64(UInt32(bitPattern: int32Value))
        } else {
            rawId = UInt64(id)
        }

        let idLowBits = rawId & 0xffff_ffff
        let idHighBits = (rawId >> 32) & 0xffff_ffff
        var data: UInt64 = 0

        if namespace == 0x7 && id == 0 {
            data |= UInt64(0x7fff_ffff) << 32
            data |= idLowBits
        } else {
            data |= UInt64(namespace & 0x7) << 32
            data |= idHighBits << 35
            data |= idLowBits
        }
        return Int64(bitPattern: data)
    }

    private static func normalizedSectionName(_ value: Any) -> String? {
        let raw = String(describing: value)
        for candidate in settingsSectionNames {
            if raw.range(of: candidate, options: [.caseInsensitive, .diacriticInsensitive]) != nil {
                return candidate
            }
        }
        return nil
    }

    @objc(isSettingsFromObject:)
    public static func isSettings(from object: AnyObject) -> NSNumber {
        guard let value = directChild(named: "isSettings", in: object) as? Bool else {
            return NSNumber(value: false)
        }
        return NSNumber(value: value)
    }

    @objc(accountPeerIdFromObject:)
    public static func accountPeerId(from object: AnyObject) -> NSNumber? {
        guard let peerId = directChild(named: "peerId", in: object),
              let namespaceValue = directChild(named: "namespace", in: peerId),
              let idValue = directChild(named: "id", in: peerId),
              let namespace = uint32Value(namespaceValue),
              let id = int64Value(idValue),
              let packed = packedPeerId(namespace: namespace, id: id) else {
            return nil
        }
        guard packed != 0 else { return nil }
        return NSNumber(value: packed)
    }

    @objc(languageCodeFromObject:)
    public static func languageCode(from object: AnyObject) -> NSString? {
        var visited = Set<ObjectIdentifier>()
        guard let node = findClassObject(
            typeNameContains: "PeerInfoScreenNode",
            in: object,
            depth: 5,
            visited: &visited
        ), let presentationData = directChild(named: "presentationData", in: node),
           let strings = directChild(named: "strings", in: presentationData),
           let rawCode = directChild(named: "baseLanguageCode", in: strings) as? String else {
            return nil
        }
        return (rawCode.lowercased().hasPrefix("ru") ? "ru" : "en") as NSString
    }

    @objc(regularSectionNodesFromObject:)
    public static func regularSectionNodes(from object: AnyObject) -> [NSDictionary] {
        var visited = Set<ObjectIdentifier>()
        guard let node = findClassObject(typeNameContains: "PeerInfoScreenNode", in: object, depth: 5, visited: &visited),
              let sectionsAny = directChild(named: "regularSections", in: node),
              let sections = unwrapOptional(sectionsAny) else {
            return []
        }

        var result: [NSDictionary] = []
        let dictionaryMirror = Mirror(reflecting: sections)
        guard dictionaryMirror.displayStyle == .dictionary else { return [] }

        for entry in dictionaryMirror.children {
            let tuple = Mirror(reflecting: entry.value)
            let values = Array(tuple.children.map { $0.value })
            guard values.count >= 2,
                  let keyValue = unwrapOptional(values[0]),
                  let nodeValue = unwrapOptional(values[1]),
                  let key = normalizedSectionName(keyValue) else {
                continue
            }
            let nodeType = String(reflecting: Swift.type(of: nodeValue))
            guard nodeType.contains("PeerInfoScreenItemSectionContainerNode"),
                  Mirror(reflecting: nodeValue).displayStyle == .class else {
                continue
            }
            result.append(["key": key, "node": nodeValue as AnyObject])
        }
        return result
    }
}
