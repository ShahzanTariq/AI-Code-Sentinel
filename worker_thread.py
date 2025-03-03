import sys
import os
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PySide6.QtCore import QThread, Signal

from script_utils import ScriptChangeHandler


class WorkerThread(QThread):
    output_signal = Signal(str, str)
    finished_signal = Signal()

    def __init__(self, script_path, script_args, mainFile_path = None):
        super().__init__()
        self.script_path = script_path
        self.script_args = script_args
        self.mainFile_path = mainFile_path
        self.observer = None

    def run(self):
        event_handler = ScriptChangeHandler(self.script_path, *self.script_args, self.mainFile_path)
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
