# Hermes Agent: Matrix Integration & Operational Architecture

**Date:** 2026-09-11  
**System:** Linux VPS (`vmi3420780`, Ubuntu 6.8.0-136-generic)  
**Install Path:** `/home/hermes/.hermes/hermes-agent`  
**Runtime:** Python 3.11.16  
**Repository:** https://github.com/biggieb327-lgtm/obsidian-vault

---

## 1. Overview & System Topology

Hermes operates as a persistent daemon running on a Linux VPS. It interacts via multiple messaging platforms (Matrix primary, Telegram secondary, Webhook, API Server). Incoming user messages flow from the platform adapter through the gateway runner, into the agent turn loop, out to LLM providers with tool definitions, and return asynchronously back to the platform.

```
┌────────────────────────────────────────────────────────┐
│                   Matrix Homeserver                    │
│                     (matrix.org)                       │
└──────────────────────────┬─────────────────────────────┘
                           │ Sync / Events (HTTPS / E2EE)
                           ▼
┌────────────────────────────────────────────────────────┐
│       Hermes Matrix Adapter (plugins/platforms/matrix) │
│                Built on `mautrix-python`               │
└──────────────────────────┬─────────────────────────────┘
                           │ MessageEvent (Normalised)
                           ▼
┌────────────────────────────────────────────────────────┐
│         Gateway Core (gateway/run.py & run_*.py)       │
│  - Active session lock / pending debounce              │
│  - Slash command interception                          │
│  - TurnContext & history assembly                      │
└──────────────────────────┬─────────────────────────────┘
                           │ run_conversation()
                           ▼
┌────────────────────────────────────────────────────────┐
│      Agent Execution Loop (agent/conversation_loop.py) │
│  - System prompt & memory injection                    │
│  - Tool schema gathering (OpenAI format)               │
│  - Tool execution & loopback                           │
└──────────────┬──────────────────────────┬──────────────┘
               │                          │
        API Call (JSON)             Tool Dispatch
               ▼                          ▼
┌──────────────────────────────┐  ┌──────────────────────┐
│ LLM Provider                 │  │ Hermes Tool Registry │
│ - Custom: local-router       │  │ - Terminal / File    │
│   (llama3.2:3b on Z Fold7)   │  │ - Qdrant search      │
│ - Backup: OpenRouter         │  │ - Obsidian / YNAB    │
│   (nex-n2.5-mini:free)       │  │ - Web search/extract │
└──────────────────────────────┘  └──────────────────────┘
```

---

## 2. Matrix Platform Implementation

### 2.1 Library & Dependencies
Hermes uses **`mautrix`** (`mautrix-python`), providing native async Matrix client functionality, Olm/Megolm E2EE encryption support via SQLite, and media transfer capabilities.
- Source path: `/home/hermes/.hermes/hermes-agent/plugins/platforms/matrix/adapter.py`
- Adapter Class: `MatrixAdapter(BasePlatformAdapter)`

### 2.2 Connection Lifecycle
1. **Initialisation (`connect()`):**
   - Reads homeserver URL (`https://matrix.org`), credentials, and device configuration.
   - Instantiates `mautrix.client.Client` with `MemoryStateStore` and `MemorySyncStore`.
   - SQLite crypto store initialised at `platforms/matrix/store/crypto.db`.
   - Starts `/sync` polling loop via `client.start()` / `asyncio.create_task(self._sync_loop())`.
2. **Event Handling (`_on_room_message()`):**
   - Listens for `m.room.message` events (`m.text`, `m.image`, `m.file`, `m.audio`).
   - Ignores self-sent messages, bot notices (`m.notice` unless configured), and duplicate transaction IDs.
   - Decodes message body, handles reply fallbacks, strips mentions, and packages payload into a standardized `MessageEvent`.
3. **Delivery (`send()`):**
   - Formats markdown into Matrix-compliant HTML (converting tables into block attributes, code blocks, lists).
   - Splits messages exceeding `max_message_length` (default ~4000 characters).
   - Transmits via `client.send_message_event(RoomID, EventType.ROOM_MESSAGE, content)`.
   - Supports media uploads (`m.image`, `m.file`, `m.audio`) via Matrix Content Repository (`_upload_media()`).

---

## 3. Configuration & Secrets Management

Hermes uses a strict separation between declarative operational configuration and sensitive secrets:

1. **`~/.hermes/config.yaml`**:
   - Primary agent configuration: default models, context limits, tool guardrails, platform definitions, compression thresholds.
   - Matrix platform block:
     ```yaml
     platforms:
       matrix:
         enabled: true
         home_channel:
           platform: matrix
           chat_id: '!QXgRnRSGvwdqhAsXqA:matrix.org'
           name: Hermes
           user_id: '@brianault327:matrix.org'
           scope_id: matrix.org
     ```
2. **`~/.hermes/.env`**:
   - Holds credentials and tokens:
     - `MATRIX_HOMESERVER`: `https://matrix.org`
     - `MATRIX_USER_ID`: `@...:matrix.org`
     - `MATRIX_PASSWORD`: Auth token / password
     - `MATRIX_ENCRYPTION`: `true`
     - `OPENROUTER_API_KEY`: Fallback LLM credentials
     - `NOTION_API_KEY`, `YNAB_API_KEY`: Domain integrations
   - File permissions: `600` (read/write only by user `hermes`).

---

## 4. End-to-End Execution Flow (Message → LLM → Tool → Output)

### Step 1: Receiving Inbound Message
In `plugins/platforms/matrix/adapter.py`:
```python
async def _on_room_message(self, event: Any) -> None:
    room_id = str(getattr(event, "room_id", ""))
    sender = str(getattr(event, "sender", ""))
    if self._is_self_sender(sender):
        return
    # Extract body, resolve context, wrap as MessageEvent
    message_event = self._build_message_event(event, body, is_dm=True)
    await self.handle_message(message_event)
```
In `gateway/platforms/base.py`:
- `handle_message()` checks `_active_sessions`.
- Dispatches to `_process_message_background()`.

### Step 2: Forwarding to Gateway & LLM
In `gateway/run_turn_runner.py`:
```python
def run_sync(self):
    # Assembles system prompt (SOUL.md, AGENTS.md, MEMORY.md)
    # Passes conversation history and tool definitions
    result = agent.run_conversation(api_message, **kwargs)
    return result
```

In `agent/conversation_loop.py`:
- Queries `tools/registry.py` for enabled tools matching OpenAI schema (`{"type": "function", "function": {...}}`).
- Calls LLM endpoint:
```python
response = client.chat.completions.create(
    model=model,
    messages=messages,
    tools=tool_schemas,
    temperature=0.1,
    max_tokens=8192
)
```

### Step 3: Executing Tool Calls
In `agent/turn_tool_round.py` and `agent/tool_executor.py`:
```python
for tc in assistant_message.tool_calls:
    tool_name = tc.function.name
    tool_args = json.loads(tc.function.arguments)
    # Dispatches to tools/registry.py
    result_str = model_tools.handle_function_call(tool_name, tool_args, task_id)
    messages.append({
        "role": "tool",
        "tool_call_id": tc.id,
        "name": tool_name,
        "content": result_str
    })
```
The agent re-enters the loop with the tool output until the model outputs a final assistant text response.

### Step 4: Transmitting Back to Matrix
In `gateway/platforms/base.py` & `plugins/platforms/matrix/adapter.py`:
```python
await delivery_adapter.send(
    chat_id=event.source.chat_id,
    content=final_text_response,
    reply_to=event.message_id
)
```
The `MatrixAdapter` renders markdown, formats HTML, breaks messages into chunks under 4000 chars, and posts events to Matrix room `!QXgRnRSGvwdqhAsXqA:matrix.org`.

---

## 5. Tool System & Extensibility

Tools are defined via standard OpenAI JSON schemas and registered in `tools/registry.py`:

```python
from tools.registry import registry

registry.register(
    name="qdrant_search",
    toolset="memory",
    schema={
        "name": "qdrant_search",
        "description": "Semantic search over indexed documentation and vault notes",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "default": 5}
            },
            "required": ["query"]
        }
    },
    handler=lambda args, **kw: run_qdrant_search(args.get("query"), args.get("limit", 5)),
    check_fn=lambda: True
)
```

**Active Toolsets:**
- `terminal`, `file`, `web_search`, `web_extract`, `patch`, `search_files`
- `qdrant_search`, `qdrant_status`
- `obsidian_search_notes`, `obsidian_create_note`, `obsidian_read_note`, `obsidian_daily_note`
- `ynab_budget_overview`, `ynab_transactions`, `ynab_create_transaction`, `ynab_categories`

---

## 6. Process Supervision & Deployment

### 6.1 Host Environment
- **Host:** Linux VPS (`vmi3420780`), Contabo infrastructure.
- **Tailscale IP:** `100.81.134.67`
- **Fallback Node:** `100.113.100.67:11434` (Samsung Z Fold7 / Termux Ollama)

### 6.2 Systemd User Services
Managed under `systemd --user` for user `hermes`:
1. `hermes-gateway.service`: Main gateway listening on port `8642`, running Matrix connection and cron scheduler.
2. `hermes-gateway-implementer.service`: Isolated secondary implementer profile gateway.
3. `hermes-serve.service`: Web backend running on port `9119`.
4. `hermes-bridge.service`: Console bridge running on port `9131`.

Status check command:
```bash
systemctl --user status hermes-gateway
```

### 6.3 Automated Crons & Auto-Sync
- **Cron Jobs (`~/.hermes/cron/jobs.json`):**
  - `bulletproof-hermes`: Comprehensive health audit every 6 hours.
  - `morning-briefing`: News, weather, and status every day at 08:00.
  - `obsidian_auto_push.sh`: Auto-commits and pushes vault changes to GitHub every 10 minutes.
  - `memory-curator`: Cleans and compacts `MEMORY.md` daily.
