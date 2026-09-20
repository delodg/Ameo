# Ameo — xiaozhi-esp32 fork with OpenRouter

This is a fork of [78/xiaozhi-esp32](https://github.com/78/xiaozhi-esp32) (the
ESP32 firmware) paired with the companion backend
[xinnan-tech/xiaozhi-esp32-server](https://github.com/xinnan-tech/xiaozhi-esp32-server)
(added as a git submodule in `server-backend/`), wired up to use
**OpenRouter** as the LLM instead of the default Chinese providers.

The ESP32 firmware does **not** call an LLM directly — it streams audio to a
backend server over WebSocket/MQTT, and that server runs ASR → LLM → TTS.
To use OpenRouter, we run that backend locally and point OpenRouter at it.

```
Your ESP32  <--WiFi/WebSocket-->  xiaozhi-server (Python, local)  <--HTTPS-->  OpenRouter
```

## 1. Get the repo & submodule

```bash
git clone https://github.com/delodg/Ameo.git
cd Ameo
git submodule update --init --recursive
```

## 2. Configure OpenRouter

```bash
cp .env.local.example .env.local
```

Edit `.env.local`:

```
OPENROUTER_API_KEY=sk-or-v1-...        # from https://openrouter.ai/keys
OPENROUTER_MODEL=openai/gpt-4o-mini    # any model id from openrouter.ai/models
SERVER_LAN_IP=192.168.1.100            # your PC's LAN IP (run `ipconfig`)
```

`SERVER_LAN_IP` matters: the ESP32 is a separate device on your WiFi, it must
reach your PC's IP, not `127.0.0.1`.

Generate the backend config override:

```bash
python scripts/apply_openrouter_config.py
```

This writes `server-backend/main/xiaozhi-server/data/.config.yaml` (git-ignored,
keeps your API key out of the repo) setting `LLM: OpenRouterLLM` with
`type: openai` pointed at `https://openrouter.ai/api/v1`.

## 3. Run the backend server

Option A — Python directly:

```bash
cd server-backend/main/xiaozhi-server
pip install -r requirements.txt
python app.py
```

Option B — Docker:

```bash
cd server-backend
docker compose -f docker-compose.yml up
```

Watch the startup log — it prints the websocket/OTA URLs it's actually
listening on. Confirm it matches `ws://<SERVER_LAN_IP>:8000/xiaozhi/v1/`.

## 4. Build & flash the ESP32 firmware

```bash
cd ../../..            # back to Ameo/ (the firmware root)
idf.py set-target esp32s3      # or esp32, esp32c3, esp32c6... match your board
idf.py menuconfig              # under "Xiaozhi Assistant" set OTA/WebSocket
                                # server URL to your local server
idf.py -p COM5 flash monitor
```

Requires ESP-IDF v6.0.1+ installed (see main `README.md`).

## 5. Test it

Talk to the device — wake word, then ask something. Watch the
`xiaozhi-server` console logs to confirm requests are going out to
`openrouter.ai` and responses are coming back.

## Notes

- `.env.local` is **never committed** (see `.gitignore`).
- Re-run `scripts/apply_openrouter_config.py` any time you change
  `.env.local` (different model, new key, etc.), then restart the server.
- To pick a different OpenRouter model, just change `OPENROUTER_MODEL` —
  no firmware rebuild needed, only a server restart.
- Upstream remotes:
  - `origin` → https://github.com/delodg/Ameo.git (your fork)
  - `upstream` → https://github.com/78/xiaozhi-esp32.git (original firmware)
  - `server-backend` submodule → https://github.com/xinnan-tech/xiaozhi-esp32-server.git
