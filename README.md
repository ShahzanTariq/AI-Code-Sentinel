# AI Code Sentinel

## Overview
AI Debugger is a Python-based debugging assistant that integrates with VS Code. It monitors changes to Python scripts, runs them automatically, and provides AI-powered suggestions for error fixes using the Gemini API. The project uses PySide6 for the GUI and Watchdog for real-time file monitoring.

## Features
- **Real-time Error Detection**: Monitors Python files for changes and automatically runs them.
- **AI-Powered Fixes**: Uses the Gemini API to suggest fixes for detected errors.
- **GUI Interface**: Built with PySide6 for easy interaction.
- **Automated Execution**: Runs scripts whenever modifications are detected.

## Installation
### Prerequisites
Ensure you have the following installed:
- Python 3.8+
- Pip
- Virtual Environment (optional but recommended)

### Install Dependencies
Clone the repository and install the required dependencies:
```sh
# Clone the repository
git clone https://github.com/yourusername/AI-Code-Sentinel.git
cd ai-debugger

# Create and activate a virtual environment (optional)
python -m venv venv
source venv/bin/activate  # On Windows use: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage
### Running the Debugger
```sh
python main.py
```
This will launch the GUI, where you can select a file to monitor and execute.
![image](https://github.com/user-attachments/assets/97155c0d-3df8-400b-a252-131eeac8c3ca)

## Configuration
### Adding Your API Key
To use the AI-powered debugging features, you need to provide your Gemini API key.

1. **Obtain Your API Key:**
   - Sign up for an API key from [Google Studios](https://aistudio.google.com/apikey).
   - Copy your API key once generated.

2. **Add the API Key to the Project:**
   - Create a `.env` file in the project root directory.
   - Open `.env` and add the following line:
     ```sh
     GEMINI_API_KEY=your_api_key_here
     ```
   - Save the file.

3. **Ensure the Project Loads the Key:**
   - The script will automatically read from `.env` if properly configured.
   - If needed, install `python-dotenv` by running:
     ```sh
     pip install python-dotenv
     ```


## File Structure
```
ai-debugger/
│-- main.py           # Launches the application
│-- worker_thread.py  # Handles file monitoring and script execution
│-- main_window.py    # Defines the GUI using PySide6
│-- script_utils.py   # Handles AI-powered debugging logic
│-- requirements.txt  # List of dependencies
```

