import time
import subprocess
import sys
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class ScriptChangeHandler(FileSystemEventHandler):
    def __init__(self, script_path, *args):
        self.script_path = script_path
        self.script_args = args

    def on_modified(self, event):
        if event.src_path == self.script_path:  # Only trigger if the target script is modified.
            print(f"Detected change in {self.script_path}. Re-running script...")
            error_code, stdout, stderr = run_script_and_capture_error(self.script_path, *self.script_args)  # Assuming you have the error_capture function from before.
            process_output(error_code, stdout, stderr) # Process output as before


def run_script_and_capture_error(script_path, *args): # Same as before
    """
    Runs a script and captures its error code.

    Args:
        script_path: The path to the script to execute.
        *args: Additional arguments to pass to the script.

    Returns:
        A tuple containing:
        - The error code (0 for success, non-zero for error).
        - The standard output (stdout) of the script.
        - The standard error (stderr) of the script.
    """
    try:
        process = subprocess.run(
            [sys.executable, script_path] + list(args),  # Use sys.executable to ensure the correct Python interpreter
            capture_output=True,
            text=True,  # Capture output as text
            check=False  # Don't raise an exception on non-zero exit codes
        )
        return process.returncode, process.stdout, process.stderr
    except FileNotFoundError:
        return -1, "", f"Error: Script not found at '{script_path}'"
    except Exception as e:
        return -1, "", f"An unexpected error occurred: {e}"

def process_output(error_code, stdout, stderr): # Function to handle output (example)
    print("Script Output (stdout):")
    print(stdout)
    if error_code != 0:
        print(f"Error Code: {error_code}")
        print("Script Error (stderr):")
        print(stderr)
    else:
        print("Script executed successfully.")


if __name__ == "__main__":
    print("it is working??")
    if len(sys.argv) < 2:
        print("Usage: python watch_and_run.py <script_path> [<arg1> <arg2> ...]")
        sys.exit(1)

    script_path = sys.argv[1]

    if not os.path.exists(script_path):
      print(f"Error: {script_path} not found.")
      sys.exit(1)
    
    script_args = sys.argv[2:]

    event_handler = ScriptChangeHandler(script_path, *script_args)
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(script_path), recursive=False)  # Watch only the script's directory
    observer.start()


    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()