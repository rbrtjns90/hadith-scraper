import sys
import os
from PyQt6.QtCore import QThread, pyqtSignal
from pathlib import Path
from docx import Document
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QLabel, QLineEdit, QTextEdit, QFileDialog, QListWidget, QListWidgetItem
)
from PyQt6.QtGui import QTextCursor, QColor, QTextCharFormat, QTextDocument
from PyQt6.QtCore import Qt


class HadithSearchApp(QWidget):
    """GUI Application to search through Hadith `.docx` files."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Hadith Search")
        self.setGeometry(100, 100, 700, 500)

        # Layout
        layout = QVBoxLayout()

        # Search Label & Input
        self.label = QLabel("Enter search term:")
        layout.addWidget(self.label)

        self.search_input = QLineEdit()
        layout.addWidget(self.search_input)

        # Search & Stop Buttons
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.start_search)
        layout.addWidget(self.search_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_search)
        layout.addWidget(self.stop_button)

        # Results Display
        self.results_box = QTextEdit()
        self.results_box.setReadOnly(True)
        layout.addWidget(self.results_box)

        # Select Folder Button
        self.folder_button = QPushButton("Select Hadith Folder")
        self.folder_button.clicked.connect(self.select_folder)
        layout.addWidget(self.folder_button)

        # File Selection List
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        layout.addWidget(self.file_list)

        self.load_files_button = QPushButton("Load `.docx` Files")
        self.load_files_button.clicked.connect(self.load_docx_files)
        layout.addWidget(self.load_files_button)

        self.setLayout(layout)

        # Default folder path
        self.hadith_folder = Path("hadith_documents")
        self.stop_flag = False

    def select_folder(self):
        """Open file dialog to select the Hadith `.docx` folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.hadith_folder = Path(folder)
            self.load_docx_files()

    def load_docx_files(self):
        """Load `.docx` files from the selected folder into the list."""
        self.file_list.clear()
        if self.hadith_folder.exists():
            for doc_file in self.hadith_folder.glob("*.docx"):
                item = QListWidgetItem(doc_file.name)
                item.setData(Qt.ItemDataRole.UserRole, doc_file)  # Store file path
                self.file_list.addItem(item)

    def start_search(self):
        """Start search in a separate thread to keep GUI responsive."""
        search_term = self.search_input.text().strip().lower()
        if not search_term:
            self.results_box.setText("⚠️ Please enter a search term.")
            return

        selected_items = self.file_list.selectedItems()
        if not selected_items:
            self.results_box.setText("⚠️ Please select at least one `.docx` file.")
            return

        self.results_box.setText("🔍 Searching... Please wait.")
        self.stop_flag = False
        self.search_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        selected_files = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]

        self.search_thread = SearchThread(search_term, selected_files)
        self.search_thread.results_ready.connect(self.display_results)
        self.search_thread.start()

    def stop_search(self):
        """Stop the search process."""
        self.stop_flag = True
        self.results_box.append("\n🛑 Search stopped.")
        self.search_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def display_results(self, search_term, results):
        """Display results in the GUI with highlighted search term."""
        if results:
            self.results_box.setPlainText("\n".join(results))
            self.highlight_search_term(search_term)
        else:
            self.results_box.setText("❌ No matches found.")

        self.search_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def highlight_search_term(self, search_term):
        """Highlight search term in the results box."""
        document = self.results_box.document()
        text_cursor = QTextCursor(document)
        text_format = QTextCharFormat()
        text_format.setBackground(QColor("yellow"))

        text_cursor.movePosition(QTextCursor.MoveOperation.Start)
        while not text_cursor.isNull():
            text_cursor = document.find(search_term, text_cursor, QTextDocument.FindFlag.FindCaseSensitively)
            if not text_cursor.isNull():
                text_cursor.mergeCharFormat(text_format)


class SearchThread(QThread):
    results_ready = pyqtSignal(str, list)

    def __init__(self, search_term, selected_files):
        super().__init__()
        self.search_term = search_term
        self.selected_files = selected_files
        self.stop_flag = False

    def run(self):
        results = []
        for doc_file in self.selected_files:
            if self.stop_flag:
                break

            try:
                doc = Document(doc_file)
                found_texts = []
                for para in doc.paragraphs:
                    if self.search_term in para.text.lower():
                        found_texts.append(para.text.strip())

                if found_texts:
                    results.append(f"\n📁 **{doc_file.name}**\n" + "\n".join(found_texts))
            except Exception as e:
                results.append(f"⚠️ Error reading {doc_file.name}: {e}")

        self.results_ready.emit(self.search_term, results)

    def display_results(self, search_term, results):
        """Display results in the GUI with highlighted search term."""
        if results:
            self.results_box.setPlainText("\n".join(results))
            self.highlight_search_term(search_term)
        else:
            self.results_box.setText("❌ No matches found.")

        self.search_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def highlight_search_term(self, search_term):
        """Highlight search term in the results box."""
        text_cursor = self.results_box.textCursor()
        text_format = QTextCharFormat()
        text_format.setBackground(QColor("yellow"))

        text_cursor.movePosition(QTextCursor.MoveOperation.Start)
        while text_cursor.find(search_term, QTextCursor.FindFlag.CaseInsensitive):
            text_cursor.mergeCharFormat(text_format)


# Run the Application
app = QApplication(sys.argv)
window = HadithSearchApp()
window.show()
sys.exit(app.exec())
