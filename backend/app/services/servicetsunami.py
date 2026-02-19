import httpx
from app.core.config import settings

class ServiceTsunamiClient:
    def __init__(self):
        self.base_url = settings.SERVICETSUNAMI_API_URL
        self._token: str | None = None

    async def _get_token(self) -> str:
        if self._token:
            return self._token
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/api/v1/auth/login",
                data={
                    "username": settings.SERVICETSUNAMI_EMAIL,
                    "password": settings.SERVICETSUNAMI_PASSWORD,
                },
            )
            resp.raise_for_status()
            self._token = resp.json()["access_token"]
            return self._token

    async def _headers(self) -> dict:
        token = await self._get_token()
        return {"Authorization": f"Bearer {token}"}

    async def send_whatsapp(self, phone_number: str, message: str) -> dict:
        async with httpx.AsyncClient() as client:
            headers = await self._headers()
            session_resp = await client.post(
                f"{self.base_url}/api/v1/chat/sessions",
                headers=headers,
                json={"title": f"WhatsApp to {phone_number}"},
            )
            session_resp.raise_for_status()
            session_id = session_resp.json()["id"]
            msg_resp = await client.post(
                f"{self.base_url}/api/v1/chat/sessions/{session_id}/messages",
                headers=headers,
                json={"content": f"Send WhatsApp to {phone_number}: {message}"},
            )
            msg_resp.raise_for_status()
            return msg_resp.json()

    async def trigger_scraping_pipeline(self, pipeline_id: str) -> dict:
        async with httpx.AsyncClient() as client:
            headers = await self._headers()
            resp = await client.post(
                f"{self.base_url}/api/v1/data_pipelines/{pipeline_id}/execute",
                headers=headers,
            )
            resp.raise_for_status()
            return resp.json()

tsunami_client = ServiceTsunamiClient()
