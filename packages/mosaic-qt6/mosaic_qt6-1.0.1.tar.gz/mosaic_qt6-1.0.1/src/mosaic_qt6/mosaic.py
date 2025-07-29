import re
import sys
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, cast

from bs4 import BeautifulSoup, Tag

try:
    from PySide6.QtCore import QDate, QDateTime, QEvent, QObject, Qt, QTime, QUrl
    from PySide6.QtGui import QKeyEvent, QTextCursor
    from PySide6.QtWidgets import (
        QApplication,
        QButtonGroup,
        QCheckBox,
        QComboBox,
        QDateEdit,
        QDateTimeEdit,
        QDial,
        QDoubleSpinBox,
        QLabel,
        QLineEdit,
        QPlainTextEdit,
        QProgressBar,
        QPushButton,
        QRadioButton,
        QSlider,
        QSpinBox,
        QTimeEdit,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    raise ImportError("PySide6 is missing! Please install it using pip. The recommended command is: pip install --no-deps PySide6 shiboken6 PySide6-Essentials")

CTRL = Qt.KeyboardModifier.ControlModifier
SHIFT = Qt.KeyboardModifier.ShiftModifier
ALT = Qt.KeyboardModifier.AltModifier
Key_Return = Qt.Key_Return # type: ignore
Key_Enter = Qt.Key_Enter # type: ignore
Key_Escape = Qt.Key_Escape # type: ignore
Key_Tab = Qt.Key_Tab # type: ignore
Key_Backspace = Qt.Key_Backspace # type: ignore
Key_Left = Qt.Key_Left # type: ignore
Key_Right = Qt.Key_Right # type: ignore
Key_Up = Qt.Key_Up # type: ignore
Key_Down = Qt.Key_Down # type: ignore
F = TypeVar("F", bound=Callable[..., object])

class EventManager:
    def __init__(self):
        self.listeners: Dict[str, Dict[str, List[Callable[[], None]]]] = {
            "click": {},
            "keypress": {},
        }

    def click(self, widget_id: str) -> Callable[[F], F]:
        def decorator(func: F) -> F:
            self.define("click", widget_id, func)
            return func
        return decorator

    def keypress(self, combo_str: str) -> Callable[[F], F]:
        def decorator(func: F) -> F:
            self.define("keypress", combo_str.lower(), func)
            return func
        return decorator

    def define(self, event: str, key_or_id: str, func: Callable[..., Any]) -> None:
        self.listeners.setdefault(event, {}).setdefault(key_or_id, []).append(func)

    def trigger(self, event: str, key_or_id: str):
        for func in self.listeners.get(event, {}).get(key_or_id, []):
            func()


class MosaicWindow(QWidget):
    def __init__(self, html: str, mode: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.events = EventManager()
        self.widgets: Dict[str, Union[QWidget, QLabel, QPushButton, QLineEdit, QPlainTextEdit]] = {}
        self.setWindowTitle("Mosaic Window")
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.radio_groups: dict[str, QButtonGroup] = {}

        soup = BeautifulSoup(html, "html.parser")
        body = soup.body
        if body is None:
            raise ValueError("HTML must have a <body> tag")
        self.parse_body(body)

        if soup.title:
            self.setWindowTitle(soup.title.text)

        if mode == "dialog":
            self.setWindowModality(Qt.WindowModality.ApplicationModal)

    def parse_body(self, body: Tag):
        for tag in body.find_all(recursive=False):
            widget = None
            id_ = tag.get("id")

            if tag.name == "p":
                widget = QLabel(tag.text)
            elif tag.name == "button":
                widget = QPushButton(tag.text)
                if id_ == "exit":
                    widget.clicked.connect(self.close)
                else:
                    widget.clicked.connect(lambda checked=False, i=id_: self.events.trigger("click", i))
            elif tag.name == "input" and tag.get("type") == "text":
                widget = QLineEdit()
                widget.setPlaceholderText(tag.get("placeholder", ""))
            elif tag.name == "input" and tag.get("type") == "checkbox":
                widget = QCheckBox()
                if tag.has_attr("checked") and tag["checked"].lower() == "true":
                    widget.setChecked(True)
            elif tag.name == "textarea":
                widget = QPlainTextEdit()
                if tag.has_attr("readonly") and tag["readonly"].lower() == "true":
                    widget.setReadOnly(True)
            elif tag.name == "input" and tag.get("type") == "radio":
                widget = QRadioButton()
                if tag.has_attr("checked") and tag["checked"].lower() == "true":
                    widget.setChecked(True)

                radio_name = tag.get("name")
                if radio_name:
                    group = self.radio_groups.setdefault(radio_name, QButtonGroup(self))
                    group.addButton(widget)
            elif tag.name == "select":
                widget = QComboBox()
                for option in tag.find_all("option"):
                    text = option.text.strip()
                    widget.addItem(text)
                    if option.has_attr("selected"):
                        widget.setCurrentText(text)
            elif tag.name == "progress":
                widget = QProgressBar()
                max_val = int(tag.get("max", "100"))
                val = int(tag.get("value", "0"))
                widget.setMaximum(max_val)
                widget.setValue(val)
            elif tag.name == "input" and tag.get("type") == "range":
                widget = QSlider(Qt.Horizontal) # type: ignore
                widget.setMinimum(int(tag.get("min", 0)))
                widget.setMaximum(int(tag.get("max", 100)))
                widget.setValue(int(tag.get("value", 0)))
                if tag.get("orient") == "vertical":
                    widget.setOrientation(Qt.Vertical) # type: ignore
            elif tag.name == "input" and tag.get("type") == "number":
                step = float(tag.get("step", "1"))
                if step != 1:
                    widget = QDoubleSpinBox()
                    widget.setSingleStep(step)
                else:
                    widget = QSpinBox()
                    widget.setMinimum(int(tag.get("min", "0")))
                    widget.setMaximum(int(tag.get("max", "100")))
                    widget.setValue(float(tag.get("value", "0"))) # type: ignore

            elif tag.name == "dial":
                widget = QDial()
                widget.setMinimum(int(tag.get("min", "0")))
                widget.setMaximum(int(tag.get("max", "100")))
                widget.setValue(int(tag.get("value", "0")))

            elif tag.name == "input" and tag.get("type") == "date":
                widget = QDateEdit()
            elif tag.name == "input" and tag.get("type") == "time":
                widget = QTimeEdit()
            elif tag.name == "input" and tag.get("type") == "datetime-local":
                widget = QDateTimeEdit()
            elif tag.name == "iframe":
                try:
                    from PySide6.QtWebEngineWidgets import QWebEngineView

                    widget = QWebEngineView()
                    if tag.has_attr("src"):
                        widget.setUrl(QUrl(tag["src"]))
                    else:
                            html = tag.decode_contents()
                            widget.setHtml(html)
                except ImportError:
                    raise ImportError("You've installed PySide6 with the recommended command - but iframe elements also need PySide6-Addons! Please install that before continuing.")

            if widget:
                if id_:
                    self.widgets[id_] = widget
                self.main_layout.addWidget(widget)
        if body.get("id"):
            id_attr = body.get("id")
            if isinstance(id_attr, str):
                self.setObjectName(id_attr)
                self.widgets[id_attr] = self
            elif isinstance(id_attr, list):
                raise ValueError("Unexpected list for body id attribute")

    def add_css(self, css_string: str):
        rules = re.findall(r"#([\w\-]+)\s*\{([^}]*)\}", css_string)
        for widget_id, style_block in rules:
            widget = self.widgets.get(widget_id)
            if widget:
                style_block = style_block.strip().replace("\n", "").strip()
                widget.setStyleSheet(style_block)

    def keyPressEvent(self, event: QKeyEvent):
        combo = self._format_key_event(event)
        self.events.trigger("keypress", combo)

    def _format_key_event(self, event: QKeyEvent) -> str:
        parts: list[str] = []

        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            parts.append("ctrl")
        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            parts.append("shift")
        if event.modifiers() & Qt.KeyboardModifier.AltModifier:
            parts.append("alt")

        key = event.key()
        if key == Key_Return or key == Qt.Key_Enter: # type: ignore
            parts.append("enter")
        elif key == Key_Escape: # type: ignore
            parts.append("esc")
        elif key == Key_Backspace: # type: ignore
            parts.append("backspace")
        elif key == Key_Tab: # type: ignore
            parts.append("tab")
        elif key == Key_Up: # type: ignore
            parts.append("up")
        elif key == Key_Down: # type: ignore
            parts.append("down")
        elif key == Key_Left: # type: ignore
            parts.append("left")
        elif key == Key_Right: # type: ignore
            parts.append("right")
        elif key >= Qt.Key_F1 and key <= Qt.Key_F35: # type: ignore
            parts.append(f"f{key - Qt.Key_F1 + 1}") # type: ignore
        else:
            key_text = event.text().lower()
            if key_text and key_text.isprintable():
                parts.append(key_text)

        return "+".join(parts)
    
    def add_line(self, widget_id: str, text: str) -> None:
        widget = self.widgets.get(widget_id)
        if widget is None:
            raise KeyError(f"No widget with ID '{widget_id}'")
        if isinstance(widget, QPlainTextEdit):
            current = widget.toPlainText()
            new_text = f"{current}\n{text}" if current else text
            widget.setPlainText(new_text)
            widget.moveCursor(QTextCursor.MoveOperation.End)
        else:
            raise ValueError("chaange_text() must only be called on <textarea> elements!")
    
    def add_text(self, widget_id: str, text: str) -> None:
        widget = self.widgets.get(widget_id)
        if isinstance(widget, QPlainTextEdit):
            current = widget.toPlainText()
            new_text = f"{current}{text}" if current else text
            widget.setPlainText(new_text)
            widget.moveCursor(QTextCursor.MoveOperation.End)
        else:
            raise ValueError("chaange_text() must only be called on <textarea> elements!")
    
    def get_value(self, widget_id: str) -> float | int | str | bool | None:
        widget = self.widgets.get(widget_id)
        group = self.radio_groups.get(widget_id)
        if widget is None and group is None:
            raise KeyError(f"No widget with ID '{widget_id}'")
        if isinstance(widget, (QSlider, QSpinBox, QDoubleSpinBox, QDial, QProgressBar)):
            return widget.value()
        elif isinstance(widget, (QLineEdit, QLabel)):
            return widget.text()
        elif isinstance(widget, QPlainTextEdit):
            return widget.toPlainText()
        elif isinstance(widget, QComboBox):
            return widget.currentText()
        elif isinstance(group, QButtonGroup):
            checked_button = group.checkedButton()
            if not checked_button:
                return None
            for widget_id, widget in self.widgets.items():
                if widget is checked_button:
                    return widget_id
            return None
        if isinstance(widget, (QCheckBox, QRadioButton)):
            return widget.isChecked()
        raise ValueError(f"get_text() cannot be called on widget '{widget_id}' of unsupported type: {type(widget).__name__}")
    def set_value(self, widget_id: str, value: int | float | str | bool) -> None:
        widget = self.widgets.get(widget_id)
        if widget is None:
            raise KeyError(f"No widget with ID '{widget_id}'")
        if isinstance(widget, (QSlider, QSpinBox, QDial, QProgressBar)):
            if isinstance(value, int):
                widget.setValue(value)
            else:
                raise ValueError(f"Value must be a string when calling on QLabel or QLineEdit widgets!")
        elif isinstance(widget, QDoubleSpinBox):
            if isinstance(value, float):
                widget.setValue(value)
            else:
                raise ValueError(f"Value must be a float when calling on QDoubleSpinBox widgets!")
        elif isinstance(widget, (QDateEdit, QTimeEdit, QDateTimeEdit)):
            if isinstance(widget, QDateEdit):
                    widget.setDate(QDate.fromString(str(value), "yyyy-MM-dd"))
            elif isinstance(widget, QTimeEdit):
                widget.setTime(QTime.fromString(str(value), "HH:mm:ss"))
            else:
                widget.setDateTime(QDateTime.fromString(str(value), "yyyy-MM-dd HH:mm:ss"))
        elif isinstance(widget, (QLabel, QLineEdit)):
            if isinstance(value, str):
                widget.setText(value)
            else:
                raise ValueError(f"Value must be a string when calling on QLabel or QLineEdit widgets!")
        elif isinstance(widget, QPlainTextEdit):
            if isinstance(value, str):
                widget.setPlainText(value)
            else:
                raise ValueError(f"Value must be a string when calling on QPlainTextEdit widgets!")
        elif isinstance(widget, (QCheckBox, QRadioButton)):
            if isinstance(value, bool):
                widget.setChecked(value)
            else:
                raise ValueError(f"Value must be a boolean when calling on QCheckBox or QRadioButton widgets!")
        else:
            raise ValueError(f"set_value() unsupported on widget {widget_id} ({type(widget).__name__})")

class Mosaic(QObject):
    def __init__(self):
        super().__init__()
        app = QApplication.instance()
        if not isinstance(app, QApplication):
            app = QApplication(sys.argv)
        self.app = app
        self.windows: list[MosaicWindow] = []
        self.global_events = EventManager()
        self.app.installEventFilter(self)

    def render(self, html: str, mode: str="window"):
        if mode == "dialog":
            window = MosaicWindow(html, mode)
            window.setWindowFlags(Qt.WindowType.Dialog)
        else:
            window = MosaicWindow(html, mode)

        window.show()
        self.windows.append(window)
        return window

    def exec(self):
        self.app.exec()

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.KeyPress:
            key_event = cast(QKeyEvent, event)
            combo = self._format_key_event(key_event)
            self.global_events.trigger("keypress", combo)
        return super().eventFilter(obj, event)

    def _format_key_event(self, event: QKeyEvent) -> str:
        parts: list[str] = []

        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            parts.append("ctrl")
        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            parts.append("shift")
        if event.modifiers() & Qt.KeyboardModifier.AltModifier:
            parts.append("alt")

        key = event.key()
        if key == Key_Return or key == Key_Enter:
            parts.append("enter")
        elif key == Key_Escape:
            parts.append("esc")
        elif key == Key_Tab:
            parts.append("tab")
        elif key == Key_Up: # type: ignore
            parts.append("up")
        elif key == Key_Down: # type: ignore
            parts.append("down")
        elif key == Key_Left: # type: ignore
            parts.append("left")
        elif key == Key_Right: # type: ignore
            parts.append("right")
        elif key >= Qt.Key_F1 and key <= Qt.Key_F35: # type: ignore
            parts.append(f"f{key - Qt.Key_F1 + 1}") # type: ignore
        else:
            key_text = event.text().lower()
            if key_text and key_text.isprintable():
                parts.append(key_text)

        return "+".join(parts)