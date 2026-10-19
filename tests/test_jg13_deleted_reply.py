"""Production source contracts, not Swift compilation or device evidence."""
import os
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("JG13_SOURCE", ROOT / "work/swiftgram-src"))


class DeletedReplyTests(unittest.TestCase):
    def assertIn(self, member, container, msg=None):
        self.assertTrue(member in container, msg or f"Missing source contract: {member}")

    def setUp(self):
        self.text = (SOURCE / "submodules/TelegramCore/Sources/PendingMessages/EnqueueMessage.swift").read_text()

    def test_poll_and_todo_include_internal_text_and_entities(self):
        for fragment in ("poll.text", "poll.textEntities", "poll.options", "option.entities",
                         "todo.text", "todo.textEntities", "todo.items", "item.entities", "todo.completions"):
            self.assertIn(fragment, self.text)
        self.assertIn("body.entities", self.text)

    def test_normal_sends_skip_settings_transaction_and_worker(self):
        resolver = self.text.split("private func ghostBaseResolveDeletedReplies(", 1)[1]
        self.assertIn("guard messages.contains", resolver)
        self.assertLess(resolver.index("guard messages.contains"), resolver.index("ghostBaseDeletedBool("))
        self.assertIn("guard plans.contains(where: { $0.source != nil }) else", resolver)
        self.assertLess(resolver.index("guard plans.contains"), resolver.index("DispatchQueue.global"))

    def test_app_language_is_read_only_for_deleted_reply_plans(self):
        account = (SOURCE / "submodules/TelegramCore/Sources/Account/Account.swift").read_text()
        self.assertIn("func jerkgramDeletedReplyLanguageCode()", account)
        self.assertIn("primaryComponent.languageCode", account)
        resolver = self.text.split("private func ghostBaseResolveDeletedReplies(", 1)[1]
        self.assertLess(resolver.index("guard plans.contains"), resolver.index("account.jerkgramDeletedReplyLanguageCode()"))
        self.assertIn("languageCode: languageCode", resolver)
        self.assertNotIn("Locale.preferredLanguages", self.text)

    def test_native_attachment_does_not_repeat_its_type(self):
        self.assertIn("if recoveredMedia && !interactiveSnapshot", self.text)
        self.assertIn("JerkgramDeletedReplyLabel.deletedMessage.text(languageCode:", self.text)

    def test_final_builder_budgets_quote_and_preserves_user_text(self):
        builder = self.text.split("private func ghostBaseBuildPortableDeletedReply(", 1)[1].split("private func ghostBaseBuildRecoveredAlbumTail", 1)[0]
        self.assertIn("JerkgramDeletedReplyText.fittedQuote(", builder)
        self.assertIn("limits.maxCaptionLength", builder)
        self.assertIn("limits.maxMessageLength", builder)
        self.assertIn("fittedQuote.retainedLength", builder)
        self.assertIn("quoteText + separator + userText", builder)
        self.assertIn("UserLimitsConfiguration(appConfiguration:", self.text)


if __name__ == "__main__":
    unittest.main()
