import pytz
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from .constants import (
    CHAT_DATA_SEND_MESSAGE_TEST, 
    CHAT_DATA_SEND_MESSAGE_WITH_ALERT_TEST,
    CHAT_DATA_SEND_MESSAGE_EXCEPTION_CONTACT_TEST,
    CHAT_DATA, 
    CONTACT_DATA, 
    SEND_MESSAGE_RESPONSE
)


contact_mock = MagicMock()
contact_mock.id = '6569d66fa3544ba92d2f0cf3'
contact_mock.name = 'Tatianno'
contact_mock.number = '551199779298'


class BaseProviderMagicMock(MagicMock):
    calls_number_to_api = 0
    _send_message_response = SEND_MESSAGE_RESPONSE
    _chat_data = CHAT_DATA
    
    def get_chats(self, status, type_chat, page):
        self.calls_number_to_api += 1
        data = {}
        
        if self.calls_number_to_api == 1:
            data = self._chat_data
            
        return MagicMock(
            status_code=200, 
            json=MagicMock(return_value=data)
        )
    
    def send_message(self, contact_id, message):
        return MagicMock(
            status_code=202,
            json=MagicMock(return_value=SEND_MESSAGE_RESPONSE)
        )
    
    def finish_chat(self, chat_id):
        sucess_ids = [
            '67fea06c7d6367790067b4af',
            '67fe9d01d61e5036777e0ad6',
            '67fe867d3622f66e0b459f7c', 
            '67fe7df4867b172be47e5749', 
            '67fe42291f1c597687e93642'
        ]

        if chat_id in sucess_ids:
            return MagicMock(
                status_code=200
            )
        
        return MagicMock(
            status_code=400, 
        )


class ProviderSendMessageMagicMock(BaseProviderMagicMock):
    _chat_data = CHAT_DATA_SEND_MESSAGE_TEST


class ProviderSendMessageWithAlertMagicMock(BaseProviderMagicMock):
    _chat_data = CHAT_DATA_SEND_MESSAGE_WITH_ALERT_TEST


class ProviderSendMessageWithAlertExceptionContactMagicMock(BaseProviderMagicMock):
    _chat_data = CHAT_DATA_SEND_MESSAGE_EXCEPTION_CONTACT_TEST
    
    
class ProviderMagicMock(BaseProviderMagicMock): ...


def get_limit_date(hours: int) -> datetime:
    limit_date = datetime.strptime(
        "2025-04-15T19:43:38", "%Y-%m-%dT%H:%M:%S"
    ).replace(tzinfo=pytz.timezone("America/Sao_Paulo")) - timedelta(hours=hours)
    return limit_date