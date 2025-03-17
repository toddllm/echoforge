# EchoForge Testing Documentation

This document provides information about testing procedures and results for the EchoForge application, with a focus on the Direct CSM implementation.

## Direct CSM Admin Integration Testing

### Manual Testing (2025-03-17)

We performed manual testing of the Direct CSM integration in the admin page with the following results:

#### API Endpoints

1. **Direct CSM Info Endpoint**
   - Endpoint: `/api/admin/models/direct-csm-info`
   - Authentication: Required (Basic Auth)
   - Result: Successfully retrieved Direct CSM information
   - Response:
     ```json
     {
       "enabled": true,
       "loaded": true,
       "path": "/home/tdeshane/tts_poc/voice_poc/csm",
       "path_exists": true,
       "has_required_files": true,
       "status": "Active"
     }
     ```

2. **Toggle Direct CSM Endpoint**
   - Endpoint: `/api/admin/models/toggle-direct-csm`
   - Method: POST
   - Authentication: Required (Basic Auth)
   - Payload: `{"enable": false}` or `{"enable": true}`
   - Result: Successfully toggled Direct CSM on and off
   - Response when disabling:
     ```json
     {
       "status": "success",
       "message": "Direct CSM disabled and model reloaded",
       "direct_csm_enabled": false
     }
     ```
   - Response when enabling:
     ```json
     {
       "status": "success",
       "message": "Direct CSM enabled and model reloaded",
       "direct_csm_enabled": true
     }
     ```

3. **Test Direct CSM Endpoint**
   - Endpoint: `/api/admin/models/test-direct-csm`
   - Method: POST
   - Authentication: Required (Basic Auth)
   - Result: Successfully initiated Direct CSM test
   - Response:
     ```json
     {
       "task_id": "85f347e6-e8b4-4a52-a4c7-620521b1423d",
       "status": "pending",
       "message": "Direct CSM test has been started"
     }
     ```
   - Generated audio file: `/tmp/echoforge/voices/test/direct_csm_test_1742184298.wav`
   - Audio file accessible via: `/voices/test/direct_csm_test_1742184298.wav`

4. **Voice Generation Endpoint**
   - Endpoint: `/api/admin/generate-voice`
   - Method: POST
   - Authentication: Required (Basic Auth)
   - Payload:
     ```json
     {
       "text": "This is a test of the direct CSM implementation in the admin page. The voice should be clear and natural sounding.",
       "speaker_id": 1,
       "temperature": 0.7,
       "top_k": 50,
       "style": "natural",
       "device": "cuda"
     }
     ```
   - Result: Successfully generated voice
   - Response:
     ```json
     {
       "task_id": "45825117-cf45-421c-8525-9aada1f4c2b8",
       "status": "pending",
       "message": "Voice generation has been started"
     }
     ```
   - Generated audio file: `/tmp/echoforge/voices/admin/voice_1742184428_e9688ae5.wav`
   - Audio file accessible via: `/voices/admin/voice_1742184428_e9688ae5.wav`

#### UI Integration

The Direct CSM integration in the admin UI includes:

1. **Model Details Modal**
   - Direct CSM Information section
   - Toggle Direct CSM button
   - Test Direct CSM button
   - Status indicators

2. **Config Page**
   - Direct CSM settings in the Model tab
   - Enable/disable Direct CSM checkbox
   - Direct CSM path input field

### Automated Testing

We created a test script (`scripts/test_admin_direct_csm.py`) to verify the Direct CSM integration. The script tests:

1. Direct CSM configuration validation
2. Direct CSM API endpoints
3. Voice generation using Direct CSM

The script successfully verified:
- Direct CSM configuration is valid
- Direct CSM info endpoint returns correct information
- Direct CSM can be toggled on and off
- Direct CSM test generates audio files
- Voice generation creates audio files in the admin directory

## Known Issues and TODOs

### Server Threading

**Issue**: The server is not threaded, which causes it to become unresponsive during long-running tasks like Direct CSM testing and voice generation. This prevents concurrent requests like checking task status while a task is running.

**TODO**: Make the API server threaded to handle concurrent requests.

### Task Status Tracking

**Issue**: The task status tracking system is not working correctly. The task status endpoint (`/api/tasks/{task_id}`) returns 404 for tasks that are in progress or have completed.

**TODO**: Improve task status tracking and polling.

### Port Configuration

**Issue**: The server attempts to bind to port 8000 by default, which may already be in use.

**TODO**: Update the server configuration to use the configured port (8765) consistently.

### API Documentation

**TODO**: Update the API documentation to include the new Direct CSM endpoints.

### UI Improvements

**TODO**: Enhance the admin UI for Direct CSM management:
- Add progress indicators for long-running tasks
- Improve error handling and display
- Add audio playback controls for generated voices

## Next Steps

1. Address the threading issue to improve server responsiveness
2. Fix task status tracking
3. Update API documentation
4. Enhance the admin UI
5. Integrate Direct CSM into the main app interface 