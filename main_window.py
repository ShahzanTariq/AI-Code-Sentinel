from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLabel, QLineEdit, QFileDialog, QPlainTextEdit
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize
from worker_thread import WorkerThread
import os
import re 

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Code Sentinel")
        self.worker_thread = None

        self.setWindowFlag(Qt.WindowStaysOnTopHint, False)

        icon_path = "Icon.png"
        icon = QIcon(str(icon_path))
        self.setWindowIcon(icon)

        layout = QVBoxLayout()
        plainText_layout = QHBoxLayout()

        self.folder_path_label = QLabel("Selected Folder:")
        layout.addWidget(self.folder_path_label)

        self.folder_path_edit = QLineEdit()
        layout.addWidget(self.folder_path_edit)

        self.mainFile_path_label = QLabel("Selected Main File:")
        layout.addWidget(self.mainFile_path_label)

        self.mainFile_path_edit = QLineEdit()
        layout.addWidget(self.mainFile_path_edit)

        # Browse button
        fileSelection_layout = QHBoxLayout()
        self.browse_button = QPushButton("Browse")
        fileSelection_layout.addWidget(self.browse_button)
        self.browse_button.clicked.connect(self.browse_file)

        # Main File button
        self.mainFile_button = QPushButton("Select Main File")
        fileSelection_layout.addWidget(self.mainFile_button)
        self.mainFile_button.clicked.connect(self.mainFile_select)
        layout.addLayout(fileSelection_layout)

        # Watch button (toggleable) 
        toggle_layout = QHBoxLayout()
        self.watch_button = QPushButton("Start Watching")
        self.watch_button.clicked.connect(self.toggle_watching)  # Connect to toggle function
        toggle_layout.addWidget(self.watch_button,9)

        # Pin button (toggleable)
        self.pin_button = QPushButton("Pin Window")
        self.pin_button.clicked.connect(self.toggle_pin)
        toggle_layout.addWidget(self.pin_button)

        layout.addLayout(toggle_layout)
        
        # Error Section (Vertical Layout)
        error_layout = QVBoxLayout()
        error_title = QLabel("Error:")
        stderror_title = QLabel("Terminal Output:")
        error_layout.addWidget(error_title)
        self.error_text = QPlainTextEdit(readOnly=True)
        error_layout.addWidget(self.error_text)
        error_layout.addWidget(stderror_title)
        self.stderror_text = QPlainTextEdit(readOnly=True)
        error_layout.addWidget(self.stderror_text)
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


    def mainFile_select(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File", ".", "Python Files (*.py)") # Uses _ to hold second str
        if file_path:
            self.mainFile_path_edit.setText(file_path)


    def toggle_watching(self):
        if self.worker_thread is None or not self.worker_thread.isRunning():
            self.start_watching() # Call existing start_watching function
        else:
            self.stop_watching() # Call existing stop_watching function
            
    def toggle_pin(self):
        if self.windowFlags() & Qt.WindowStaysOnTopHint:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
            self.pin_button.setText("Pin Window") 
        else:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
            self.pin_button.setText("Unpin Window") 
        self.current_size = QSize(self.width(),self.height())
        self.show()
        self.resize(self.current_size)

    def start_watching(self):
        script_path = self.folder_path_edit.text()
        mainFile_path = self.mainFile_path_edit.text()

        if not script_path:
            self.error_text.appendPlainText("Please select a folder first.")
            return
        if not os.path.exists(script_path):
            self.error_text.appendPlainText(f"Error: {script_path} not found.")
            return
        if self.worker_thread is not None and self.worker_thread.isRunning():  # Prevent multiple starts
            self.error_text.appendPlainText("Watcher is already running.")
            return
        
        self.worker_thread = WorkerThread(script_path, mainFile_path) 
        self.worker_thread.output_signal.connect(self.append_output)  # Connect to append output to the GUI
        self.worker_thread.finished_signal.connect(self.stop_watching)  # Connect to cleanup
        self.worker_thread.start()
        self.error_text.setPlainText("Watcher started.")
        self.browse_button.setEnabled(False) #Stops user from changing folder while watcher is running
        self.mainFile_button.setEnabled(False)
        self.watch_button.setText("Stop Watching")  # Change button text


    def empty_text(self):
        self.cause_text.setPlainText("")
        self.solution_text.setPlainText("")
        self.stderror_text.setPlainText("")
        self.error_text.setPlainText("")
    

    # Set up to split texts into corresponding plaintext boxes (error, cause, solution)
    def append_output(self, output, stderr):
        if output == "Script executed successfully.":
            self.empty_text()
            self.error_text.setPlainText(output) #Using setPlaintext helps clean up the PlainText box in GUI
            return
        
        match = re.search(r"Error:\s*(.+?)\s*Cause:\s*(.+?)\s*Solution:\s*(.+)", output, re.DOTALL)
        if match:
            error = match.group(1).strip()
            cause = match.group(2).strip()
            solution = match.group(3).strip()
            solution = re.sub(r"```python\s*|\s*```", "", solution)
        else:
            return None  # Return None if the pattern is not found
        
        self.error_text.setPlainText(error) #Using setPlaintext helps clean up the PlainText box in GUI
        self.cause_text.setPlainText(cause)
        self.solution_text.setPlainText(solution)
        self.stderror_text.setPlainText(stderr)


    def stop_watching(self):
        if self.worker_thread is not None and self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait()
            self.worker_thread = None  # Reset the thread object
            self.empty_text()
            self.error_text.setPlainText("Watcher stopped.")
            self.worker_finished()
            
            self.watch_button.setText("Start Watching")  # Change button text
            self.browse_button.setEnabled(True) # Allows user to browse folders again
            self.mainFile_button.setEnabled(True)
        else:
            self.error_text.appendPlainText("Watcher is not running.")


    def worker_finished(self):
        self.error_text.appendPlainText("Watcher thread finished.")
        self.worker_thread = None # Reset the thread object