import sys
import os
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from google import genai
from dotenv import load_dotenv
import re

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLabel, QLineEdit, QFileDialog, QPlainTextEdit, QGroupBox
from PySide6.QtCore import QThread, Signal

load_dotenv()
api = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api)

class ScriptChangeHandler(FileSystemEventHandler):
    def __init__(self, script_path, *args):
        self.script_path = script_path
        self.script_args = args
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
                error_code, stdout, stderr = run_script_and_capture_error(event.src_path, *self.script_args)
                output = process_output(error_code, stdout, stderr)
                self.output_signal.emit(output)  # Emit the output to the GUI


def run_script_and_capture_error(script_path, *args):
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
        event_handler.output_signal = self.output_signal  # Pass the signal to the event handler
        self.observer = Observer()
        self.observer.schedule(event_handler, path=os.path.dirname(self.script_path), recursive=True) #Observer is gonna check script_path for creation, deletion, modification, and moving. But our event_handler (scriptchangehandler) only handles modification events.
        self.observer.start() # Starts observing

        try:
            #This allows the thread to respond to events and to recieve signals
            self.exec() #Starts Qt event loop for thread
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
        plainText_layout = QHBoxLayout()

        self.folder_path_label = QLabel("Selected File:")
        layout.addWidget(self.folder_path_label)


        self.folder_path_edit = QLineEdit()
        layout.addWidget(self.folder_path_edit)

        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_file)
        layout.addWidget(self.browse_button)

        self.watch_button = QPushButton("Start Watching")
        self.watch_button.clicked.connect(self.toggle_watching)  # Connect to toggle function
        layout.addWidget(self.watch_button)
        
        # Error Section (Vertical Layout)
        error_layout = QVBoxLayout()
        error_title = QLabel("Error:")
        error_layout.addWidget(error_title)
        self.error_text = QPlainTextEdit(readOnly=True)
        error_layout.addWidget(self.error_text)
        plainText_layout.addLayout(error_layout)  

        # Cause Section (Vertical Layout)
        cause_layout = QVBoxLayout()
        cause_title = QLabel("Cause:")
        cause_layout.addWidget(cause_title)
        self.cause_text = QPlainTextEdit(readOnly=True)
        cause_layout.addWidget(self.cause_text)
        plainText_layout.addLayout(cause_layout)


        # Solution Section (Vertical Layout)
        solution_layout = QVBoxLayout()
        solution_title = QLabel("Solution:")
        solution_layout.addWidget(solution_title)
        self.solution_text = QPlainTextEdit(readOnly=True)
        solution_layout.addWidget(self.solution_text)
        plainText_layout.addLayout(solution_layout)

        
        layout.addLayout(plainText_layout)
        self.setLayout(layout)


    def browse_file(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder", ".")
        if folder_path:
            self.folder_path_edit.setText(folder_path)
            self.folder_path_label.setText(f"Selected Folder: {folder_path}")

    def toggle_watching(self):
        if self.worker_thread is None or not self.worker_thread.isRunning():
            self.start_watching() # Call existing start_watching function
            
        else:
            self.stop_watching() # Call existing stop_watching function
            

    def start_watching(self):
        script_path = self.folder_path_edit.text()

        if not script_path:
            self.error_text.appendPlainText("Please select a file first.")
            return

        if not os.path.exists(script_path):
            self.error_text.appendPlainText(f"Error: {script_path} not found.")
            return


        if self.worker_thread is not None and self.worker_thread.isRunning():  # Prevent multiple starts
            self.error_text.appendPlainText("Watcher is already running.")
            return

        
        self.worker_thread = WorkerThread(script_path, []) # No script arguments for now
        self.worker_thread.output_signal.connect(self.append_output)  # Connect to append output to the GUI
        self.worker_thread.finished_signal.connect(self.worker_finished)  # Connect to cleanup
        self.worker_thread.start()
        self.error_text.setPlainText("Watcher started.")
        self.browse_button.setEnabled(False) #Stops user from changing folder while watcher is running
        self.watch_button.setText("Stop Watching")  # Change button text

    # Set up to split texts into corresponding plaintext boxes (error, cause, solution)
    def append_output(self, output):
        #self.error_text.appendPlainText(output)
        if output == "Script executed successfully.":
            self.error_text.setPlainText(output) #Using setPlaintext helps clean up the PlainText box in GUI
            self.cause_text.setPlainText("")
            self.solution_text.setPlainText("")
            return
        
        match = re.search(r"Error:\s*(.+?)\s*Cause:\s*(.+?)\s*Solution:\s*(.+)", output, re.DOTALL)

        if match:
            error = match.group(1).strip()
            cause = match.group(2).strip()
            solution = match.group(3).strip()
        else:
            return None  # Return None if the pattern is not found
        self.error_text.setPlainText(error) #Using setPlaintext helps clean up the PlainText box in GUI
        self.cause_text.setPlainText(cause)
        self.solution_text.setPlainText(solution)


    def stop_watching(self):
        if self.worker_thread is not None and self.worker_thread.isRunning():
            self.worker_thread.terminate() # Forcefully stop the thread
            self.worker_thread = None  # Reset the thread object
            self.error_text.setPlainText("Watcher stopped.")
            self.worker_finished()
            self.watch_button.setText("Start Watching")  # Change button text
            self.browse_button.setEnabled(True) # Allows user to browse folders again
        else:
            self.error_text.appendPlainText("Watcher is not running.")


    def worker_finished(self):
        self.error_text.appendPlainText("Watcher thread finished.")
        self.worker_thread = None # Reset the thread object


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())