import requests
import json


class ChatBotProvider:

    def __init__(self, base_url: str, access_token: str):
        self.base_url = base_url
        self.access_token = access_token
    
    def get_chats(self, status:int, type_chat: int, page: int=1) -> requests.Response:
        url = f'{self.base_url}/core/v2/api/chats/list'
        headers = self._get_token()
        data = {
            'status': status,
            'typeChat': type_chat,
            'page': page
        }
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(data)
        )
        return response
    
    def finish_chat(self, chat_id: str, send_message_finalized: bool=True) -> requests.Response:
        url = f'{self.base_url}/core/v2/api/chats/{chat_id}/finalize'
        headers = self._get_token()
        data = {
            'sendMessageFinalized': send_message_finalized,
            'fidelityUser': False,
            'sendResearchSatisfaction': False 
        }
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(data)
        )
        return response

    def send_template(self, numero: str, template_id: str) -> requests.Response:
        url = f'{self.base_url}/core/v2/api/chats/send-template'
        headers = self._get_token()
        data = {
            "forceSend": True,
            "number": numero,
            "templateId": template_id,
            "verifyContact": False
        }
        response = requests.post(
            url,
            data=json.dumps(data),
            headers=headers
        )
        return response
    
    def send_message(self, contact_id: str, message: str) -> requests.Response: 
        url = f'{self.base_url}/core/v2/api/chats/send-text'
        headers = self._get_token()
        data = {
            "contactId": contact_id,
            "forceSend": True,
            "isWhisper": False,
            "verifyContact": False,
            "message": message    
        }
        response = requests.post(
            url,
            data=json.dumps(data),
            headers=headers,
        )
        return response
    
    def get_contact(self, number: str) -> requests.Response:
        url = f'{self.base_url}/core/v2/api/contacts/number/{number}'
        headers = self._get_token()
        response = requests.get(
            url,
            headers=headers
        )
        return response
        
    def _get_token(self) -> dict:
        return {
            'access-token': self.access_token,
            'Content-Type': 'application/json'
        }
        