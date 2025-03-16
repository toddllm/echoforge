# EchoForge Developer Guide

This guide provides information for developers who want to understand, modify, or extend the EchoForge application.

## Architecture Overview

EchoForge is built using a modern web application architecture with a Python backend and JavaScript frontend.

### High-Level Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Web Interface  │◄────►  FastAPI Server │◄────►  CSM Model     │
│  (HTML/JS/CSS)  │     │  (Python)       │     │  (PyTorch)      │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │
                              │
                        ┌─────▼─────┐
                        │           │
                        │  Task     │
                        │  Queue    │
                        │           │
                        └───────────┘
```

### Components

1. **Web Interface**: HTML, CSS, and JavaScript frontend that provides the user interface.
2. **FastAPI Server**: Python backend that handles HTTP requests and serves the web interface.
3. **CSM Model**: The Conversational Speech Model that generates speech from text.
4. **Task Queue**: Manages background tasks for speech generation.

## Code Organization

The EchoForge codebase is organized as follows:

```
echoforge/
├── app/                  # Python application code
│   ├── api/              # API endpoints and routers
│   ├── core/             # Core application logic
│   ├── models/           # Model implementations
│   ├── ui/               # UI routes and templates
│   └── main.py           # Application entry point
├── static/               # Static assets
│   ├── css/              # CSS stylesheets
│   ├── js/               # JavaScript files
│   ├── images/           # Image assets
│   └── samples/          # Voice sample files
├── templates/            # HTML templates
├── tests/                # Test code
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── docs/                 # Documentation
└── .venv/                # Virtual environment (not in repo)
```

### Key Files

- `app/main.py`: Application entry point that sets up FastAPI and routes.
- `app/api/router.py`: API endpoint definitions.
- `app/models/csm_model.py`: CSM model implementation.
- `app/core/task_manager.py`: Background task management.
- `static/js/main.js`: Main JavaScript file for the web interface.
- `static/js/characters.js`: JavaScript for the character showcase.
- `templates/base.html`: Base HTML template.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git
- Node.js and npm (optional, for frontend development)

### Setting Up the Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/echoforge.git
   cd echoforge
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application in development mode:
   ```bash
   python -m app.main --dev
   ```

5. Access the application at http://localhost:8765

### Running Tests

To run the test suite:

```bash
python -m pytest
```

To run specific tests:

```bash
python -m pytest tests/unit/test_api_endpoints.py
```

To run tests with coverage:

```bash
python -m pytest --cov=app
```

## API Development

### Adding a New Endpoint

1. Define the endpoint in `app/api/router.py`:
   ```python
   @router.get("/new-endpoint")
   async def new_endpoint():
       return {"message": "This is a new endpoint"}
   ```

2. Add tests for the endpoint in `tests/unit/test_api_endpoints.py`.

3. Document the endpoint in the API reference.

### Error Handling

Use FastAPI's HTTPException for error handling:

```python
from fastapi import HTTPException

@router.get("/item/{item_id}")
async def get_item(item_id: str):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item": items[item_id]}
```

## Frontend Development

### JavaScript Organization

The frontend JavaScript is organized as follows:

- `main.js`: Core functionality and initialization.
- `characters.js`: Character showcase functionality.
- `theme.js`: Theme switching and preferences.

### Adding a New Feature

1. Identify the appropriate JavaScript file for your feature.
2. Add your code following the existing patterns.
3. Test your changes in the browser.
4. Add appropriate error handling and user feedback.

### CSS Styling

The application uses a custom CSS framework with variables for theming:

```css
:root {
  --primary-color: #3498db;
  --secondary-color: #2ecc71;
  --text-color: #333333;
  --background-color: #ffffff;
}

[data-theme="dark"] {
  --primary-color: #3498db;
  --secondary-color: #2ecc71;
  --text-color: #f5f5f5;
  --background-color: #222222;
}
```

## Model Integration

### Working with the CSM Model

The CSM model is integrated through the `CSMModel` class in `app/models/csm_model.py`. This class handles:

1. Loading the model
2. Processing text inputs
3. Generating speech outputs
4. Error handling and fallbacks

### Adding a New Model

To add a new model:

1. Create a new model class in `app/models/` that implements the same interface as `CSMModel`.
2. Update the model factory in `app/models/__init__.py` to include your new model.
3. Add appropriate configuration options in `app/core/config.py`.
4. Update the documentation to reflect the new model.

## Deployment

### Production Deployment

For production deployment:

1. Build the application:
   ```bash
   python -m app.build
   ```

2. Deploy using Docker:
   ```bash
   docker build -t echoforge .
   docker run -p 8765:8765 echoforge
   ```

### Environment Variables

Configure the application using environment variables:

- `ECHOFORGE_ENV`: Set to `production` for production mode.
- `ECHOFORGE_HOST`: Host to bind the server to.
- `ECHOFORGE_PORT`: Port to bind the server to.
- `ECHOFORGE_MODEL_PATH`: Path to the CSM model.
- `ECHOFORGE_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR).

## Contributing

### Contribution Guidelines

1. Fork the repository.
2. Create a feature branch.
3. Make your changes.
4. Run tests to ensure they pass.
5. Submit a pull request.

### Code Style

- Python code should follow PEP 8.
- JavaScript code should follow the project's ESLint configuration.
- Use meaningful variable and function names.
- Add comments for complex logic.
- Write docstrings for all functions and classes.

### Documentation

- Update documentation when making changes.
- Add docstrings to new functions and classes.
- Update the API reference for new or modified endpoints.
- Keep the user guide up-to-date with UI changes. 