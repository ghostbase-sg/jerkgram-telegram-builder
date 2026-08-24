#!/usr/bin/env python3
from pathlib import Path
import os

ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
SETTINGS = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
ABOUT_BUILD_FOOTER_SWIFT = r"Jerkgram\nBase: Official Telegram 12.9.2\nBuild: 118"

def require(value, message):
    if not value: raise RuntimeError("[Build118 About cards] " + message)

def once(text, old, new, name):
    require(text.count(old) == 1, name + " anchor count != 1")
    return text.replace(old, new, 1)

def patch(text):
    text = once(text, "                    height: .generic,\n", "                    height: .peerList,\n", "card height")
    text = once(text, '''private func jerkgramAboutChannelState(
    context: AccountContext,
    enabled: Bool
) -> Signal<JerkgramAboutChannelState, NoError> {''', '''private func jerkgramAboutChannelState(
    context: AccountContext,
    enabled: Bool,
    username: String
) -> Signal<JerkgramAboutChannelState, NoError> {''', "state signature")
    text = once(text, 'resolvePeerByName(name: "JerkgramApp", referrer: nil)', 'resolvePeerByName(name: username, referrer: nil)', "resolver")
    text = once(text, "    aboutChannelState: JerkgramAboutChannelState\n", "    aboutChannelState: JerkgramAboutChannelState,\n    aboutCommunityState: JerkgramAboutChannelState\n", "entries states")
    start = text.index("// MARK: Jerkgram v1.2F BUILD117_ABOUT_CHANNEL_CARD1\n    if page == .about {")
    end = text.index("\n    }", start) + len("\n    }")
    old_block = text[start:end]
    new_block = r'''// MARK: Jerkgram v1.2G BUILD118_ABOUT_CHANNEL_CARDS1
    if page == .about {
        func channelEntry(index: Int32, username: String, state: JerkgramAboutChannelState) -> GhostBaseSettingsEntry {
            switch state {
            case .loading:
                return .aboutChannel(0, index, username, nil, strings.communityLoading, true)
            case let .available(peer, preview):
                let visiblePreview = preview.isEmpty ? strings.communityNoPosts : "@\(username) · \(preview)"
                return .aboutChannel(0, index, username, peer, visiblePreview, false)
            case .unavailable:
                return .aboutChannel(0, index, username, nil, strings.communityUnavailable, false)
            }
        }
        return [
            .header(0, strings.about),
            channelEntry(index: 1, username: "JerkgramApp", state: aboutChannelState),
            channelEntry(index: 2, username: "JerkgramCommunity", state: aboutCommunityState),
            .info(1, "__JERKGRAM_BUILD118_FOOTER__")
        ]
    }'''.replace("__JERKGRAM_BUILD118_FOOTER__", ABOUT_BUILD_FOOTER_SWIFT)
    text = text[:start] + new_block + text[end:]
    text = once(text, '''    let aboutChannelSignal = jerkgramAboutChannelState(
        context: context,
        enabled: page == .about
    )''', '''    let aboutChannelSignal = jerkgramAboutChannelState(
        context: context,
        enabled: page == .about,
        username: "JerkgramApp"
    )
    let aboutCommunitySignal = jerkgramAboutChannelState(
        context: context,
        enabled: page == .about,
        username: "JerkgramCommunity"
    )''', "controller states")
    text = once(text, '''        statePromise.get(),
        aboutChannelSignal
    )
    |> deliverOnMainQueue
    |> map { presentationData, state, aboutChannelState''', '''        statePromise.get(),
        aboutChannelSignal,
        aboutCommunitySignal
    )
    |> deliverOnMainQueue
    |> map { presentationData, state, aboutChannelState, aboutCommunityState''', "combined states")
    text = once(text, "                aboutChannelState: aboutChannelState\n", "                aboutChannelState: aboutChannelState,\n                aboutCommunityState: aboutCommunityState\n", "entries call")
    return text

def main():
    require(SETTINGS.is_file(), "settings owner missing")
    text = SETTINGS.read_text()
    require("BUILD118_ABOUT_CHANNEL_CARDS1" not in text, "already applied")
    SETTINGS.write_text(patch(text), encoding="utf-8")
    print("[Build118 About cards] @JerkgramApp and @JerkgramCommunity live cards installed")

if __name__ == "__main__": main()
