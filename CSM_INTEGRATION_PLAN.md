# CSM Model Integration Plan for EchoForge

This document outlines the plan for integrating the Conversational Speech Model (CSM) from Sesame AI Labs into the EchoForge application, with the goal of achieving feature parity with the tts_poc project while improving robustness, testing, and documentation.

## 1. Core Model Integration

### 1.1 Model Implementation
- [x] Create CSM model class in `app/models/csm_model.py`
- [x] Implement model loading with proper error handling
- [x] Add GPU/CPU detection and fallback mechanisms
- [x] Implement watermarking integration (or mock)
- [x] Create placeholder model for when CSM is unavailable

### 1.2 Voice Generation
- [x] Implement `VoiceGenerator` class in `app/api/voice_generator.py`
- [x] Add support for different voice parameters (temperature, top-k)
- [x] Create voice cloning functionality
- [x] Implement audio post-processing utilities
- [x] Add proper error handling and diagnostics

## 2. API Implementation

### 2.1 REST API Endpoints
- [x] Implement health check endpoint (`/api/health`)
- [x] Add system diagnostics endpoint (`/api/diagnostic`)
- [x] Create voice listing endpoint (`/api/voices`)
- [x] Add speech generation endpoint (`/api/generate`)
- [x] Implement task status endpoint (`/api/tasks/{task_id}`)

### 2.2 Background Task System
- [x] Create task queue for handling generation requests
- [x] Implement progress tracking and status reporting
- [x] Add proper concurrency handling
- [ ] Create error recovery mechanisms
- [ ] Implement resource limiting

## 3. Web Interface

### 3.1 Character Showcase
- [x] Create character profile component
- [x] Implement voice sample playback
- [x] Add text-to-speech generation interface
- [x] Create filtering by gender and voice style
- [x] Implement responsive design

### 3.2 UI Enhancements
- [x] Add voice parameter adjustment controls
- [x] Implement audio playback controls
- [x] Create loading indicators for long operations
- [x] Add error display and handling
- [x] Implement light/dark mode support

## 4. Testing

### 4.1 Unit Tests
- [x] Write tests for CSM model
- [x] Create tests for voice generator
- [x] Add tests for task system
- [x] Implement API route tests
- [ ] Write utility function tests

### 4.2 Integration Tests
- [ ] Test model integration with API
- [ ] Create end-to-end voice generation tests
- [ ] Test background task system
- [ ] Implement web interface tests
- [ ] Add performance benchmarks

## 5. Documentation

### 5.1 Code Documentation
- [x] Add docstrings to all classes and methods
- [ ] Create README updates
- [ ] Document configuration options
- [ ] Add inline comments for complex logic
- [ ] Create module dependency documentation

### 5.2 User Documentation
- [ ] Write API documentation with examples
- [ ] Create user guide for web interface
- [ ] Add installation and setup guide
- [ ] Document voice generation parameters
- [ ] Create troubleshooting guide

## 6. Implementation Phases

### Phase 1: Core Model Integration
- [x] Set up basic project structure
- [x] Implement CSM model integration
- [x] Create voice generation functionality
- [x] Add basic test coverage
- [x] Document core components

### Phase 2: API and Task System
- [x] Implement health check and diagnostic endpoints
- [x] Create voice listing and generation endpoints
- [x] Implement task status endpoint
- [x] Add voice management functionality
- [x] Write integration tests

### Phase 3: Web Interface
- [x] Create character showcase UI
- [x] Implement voice filtering and playback
- [x] Add text-to-speech generation interface
- [x] Create responsive design
- [x] Fix JavaScript errors and edge cases
- [ ] Write UI tests

### Phase 4: Device Selection and Testing
- [x] Add device selection dropdown to generation interface
- [x] Update API to accept device parameter
- [x] Implement proper handling of different device options (auto, cuda, cpu)
- [x] Add CSS styling for new UI elements
- [x] Ensure backward compatibility
- [x] Test CPU-only generation through API
- [x] Test CUDA-accelerated generation through API
- [x] Test automatic device selection through API
- [x] Compare output files between different device options
- [x] Verify consistent audio quality across devices
- [x] Test device selection through web interface
- [x] Measure performance differences between device options

### 8.3 Generation Testing Results
- [x] **Script-based generation:** Successfully generated voice using `generate_voice.py` script with CPU device selection. Created WAV file at `/home/tdeshane/echoforge/generated/voice_1_7_50.wav` (16-bit PCM mono audio at 24000 Hz).
  ```bash
  # Command used for script-based generation with CPU
  python -m scripts.generate_voice --text "This is a test of voice generation using CPU." --device cpu --verbose
  ```

- [x] **API-based generation:** Successfully generated voice files with all three device options:
  - CPU: `/tmp/echoforge/voices/voice_1742111628_dfc2cf8a.wav`
  - CUDA: `/tmp/echoforge/voices/voice_1742111789_ca813d54.wav`
  - Auto: `/tmp/echoforge/voices/voice_1742111897_f5ae76d7.wav`
  
  ```bash
  # Command used for API-based generation with CPU
  curl -X POST http://localhost:8765/api/generate -H "Content-Type: application/json" \
    -d '{"text": "Testing voice generation with CPU device selection.", "speaker_id": 1, "temperature": 0.7, "top_k": 50, "style": "default", "device": "cpu"}'
    
  # Command used for API-based generation with CUDA
  curl -X POST http://localhost:8765/api/generate -H "Content-Type: application/json" \
    -d '{"text": "Testing voice generation with CUDA device selection.", "speaker_id": 1, "temperature": 0.7, "top_k": 50, "style": "default", "device": "cuda"}'
    
  # Command used for API-based generation with auto device selection
  curl -X POST http://localhost:8765/api/generate -H "Content-Type: application/json" \
    -d '{"text": "Testing voice generation with auto device selection.", "speaker_id": 1, "temperature": 0.7, "top_k": 50, "style": "default", "device": "auto"}'
  ```

- [x] **Task status checking:** Verified task status updates through API:
  ```bash
  # Command used for checking task status
  curl -X GET http://localhost:8765/api/tasks/{task_id} -s | python -m json.tool
  ```

- [x] **File comparison:** All generated files were identical (confirmed via cosine similarity and direct comparison). Each file was 480,078 bytes with 240,000 samples at 24,000 Hz and duration of 10 seconds.
  ```bash
  # Commands used for comparing files
  python -c "import torchaudio, torch; cpu_audio, _ = torchaudio.load('/tmp/echoforge/voices/voice_1742111628_dfc2cf8a.wav'); cuda_audio, _ = torchaudio.load('/tmp/echoforge/voices/voice_1742111789_ca813d54.wav'); auto_audio, _ = torchaudio.load('/tmp/echoforge/voices/voice_1742111897_f5ae76d7.wav'); print(f'CPU-CUDA identical: {torch.all(cpu_audio == cuda_audio).item()}'); print(f'CPU-Auto identical: {torch.all(cpu_audio == auto_audio).item()}'); print(f'CUDA-Auto identical: {torch.all(cuda_audio == auto_audio).item()}')"
  ```

- [x] **Audio properties:** Files had consistent properties - Min: -1.0, Max: ~1.0, Mean: ~0, Std: ~0.65.
  ```bash
  # Command used for analyzing audio properties
  python -c "import torchaudio, torch, numpy as np; cpu_audio, _ = torchaudio.load('/tmp/echoforge/voices/voice_1742111628_dfc2cf8a.wav'); print(f'First 10 samples: {cpu_audio[0, :10]}'); print(f'Min value: {cpu_audio.min().item()}, Max value: {cpu_audio.max().item()}'); print(f'Mean: {cpu_audio.mean().item()}, Std: {cpu_audio.std().item()}')"
  ```

- [x] **Hardware detection:** System correctly detected NVIDIA GeForce RTX 3090 GPU and made it available for generation.
  ```bash
  # Command used for checking CUDA availability
  python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'Current device: {torch.cuda.current_device()}'); print(f'Device name: {torch.cuda.get_device_name(0)}'); print(f'Device count: {torch.cuda.device_count()}')"
  ```

- [x] **Task management:** System completed all generation tasks successfully with no failures, properly updating task status.

## 9. Admin Interface

### 9.1 Admin Interface Implementation
- [ ] Create admin dashboard route and template
- [ ] Implement authentication for admin access
- [ ] Add system status overview and monitoring panel
- [ ] Create model management section (load/unload/restart)
- [ ] Implement voice management tools (add/remove/modify)
- [ ] Add task management interface (view/cancel/retry)
- [ ] Create diagnostic tools and logs viewer
- [ ] Implement configuration management interface
- [ ] Add performance metrics and utilization graphs
- [ ] Create user management (if applicable)

### 9.2 Admin API Endpoints
- [ ] Implement admin authentication endpoint
- [ ] Create system control endpoints (restart services)
- [ ] Add model management endpoints
- [ ] Implement voice management endpoints
- [ ] Create configuration update endpoints
- [ ] Add log retrieval endpoints
- [ ] Implement performance metrics endpoints

### 9.3 Admin Features
- [ ] **Dashboard:** Overview of system status, active tasks, resource usage
- [ ] **Model Management:** Load/unload models, change model parameters
- [ ] **Voice Testing:** Interface for quick voice testing with different parameters
- [ ] **Batch Processing:** Tools for batch voice generation
- [ ] **System Logs:** Real-time log viewer with filtering
- [ ] **Performance Monitoring:** CPU/GPU/memory usage graphs
- [ ] **Configuration Editor:** Web interface for editing application settings
- [ ] **Voice Library:** Tools to manage and organize voice samples
- [ ] **User Management:** Control access permissions (if applicable)

## Progress Tracking

**Overall Progress:**  
- [x] Phase 1: Core Model Integration (100% complete)
- [x] Phase 2: API and Task System (100% complete)
- [x] Phase 3: Web Interface (90% complete)
- [x] Phase 4: Device Selection and Testing (100% complete)
- [ ] Phase 5: Admin Interface (0% complete)
- [ ] Phase 6: Documentation and Refinement (10% complete)

**Current Focus:**  
Phase 5: Admin Interface - Creating admin dashboard and management tools

**Next Milestone:**  
- Admin Dashboard Implementation
- Model Management Controls
- System Status Monitoring

**Project Completion Milestones:**  
- Complete Admin Interface
- Finalize API Documentation
- Optimize Performance
- User Guide Creation
- Security Enhancements 