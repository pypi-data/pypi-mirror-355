# dvoice-tts-py

A Python client for the [DVoice TTS API](https://oyqiz.airi.uz), providing text-to-speech functionality with support for single audio generation via HTTP and real-time audio streaming over WebSocket.

## 🚀 Features

- Generate audio files in multiple formats (`mp3`, `wav`, `ogg`, `aac`, `flac`).
- Stream audio in real-time for low-latency applications.
- Simple and intuitive API for easy integration.
- Robust error handling for reliable usage.

## 📦 Installation

Install the package using pip:

```bash
pip install dvoice-tts
```

## 🧠 Usage

### Importing and Initializing

```python
from dvoice_tts import TTS

# Initialize the client with your API token
tts = TTS(token="YOUR_API_TOKEN")
```

Replace `"YOUR_API_TOKEN"` with your actual API token from the DVoice TTS service.

### Obtaining an API Token

To use the DVoice TTS API, you need a valid API token. Visit the main website at [dvoice.uz](https://dvoice.uz) and navigate to [profile.dvoice.uz](https://profile.dvoice.uz) to create an account or log in. Once logged in, you can generate or retrieve your API token from your profile dashboard.

### 🔊 Generating a Single Audio File

Use the `single()` method to generate an audio file from text:

```python
try:
    audio = tts.single(
        model="default",
        text="Salom!",
        format="mp3"  # Options: 'mp3', 'wav', 'ogg', 'aac', 'flac'
    )
    # Save audio to file
    with open("output.mp3", "wb") as f:
        f.write(audio)
    print("Audio file saved as output.mp3")
except Exception as e:
    print(f"Error generating audio: {e}")
```

### 🌊 Real-Time Audio Streaming

Use the `stream()` method to receive audio chunks in real-time over WebSocket:

```python
def on_chunk(err, chunk, close):
    if err:
        print(f"Stream error: {err}")
        close()  # Close the connection on error
    elif chunk:
        # Process the audio chunk (e.g., feed to an audio player)
        print(f"Received audio chunk: {len(chunk)} bytes")
    else:
        # Stream has ended
        print("Stream completed")
        close()  # Close the connection

tts.stream(
    model="default",
    text="Davomiy nutqni real vaqtda translatsiya qilish!",
    format="mp3",  # Options: 'mp3', 'wav', 'ogg', 'aac', 'flac'
    callback=on_chunk
)
```

The `close()` function can be called within the callback to terminate the WebSocket connection manually.

## 📜 API Reference

### `TTS(token: str)`

Creates a new TTS client instance.

- **Parameters**:
  - `token` (str): Your API token for DVoice TTS authentication.

### `tts.single(model: str, text: str, format: str) -> bytes`

Generates a single audio file from text via HTTP.

- **Parameters**:
  - `model` (str): The TTS model to use (e.g., `"default"`).
  - `text` (str): The text to convert to speech.
  - `format` (str): Audio format (`"mp3"`, `"wav"`, `"ogg"`, `"aac"`, `"flac"`).
- **Returns**: `bytes` - The audio data as bytes.
- **Raises**: `Exception` if the request fails.

### `tts.stream(model: str, text: str, format: str, callback: Callable[[Optional[Exception], Optional[bytes], Callable[[], None]], None]) -> None`

Streams audio chunks in real-time over WebSocket.

- **Parameters**:
  - `model` (str): The TTS model to use (e.g., `"default"`).
  - `text` (str): The text to convert to speech.
  - `format` (str): Audio format (`"mp3"`, `"wav"`, `"ogg"`, `"aac"`, `"flac"`).
  - `callback` (Callable): A function that receives `(err, chunk, close)`:
    - `err` (Exception | None): Any error that occurs.
    - `chunk` (bytes | None): Audio data chunk, or `None` if the stream ends.
    - `close` (Callable): Function to close the WebSocket connection.
- **Returns**: `None`

## 🛠️ Error Handling

Both `single()` and `stream()` methods include error handling:

- For `single()`, errors are raised as exceptions and can be caught using `try/except`.
- For `stream()`, errors are passed to the callback as the `err` parameter.

Example:

```python
try:
    audio = tts.single(model="default", text="Test", format="mp3")
except Exception as e:
    print(f"Failed to generate audio: {e}")
```

## 📝 Notes

- Ensure a valid API token is provided to authenticate with the DVoice TTS API.
- The `stream()` method is suitable for applications requiring real-time audio, such as live voice assistants or interactive systems.
- Refer to the [DVoice TTS API documentation](https://oyqiz.airi.uz/api/v2/tts) for supported models and additional configuration options.
- WebSocket streaming uses the endpoint `ws://oyqiz.airi.uz/stream`.

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

## 🌐 Links

- **API Documentation**: [https://oyqiz.airi.uz/api/v2/tts](https://oyqiz.airi.uz/api/v2/tts)
- **WebSocket Endpoint**: `ws://oyqiz.airi.uz/stream`

## 🌟 Contributing

Contributions are welcome! Please submit a pull request or open an issue on the GitHub repository for bug reports, feature requests, or improvements.
