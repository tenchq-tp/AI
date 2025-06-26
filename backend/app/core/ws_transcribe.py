import asyncio
import websockets
import json

WS_URL = 'wss://ai-asr.welcome-ddns.com:443/api'
CHUNK_SIZE = 1024  # Bytes per chunk
WS_TIMEOUT = 60  # Seconds

async def transcribe_audio_via_ws(audio_path: str) -> dict:
    try:
        print(f"Connecting to WebSocket for: {audio_path}")
        async with websockets.connect(WS_URL, open_timeout=WS_TIMEOUT) as websocket:
            print("✅ WebSocket connected")

            result = {}

            async def send_audio():
                print("📤 Sending audio...")
                with open(audio_path, 'rb') as f:
                    while chunk := f.read(CHUNK_SIZE):
                        await websocket.send(chunk)
                        # print("✅ Sent audio chunk")
                await websocket.send("eof")
                print("✅ Sent EOF")

            async def receive_transcriptions():
                nonlocal result
                try:
                    async for message in websocket:
                        print("📩 Received message")
                        decoded = json.loads(message)
                        print("Transcription received:", decoded)
                        result = decoded
                        if decoded.get("status") == "Success":
                            break 
                except websockets.exceptions.ConnectionClosed:
                    print("⚠️ WebSocket connection closed")

            await asyncio.wait_for(
                asyncio.gather(send_audio(), receive_transcriptions()),
                timeout=WS_TIMEOUT
            )

            return result

    except asyncio.TimeoutError:
        print("❌ WebSocket transcription timeout")
        return {"status": "Timeout", "text_with_time": []}
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        return {"status": "Error", "text_with_time": []}
