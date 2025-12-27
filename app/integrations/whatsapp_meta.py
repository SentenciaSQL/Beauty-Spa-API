import httpx
from app.core.config import settings

class WhatsAppMetaClient:
    def __init__(self):
        self.base = "https://graph.facebook.com/v22.0"  # ajusta si tu doc usa otra versión
        self.phone_number_id = settings.WA_PHONE_NUMBER_ID
        self.token = settings.WA_ACCESS_TOKEN
        self.lang = getattr(settings, "WA_DEFAULT_LANG", "es")

    def send_template(
        self,
        *,
        to_e164: str,
        template_name: str,
        body_params: list[str],
    ) -> None:
        url = f"{self.base}/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to_e164.replace("+", ""),  # Meta suele pedir sin '+'
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": self.lang},
                "components": [
                    {
                        "type": "body",
                        "parameters": [{"type": "text", "text": p} for p in body_params],
                    }
                ],
            },
        }

        headers = {"Authorization": f"Bearer {self.token}"}
        r = httpx.post(url, json=payload, headers=headers, timeout=20.0)
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError:
            print("WhatsApp error:", r.status_code, r.text)
            return
