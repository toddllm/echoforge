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
git clone https://github.com/yourusername/echoforge.git
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
- `static/` - Static assets (CSS, JavaScript, images)
- `templates/` - HTML templates
- `tests/` - Test suite

## License

[MIT License](LICENSE)

## Acknowledgements

- This project uses the CSM model architecture for voice generation
- Special thanks to the open-source community for their contributions to speech synthesis technology

