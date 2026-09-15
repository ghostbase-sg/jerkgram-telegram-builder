import unittest

from scripts.verify_m1_swiftcall_ir import swiftself_call_line


class SwiftcallIRVerifierTests(unittest.TestCase):
    def test_accepts_swiftself_on_second_argument_with_llvm_attributes(self):
        source = (
            "%host = call swiftcc ptr %initializer("
            "ptr noundef null, ptr noundef swiftself %displayClass)\n"
        )
        self.assertEqual(swiftself_call_line(source), source.strip())

    def test_rejects_swiftself_on_first_argument(self):
        source = (
            "%host = call swiftcc ptr %initializer("
            "ptr swiftself %displayClass, ptr null)\n"
        )
        self.assertIsNone(swiftself_call_line(source))

    def test_rejects_call_without_swiftself(self):
        source = "%host = call swiftcc ptr %initializer(ptr null, ptr %displayClass)\n"
        self.assertIsNone(swiftself_call_line(source))


if __name__ == "__main__":
    unittest.main()
