# EchoForge: AI-Powered Character Voice Creation

EchoForge is a comprehensive platform for creating, managing and using AI-generated character voices. The system enables users to create unique voice profiles with customizable characteristics, generate speech from text, and manage a library of character voices for various applications.

## Features

- **Character Creation**: Create unique character profiles with names, backstories, and voice characteristics.
- **Voice Management**: Organize and categorize voice profiles by gender, style, emotion, and other attributes.
- **Text-to-Speech Generation**: Convert text to speech using selected character voices.
- **API Access**: Use character voices programmatically via a REST API.
- **User-Friendly Interface**: Simple web interface for creating and testing voices.
- **Voice Library**: Browse and search through existing character voices.

## Technical Stack

- **Backend**: Python, Flask, PyTorch
- **Frontend**: HTML5, CSS3, JavaScript
- **TTS Core**: Custom TTS models based on state-of-the-art architectures
- **Storage**: SQLite (development), PostgreSQL (production)
- **API**: RESTful API with JSON payloads

## Getting Started

### Prerequisites

- Python 3.10+
- PyTorch 2.0+
- CUDA-compatible GPU (optional but recommended)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/echoforge.git
   cd echoforge
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python main.py
   ```

4. Open your browser and navigate to:
   ```
   http://localhost:8000
   ```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built using state-of-the-art TTS models and techniques
- Inspired by the need for more accessible character voice creation tools
