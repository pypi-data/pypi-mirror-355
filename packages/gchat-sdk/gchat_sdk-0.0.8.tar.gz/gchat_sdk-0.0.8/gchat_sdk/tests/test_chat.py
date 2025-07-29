import pytz
from unittest import TestCase
from datetime import datetime
from gchat_sdk.entities.chat import Chat
from .utils import contact_mock


class ChatTestCase(TestCase):
    
    def test_chat_instance(self):
        chat = Chat(
            id='67fea56f0b473cc94365c920', 
            last_message_date='2025-04-15T16:27:16', 
            last_message='Test message',
            is_me=False,
            contact=contact_mock
        )
        expected_date = datetime.fromisoformat('2025-04-15T16:27:16')
        tzinfo = pytz.timezone("America/Sao_Paulo")
        expected_date = tzinfo.localize(expected_date)
        self.assertEqual(chat.id, '67fea56f0b473cc94365c920')
        self.assertEqual(chat.last_message_date, expected_date)
        self.assertEqual(chat.last_message, 'Test message')
        self.assertFalse(chat.is_me)
        self.assertEqual(chat.contact.id, contact_mock.id)
        self.assertEqual(chat.contact.name, contact_mock.name)
        self.assertEqual(chat.contact.number, contact_mock.number)