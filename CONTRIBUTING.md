# Contributing to BDD Automation Generator

Thank you for considering contributing to this project! Here are some guidelines to help you get started.

## Development Environment Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/BDD-Automation-Generator.git
   cd BDD-Automation-Generator
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your Gemini API key:
   ```
   # On Windows
   set GEMINI_API_KEY=your_api_key_here
   
   # On macOS/Linux
   export GEMINI_API_KEY=your_api_key_here
   ```

## Code Structure

- `bdd_generator.py`: Main application file with GUI and backend logic
- `requirements.txt`: Python dependencies
- `BDD_Automation_Generator_Distribution/`: Distribution version with launcher scripts
- `BDD_Automation_Generator_Portable/`: Standalone executable version

## Pull Request Guidelines

1. Fork the repository
2. Create a new branch for your feature or bug fix
3. Write tests if applicable
4. Update documentation if necessary
5. Submit a pull request with a clear description of your changes

## Building the Executable

To build the standalone executable:

```
pyinstaller --onefile --windowed --icon=app_icon.ico bdd_generator.py
```

## Coding Conventions

- Follow PEP 8 style guide
- Use meaningful variable and function names
- Add comments for complex logic
- Write docstrings for all functions and classes

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.
