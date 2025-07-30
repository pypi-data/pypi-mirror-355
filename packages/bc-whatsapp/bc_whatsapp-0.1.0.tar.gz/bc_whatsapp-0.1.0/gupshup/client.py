import json
import urllib.request

from gupshup.send import Send


class Client:
    BASE_URL_API = "https://api.gupshup.io/wa/"
    BASE_URL_SEND_MESSAGE = f"{BASE_URL_API}api/v1/msg"
    BASE_URL_TEMPLATES = f"{BASE_URL_API}api/v1/template/msg"
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Cache-Control": "no-cache"}

    def __init__(self, app_name, api_token, app_number, api_id):
        self.app_name = app_name
        self.app_number = app_number
        self.api_token = api_token
        self.api_id = api_id
        self.headers_set()

    def headers_set(self):
        self.headers["accept"] = "application/json"
        self.headers["Content-Type"] = "application/x-www-form-urlencoded"
        self.headers["apikey"] = f"{self.api_token}"
        self.headers["Cache-Control"] = "no-cache"

    def send_text(self, destination_number, destination_text, context_msg_id=None, timeout=10):
        url = f'{self.BASE_URL_SEND_MESSAGE}'
        data = (Send(self.app_number, destination_number, self.app_name)
                .session_text(destination_text, context_msg_id))
        req = urllib.request.Request(url, data=data, headers=self.headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode()
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            raise RuntimeError(f"HTTP {e.code}: {body}") from None
        except urllib.error.URLError as e:
            raise RuntimeError(f"Failed to reach server: {e.reason}") from None

        if not raw.strip():
            raise ValueError(f"Empty API response for {destination_number}")

        return json.loads(raw)

    def send_image(self, destination_number, image_url, caption="", context_msg_id=None, timeout=10):
        url = f'{self.BASE_URL_SEND_MESSAGE}'
        data = (Send(self.app_number, destination_number, self.app_name)
                .session_image(image_url, caption, context_msg_id))
        req = urllib.request.Request(url, data=data, headers=self.headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode()
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            raise RuntimeError(f"HTTP {e.code}: {body}") from None
        except urllib.error.URLError as e:
            raise RuntimeError(f"Failed to reach server: {e.reason}") from None

        if not raw.strip():
            raise ValueError(f"Empty API response for {destination_number}")

        return json.loads(raw)

    def send_document(self, destination_number, document_url, filename, context_msg_id=None, timeout=10):
        url = f'{self.BASE_URL_SEND_MESSAGE}'
        data = (Send(self.app_number, destination_number, self.app_name)
                .session_document(document_url, filename, context_msg_id))
        req = urllib.request.Request(url, data=data, headers=self.headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode()
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            raise RuntimeError(f"HTTP {e.code}: {body}") from None
        except urllib.error.URLError as e:
            raise RuntimeError(f"Failed to reach server: {e.reason}") from None

        if not raw.strip():
            raise ValueError(f"Empty API response for {destination_number}")

        return json.loads(raw)

    def send_audio(self, destination_number, audio_url, context_msg_id=None, timeout=10):
        url = f'{self.BASE_URL_SEND_MESSAGE}'
        data = (Send(self.app_number, destination_number, self.app_name)
                .session_audio(audio_url, context_msg_id))
        req = urllib.request.Request(url, data=data, headers=self.headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode()
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            raise RuntimeError(f"HTTP {e.code}: {body}") from None
        except urllib.error.URLError as e:
            raise RuntimeError(f"Failed to reach server: {e.reason}") from None

        if not raw.strip():
            raise ValueError(f"Empty API response for {destination_number}")

        return json.loads(raw)

    def send_video(self, destination_number, video_url, caption="", context_msg_id=None, timeout=10):
        url = f'{self.BASE_URL_SEND_MESSAGE}'
        data = (Send(self.app_number, destination_number, self.app_name)
                .session_video(video_url, caption, context_msg_id))
        req = urllib.request.Request(url, data=data, headers=self.headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode()
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            raise RuntimeError(f"HTTP {e.code}: {body}") from None
        except urllib.error.URLError as e:
            raise RuntimeError(f"Failed to reach server: {e.reason}") from None

        if not raw.strip():
            raise ValueError(f"Empty API response for {destination_number}")

        return json.loads(raw)

    def send_sticker(self, destination_number, sticker_url, context_msg_id=None, timeout=10):
        url = f'{self.BASE_URL_SEND_MESSAGE}'
        data = (Send(self.app_number, destination_number, self.app_name)
                .session_sticker(sticker_url, context_msg_id))
        req = urllib.request.Request(url, data=data, headers=self.headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode()
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            raise RuntimeError(f"HTTP {e.code}: {body}") from None
        except urllib.error.URLError as e:
            raise RuntimeError(f"Failed to reach server: {e.reason}") from None

        if not raw.strip():
            raise ValueError(f"Empty API response for {destination_number}")

        return json.loads(raw)

    def send_reaction(self, destination_number, emoji, msg_id, timeout=10):
        url = f'{self.BASE_URL_SEND_MESSAGE}'
        data = (Send(self.app_number, destination_number, self.app_name)
                .session_reaction(emoji, msg_id))
        req = urllib.request.Request(url, data=data, headers=self.headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode()
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            raise RuntimeError(f"HTTP {e.code}: {body}") from None
        except urllib.error.URLError as e:
            raise RuntimeError(f"Failed to reach server: {e.reason}") from None

        if not raw.strip():
            raise ValueError(f"Empty API response for {destination_number}")

        return json.loads(raw)

    def send_location(self, destination_number, latitude: float, longitude: float, name: str,
                      address: str, context_msg_id=None, timeout=10):
        url = f'{self.BASE_URL_SEND_MESSAGE}'
        data = (Send(self.app_number, destination_number, self.app_name)
                .session_location(latitude, longitude, name, address, context_msg_id))
        req = urllib.request.Request(url, data=data, headers=self.headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode()
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            raise RuntimeError(f"HTTP {e.code}: {body}") from None
        except urllib.error.URLError as e:
            raise RuntimeError(f"Failed to reach server: {e.reason}") from None

        if not raw.strip():
            raise ValueError(f"Empty API response for {destination_number}")

        return json.loads(raw)

    def send_list(self, destination_number, title: str, body: str, global_button_title: str, sections: list,
                  context_msg_id=None, timeout=10):
        url = f'{self.BASE_URL_SEND_MESSAGE}'
        data = (Send(self.app_number, destination_number, self.app_name)
                .session_list(title, body, global_button_title, sections, context_msg_id))
        req = urllib.request.Request(url, data=data, headers=self.headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode()
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            raise RuntimeError(f"HTTP {e.code}: {body}") from None
        except urllib.error.URLError as e:
            raise RuntimeError(f"Failed to reach server: {e.reason}") from None

        if not raw.strip():
            raise ValueError(f"Empty API response for {destination_number}")

        return json.loads(raw)

    def send_quick_reply(self, destination_number, title: str, body: str, buttons: list,
                         context_msg_id=None, timeout=10):
        url = f'{self.BASE_URL_SEND_MESSAGE}'
        data = (Send(self.app_number, destination_number, self.app_name)
                .session_quick_reply(title, body, buttons, context_msg_id))
        req = urllib.request.Request(url, data=data, headers=self.headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode()
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            raise RuntimeError(f"HTTP {e.code}: {body}") from None
        except urllib.error.URLError as e:
            raise RuntimeError(f"Failed to reach server: {e.reason}") from None

        if not raw.strip():
            raise ValueError(f"Empty API response for {destination_number}")

        return json.loads(raw)

    def send_catalog(self, destination_number, product_retailer_id: str, context_msg_id=None, timeout=10):
        url = f'{self.BASE_URL_SEND_MESSAGE}'
        data = (Send(self.app_number, destination_number, self.app_name)
                .session_catalog(product_retailer_id, context_msg_id))
        req = urllib.request.Request(url, data=data, headers=self.headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode()
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            raise RuntimeError(f"HTTP {e.code}: {body}") from None
        except urllib.error.URLError as e:
            raise RuntimeError(f"Failed to reach server: {e.reason}") from None

        if not raw.strip():
            raise ValueError(f"Empty API response for {destination_number}")

        return json.loads(raw)

    def send_single_product(self, destination_number, catalog_id: str, product_retailer_id: str,
                            context_msg_id=None, timeout=10):
        url = f'{self.BASE_URL_SEND_MESSAGE}'
        data = (Send(self.app_number, destination_number, self.app_name)
                .session_single_product(catalog_id, product_retailer_id, context_msg_id))
        req = urllib.request.Request(url, data=data, headers=self.headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode()
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            raise RuntimeError(f"HTTP {e.code}: {body}") from None
        except urllib.error.URLError as e:
            raise RuntimeError(f"Failed to reach server: {e.reason}") from None

        if not raw.strip():
            raise ValueError(f"Empty API response for {destination_number}")

        return json.loads(raw)

    def send_multiple_products(self, destination_number, catalog_id: str, product_retailer_ids: list,
                               context_msg_id=None, timeout=10):
        url = f'{self.BASE_URL_SEND_MESSAGE}'
        data = (Send(self.app_number, destination_number, self.app_name)
                .session_multiple_products(catalog_id, product_retailer_ids, context_msg_id))
        req = urllib.request.Request(url, data=data, headers=self.headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode()
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            raise RuntimeError(f"HTTP {e.code}: {body}") from None
        except urllib.error.URLError as e:
            raise RuntimeError(f"Failed to reach server: {e.reason}") from None

        if not raw.strip():
            raise ValueError(f"Empty API response for {destination_number}")

        return json.loads(raw)

    def send_cta_url(self, destination_number, title: str, cta_url: str, body: str, context_msg_id: str = None,
                     timeout=10):
        url = f'{self.BASE_URL_SEND_MESSAGE}'
        data = (Send(self.app_number, destination_number, self.app_name)
                .session_cta_url(title, cta_url, body, context_msg_id))
        req = urllib.request.Request(url, data=data, headers=self.headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode()
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            raise RuntimeError(f"HTTP {e.code}: {body}") from None
        except urllib.error.URLError as e:
            raise RuntimeError(f"Failed to reach server: {e.reason}") from None

        if not raw.strip():
            raise ValueError(f"Empty API response for {destination_number}")

        return json.loads(raw)

    def get_mark_as_read(self, msg_id: str):
        url = f"{self.BASE_URL_API}app/{self.api_id}/msg/{msg_id}"

        req = urllib.request.Request(url=url, headers=self.headers, method="GET")

        try:
            response = urllib.request.urlopen(req)
            return response.read().decode()
        except Exception as e:
            return f"Erro ao marcar como lida: {e}"

    def set_mark_as_read(self, msg_id: str):
        url = f"{self.BASE_URL_API}app/{self.api_id}/msg/{msg_id}/read"

        req = urllib.request.Request(url=url, headers=self.headers, method="PUT")

        try:
            response = urllib.request.urlopen(req)
            return response.read().decode()
        except Exception as e:
            return f"Erro ao marcar como lida: {e}"
