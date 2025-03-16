# EchoForge API Reference

This document provides detailed information about the EchoForge REST API endpoints, including request parameters, response formats, and example usage.

## Base URL

All API endpoints are relative to the base URL of your EchoForge installation:

```
http://your-server:port/api
```

## Authentication

Currently, the API does not require authentication. This may change in future versions.

## Endpoints

### Health Check

```
GET /health
```

Returns the health status of the EchoForge service.

#### Response

```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

#### Status Codes

- `200 OK`: Service is healthy
- `500 Internal Server Error`: Service is unhealthy

#### Example

```bash
curl -X GET http://localhost:8765/api/health
```

### System Diagnostics

```
GET /diagnostic
```

Returns diagnostic information about the system, including model status, CUDA availability, and task queue status.

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | boolean | Include model information (default: false) |
| `tasks` | boolean | Include task queue information (default: false) |

#### Response

```json
{
  "status": "ok",
  "timestamp": "2025-03-16T12:34:56.789Z",
  "system": {
    "version": "1.0.0",
    "python_version": "3.10.12",
    "platform": "Linux-5.15.0-x86_64-with-glibc2.31",
    "cuda_available": true,
    "cuda_version": "11.8"
  },
  "model": {
    "loaded": true,
    "name": "csm_model",
    "device": "cuda:0"
  },
  "tasks": {
    "active": 0,
    "completed": 12,
    "failed": 2
  }
}
```

#### Status Codes

- `200 OK`: Diagnostic information retrieved successfully
- `500 Internal Server Error`: Error retrieving diagnostic information

#### Example

```bash
curl -X GET "http://localhost:8765/api/diagnostic?model=true&tasks=true"
```

### List Voices

```
GET /voices
```

Returns a list of available voices for text-to-speech generation.

#### Response

```json
[
  {
    "speaker_id": "1",
    "name": "Alex",
    "gender": "male",
    "style": "casual",
    "description": "A friendly male voice with a casual tone"
  },
  {
    "speaker_id": "2",
    "name": "Sophia",
    "gender": "female",
    "style": "professional",
    "description": "A clear female voice with a professional tone"
  }
]
```

#### Status Codes

- `200 OK`: Voices retrieved successfully
- `500 Internal Server Error`: Error retrieving voices

#### Example

```bash
curl -X GET http://localhost:8765/api/voices
```

### Generate Speech

```
POST /generate
```

Generates speech from text using the specified voice and parameters.

#### Request Body

```json
{
  "text": "Hello, this is a test of the EchoForge text-to-speech system.",
  "speaker_id": "1",
  "temperature": 0.8,
  "top_k": 50,
  "style": "casual"
}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | string | The text to convert to speech (required) |
| `speaker_id` | string | The ID of the voice to use (required) |
| `temperature` | float | Controls randomness in generation (default: 0.7, range: 0.1-1.5) |
| `top_k` | integer | Controls diversity of output (default: 50, range: 1-100) |
| `style` | string | Voice style to use (default: depends on voice) |

#### Response

```json
{
  "task_id": "12345678-1234-5678-1234-567812345678",
  "status": "processing"
}
```

#### Status Codes

- `202 Accepted`: Request accepted, processing started
- `400 Bad Request`: Invalid request parameters
- `500 Internal Server Error`: Error processing request

#### Example

```bash
curl -X POST http://localhost:8765/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is a test of the EchoForge text-to-speech system.",
    "speaker_id": "1",
    "temperature": 0.8,
    "top_k": 50,
    "style": "casual"
  }'
```

### Task Status

```
GET /tasks/{task_id}
```

Returns the status of a speech generation task.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | string | The ID of the task to check (required) |

#### Response

```json
{
  "task_id": "12345678-1234-5678-1234-567812345678",
  "status": "completed",
  "result_url": "/static/generated/12345678-1234-5678-1234-567812345678.mp3",
  "created_at": "2025-03-16T12:34:56.789Z",
  "completed_at": "2025-03-16T12:35:01.234Z"
}
```

Possible status values:
- `queued`: Task is in the queue waiting to be processed
- `processing`: Task is currently being processed
- `completed`: Task has completed successfully
- `failed`: Task failed to complete

#### Status Codes

- `200 OK`: Task status retrieved successfully
- `404 Not Found`: Task not found
- `500 Internal Server Error`: Error retrieving task status

#### Example

```bash
curl -X GET http://localhost:8765/api/tasks/12345678-1234-5678-1234-567812345678
```

## Error Handling

All API endpoints return errors in a consistent format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

## Rate Limiting

Currently, there are no rate limits on the API. This may change in future versions.

## Versioning

The current API version is v1. The version is not included in the URL path but may be in future releases. 