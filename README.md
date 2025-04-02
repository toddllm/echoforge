# EchoForge - Voice Generation Platform

EchoForge is an advanced voice generation platform that allows you to create lifelike vocal content with customizable parameters.

## 🚨 Debug Mode Available 🚨

For troubleshooting API issues, a new debug page has been added. To access it:
1. Start the server as described below
2. Visit: `http://localhost:8765/debug`
3. Use the debug interface to test different API endpoints and trace request/response flow

## Repository

https://github.com/toddllm/echoforge

## Features

- Text-to-speech generation with multiple character voices
- Adjustable generation parameters (temperature, top-k, style)
- Background task processing for long-running generations
- RESTful API for integration with other applications
- Web interface with light and dark mode support
- Easy environment configuration

## Technology

EchoForge is built on top of the [Conversational Speech Model (CSM)](https://github.com/SesameAILabs/csm) from Sesame AI Labs. CSM is a speech generation model that generates high-quality, natural-sounding speech from text input. The model architecture employs a Llama backbone and a smaller audio decoder that produces Mimi audio codes.

Key features of the CSM model:
- High-quality speech synthesis
- Support for multiple speakers
- Contextual awareness for more natural-sounding conversations
- Adjustable generation parameters (temperature, top-k)

EchoForge wraps this technology in a user-friendly web interface and API, making it accessible for various applications.

### Direct CSM Implementation

EchoForge now uses the Direct CSM implementation by default for faster voice generation, especially on CUDA-enabled devices.

#### Features
- Up to 25x faster generation on GPU compared to CPU
- Maintains the same high-quality voice output
- Automatically falls back to CPU if CUDA is unavailable

#### Usage
To start the server with Direct CSM enabled:
```
python run.py --direct-csm
```

When using the API, specify `device=cuda` for faster generation:
```
curl -X POST http://localhost:8779/api/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "Your text here", "voice": "male", "temperature": 0.7, "device": "cuda"}'
```

#### Performance
- CUDA generation: ~3-6 seconds
- CPU generation: ~150 seconds

## Installation

### Option 1: Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a faster, more reliable Python package installer and resolver.

1. Install uv:
```bash
pip install uv
```

2. Clone the repository:
```bash
git clone https://github.com/yourusername/echoforge.git
cd echoforge
```

3. Create a virtual environment and install dependencies:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

### Option 2: Using pip

1. Clone the repository:
```bash
git clone https://github.com/yourusername/echoforge.git
cd echoforge
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

1. Create a `.env` file in the project root with the following content:
```
DEBUG=true
HOST=0.0.0.0
PORT=8765
OUTPUT_DIR=./static/voices
STATIC_DIR=./static
TEMPLATES_DIR=./templates
```

2. Configure voice directories:
```bash
# Create directories for voice data
mkdir -p static/voices/creative
```

## Running the Server

### Starting the Server

Use the provided script to start the server:

```bash
./start_server.sh
```

Or manually:

```bash
uvicorn run:app --host 0.0.0.0 --port 8765 --reload
```

### Stopping the Server

Use the provided script to stop the server:

```bash
./stop_server.sh
```

## Using the Debug Page

The debug page is a powerful tool for troubleshooting voice generation issues:

1. Navigate to `http://localhost:8765/debug` in your browser
2. The debug page provides:
   - API selection between `/api/v1/generate` and `/api/voices/generate`
   - Detailed request/response information
   - Task ID validation and tracking
   - Audio URL construction debugging
   - Network connection testing

### Debug Page Features

- **API Version Selection**: Test both API versions to identify compatibility issues
- **Parameter Controls**: Adjust voice generation parameters like temperature and top-k
- **Request Inspection**: View the exact request payload being sent
- **Response Monitoring**: See the raw response and parsed data
- **Status Checking**: Monitor the task progress through different endpoints
- **URL Validation**: Troubleshoot issues with audio URL construction
- **Network Testing**: Test if endpoints are accessible and responding

## API Endpoints

### Voice Generation

- `POST /api/v1/generate`: Generate voice using API v1
  ```json
  {
    "text": "Text to convert to speech",
    "speaker_id": 1,
    "temperature": 0.7,
    "top_k": 50,
    "device": "auto"
  }
  ```

- `POST /api/voices/generate`: Generate voice using voices API
  ```json
  {
    "text": "Text to convert to speech",
    "speaker_id": 1,
    "temperature": 0.7,
    "top_k": 50,
    "device": "auto"
  }
  ```

### Task Status

- `GET /api/v1/tasks/{task_id}`: Check task status with API v1
- `GET /api/voices/tasks/{task_id}`: Check task status with voices API

### Voice Listing

- `GET /api/voices`: Get list of available voices
- `GET /api/voices/list`: Alternative endpoint for voice listing

## Troubleshooting

### Common Issues

1. **"GET http://localhost:8765/undefined 404 (Not Found)"**
   - This indicates an issue with audio URL construction
   - Use the debug page to trace the URL construction process
   - Ensure task IDs are properly validated

2. **Speaker ID validation errors**
   - If using `speaker_id: 0`, the system will automatically map to `speaker_id: 1`
   - Verify speaker IDs in the range 1-5 are available

3. **API endpoint not found**
   - The system supports both `/api/v1/generate` and `/api/voices/generate`
   - Use the debug page to test which endpoint is working
   - Check for typos in endpoint URLs

4. **Voice files not playing**
   - Ensure the `static/voices/creative` directory contains voice files
   - Check the audio URL construction in the debug logs
   - Verify file permissions on the voice files

### Using the Debug Console

The debug page contains a JavaScript console that provides detailed logging:

1. Open your browser's developer tools (F12 or right-click -> Inspect)
2. Navigate to the Console tab
3. Look for errors or warnings related to API calls
4. The debug page will also display detailed logs in its interface

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- This project uses the [CSM model architecture](https://github.com/SesameAILabs/csm) from Sesame AI Labs for voice generation
- Special thanks to the open-source community for their contributions to speech synthesis technology

## Voice Generation Interface

The EchoForge admin panel includes a simplified voice generation interface that allows you to:

1. Enter text to be spoken
2. Select a voice (Male, Female, or Child)
3. Adjust temperature settings
4. Generate and download audio files

To access the voice generation interface:
1. Navigate to `http://[server-address]:[port]/admin/voices`
2. Log in with your admin credentials
3. Use the form to generate voice samples

The interface provides real-time feedback on generation status and device information during processing.