import time

import requests
from VendorApi.Whatsapp import api
from VendorApi.Whatsapp import ( SendException, WebHookException )

MAX_TIMEOUT = 4

class Message:
    def __init__(self, phone_number_id, token):
        self.phone_number_id = phone_number_id
        self.token = token
        self.send_url = api.send.format(phone_number_id=self.phone_number_id)
        self.status_url = api.status.format(phone_number_id=self.phone_number_id)

    @property
    def headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def send_message(self, recipient_id, message_body):
        pass

    def check_message_status(self, recipient_id):
        pass


class TextMessage(Message):
    def __init__(self, phone_number_id, token):
        super().__init__(phone_number_id, token)

    def send_message(self, recipient_id, message_body):
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "text",
            "text": {"body": message_body}
        }
        response = requests.post(
            self.send_url,
            json=payload,
            headers=self.headers
        )
        if response.status_code not in range(200, 299):
            raise SendException(response.text)
        self.check_message_status(recipient_id)
        return response

    def check_message_status(self, recipient_id):
        try:
            def read_status():
                return requests.get(
                    self.status_url.format(recipient_id=recipient_id),
                    verify=False
                ).json()
            max_time = time.time() + MAX_TIMEOUT
            while time.time() < max_time:
                response = read_status()
                if not response.get(recipient_id):
                    time.sleep(0.1)
                    continue
                status = response.get(recipient_id).get("status")
                if status == 'failed':
                    raise SendException(response.get(recipient_id).get('error_details'))
                return status
            raise WebHookException("Timed out waiting for message status")
        except Exception as e:
            raise WebHookException(e)
