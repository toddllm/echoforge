# EchoForge

EchoForge is a web application for generating character voices using deep learning models. It provides a simple interface for converting text to speech with various voice options.

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

### Prerequisites

- Python 3.8 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Using uv (Recommended)

EchoForge uses [uv](https://github.com/astral-sh/uv) for fast, reliable Python package management. To set up the environment with uv:

```bash
# Clone the repository
git clone https://github.com/toddllm/echoforge.git
cd echoforge

# Run the setup script
chmod +x setup_env.sh
./setup_env.sh
```

The setup script will:
1. Install uv if it's not already installed
2. Create a virtual environment
3. Install dependencies using `uv sync` (faster than pip)
4. Create a default `.env.local` file for local configuration

### Using pip

If you prefer to use pip:

```bash
# Clone the repository
git clone https://github.com/toddllm/echoforge.git
cd echoforge

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

EchoForge can be configured using environment variables or `.env` files:

- `.env` - Base environment configuration
- `.env.local` - Local overrides (not committed to version control)

### Environment Variables

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `ALLOW_PUBLIC_SERVING` | Allow serving on all network interfaces | `false` |
| `PUBLIC_HOST` | Host to bind when public serving is enabled | `0.0.0.0` |
| `PORT` | Port to run the server on | `8765` |
| `DEFAULT_THEME` | Default UI theme (light or dark) | `light` |
| `ENABLE_AUTH` | Enable HTTP Basic authentication | `false` |
| `AUTH_USERNAME` | Username for authentication | `echoforge` |
| `AUTH_PASSWORD` | Password for authentication | `changeme123` |
| `MODEL_PATH` | Path to the model checkpoint | `/path/to/model/checkpoint` |
| `OUTPUT_DIR` | Directory to store generated voice files | `/tmp/echoforge/voices` |

### Local Configuration

For your local environment, you can create a `.env.local` file with your specific settings:

```
# Server settings
ALLOW_PUBLIC_SERVING=true
PUBLIC_HOST=0.0.0.0

# Theme settings
DEFAULT_THEME=dark

# Authentication settings
ENABLE_AUTH=true
AUTH_USERNAME=your_username
AUTH_PASSWORD=your_secure_password
```

## Running the Application

### Development Mode

```bash
# Activate the virtual environment (if not already activated)
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run the server
./run_server.sh
```

The server will start on the configured host and port (default: http://127.0.0.1:8765).

### Docker

To run EchoForge in Docker:

```bash
# Build the Docker image
docker build -t echoforge .

# Run the container
docker run -p 8765:8765 echoforge
```

## API Documentation

EchoForge provides a RESTful API for voice generation:

### Endpoints

#### Health Check

```
GET /api/health
```

Returns the status and version of the API.

#### List Available Voices

```
GET /api/voices
```

Returns a list of available voice options.

#### Generate Voice

```
POST /api/generate
```

Request body:
```json
{
  "text": "Text to convert to speech",
  "speaker_id": 1,
  "temperature": 0.5,
  "top_k": 80,
  "style": "default"
}
```

Returns a task ID for tracking the generation process.

#### Get Task Status

```
GET /api/tasks/{task_id}
```

Returns the status of a voice generation task.

## Development

### Running Tests

```bash
# Run all tests
./run_tests.sh
```

### Project Structure

- `app/` - Application code
  - `api/` - API endpoints and voice generation
  - `core/` - Core functionality and configuration
  - `models/` - Model implementations including Direct CSM
- `static/` - Static assets (CSS, JavaScript, images)
- `templates/` - HTML templates
- `tests/` - Test suite
- `scripts/` - Utility scripts for testing and development
- `docs/` - Documentation

## Roadmap

Here are our development milestones for EchoForge:

### Milestone 1: Enhanced Voice Generation

- [x] Direct CSM implementation for improved voice quality
- [ ] Voice fine-tuning interface for creating custom character voices
- [ ] Batch processing for generating multiple voice clips at once
- [ ] Improved voice style controls (emotion, pace, emphasis)
- [ ] Enhanced audio playback controls (speed, pitch adjustment)

### Milestone 2: User Experience & Management

- [ ] User accounts and voice library management
- [ ] Project organization for managing multiple voice generation tasks
- [ ] Improved UI with customizable workspace
- [ ] Export options for various audio formats and quality settings
- [ ] Usage analytics and generation history

### Milestone 3: Advanced Voice Features

- [ ] Voice cloning from sample audio
- [ ] Multi-speaker conversation generation
- [ ] Context-aware voice continuity between generations
- [ ] Advanced audio post-processing options
- [ ] Voice style transfer between characters

### Milestone 4: Ecosystem Integration

- [ ] Integration with popular content creation tools
- [ ] Mobile application for on-the-go voice generation
- [ ] API marketplace for voice models and styles
- [ ] Plugin system for extending functionality
- [ ] Integration with virtual production pipelines

## Contributing

We welcome contributions to EchoForge! Here are some areas where help is needed:

- Adding new voice models and styles
- Improving the web interface
- Enhancing documentation
- Writing tests
- Performance optimization

Please see our [Contributing Guidelines](CONTRIBUTING.md) for more information.

## Ethical Use

EchoForge is designed for creative and legitimate use cases. Please use this technology responsibly:

- Always disclose when audio is AI-generated when appropriate
- Do not use for impersonation without explicit consent
- Respect copyright and intellectual property rights
- Follow applicable laws and regulations regarding synthetic media

## License

[MIT License](LICENSE)

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