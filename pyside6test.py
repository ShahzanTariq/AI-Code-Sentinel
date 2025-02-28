import sys
import os
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from google import genai
from dotenv import load_dotenv

from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, 
                               QPushButton, QLabel, QLineEdit, 
                               QFileDialog, QPlainTextEdit)
from PySide6.QtCore import QThread, Signal

load_dotenv()
api = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api)

class ScriptChangeHandler(FileSystemEventHandler):
    print("scirpchangehandler is being run")
    def __init__(self, script_path, *args):
        self.script_path = script_path
        self.script_args = args
        self.last_triggered = 0
        self.debounce_interval = 3

    def on_modified(self, event):
        print("file has been modified")
        if os.path.normpath(event.src_path) == os.path.normpath(self.script_path):
            current_time = time.time()
            if current_time - self.last_triggered > self.debounce_interval:
                self.last_triggered = current_time
                print(f"Detected change in {self.script_path}. Re-running script...")
                error_code, stdout, stderr = run_script_and_capture_error(self.script_path, *self.script_args)
                process_output(error_code, stdout, stderr)


def run_script_and_capture_error(script_path, *args):
    print('the capture has started')
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
    

def process_output(error_code, stdout, stderr):
    print("Script Output (stdout):")
    print(stdout)
    if error_code != 0:
        print(f"Error Code: {error_code}")
        print("Script Error (stderr):")
        print(stderr)
        solution = ai_help(stderr) 
        print(solution.text)
    else:
        print("Script executed successfully.")

    

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


class WorkerThread(QThread):
    output_signal = Signal(str)
    finished_signal = Signal()

    def __init__(self, script_path, script_args):
        super().__init__()
        self.script_path = script_path
        self.script_args = script_args
        self.observer = None

    def run(self):
        event_handler = ScriptChangeHandler(self.script_path, *self.script_args)
        self.observer = Observer()
        self.observer.schedule(event_handler, path=os.path.dirname(self.script_path), recursive=False)
        self.observer.start()

        try:
            while True:  # Keep the thread running
                time.sleep(1)
        except KeyboardInterrupt:
            pass  # Allow graceful stopping from the GUI
        finally:
            if self.observer:
                self.observer.stop()
                self.observer.join()
            self.finished_signal.emit()  # Signal thread completion



class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Script Watcher")
        self.worker_thread = None

        layout = QVBoxLayout()

        self.file_path_label = QLabel("Selected File:")
        layout.addWidget(self.file_path_label)


        self.file_path_edit = QLineEdit()
        layout.addWidget(self.file_path_edit)

        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_file)
        layout.addWidget(browse_button)

        start_button = QPushButton("Start Watching")
        start_button.clicked.connect(self.start_watching)
        layout.addWidget(start_button)


        stop_button = QPushButton("Stop Watching")
        stop_button.clicked.connect(self.stop_watching)
        layout.addWidget(stop_button)

        self.output_text = QPlainTextEdit(readOnly=True)
        layout.addWidget(self.output_text)

        self.setLayout(layout)

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Script", "", "Python Files (*.py)")
        if file_path:
            self.file_path_edit.setText(file_path)
            self.file_path_label.setText(f"Selected File: {file_path}")

    def start_watching(self):
        script_path = self.file_path_edit.text()

        if not script_path:
            self.output_text.appendPlainText("Please select a file first.")
            return

        if not os.path.exists(script_path):
            self.output_text.appendPlainText(f"Error: {script_path} not found.")
            return


        if self.worker_thread is not None and self.worker_thread.isRunning():  # Prevent multiple starts
            self.output_text.appendPlainText("Watcher is already running.")
            return

        self.worker_thread = WorkerThread(script_path, []) # No script arguments for now
        self.worker_thread.finished_signal.connect(self.worker_finished)  # Connect to cleanup
        self.worker_thread.start()
        self.output_text.appendPlainText("Watcher started.")



    def stop_watching(self):
        if self.worker_thread is not None and self.worker_thread.isRunning():
            self.worker_thread.terminate() # Forcefully stop the thread
            self.worker_thread = None  # Reset the thread object
            self.output_text.appendPlainText("Watcher stopped.")
        else:
            self.output_text.appendPlainText("Watcher is not running.")


    def worker_finished(self):
        self.output_text.appendPlainText("Watcher thread finished.")
        self.worker_thread = None # Reset the thread object


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())