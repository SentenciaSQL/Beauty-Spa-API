from fastapi import APIRouter, Depends, HTTPException
import httpx

from app.core.config import settings
from app.core.deps import require_roles

router = APIRouter(prefix="/admin/whatsapp-debug", tags=["admin-whatsapp-debug"])

def only_digits(phone: str) -> str:
    return "".join(ch for ch in phone if ch.isdigit())

@router.post("/hello", dependencies=[Depends(require_roles("ADMIN"))])
def send_hello_world(to_e164: str):
    """
    TEMPORAL: manda el template 'hello_world' para validar WhatsApp Cloud API.
    No depende del resto del sistema.
    Uso:
      POST /api/v1/admin/whatsapp-debug/hello?to_e164=+1809XXXXXXX
    """
    try:
        url = f"https://graph.facebook.com/v22.0/{settings.WA_PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {settings.WA_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": only_digits(to_e164),
            "type": "template",
            "template": {
                "name": "hello_world",
                "language": {"code": "en_US"},
            },
        }

        r = httpx.post(url, json=payload, headers=headers, timeout=20.0)

        if r.status_code >= 400:
            # devolvemos el error de Meta tal cual, para debug fácil
            raise HTTPException(status_code=502, detail={"wa_status": r.status_code, "wa_body": r.text})

        return {"ok": True, "meta": r.json()}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
