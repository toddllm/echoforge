# Contributing to EchoForge

Thank you for your interest in contributing to EchoForge! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

Please be respectful and considerate of others when contributing to this project. We aim to foster an inclusive and welcoming community.

## How to Contribute

### Reporting Bugs

If you find a bug in the application, please create an issue on GitHub with the following information:

- A clear, descriptive title
- Steps to reproduce the bug
- Expected behavior
- Actual behavior
- Screenshots if applicable
- Environment details (OS, browser, Python version, etc.)

### Suggesting Features

We welcome feature suggestions! Please create an issue on GitHub with:

- A clear, descriptive title
- A detailed description of the proposed feature
- Any relevant mockups or examples
- Use cases for the feature

### Pull Requests

1. Fork the repository
2. Create a new branch for your feature or bugfix
3. Make your changes
4. Add or update tests as necessary
5. Ensure all tests pass
6. Update documentation if needed
7. Submit a pull request

## Development Setup

Please follow the installation instructions in the README.md file to set up your development environment.

### Running Tests

```bash
# Run all tests
./run_tests.sh

# Run specific tests
python -m unittest tests/unit/test_theme.py
```

## Coding Standards

- Follow PEP 8 style guidelines for Python code
- Use meaningful variable and function names
- Write docstrings for all functions, classes, and modules
- Keep functions small and focused on a single task
- Add comments for complex logic

## Git Workflow

- Keep commits small and focused on a single change
- Write clear, descriptive commit messages
- Reference issue numbers in commit messages when applicable
- Rebase your branch before submitting a pull request

## Documentation

- Update the README.md file with any new features or changes
- Document new API endpoints
- Add inline comments for complex code
- Update environment variable documentation if you add new configuration options

## Testing

- Write unit tests for new functionality
- Ensure existing tests pass with your changes
- Consider edge cases in your tests
- Test both success and failure scenarios

## License

By contributing to EchoForge, you agree that your contributions will be licensed under the project's MIT License. 