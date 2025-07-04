# BDD Automation Generator

A comprehensive Python application that generates BDD (Behavior Driven Development) automation files from user stories using Google's Gemini AI.

## 🚀 Features

- **Two-Step Workflow**: Generate and review test cases first, then create BDD automation files
- **Multi-Language Support**: Generates automation files for JavaScript (Cucumber.js), Java (Cucumber-JVM), and Python (Behave)
- **AI-Powered**: Uses Google Gemini API for intelligent test case and code generation
- **Comprehensive Test Coverage**: Creates positive, negative, and edge case scenarios
- **User-Friendly GUI**: Intuitive interface with progress tracking and status updates
- **Cross-Platform**: Works on Windows, macOS, and Linux

## 📦 Quick Setup

### Option 1: Automated Setup (Recommended)
```bash
# Download and run the setup script
python setup_environment.py
```

### Option 2: Manual Setup
```bash
# 1. Clone or download the project
git clone <repository-url> # or download zip

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Set up your Gemini API key (choose one method):

# Method A: Environment Variable (Recommended)
set GEMINI_API_KEY=your_api_key_here  # Windows
export GEMINI_API_KEY=your_api_key_here  # macOS/Linux

# Method B: Edit config.py file
# Open config.py and add your API key to GEMINI_API_KEY

# 4. Run the application
python bdd_generator.py
```

## 🔑 Getting a Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated API key
5. Use it in the setup methods above

## 🎯 How to Use

### Step 1: Prepare Your Input File
Create an Excel file with user stories containing these columns:
- **User Story ID**: Unique identifier (e.g., US001)
- **Title**: Brief description of the feature
- **Acceptance Criteria**: Detailed requirements and scenarios

### Step 2: Generate Test Cases
1. Launch the application: `python bdd_generator.py`
2. Click "Select File" and choose your user stories Excel file
3. Click "Generate Test Cases" and wait for completion
4. Click "View Test Cases" to review the generated comprehensive test cases
5. Edit the test cases file if needed

### Step 3: Generate BDD Files
1. Click "Generate BDD Files" after test cases are ready
2. Wait for the multi-language automation files to be generated
3. Click "Open Output Folder" to access the generated files

### Output Structure
```
GeneratedBDDFiles/
├── Comprehensive_Test_Cases.xlsx
└── BDD_Automation_Files/
    ├── feature_file.feature
    ├── javascript/
    │   ├── steps.js
    │   ├── pages.js
    │   └── package.json
    ├── java/
    │   ├── StepDefinitions.java
    │   ├── ApplicationPage.java
    │   └── pom.xml
    └── python/
        ├── steps.py
        ├── pages.py
        └── requirements.txt
```

## 🔧 Configuration

### Environment Variables
- `GEMINI_API_KEY`: Your Google Gemini API key (required)

### Customizable Settings (config.py)
- Output directory location
- API retry settings
- Supported file extensions
- Gemini model version

## 🚚 Distribution Options

### Create Standalone Executable
```bash
# Create a portable .exe file (Windows)
python build_exe.py

# The executable will be created in the 'dist' folder
```

### Share with Others
1. **Minimal Share**: Share the Python files + requirements.txt
2. **Complete Share**: Include setup scripts and documentation
3. **Executable Share**: Distribute the standalone .exe file

## 🛠️ Development Setup

For developers who want to modify the code:

```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest black flake8  # Optional dev tools

# Run tests (if available)
python -m pytest

# Format code
black bdd_generator.py
```

## 📋 System Requirements

- **Python**: 3.8 or higher
- **Operating System**: Windows 10/11, macOS 10.14+, or Linux
- **RAM**: 4 GB minimum (8 GB recommended)
- **Storage**: 500 MB free space
- **Internet**: Required for Gemini API calls

## 🔍 Troubleshooting

### Common Issues

**API Key Not Working**
- Verify your API key is correct
- Check if the key has proper permissions
- Ensure you have API quota remaining

**Application Won't Start**
- Check Python version: `python --version`
- Install missing dependencies: `pip install -r requirements.txt`
- Check for permission issues in the output directory

**Files Not Generated**
- Verify input Excel file format is correct
- Check internet connection for API calls
- Review the application logs for detailed error messages

### Getting Help
- Check the log file: `bdd_generator.log`
- Review error messages in the GUI status bar
- Ensure all dependencies are properly installed

## 📄 License

This project is provided as-is for educational and commercial use.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and enhancement requests.

---

**Made with ❤️ and AI assistance**
