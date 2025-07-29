import pytz
from datetime import datetime


class Contact:

    def __init__(self, id: str, name: str, number: str) -> None:
        self.id = id
        self.name = name
        self.number = number


class Chat:
    
    def __init__(self, id: str, last_message_date: str, last_message: str, is_me: bool, contact: Contact):
        self.id = id
        self.contact = contact
        self.last_message_date = self._date_converter(last_message_date)
        self.last_message = last_message
        self.is_me = is_me

    def _date_converter(self, date_string):
        dt_naive = datetime.fromisoformat(date_string)
        tz = pytz.timezone("America/Sao_Paulo")
        dt_aware = tz.localize(dt_naive)
        return dt_aware