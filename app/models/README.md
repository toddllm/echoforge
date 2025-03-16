# CSM Model Implementation

This directory contains the implementation of the Conversational Speech Model (CSM) from Sesame AI Labs for the EchoForge application.

## Overview

The CSM model is a speech generation model that generates high-quality, natural-sounding speech from text input. The model architecture employs a Llama backbone and a smaller audio decoder that produces Mimi audio codes.

## Files

- `csm_model.py`: Main implementation of the CSM model wrapper with proper error handling, GPU/CPU detection, and fallback mechanisms.
- `__init__.py`: Package initialization file that exposes the CSM model classes.

## Classes

### CSMModel

The main class that wraps the CSM model. It handles model loading, GPU/CPU detection, and provides fallback mechanisms.

```python
from app.models import create_csm_model

# Create a CSM model instance
model = create_csm_model()

# Generate speech
audio, sample_rate = model.generate_speech(
    text="Hello, world!",
    speaker_id=1,
    temperature=0.9,
    top_k=50
)

# Save the audio
model.save_audio(audio, sample_rate, "output.wav")

# Clean up
model.cleanup()
```

### PlaceholderCSMModel

A placeholder implementation of the CSM model for when the real model is unavailable. It generates a simple sine wave instead of actual speech.

```python
from app.models import create_csm_model

# Create a placeholder CSM model instance
model = create_csm_model(use_placeholder=True)

# Generate speech (will be a sine wave)
audio, sample_rate = model.generate_speech("Hello, world!")

# Save the audio
model.save_audio(audio, sample_rate, "output.wav")
```

## Factory Function

### create_csm_model

A factory function that creates a CSM model instance. It attempts to create a real CSM model, but falls back to a placeholder if the real model cannot be loaded or if `use_placeholder` is True.

```python
from app.models import create_csm_model

# Create a CSM model instance (real or placeholder)
model = create_csm_model(
    model_path=None,  # Will download from Hugging Face if None
    device=None,      # Will use CUDA if available, otherwise CPU
    use_placeholder=False
)
```

## Error Handling

The CSM model implementation provides proper error handling with custom exception classes:

- `CSMModelError`: Base exception for CSM model errors.
- `CSMModelNotFoundError`: Exception raised when the CSM model cannot be found.
- `CSMModelLoadError`: Exception raised when the CSM model cannot be loaded.

## GPU/CPU Detection

The CSM model automatically detects whether to use GPU or CPU based on availability and memory requirements. It requires at least 2GB of free GPU memory to use CUDA, otherwise it falls back to CPU.

## Example

See the `examples/csm_model_example.py` script for a complete example of how to use the CSM model. 