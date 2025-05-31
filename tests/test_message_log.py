import unittest

from message_log import MessageLog


class TestMessageLog(unittest.TestCase):
    def test_add_message_and_get_messages(self):
        log = MessageLog(max_messages=5)
        log.add_message("message1")
        log.add_message("message2")
        self.assertEqual(log.get_messages(), ["message1", "message2"])

    def test_max_messages_respected(self):
        log = MessageLog(max_messages=3)
        log.add_message("msg1")
        log.add_message("msg2")
        log.add_message("msg3")
        log.add_message("msg4")
        log.add_message("msg5")
        self.assertEqual(log.get_messages(), ["msg3", "msg4", "msg5"])

    def test_add_fewer_than_max_messages(self):
        log = MessageLog(max_messages=5)
        log.add_message("m1")
        log.add_message("m2")
        log.add_message("m3")
        self.assertEqual(log.get_messages(), ["m1", "m2", "m3"])

    def test_add_exactly_max_messages(self):
        log = MessageLog(max_messages=2)
        log.add_message("test1")
        log.add_message("test2")
        self.assertEqual(log.get_messages(), ["test1", "test2"])
        log.add_message("test3")
        self.assertEqual(log.get_messages(), ["test2", "test3"])

    def test_get_messages_returns_copy(self):
        log = MessageLog(max_messages=5)
        original_message = "original_message"
        log.add_message(original_message)

        messages1 = log.get_messages()
        messages1.append("new_message_in_copy")

        messages2 = log.get_messages()
        self.assertEqual(messages2, [original_message])
        self.assertNotEqual(messages1, messages2)
        self.assertEqual(len(messages2), 1)

    def test_init_with_zero_max_messages(self):
        log = MessageLog(max_messages=0)
        log.add_message("msg1")
        self.assertEqual(log.get_messages(), [])

    def test_init_with_one_max_message(self):
        log = MessageLog(max_messages=1)
        log.add_message("msg1")
        self.assertEqual(log.get_messages(), ["msg1"])
        log.add_message("msg2")
        self.assertEqual(log.get_messages(), ["msg2"])


if __name__ == "__main__":
    unittest.main()
