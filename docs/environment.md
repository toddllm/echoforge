# Environment Configuration

EchoForge uses environment variables for configuration. These can be set directly in your environment or through `.env` files.

## Configuration Files

EchoForge supports two configuration files:

- `.env` - Base configuration with default values
- `.env.local` - Local overrides (not committed to version control)

The `.env.local` file takes precedence over `.env`, allowing you to customize your local environment without modifying the base configuration.

## Environment Variables

### Server Settings

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `ALLOW_PUBLIC_SERVING` | Allow serving on all network interfaces | `false` | `true` |
| `PUBLIC_HOST` | Host to bind when public serving is enabled | `0.0.0.0` | `0.0.0.0` |
| `PORT` | Port to run the server on | `8765` | `9000` |

### Authentication Settings

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `ENABLE_AUTH` | Enable HTTP Basic authentication | `false` | `true` |
| `AUTH_USERNAME` | Username for authentication | `echoforge` | `admin` |
| `AUTH_PASSWORD` | Password for authentication | `changeme123` | `secure_password` |
| `AUTH_REQUIRED_FOR_PUBLIC` | Require authentication for public access | `true` | `false` |

### Voice Generation Settings

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `DEFAULT_TEMPERATURE` | Default temperature for voice generation | `0.7` | `0.5` |
| `DEFAULT_TOP_K` | Default top-k value for voice generation | `80` | `50` |
| `DEFAULT_SPEAKER_ID` | Default speaker ID | `1` | `2` |
| `DEFAULT_STYLE` | Default voice style | `default` | `cheerful` |
| `DEFAULT_DEVICE` | Device to use for inference | `cpu` | `cuda` |

### Model Settings

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `MODEL_PATH` | Path to the model checkpoint | `/path/to/model/checkpoint` | `/models/voice_model.pt` |
| `OUTPUT_DIR` | Directory to store generated voice files | `/tmp/echoforge/voices` | `/data/voices` |

### Task Management

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `MAX_TASKS` | Maximum number of concurrent tasks | `10` | `20` |
| `TASK_CLEANUP_KEEP_NEWEST` | Number of newest tasks to keep during cleanup | `50` | `100` |
| `VOICE_FILE_MAX_AGE_HOURS` | Maximum age of voice files before cleanup (hours) | `24` | `48` |

## Example Configuration

Here's an example `.env.local` file for a development environment:

```
# Server settings
ALLOW_PUBLIC_SERVING=true
PUBLIC_HOST=0.0.0.0
PORT=9000

# Authentication settings
ENABLE_AUTH=true
AUTH_USERNAME=dev
AUTH_PASSWORD=dev_password

# Model settings
MODEL_PATH=/home/user/models/voice_model.pt
OUTPUT_DIR=/home/user/echoforge/voices
```

## Using with Docker

When using Docker, you can pass environment variables using the `-e` flag:

```bash
docker run -p 8765:8765 \
  -e ALLOW_PUBLIC_SERVING=true \
  -e ENABLE_AUTH=true \
  -e AUTH_USERNAME=admin \
  -e AUTH_PASSWORD=secure_password \
  echoforge
```

Alternatively, you can use Docker's `--env-file` option:

```bash
docker run -p 8765:8765 --env-file .env.production echoforge
``` 