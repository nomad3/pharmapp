# PharmApp ↔ ServiceTsunami WhatsApp Integration

> **For the ServiceTsunami agent:** This document describes exactly what PharmApp has built and what ServiceTsunami needs to implement to complete the WhatsApp integration via OpenClaw.

**Goal:** Enable PharmApp to send and receive WhatsApp messages through ServiceTsunami's SkillRouter → OpenClaw pipeline.

**Status:** PharmApp side is complete. ServiceTsunami side needs the SkillRouter WhatsApp handler and OpenClaw webhook forwarding.

---

## Architecture Overview

```
PharmApp (FastAPI :8000)
  │
  ├── Outbound: POST /api/v1/tasks  ──→  ServiceTsunami API (:8001)
  │                                            │
  │                                       SkillRouter.execute_skill("whatsapp", payload)
  │                                            │
  │                                       OpenClaw Instance (:18789)
  │                                         POST /api/execute
  │                                            │
  │                                       WhatsApp Cloud API
  │                                            │
  └── Inbound:  WhatsApp Cloud API  ──→  OpenClaw webhook receiver
                                            │
                                       POST PharmApp /api/v1/webhooks/whatsapp
                                         (with X-Webhook-Signature header)
```

---

## Part 1: What PharmApp Has Built

### 1.1 Outbound — Sending WhatsApp Messages

PharmApp sends WhatsApp messages by creating AgentTasks via `POST /api/v1/tasks`.

**Client file:** `backend/app/services/servicetsunami.py`
**WhatsApp templates:** `backend/app/services/whatsapp.py`

#### Task Payload for `send_message`

```json
{
  "assigned_agent_id": "<SERVICETSUNAMI_AGENT_ID or null>",
  "task_type": "whatsapp",
  "objective": "Send WhatsApp to +56912345678",
  "context": {
    "skill": "whatsapp",
    "payload": {
      "action": "send_message",
      "recipient_phone": "+56912345678",
      "message_body": "🔐 *PharmApp — Código de verificación*\n\nTu código es: *123456*\n\nExpira en 5 minutos.",
      "message_type": "text"
    }
  },
  "requires_approval": false,
  "priority": "high"
}
```

#### Task Payload for `send_template`

```json
{
  "assigned_agent_id": "<SERVICETSUNAMI_AGENT_ID or null>",
  "task_type": "whatsapp",
  "objective": "Send template 'order_confirmation' to +56912345678",
  "context": {
    "skill": "whatsapp",
    "payload": {
      "action": "send_template",
      "recipient_phone": "+56912345678",
      "template_name": "order_confirmation",
      "template_params": {
        "order_id": "abc12345",
        "total": "15000"
      }
    }
  },
  "requires_approval": false,
  "priority": "high"
}
```

#### Message Types PharmApp Sends

| Function | Trigger | Message Content |
|----------|---------|-----------------|
| `send_otp` | User requests login | Verification code, 5-min expiry |
| `send_order_confirmation` | Order created | Order ID, total, payment URL |
| `send_payment_confirmed` | MercadoPago/Transbank webhook | Payment received confirmation |
| `send_delivery_update` | Order status change | Dispatched (with rider/ETA) or Delivered |
| `send_price_alert` | Price drop detected | Medication name, new price, pharmacy |

### 1.2 Inbound — Receiving WhatsApp Messages

PharmApp exposes two webhook endpoints for incoming WhatsApp messages.

**Webhook file:** `backend/app/api/v1/webhooks.py`

#### POST `/api/v1/webhooks/whatsapp` — Incoming Messages

Expects the standard WhatsApp Cloud API webhook format:

```json
{
  "entry": [
    {
      "changes": [
        {
          "value": {
            "messages": [
              {
                "from": "+56912345678",
                "id": "wamid.xxx",
                "type": "text",
                "text": {
                  "body": "Quiero buscar paracetamol"
                }
              }
            ]
          }
        }
      ]
    }
  ]
}
```

**Signature verification:** If `PHARMAPP_WEBHOOK_SECRET` is set, PharmApp validates the `X-Webhook-Signature` header:

```python
expected = hmac.new(
    PHARMAPP_WEBHOOK_SECRET.encode(),
    raw_body,
    hashlib.sha256
).hexdigest()
# Header: X-Webhook-Signature: <hex digest>
```

**Processing flow:** For each message, PharmApp calls `whatsapp.handle_incoming_message()` which:
1. Creates a chat session in ServiceTsunami (`POST /api/v1/chat/sessions`)
2. Sends the message as context (`POST /api/v1/chat/sessions/{id}/messages`)
3. Gets the agent's reply
4. Sends the reply back to the user via `tsunami_client.send_whatsapp()`

#### GET `/api/v1/webhooks/whatsapp` — Verification Challenge

Standard WhatsApp Cloud API verification:

```
GET /api/v1/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=<secret>&hub.challenge=<challenge>
```

Returns the `hub.challenge` value as an integer if `hub.verify_token` matches `PHARMAPP_WEBHOOK_SECRET`.

### 1.3 Chat Sessions for Conversational Flows

PharmApp uses ServiceTsunami's chat API for conversational WhatsApp:

```python
# 1. Create session
session = await tsunami_client.create_chat_session(
    title=f"PharmApp WhatsApp — {sender_phone}"
)

# 2. Send message with context
response = await tsunami_client.send_chat_message(
    session["id"],
    f"[PharmApp WhatsApp]\nFrom: {sender_phone}\nMessage ID: {message_id}\n\n{message_body}"
)

# 3. Get agent reply
reply = response["assistant_message"]["content"]
```

### 1.4 Configuration

PharmApp expects these environment variables:

```bash
SERVICETSUNAMI_API_URL=http://host.docker.internal:8001  # or cluster URL
SERVICETSUNAMI_EMAIL=<login email>
SERVICETSUNAMI_PASSWORD=<login password>
SERVICETSUNAMI_AGENT_ID=<agent UUID to assign tasks to>

PHARMAPP_WEBHOOK_URL=http://localhost:8000/api/v1/webhooks/whatsapp
PHARMAPP_WEBHOOK_SECRET=<shared HMAC secret>
```

---

## Part 2: What ServiceTsunami Needs to Implement

### 2.1 SkillRouter: Handle `task_type="whatsapp"` → OpenClaw Execution

**File to modify:** `apps/api/app/services/orchestration/skill_router.py`

The SkillRouter already handles skill execution via OpenClaw. When a task arrives with `context.skill = "whatsapp"`, the router should:

1. Resolve the tenant's running OpenClaw instance (existing logic)
2. Load WhatsApp credentials from `CredentialVault` (existing logic)
3. POST to OpenClaw gateway with the WhatsApp payload

**Expected OpenClaw gateway call:**

```python
POST {instance.internal_url}/api/execute
{
  "skill": "whatsapp",
  "payload": {
    "action": "send_message",          # or "send_template"
    "recipient_phone": "+56912345678",
    "message_body": "Hello from PharmApp",
    "message_type": "text"
  },
  "credentials": {
    "api_key": "<decrypted WhatsApp Cloud API token>",
    "phone_number_id": "<decrypted phone number ID>"
  },
  "llm": {}  # Not needed for WhatsApp sends
}
```

**Note:** The SkillRouter may already support this generically via `execute_skill()`. Verify that `task_type="whatsapp"` tasks flow through the existing dispatch pipeline correctly. The key fields to route on:
- `context.skill` → `"whatsapp"` (used to load credentials)
- `context.payload` → forwarded as `payload` to OpenClaw

### 2.2 OpenClaw: WhatsApp Skill Handler

**Where:** Inside the OpenClaw codebase (the skill execution engine running on port 18789)

OpenClaw needs a skill handler at `POST /api/execute` that, when `skill == "whatsapp"`, makes the actual WhatsApp Cloud API call.

#### For `action: "send_message"`

```python
# WhatsApp Cloud API call
POST https://graph.facebook.com/v21.0/{phone_number_id}/messages
Authorization: Bearer {api_key}
Content-Type: application/json

{
  "messaging_product": "whatsapp",
  "to": "{recipient_phone}",
  "type": "text",
  "text": {
    "body": "{message_body}"
  }
}
```

#### For `action: "send_template"`

```python
POST https://graph.facebook.com/v21.0/{phone_number_id}/messages
Authorization: Bearer {api_key}
Content-Type: application/json

{
  "messaging_product": "whatsapp",
  "to": "{recipient_phone}",
  "type": "template",
  "template": {
    "name": "{template_name}",
    "language": {"code": "es"},
    "components": [
      {
        "type": "body",
        "parameters": [
          {"type": "text", "text": "{param_value}"}
        ]
      }
    ]
  }
}
```

#### Expected Response to SkillRouter

```json
{
  "status": "success",
  "message_id": "wamid.HBgNNTY5...",
  "recipient": "+56912345678"
}
```

Or on failure:

```json
{
  "status": "error",
  "error": "Invalid phone number",
  "details": { ... }
}
```

### 2.3 OpenClaw: Webhook Receiver & Forwarding

OpenClaw must receive WhatsApp Cloud API webhooks and forward them to PharmApp.

#### Step 1: Register webhook URL with Meta

During WhatsApp Business Account setup, register the OpenClaw instance URL as the webhook callback:
```
https://<openclaw-domain>/webhooks/whatsapp
```

#### Step 2: Implement webhook receiver in OpenClaw

```
GET  /webhooks/whatsapp  → Verification challenge (hub.mode, hub.verify_token, hub.challenge)
POST /webhooks/whatsapp  → Incoming messages
```

#### Step 3: Forward to PharmApp

When OpenClaw receives an incoming message webhook, forward the entire body to PharmApp:

```python
POST {PHARMAPP_WEBHOOK_URL}
X-Webhook-Signature: {hmac_sha256(PHARMAPP_WEBHOOK_SECRET, raw_body)}
Content-Type: application/json

<original WhatsApp Cloud API webhook body>
```

The HMAC signature is computed as:
```python
import hmac, hashlib
signature = hmac.new(
    PHARMAPP_WEBHOOK_SECRET.encode(),
    raw_body,
    hashlib.sha256
).hexdigest()
```

**Configuration needed in OpenClaw:**
- `PHARMAPP_WEBHOOK_URL` — Where to forward (e.g., `http://pharmapp-backend:8000/api/v1/webhooks/whatsapp`)
- `PHARMAPP_WEBHOOK_SECRET` — Shared secret for HMAC signing
- `WHATSAPP_VERIFY_TOKEN` — Token for Meta's webhook verification challenge

### 2.4 WhatsApp Skill Credentials Schema

Already defined in `apps/api/app/api/v1/skill_configs.py`:

```python
"whatsapp": {
    "display_name": "WhatsApp",
    "description": "Send and receive WhatsApp messages",
    "icon": "FaWhatsapp",
    "credentials": [
        {"key": "api_key", "label": "API Key", "type": "password", "required": True},
        {"key": "phone_number_id", "label": "Phone Number ID", "type": "text", "required": True},
    ],
}
```

**No changes needed** — this schema is correct. The tenant configures their WhatsApp Cloud API credentials through the UI, and `CredentialVault` encrypts them at rest.

---

## Part 3: Integration Checklist

### ServiceTsunami API (`apps/api`)

- [ ] Verify `task_type="whatsapp"` tasks route through `SkillRouter.execute_skill()` correctly
- [ ] Ensure task dispatch pipeline handles the `context.skill` and `context.payload` fields
- [ ] Test credential decryption for WhatsApp skill before OpenClaw call
- [ ] Add execution trace logging for WhatsApp skill calls

### OpenClaw Instance

- [ ] Implement WhatsApp skill handler in `POST /api/execute` for `skill="whatsapp"`
- [ ] Handle `send_message` action → WhatsApp Cloud API text message
- [ ] Handle `send_template` action → WhatsApp Cloud API template message
- [ ] Implement `GET /webhooks/whatsapp` for Meta verification challenge
- [ ] Implement `POST /webhooks/whatsapp` to receive incoming messages
- [ ] Forward incoming messages to `PHARMAPP_WEBHOOK_URL` with HMAC signature
- [ ] Return structured response (`status`, `message_id`) to SkillRouter

### Configuration & Setup

- [ ] Configure WhatsApp Business Account credentials via ServiceTsunami UI
- [ ] Set `PHARMAPP_WEBHOOK_URL` and `PHARMAPP_WEBHOOK_SECRET` in OpenClaw config
- [ ] Register OpenClaw's webhook URL with Meta's WhatsApp Business Platform
- [ ] Set `SERVICETSUNAMI_AGENT_ID` in PharmApp's `.env` (the agent to assign WhatsApp tasks to)

---

## Part 4: Testing Flow

### Outbound (PharmApp → WhatsApp)

1. PharmApp user requests OTP login
2. PharmApp calls `POST /api/v1/tasks` with `task_type="whatsapp"`, `action="send_message"`
3. ServiceTsunami creates task, dispatches via SkillRouter
4. SkillRouter resolves OpenClaw instance, loads WhatsApp credentials
5. SkillRouter calls `POST {openclaw}/api/execute` with skill="whatsapp"
6. OpenClaw calls WhatsApp Cloud API
7. User receives OTP on WhatsApp

### Inbound (WhatsApp → PharmApp)

1. User sends WhatsApp message to the business number
2. Meta sends webhook to OpenClaw's `POST /webhooks/whatsapp`
3. OpenClaw forwards body to PharmApp's `POST /api/v1/webhooks/whatsapp` with HMAC signature
4. PharmApp verifies signature, extracts message
5. PharmApp creates chat session in ServiceTsunami
6. ServiceTsunami agent processes message, returns reply
7. PharmApp sends reply back via `send_whatsapp()` (outbound flow)

---

## Key File References

### PharmApp (this repo)

| File | Purpose |
|------|---------|
| `backend/app/services/servicetsunami.py` | HTTP client — auth, task creation, chat sessions |
| `backend/app/services/whatsapp.py` | Message templates + incoming handler |
| `backend/app/api/v1/webhooks.py` | Webhook endpoints (WhatsApp, MercadoPago, Transbank) |
| `backend/app/core/config.py` | Environment variable definitions |
| `backend/.env.example` | Required env vars |

### ServiceTsunami (`../servicetsunami-agents`)

| File | Purpose |
|------|---------|
| `apps/api/app/services/orchestration/skill_router.py` | Routes skills to OpenClaw |
| `apps/api/app/services/orchestration/credential_vault.py` | Decrypts credentials at runtime |
| `apps/api/app/services/agent_tasks.py` | Task CRUD |
| `apps/api/app/api/v1/agent_tasks.py` | Task API endpoints |
| `apps/api/app/api/v1/skill_configs.py` | Skill registry (WhatsApp schema already defined) |
| `apps/api/app/models/agent_task.py` | Task model (context JSON field) |
