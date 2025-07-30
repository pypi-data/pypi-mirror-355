import json
import urllib


class SendTemplate:

    def __init__(self, source, destination, app_name):
        self.source = source
        self.destination = destination
        self.app_name = app_name

    def send_template_message(self, template_id: str, params: list, postback_texts: list = None,
                              language_code: str = "pt_BR"):
        form = {
            "channel": "whatsapp",
            "source": self.source,
            "destination": self.destination,
            "src.name": self.app_name,
            "template": json.dumps({
                "id": template_id,
                "params": params,
                "languageCode": language_code
            })
        }

        if postback_texts:
            form["postbackTexts"] = json.dumps(postback_texts)

        return urllib.parse.urlencode(form).encode("utf-8")
