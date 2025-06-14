from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QTextEdit, QDialog, QLabel
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QTextCursor
from sys import argv

import lambda_parser

def style(bg_col: tuple[int, int, int]|str, col: tuple[int, int, int]|str):
	return "background-color: " + (f"rgb{bg_col}" if isinstance(bg_col, tuple) else bg_col) + "; color: " + (f"rgb{col}" if isinstance(col, tuple) else col) + '; font: 16px "Pixelated"'

class ErrorDialog(QDialog):
	def __init__(self, text: str):
		super().__init__()

		self.setFixedSize(400, 300)
		self.setWindowTitle("Error!")
		self.setStyleSheet(style((9, 12, 41), "white"))

		self.text = QLabel(self)
		self.text.setGeometry(20, 20, 360, 260)
		self.text.setText(text)
		self.text.setWordWrap(True)

class MainWindow(QMainWindow):
	def __init__(self):
		super().__init__()

		self.setFixedSize(800, 600)
		self.setWindowTitle("Lambda Calculus Evaluator")
		self.setStyleSheet(style((9, 12, 41), "white"))

		self.run_button = QPushButton(self)
		self.run_button.setText("Evaluate")
		self.run_button.setGeometry(325, 40, 150, 50)
		self.run_button.setStyleSheet(style((29, 48, 120), "white"))
		self.run_button.setCursor(Qt.CursorShape.PointingHandCursor)
		self.run_button.clicked.connect(self.run)

		self.code_edit = QTextEdit(self)
		self.code_edit.setGeometry(20, 100, 380, 480)
		self.code_edit.setStyleSheet(style((36, 33, 82), "white"))
		self.code_edit.installEventFilter(self)
		self.code_edit.setAcceptRichText(False)

		self.result = QTextEdit(self)
		self.result.setGeometry(400, 100, 380, 480)
		self.result.setStyleSheet(style((36, 33, 82), "white"))
		self.result.installEventFilter(self)
		self.result.setReadOnly(True)

		self.num_button = QPushButton(self)
		self.num_button.setText("Convert")
		self.num_button.setGeometry(630, 40, 150, 50)
		self.num_button.setStyleSheet(style((11, 22, 64), "white"))
		self.num_button.setCursor(Qt.CursorShape.PointingHandCursor)
		self.num_button.clicked.connect(self.convert)

		self.res = None

	def eventFilter(self, a0, a1):
		if a0 == self.code_edit:
			if a1.type() == QEvent.Type.KeyPress:
				cursor = self.code_edit.textCursor()
				block = cursor.block()

				if block.text() == "/bools":
					cursor.setPosition(block.position())
					cursor.setPosition(block.position() + len(block.text()), QTextCursor.MoveMode.KeepAnchor)
					cursor.insertText("λt.λf.t -> TRUE\nλt.λf.f -> FALSE")
					return True
			
				if a1.key() in (Qt.Key.Key_At, Qt.Key.Key_Backslash):
					self.code_edit.insertPlainText("λ")
					return True
				
				if a1.modifiers() == Qt.KeyboardModifier.ControlModifier and a1.key() == Qt.Key.Key_V:
					clipboard: str = QApplication.clipboard().text()
					self.code_edit.insertPlainText(clipboard.replace("@", "λ").replace("\\", "λ"))
					return True
		return super().eventFilter(a0, a1)

	def run(self):
		context = {}
		self.res = None

		self.result.setStyleSheet(style((36, 33, 82), "white"))
		try:
			result, error = lambda_parser.run("code.lm", self.code_edit.toPlainText(), context)
		except RecursionError:
			result, error = None, "Recursion limit reached when evaluating expression."
		if error:
			self.result.setStyleSheet(style((36, 33, 82), "red"))
			self.result.setText(f"{error}")
		else:
			self.result.setText(f"{result}")
			self.res = result

	def convert(self):
		if self.res is None: return

		if repr(self.res) == self.result.toPlainText():
			value = lambda_parser.decode_church(self.res)
			if isinstance(value, int): self.result.setText(f"{value}")
			else:
				res_text: str = f"{self.res}"
				THRESHOLD = 35

				if len(res_text) > 35: res_text = res_text[:35] + "..."
				dialog = ErrorDialog(f"Cannot convert\n{res_text}\nto a numeral.")
				dialog.exec()
		else:
			self.result.setText(f"{self.res}")

if __name__ == "__main__":
	app = QApplication(argv)
	main = MainWindow()

	main.show()
	app.exec()
