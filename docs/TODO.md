# EchoForge TODO List

This document tracks the current issues and planned improvements for the EchoForge application.

## High Priority

### Server Improvements

- [ ] **Make the API server threaded** to handle concurrent requests
  - This will allow the server to process long-running tasks while still responding to status check requests
  - Consider using a task queue system like Celery or RQ
  - Alternatively, implement proper async handling in FastAPI

- [ ] **Fix task status tracking**
  - Ensure task status endpoint (`/api/tasks/{task_id}`) works correctly for in-progress and completed tasks
  - Implement proper task cleanup to avoid memory leaks
  - Add task history for completed tasks

- [ ] **Fix port configuration**
  - Update the server to consistently use the configured port (8765)
  - Add better error handling for port binding failures

### Direct CSM Integration

- [ ] **Complete main app integration**
  - Add Direct CSM options to the main voice generation page
  - Allow users to toggle between Direct CSM and standard CSM
  - Add device selection (CPU/GPU) to the UI

- [ ] **Improve error handling**
  - Add better error messages for Direct CSM failures
  - Implement automatic fallback to standard CSM if Direct CSM fails
  - Log detailed error information for debugging

## Medium Priority

### UI Improvements

- [ ] **Enhance admin UI for Direct CSM management**
  - Add progress indicators for long-running tasks
  - Improve error handling and display
  - Add audio playback controls for generated voices

- [ ] **Improve voice browser**
  - Add sorting and filtering options
  - Implement pagination for large numbers of voice files
  - Add batch operations (delete, download, etc.)

### Documentation

- [ ] **Update API documentation**
  - Document Direct CSM endpoints
  - Add examples for all API endpoints
  - Create OpenAPI/Swagger documentation

- [ ] **Improve user documentation**
  - Add more detailed usage instructions
  - Create troubleshooting guide
  - Add examples and best practices

## Low Priority

### Performance Improvements

- [ ] **Optimize Direct CSM implementation**
  - Improve memory usage
  - Reduce model loading time
  - Implement model caching

- [ ] **Add benchmarking tools**
  - Create scripts to measure performance
  - Compare Direct CSM vs. standard CSM
  - Test different hardware configurations

### Feature Additions

- [ ] **Add voice fine-tuning capabilities**
  - Allow users to fine-tune voices for specific characters
  - Implement voice style transfer
  - Add emotion controls

- [ ] **Implement batch processing**
  - Allow generating multiple voice clips at once
  - Add queue management for batch jobs
  - Implement priority system for jobs

## Completed

- [x] **Implement Direct CSM**
  - Created direct implementation of CSM model
  - Added fallback mechanisms
  - Integrated with voice generator

- [x] **Add admin page integration**
  - Added Direct CSM info endpoint
  - Added toggle Direct CSM endpoint
  - Added test Direct CSM endpoint
  - Added Direct CSM settings to config page 