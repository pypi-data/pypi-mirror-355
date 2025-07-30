# Contributing to intake-gfs-ncar

Thank you for your interest in contributing to intake-gfs-ncar! We welcome contributions from the community to help improve this package.

## How to Contribute

### Reporting Issues

If you find a bug or have a feature request, please open an issue on the [GitHub repository](https://github.com/oceanum/intake-gfs-ncar). When reporting a bug, please include:

- A clear description of the issue
- Steps to reproduce the problem
- The expected behavior
- Your operating system and Python version
- Any error messages or logs

### Setting Up the Development Environment

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/intake-gfs-ncar.git
   cd intake-gfs-ncar
   ```

3. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install the package in development mode with all dependencies:
   ```bash
   pip install -e '.[dev]'
   ```

### Making Changes

1. Create a new branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and ensure tests pass:
   ```bash
   pytest
   ```

3. Format your code using Black and isort:
   ```bash
   black .
   isort .
   ```

4. Commit your changes with a descriptive commit message:
   ```bash
   git commit -m "Add feature: brief description of changes"
   ```

5. Push your changes to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

6. Open a pull request against the main branch of the upstream repository.

### Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code
- Use type hints for function signatures
- Include docstrings for all public functions and classes following the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- Keep lines under 88 characters (Black will handle this)

### Testing

- Write tests for new features and bug fixes
- Ensure all tests pass before submitting a pull request
- Use descriptive test function names that explain what they're testing
- Mark slow tests with `@pytest.mark.slow`

### Documentation

- Update the README.md with any new features or changes
- Add docstrings to all public functions and classes
- Include examples in the examples/ directory for new features

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
