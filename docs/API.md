## `/api/generate`

Generate a voice using the specified parameters.

**Method**: POST

**Parameters**:
- `text` (string): The text to be converted to speech
- `voice` (string): Voice type to use ("male", "female", or "child")
- `temperature` (float, optional): Sampling temperature for generation (default: 0.7)
- `top_k` (integer, optional): Top-k sampling parameter (default: 80)
- `device` (string, optional): Device to use for generation ("cuda" or "cpu", default: "cpu")

**Response**:
```json
{
  "task_id": "uuid-string",
  "status": "processing"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is a test of the voice generation system.",
    "voice": "male",
    "temperature": 0.7,
    "device": "cuda"
  }'
``` 