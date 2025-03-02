from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLabel, QLineEdit, QFileDialog, QPlainTextEdit
from PySide6.QtCore import Signal
import os
import re

from worker_thread import WorkerThread # Import WorkerThread

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