import requests
from websocket import WebSocketApp
import threading
from urllib.parse import urlencode


class TTS:
    def __init__(self, token: str):
        self.token = token
        self.api_url = "https://oyqiz.airi.uz/api/v2/tts"
        self.ws_url = "ws://oyqiz.airi.uz/stream"

    def single(self, model: str, text: str, format: str) -> bytes:
        response = requests.post(
            self.api_url,
            headers={"token": f"{self.token}"},
            json={"model": model, "text": text, "format": format},
             verify=False
        )
        response.raise_for_status()
        return response.content

    def stream(self, model: str, text: str, format: str, callback):
        params = urlencode({"model": model, "text": text, "format": format})

        def on_message(ws, message):
            callback(None, message, lambda: ws.close())

        def on_error(ws, error):
            callback(error, None, lambda: ws.close())

        def on_close(ws, close_status_code, close_msg):
            callback(None, None, lambda: ws.close())

        ws = WebSocketApp(
            f"{self.ws_url}?{params}",
            header=[f"token: {self.token}"],
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )


        thread = threading.Thread(target=ws.run_forever)
        thread.daemon = True
        thread.start()
