from PyQt6.QtWidgets import QFileDialog

from .qt_app import QTApplication


class QTFileHandler(QTApplication):
    """A singleton class to handle file selection dialogs using PyQt6."""

    def select_file(self, caption="Select File", directory="", filter="All Files (*)"):
        """
        Shows a file selection dialog and returns the selected file path.

        Args:
            caption (str): The dialog window title
            directory (str): The starting directory
            filter (str): File filter pattern (e.g., "Images (*.png *.jpg);;Text files (*.txt)")

        Returns:
            str: Selected file path or empty string if canceled
        """
        file_path, _ = QFileDialog.getOpenFileName(None, caption, directory, filter)
        return file_path

    def select_files(self, caption="Select Files", directory="", filter="All Files (*)"):
        """
        Shows a file selection dialog that allows multiple selections.

        Returns:
            list: List of selected file paths
        """
        file_paths, _ = QFileDialog.getOpenFileNames(None, caption, directory, filter)
        return file_paths

    def select_directory(self, caption="Select Directory", directory=""):
        """
        Shows a directory selection dialog.

        Returns:
            str: Selected directory path or empty string if canceled
        """
        dir_path = QFileDialog.getExistingDirectory(None, caption, directory)
        return dir_path

    def save_file_dialog(self, caption="Save File", directory="", filter="All Files (*)"):
        """
        Shows a save file dialog.

        Returns:
            str: Selected save file path or empty string if canceled
        """

        file_path, _ = QFileDialog.getSaveFileName(None, caption, directory, filter)
        return file_path


def select_file(caption="Select File", directory="", filter="All Files (*)"):
    """
    Select a file using the QTApplication singleton instance.

    Args:
        caption (str): The dialog window title
        directory (str): The starting directory
        filter (str): File filter pattern (e.g., "Images (*.png *.jpg);;Text files (*.txt)")

    Returns:
        str: Selected file path or empty string if canceled
    """
    qt_app = QTFileHandler()
    return qt_app.select_file(caption, directory, filter)


def select_files(caption="Select Files", directory="", filter="All Files (*)"):
    """
    Select multiple files using the QTApplication singleton instance.

    Args:
        caption (str): The dialog window title
        directory (str): The starting directory
        filter (str): File filter pattern (e.g., "Images (*.png *.jpg);;Text files (*.txt)")

    Returns:
        list: List of selected file paths
    """
    qt_app = QTFileHandler()
    return qt_app.select_files(caption, directory, filter)


def select_directory(caption="Select Directory", directory=""):
    """
    Select a directory using the QTApplication singleton instance.

    Args:
        caption (str): The dialog window title
        directory (str): The starting directory

    Returns:
        str: Selected directory path or empty string if canceled
    """
    qt_app = QTFileHandler()
    return qt_app.select_directory(caption, directory)


def save_file_dialog(caption="Save File", directory="", filter="All Files (*)"):
    """
    Show a save file dialog using the QTApplication singleton instance.

    Args:
        caption (str): The dialog window title
        directory (str): The starting directory
        filter (str): File filter pattern (e.g., "Images (*.png *.jpg);;Text files (*.txt)")

    Returns:
        str: Selected save file path or empty string if canceled
    """
    qt_app = QTFileHandler()
    return qt_app.save_file_dialog(caption, directory, filter)


__all__ = [
    "QTFileHandler",
    "select_file",
    "select_files",
    "select_directory",
    "save_file_dialog",
]


# if __name__ == "__main__":
#     # Example usage
#     selected_file = select_file(
#         "Select a file", filter="Python files (*.py);;All files (*)"
#     )
#     print(f"Selected file: {selected_file}")

#     selected_files = select_files(
#         "Select multiple files", filter="Images (*.png *.jpg);;All files (*)"
#     )
#     print(f"Selected files: {selected_files}")
