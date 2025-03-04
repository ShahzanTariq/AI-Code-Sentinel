import sys
import subprocess
from google import genai
from dotenv import load_dotenv
from watchdog.events import FileSystemEventHandler
import os
import time

load_dotenv()
api = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api)

class ScriptChangeHandler(FileSystemEventHandler):
    def __init__(self, script_path, mainFile_path):
        self.script_path = script_path
        self.mainFile_path = mainFile_path
        self.last_triggered = 0
        self.debounce_interval = 3

    def on_modified(self, event):
        if event.is_directory:
            return None
        if event.src_path.endswith(".py"):
            current_time = time.time()
            if current_time - self.last_triggered > self.debounce_interval:
                self.last_triggered = current_time
                print(f"Detected change in {event.src_path}. Re-running script...")
                error_code, stdout, stderr = run_script_and_capture_error(event.src_path, self.mainFile_path)
                output = process_output(error_code, stdout, stderr)
                self.output_signal.emit(output, stderr)  # Emit the output to the GUI


def run_script_and_capture_error(script_path, mainFile_path):
    try:
        if os.path.isfile(mainFile_path):
                process = subprocess.run(
                [sys.executable, mainFile_path],  # Use sys.executable to ensure the correct Python interpreter
                capture_output=True,
                text=True,  # Capture output as text
                check=False  # Don't raise an exception on non-zero exit codes
            )
        else:
            process = subprocess.run(
                [sys.executable, script_path],  # Use sys.executable to ensure the correct Python interpreter
                capture_output=True,
                text=True,  # Capture output as text
                check=False  # Don't raise an exception on non-zero exit codes
            )
        return process.returncode, process.stdout, process.stderr
    except FileNotFoundError:
        return -1, "", f"Error: Script not found at '{script_path}'"
    except Exception as e:
        print(script_path)
        print(e)
        return -1, "", f"An unexpected error occurred: {e}"
    

def process_output(error_code, stdout, stderr):
    print(error_code)
    # output = "Script Output (stdout):\n"
    # output += stdout + "\n"
    if error_code != 0:
        # output += f"Error Code: {error_code}\n"
        # output += "Script Error (stderr):\n"
        # output += stderr + "\n"
        solution = ai_help(stderr)
        output = solution.text + "\n"
    else:
        output = "Script executed successfully."
    return output

    

def ai_help(stderr):
    error = stderr
    print("\nThe helper is thinking...\n")
    response = client.models.generate_content(
    model="gemini-2.0-flash-lite", contents=f"""I encountered the following error while running my Python script: {error} 
    Figure out what the solution is and what caused the problem. Keep it concise. Provide the solution in code format with comments on every line to explain it.
    The format should look similar to this:

    Error: Explains the error
    Cause: Shows why the error occurred
    Solution: Shows how to fix the error
    """
    )
    return response