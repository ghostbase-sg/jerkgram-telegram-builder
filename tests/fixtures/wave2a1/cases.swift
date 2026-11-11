func paragraph(_ text: String, attributes: ChatInputInlineAttributes = ChatInputInlineAttributes()) -> ChatInputBlock {
    return .paragraph(ChatInputParagraph(runs: [ChatInputRun(text: text, attributes: attributes)]))
}
let richRuns: [ChatInputRun] = [
    ChatInputRun(text: "bold", attributes: ChatInputInlineAttributes(bold: true, italic: true, monospace: true, strikethrough: true, underline: true, spoiler: true)),
    ChatInputRun(text: "https://example.invalid", attributes: ChatInputInlineAttributes(entity: .url("https://example.invalid"))),
    ChatInputRun(text: "mention", attributes: ChatInputInlineAttributes(entity: .mention(EnginePeer.Id(42)))),
    ChatInputRun(text: "date", attributes: ChatInputInlineAttributes(entity: .date(1234))),
    ChatInputRun(text: "\u{fffc}", attributes: ChatInputInlineAttributes(entity: .customEmoji(fileId: 123, file: nil, enableAnimation: true)))
]
let richContent = ChatInputContent(blocks: [.paragraph(ChatInputParagraph(runs: richRuns))])
let layouts: [ChatInputContent] = [
    ChatInputContent(),
    ChatInputContent(blocks: [paragraph("")]),
    ChatInputContent(blocks: [paragraph("short"), paragraph("")]),
    richContent,
    ChatInputContent(blocks: [.code(ChatInputCode(language: "swift", runs: richRuns))]),
    ChatInputContent(blocks: [.pullQuote(ChatInputPullQuote(runs: richRuns, author: [ChatInputRun(text: "off-axis author")]))]),
    ChatInputContent(blocks: [.blockQuote(ChatInputBlockQuote(content: richContent, collapsed: true))]),
    ChatInputContent(blocks: [.blockQuote(ChatInputBlockQuote(content: richContent, collapsed: false))]),
    ChatInputContent(blocks: [.blockQuote(ChatInputBlockQuote(content: ChatInputContent(blocks: [paragraph("outer"), .blockQuote(ChatInputBlockQuote(content: richContent, collapsed: true)), .code(ChatInputCode(runs: [ChatInputRun(text: "code\n")]))]), collapsed: false))]),
    ChatInputContent(blocks: [.media(ChatInputMedia()), .table(ChatInputTable()), .details(ChatInputDetails()), .buttonRow(ChatInputButtonRow())]),
    ChatInputContent(blocks: [paragraph("before"), .media(ChatInputMedia()), .table(ChatInputTable()), paragraph("after")]),
    ChatInputContent(blocks: [.paragraph(ChatInputParagraph(list: ChatInputListMembership(marker: .ordered, level: 1), runs: [ChatInputRun(text: "list text, no marker in flat projection")]))])
] + ["e\u{301}", "é", "👨‍👩‍👧‍👦", "🇷🇺", "👍🏽", "正在输入", "first\nsecond", String(repeating: "long😀 e\u{301}\n", count: 4096)].map { ChatInputContent(blocks: [paragraph($0)]) }
var oldProjectionCount = 0
for content in layouts {
    let state = InputState(content: content)
    projectionBuilds = 0
    let before = oldLiteral(state)
    oldProjectionCount += projectionBuilds
    precondition(projectionBuilds > 0, "old closure should actually construct attributed content")
    projectionBuilds = 0
    let after = newLiteral(state)
    precondition(projectionBuilds == 0, "literal validation must not construct attributed content")
    precondition((before as NSString).isEqual(to: after), "literal UTF16 parity, not canonical String equality")
    precondition(Array(before.utf16) == Array(after.utf16))
    // Both algorithms leave the authoritative input unchanged; the attributed
    // projection still carries all inline attributes for normal rendering/send.
    let display = attributedString(from: content)
    let snapshot = NSAttributedString(attributedString: display)
    _ = newLiteral(state)
    precondition(display.isEqual(to: snapshot))
}
let richProjection = attributedString(from: richContent)
for key in [ChatTextInputAttributes.bold, .init("fixture.italic"), .init("fixture.monospace"), .init("fixture.strikethrough"), .init("fixture.underline"), .init("fixture.spoiler"), .init("fixture.url"), .init("fixture.mention"), .init("fixture.date"), .init("fixture.emoji")] {
    var found = false
    richProjection.enumerateAttribute(key, in: NSRange(location: 0, length: richProjection.length), options: []) { value, _, _ in if value != nil { found = true } }
    precondition(found, "rich attribute missing in unchanged normal projection")
}
// Rapid edits/chat switches are distinct models, never a cache keyed by ID.
for revision in 0..<100 {
    let state = InputState(content: ChatInputContent(blocks: [paragraph("chat\(revision % 2) revision\(revision)😀")]))
    precondition((oldLiteral(state) as NSString).isEqual(to: newLiteral(state)))
}

let attributes: [[AnyObject]] = [[], [OtherAttribute()], [GhostBaseMessageAttribute(false)], [GhostBaseMessageAttribute(true)], [OtherAttribute(), GhostBaseMessageAttribute(true)], [GhostBaseMessageAttribute(false), GhostBaseMessageAttribute(true)], Array(repeating: OtherAttribute(), count: 128)]
var oldVisits = 0
var newVisits = 0
for show in [false, true] {
    for values in attributes {
        let baseline = FixtureMessage(attributes: CountingAttributes(values))
        let candidate = FixtureMessage(attributes: CountingAttributes(values))
        precondition(oldAllows(show, baseline) == newAllows(show, candidate), "filter behavior changed")
        if show {
            oldVisits += baseline.attributes.visits
            newVisits += candidate.attributes.visits
            precondition(candidate.attributes.visits == 0)
        } else {
            precondition(baseline.attributes.visits == candidate.attributes.visits)
        }
    }
}
precondition(oldVisits > 0 && newVisits == 0)
print("WORK input-projection layouts=\(layouts.count) old=\(oldProjectionCount) new=0; deleted-attribute visits show=true old=\(oldVisits) new=\(newVisits)")
print("PASS actual pinned plainText/projection UTF16 parity, rich/nested/off-axis cases; exact old/new deletion predicate equivalence. No UIKit/editor/device timing claim.")
