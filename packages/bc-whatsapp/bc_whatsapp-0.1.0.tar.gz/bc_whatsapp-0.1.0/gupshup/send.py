import urllib.request
import urllib.parse
import json


class Send:
    def __init__(self, source, destination, app_name):
        self.source = source
        self.destination = destination
        self.app_name = app_name

    def send_form(self, message):
        form = {
            'channel': 'whatsapp',
            'source': self.source,
            'destination': self.destination,
            'src.name': self.app_name,
            'message': json.dumps(message)
        }

        return urllib.parse.urlencode(form).encode('utf-8')

    def session_text(self, text: str, context_msg_id: str = None):
        message_obj = {
            "type": "text",
            "text": text,
            "previewUrl": False
        }
        if context_msg_id:
            message_obj["context"] = {"msgId": context_msg_id}

        return self.send_form(message_obj)

    def session_image(self, image_url: str, caption: str = "", context_msg_id: str = None):
        message_obj = {
            "type": "image",
            "originalUrl": image_url,
            "previewUrl": image_url,
        }

        if caption:
            message_obj["caption"] = caption

        if context_msg_id:
            message_obj["context"] = {"msgId": context_msg_id}

        return self.send_form(message_obj)

    def session_document(self, document_url: str, filename: str, context_msg_id: str = None):
        message_obj = {
            "type": "document",
            "url": document_url,
            "filename": filename
        }

        if context_msg_id:
            message_obj["context"] = {"msgId": context_msg_id}

        return self.send_form(message_obj)

    def session_audio(self, audio_url: str, context_msg_id: str = None):
        message_obj = {
            "type": "audio",
            "url": audio_url
        }

        if context_msg_id:
            message_obj["context"] = {"msgId": context_msg_id}

        return self.send_form(message_obj)

    def session_video(self, video_url: str,  caption: str = "", context_msg_id: str = None):
        message_obj = {
            "type": "video",
            "url": video_url
        }

        if caption:
            message_obj["caption"] = caption

        if context_msg_id:
            message_obj["context"] = {"msgId": context_msg_id}

        return self.send_form(message_obj)

    def session_sticker(self, sticker_url: str, context_msg_id: str = None):
        message_obj = {
            "type": "sticker",
            "url": sticker_url
        }

        if context_msg_id:
            message_obj["context"] = {"msgId": context_msg_id}

        return self.send_form(message_obj)

    def session_reaction(self, emoji: str, msg_id: str):
        message_obj = {
            "type": "reaction",
            "msgId": msg_id,
            "emoji": emoji
        }

        return self.send_form(message_obj)

    def session_location(self, latitude: float, longitude: float, name: str, address: str, context_msg_id: str = None):
        message_obj = {
            "type": "location",
            "latitude": latitude,
            "longitude": longitude,
            "name": name,
            "address": address
        }

        if context_msg_id:
            message_obj["context"] = {"msgId": context_msg_id}

        return self.send_form(message_obj)

    def session_list(self, title: str, body: str, global_button_title: str, sections: list, context_msg_id: str = None):
        message_obj = {
            "type": "list",
            "title": title,
            "body": body,
            "globalButtons": [
                {
                    "type": "text",
                    "title": global_button_title
                }
            ],
            "items": sections
        }

        if context_msg_id:
            message_obj["context"] = {"msgId": context_msg_id}

        return self.send_form(message_obj)

    def session_quick_reply(self, title: str, body: str, buttons: list, context_msg_id: str = None):
        message_obj = {
            "type": "quick_reply",
            "content": {
                "title": title,
                "body": body,
                "globalButtons": [
                    {"type": "text", "title": b} if isinstance(b, str) else b for b in buttons
                ]
            }
        }

        if context_msg_id:
            message_obj["content"]["msgId"] = context_msg_id

        return self.send_form(message_obj)

    def session_catalog(self, product_retailer_id: str, context_msg_id: str = None):
        message_obj = {
            "type": "catalog",
            "productRetailerId": product_retailer_id
        }

        if context_msg_id:
            message_obj["context"] = {"msgId": context_msg_id}

        return self.send_form(message_obj)

    def session_single_product(self, catalog_id: str, product_retailer_id: str, context_msg_id: str = None):
        message_obj = {
            "type": "product",
            "catalogId": catalog_id,
            "productRetailerId": product_retailer_id
        }

        if context_msg_id:
            message_obj["context"] = {"msgId": context_msg_id}

        return self.send_form(message_obj)

    def session_multiple_products(self, catalog_id: str, sections: list, context_msg_id: str = None):
        message_obj = {
            "type": "multi_product",
            "catalogId": catalog_id,
            "sections": sections
        }

        if context_msg_id:
            message_obj["context"] = {"msgId": context_msg_id}

        return self.send_form(message_obj)

    def session_cta_url(self, title: str, url: str, body: str, context_msg_id: str = None):
        message_obj = {
            "type": "cta_url",
            "title": title,
            "url": url,
            "body": body
        }

        if context_msg_id:
            message_obj["context"] = {"msgId": context_msg_id}

        return self.send_form(message_obj)
