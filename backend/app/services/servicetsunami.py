"""
ServiceTsunami client — connects to OpenClaw WhatsApp skill via the
ServiceTsunami orchestration API.

Flow:
  1. Authenticate → JWT token
  2. Create an AgentTask with task_type="whatsapp"
  3. ServiceTsunami SkillRouter resolves the tenant's OpenClaw instance
  4. SkillRouter calls OpenClaw gateway: POST {instance}/api/execute
  5. OpenClaw executes the WhatsApp skill (sends via WhatsApp Cloud API)
"""

import logging
from typing import Any

import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

_API = settings.SERVICETSUNAMI_API_URL.rstrip("/")


class ServiceTsunamiClient:
    """Thin async wrapper around the ServiceTsunami orchestration API."""

    def __init__(self) -> None:
        self._token: str | None = None

    # ── Auth ──────────────────────────────────────────────────────────

    async def _get_token(self) -> str:
        if self._token:
            return self._token
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{_API}/api/v1/auth/login",
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

    def invalidate_token(self) -> None:
        self._token = None

    # ── Generic helpers ──────────────────────────────────────────────

    async def _post(self, path: str, json: dict) -> dict:
        """POST with auto-retry on 401 (token expired)."""
        async with httpx.AsyncClient(timeout=60) as client:
            headers = await self._headers()
            resp = await client.post(f"{_API}{path}", headers=headers, json=json)

            if resp.status_code == 401:
                self.invalidate_token()
                headers = await self._headers()
                resp = await client.post(f"{_API}{path}", headers=headers, json=json)

            resp.raise_for_status()
            return resp.json()

    async def _get(self, path: str) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            headers = await self._headers()
            resp = await client.get(f"{_API}{path}", headers=headers)

            if resp.status_code == 401:
                self.invalidate_token()
                headers = await self._headers()
                resp = await client.get(f"{_API}{path}", headers=headers)

            resp.raise_for_status()
            return resp.json()

    # ── WhatsApp via OpenClaw skill ──────────────────────────────────

    async def send_whatsapp(self, phone_number: str, message: str, message_type: str = "text") -> dict:
        """
        Send a WhatsApp message through the OpenClaw WhatsApp skill.

        Creates an AgentTask that the SkillRouter dispatches to the
        tenant's running OpenClaw instance.
        """
        task_payload = {
            "assigned_agent_id": settings.SERVICETSUNAMI_AGENT_ID or None,
            "task_type": "whatsapp",
            "objective": f"Send WhatsApp to {phone_number}",
            "context": {
                "skill": "whatsapp",
                "payload": {
                    "action": "send_message",
                    "recipient_phone": phone_number,
                    "message_body": message,
                    "message_type": message_type,
                },
            },
            "requires_approval": False,
            "priority": "high",
        }
        try:
            result = await self._post("/api/v1/tasks", json=task_payload)
            logger.info("WhatsApp task created: %s → %s", result.get("id"), phone_number)
            return result
        except httpx.HTTPStatusError as exc:
            logger.error("Failed to send WhatsApp to %s: %s", phone_number, exc.response.text[:200])
            raise
        except httpx.ConnectError:
            logger.error("ServiceTsunami unreachable at %s", _API)
            raise

    async def send_whatsapp_template(
        self,
        phone_number: str,
        template_name: str,
        template_params: dict[str, Any] | None = None,
    ) -> dict:
        """Send a WhatsApp template message (for approved business templates)."""
        task_payload = {
            "assigned_agent_id": settings.SERVICETSUNAMI_AGENT_ID or None,
            "task_type": "whatsapp",
            "objective": f"Send template '{template_name}' to {phone_number}",
            "context": {
                "skill": "whatsapp",
                "payload": {
                    "action": "send_template",
                    "recipient_phone": phone_number,
                    "template_name": template_name,
                    "template_params": template_params or {},
                },
            },
            "requires_approval": False,
            "priority": "high",
        }
        try:
            return await self._post("/api/v1/tasks", json=task_payload)
        except Exception:
            logger.exception("Failed to send template '%s' to %s", template_name, phone_number)
            raise

    # ── Chat sessions (for conversational WhatsApp flows) ────────────

    async def create_chat_session(self, title: str, agent_kit_id: str | None = None) -> dict:
        """Create a chat session for a conversational WhatsApp flow."""
        payload: dict[str, Any] = {"title": title}
        if agent_kit_id:
            payload["agent_kit_id"] = agent_kit_id
        return await self._post("/api/v1/chat/sessions", json=payload)

    async def send_chat_message(self, session_id: str, content: str) -> dict:
        """Post a message to a chat session (triggers agent orchestration)."""
        return await self._post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            json={"content": content},
        )

    # ── Pipeline triggers ────────────────────────────────────────────

    async def trigger_scraping_pipeline(self, pipeline_id: str) -> dict:
        """Trigger a data pipeline run (e.g. pharmacy price scraping)."""
        return await self._post(
            f"/api/v1/data_pipelines/{pipeline_id}/run",
            json={"trigger_type": "manual", "context": {"source": "pharmapp"}},
        )

    async def get_pipeline_status(self, pipeline_id: str, run_id: str) -> dict:
        """Check the status of a pipeline run."""
        return await self._get(f"/api/v1/data_pipelines/{pipeline_id}/runs/{run_id}")

    # ── Skill config management ──────────────────────────────────────

    async def get_skill_registry(self) -> dict:
        """List all available skills and their credential schemas."""
        return await self._get("/api/v1/skill-configs/registry")

    async def get_skill_configs(self) -> dict:
        """List tenant's configured skills."""
        return await self._get("/api/v1/skill-configs/")

    # ── Task tracking ────────────────────────────────────────────────

    async def get_task(self, task_id: str) -> dict:
        """Get task status and execution trace."""
        return await self._get(f"/api/v1/tasks/{task_id}")

    async def get_task_trace(self, task_id: str) -> dict:
        """Get detailed execution trace for a task."""
        return await self._get(f"/api/v1/tasks/{task_id}/trace")


tsunami_client = ServiceTsunamiClient()
