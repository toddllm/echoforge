# EchoForge Debugging Guide

This guide provides detailed instructions for troubleshooting voice generation issues in EchoForge using the new debug page.

## Debug Page Overview

The debug page is a specialized tool designed to help diagnose API integration issues, particularly with voice generation. It's available at:

```
http://localhost:8765/debug
```

## When to Use the Debug Page

Use the debug page when:

1. Voice generation requests are failing
2. Audio files are not playing correctly
3. You receive 404 errors when attempting to access audio files
4. Task status checks are not returning expected results
5. You need to test different API endpoints to see which one works

## Debug Page Features

### 1. API Endpoint Selection

The debug page allows you to choose between different API endpoints:

- **Auto-detect**: Automatically tries both API versions
- **voices API**: Uses `/api/voices/generate` endpoint
- **v1 API**: Uses `/api/v1/generate` endpoint
- **Custom endpoint**: Allows you to specify any custom endpoint

This helps identify which API version is supported by your current server setup.

### 2. Request Parameter Controls

Full control over:
- Text input
- Speaker ID selection
- Temperature setting
- Top-K value
- Custom endpoint override

### 3. Comprehensive Logging

The debug page provides detailed logs for:
- Pre-generation setup
- Request formatting and sending
- Response parsing
- Task status checking
- Audio URL construction
- Network connectivity

### 4. Multi-Stage Request Monitoring

The debug process is broken down into distinct stages with detailed logging:
1. Request preparation
2. API endpoint selection
3. Request sending
4. Response handling
5. Task tracking
6. Audio URL construction
7. Audio playback

### 5. Network Testing Tools

Built-in tools to:
- Test URL accessibility
- Check network status
- Validate API endpoints
- Verify file URL construction

## Common Issues and Troubleshooting

### 1. "GET http://localhost:8765/undefined 404 (Not Found)"

This error occurs when the audio URL is not correctly constructed:

**Diagnostic steps using the debug page:**
1. Submit a voice generation request
2. Check the "Response Details" section to confirm a valid task_id
3. Monitor the "Task Status" section to see if the task completes
4. Examine the "Audio Output" section where the URL construction is logged
5. Look for logs containing "Raw file URL from response" and "Normalized audio URL"

**Solution:**
- If the URL contains "undefined", check the task status response format
- Verify the response contains file_url or result.file_url
- Use the debug page's URL validation to ensure the URL has a leading slash

### 2. Speaker ID Validation Errors

If you encounter errors related to invalid speaker_id values:

**Diagnostic steps:**
1. Use the debug page to set speaker_id to various values
2. Check the request payload in the "Request Details" section
3. Check server logs for any validation errors

**Solution:**
- Note that speaker_id=0 is automatically mapped to speaker_id=1
- Ensure valid speaker IDs (typically 1-5) are available in your setup
- Check "Request Data" to confirm the speaker_id is being sent correctly

### 3. Task Status Not Updating

If task status appears stuck:

**Diagnostic steps:**
1. Generate a voice with the debug page
2. Note the task_id assigned
3. Use the "Check Status Manually" button to poll the status
4. Observe which status endpoints are tried and their responses

**Solution:**
- If one status endpoint works but another doesn't, update your code to use the working endpoint
- If no status endpoints work, check server logs for task processing issues
- Verify task_id is valid and not being corrupted during transmission

### 4. Audio Not Playing

If the generated audio doesn't play:

**Diagnostic steps:**
1. Check the "Audio Output" logs in the debug page
2. Verify the audio file URL is constructed correctly
3. Check if the file exists on the server
4. Examine the audio element's src attribute

**Solution:**
- Ensure the audio path is correctly prepended with the server domain if needed
- Check file permissions on the server
- Verify the audio format is supported by the browser

## Advanced Debugging Techniques

### API Response Analysis

1. Generate a voice and let it complete
2. Review the complete response in the "Response Data" section
3. Check for any unexpected fields or missing data
4. Compare the response format to what your application expects

### Multiple API Version Testing

1. Use the "API Version" dropdown to select different APIs
2. Submit identical requests to each API
3. Compare the responses to identify differences
4. Note which API works correctly for your needs

### Network Connectivity Testing

1. Click the "Test URLs" button on the debug page
2. Examine the results for each API endpoint
3. Check for any URLs that return errors
4. Verify your network configuration allows access to all endpoints

## Using Debug Logs for Support

When seeking assistance for issues:

1. Generate a voice using the debug page
2. Copy the entire contents of all log sections:
   - Pre-generation log
   - Request log
   - Response log
   - Task log
   - Audio log
3. Include the browser information and network status
4. Share these logs with support personnel

This comprehensive data will help identify the exact cause of any issues.

## Conclusion

The debug page is a powerful tool for identifying and resolving voice generation issues in EchoForge. By providing detailed logs and fine-grained control over the request process, it helps pinpoint exactly where problems occur in the complex voice generation pipeline.

For further assistance, please refer to the main documentation or contact the EchoForge support team. 