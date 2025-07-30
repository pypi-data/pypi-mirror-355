# Compilation mode, support OS-specific options
# nuitka-project: --mode=onefile
# nuitka-project: --enable-plugin=pyside6
# nuitka-project: --include-data-dir=data=data
# nuitka-project: --include-data-files=data/pdf_icon.png=data/pdf_icon.png
# nuitka-project-if: {OS} == "Windows" and os.getenv("DEBUG_COMPILATION", "no") == "yes":
#     nuitka-project: --windows-console-mode=hide
#     nuitka-project: --windows-icon-from-ico=data/pdf_icon.png unlock_pdf_gui.py
# nuitka-project-else:
#     nuitka-project: --windows-console-mode=disable
import sys
from pathlib import Path
from typing import List
from importlib.resources import files
from PySide6.QtCore import QAbstractListModel, Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QLabel,
    QListView,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtGui import QIcon as QIcon
from unlock_pdf.core import unlock_pdf


def init_path():
    return Path.home()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Unlock PDF App")
        self.setWindowIcon(QIcon(str(files("tools") / 'data/pdf_icon.png')))

        # File/Directory Initialization
        self.init_path()

        # Set the primary widget in the middle
        widget_1: QWidget = QWidget()
        self.setCentralWidget(widget_1)

        # Set VBox Layout
        layout_1 = QVBoxLayout()
        widget_1.setLayout(layout_1)

        # Add 'Select PDF Files'
        file_open_button = QPushButton("Choose your files")
        file_open_button.clicked.connect(self.select_files)
        layout_1.addWidget(file_open_button)

        # Add 'List of files'
        self.listmodel = FileListModel()
        self.listview = QListView()
        self.listview.setModel(self.listmodel)
        layout_1.addWidget(self.listview)

        # Add 'Suffix'

        # Button
        unlock_button = QPushButton("Unlock")
        unlock_button.clicked.connect(self.unlock_pdf_button_clicked)
        layout_1.addWidget(unlock_button)


    def unlock_pdf_button_clicked(self):
        if len(self.listmodel.pdf_filenames) == 0:
            return
        
        for pdf_path in self.listmodel.pdf_filenames:
            unlock_pdf(path=pdf_path, suffix='_unlocked')
        dlg = FinishedDialog()
        dlg.exec()       
    
    def init_path(self):
        self.path: Path = Path.home()
        self.last_path: Path = self.path

    def select_files(self):
        filenames, _ = QFileDialog.getOpenFileNames(
            self,
            caption="Choose file or directory",
            dir=str(self.last_path), 
            filter = "(*.pdf);;",
        )
        
        if len(filenames) == 0:
            print("No PDF file selected.")
            self.listmodel.pdf_filenames = []
            return

        self.listmodel.pdf_filenames = [Path(filename) for filename in filenames]
        self.listmodel.layoutChanged.emit()
        self.last_path = Path(filenames[0])

class FileListModel(QAbstractListModel):
    def __init__(self, *args, pdf_filenames=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.pdf_filenames: List[Path] = pdf_filenames or [] ## Check how this is or.

    def data(self, index, role):
        if role == Qt.DisplayRole:
            filename = self.pdf_filenames[index.row()]
            return str(filename)
    
    def rowCount(self, index):
        return len(self.pdf_filenames)

class FinishedDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Done")
        message = QLabel("All pdfs are unlocked.")
        self.layout = QVBoxLayout()
        self.layout.addWidget(message)
        self.setLayout(self.layout)

def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()

if __name__ == "__main__":
    sys.exit(main())
