import os
import sys
import json
import math
import glob
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QFormLayout, QComboBox, QCheckBox, QDialog, QVBoxLayout, QLabel, QListWidget, QSlider, QColorDialog, QMessageBox, QInputDialog
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt, QUrl, QTimer, QPoint, QThread
from PySide6.QtGui import QCursor
import mouse
import random



# Dictionary of all available trail HTML files
trails = {
    os.path.basename(file).split(".")[0].title(): os.path.join(os.path.dirname(__file__), file)
    for file in glob.glob("./trails/*.html")
}

for trail in glob.glob("./custom_trails/*.json"):
    trails.update({os.path.basename(trail).split(
        ".")[0].upper(): os.path.join(os.path.dirname(__file__), trail)})


class ScreenTrail(QWebEngineView):
    def __init__(self, trail_path, settings={}):
        super().__init__()
        self.setWindowTitle("Screen Trail")
        self.showFullScreen()
        self.settings = settings

        # Set window properties for transparency
        self.setWindowFlags(Qt.FramelessWindowHint |
                            Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground, True)

        self.setUrl(QUrl.fromLocalFile(trail_path))
        self.page().setBackgroundColor(Qt.GlobalColor.transparent)
        self.setStyleSheet("background-color: transparent;")
        self.show()

        # Use a QTimer to track mouse position
        self.mouse_timer = QTimer(self)
        self.mouse_timer.timeout.connect(self.track_mouse)
        self.mouse_timer.start(10)  # Check mouse position every 10ms
        self.mouse_pos = QCursor.pos()
        self.is_mouse_pressed = False
        self.enabled = True

    def track_mouse(self):
        if self.enabled:
            distance = math.dist(self.mouse_pos.toTuple(),
                                 QCursor.pos().toTuple())
            if distance > 2:
                self.mouse_pos = QCursor.pos()
                self.on_mouse_move(self.mouse_pos)
            if mouse.is_pressed("right") or mouse.is_pressed("left"):
                if not self.page().isLoading() and not self.is_mouse_pressed:
                    self.is_mouse_pressed = True
                    x, y = QCursor.pos().toTuple()
                    self.page().runJavaScript(
                        f"mouseClick({x}, {y}, {self.settings});")
            else:
                self.is_mouse_pressed = False

    def on_mouse_move(self, pos: QPoint):
        if not self.page().isLoading():
            x, y = pos.x(), pos.y()
            self.page().runJavaScript(f"mouseMove({x}, {y}, {self.settings});")

    def mousePressEvent(self, event):
        sys.exit()

    def load_custom_trail(self, config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)

        # Use loadFinished to apply the config after the page is fully loaded
        self.page().loadFinished.connect(lambda: self.apply_trail_config(config))
        self.setUrl(QUrl.fromLocalFile(os.path.join(
            os.path.dirname(__file__), "trails", "default.html")))

    def apply_trail_config(self, config):
        # Determine color based on the configuration
        if config["colorPickType"] == "random":
            color = random.choice(config["colors"])
        elif config["colorPickType"] == "gradient":
            colors = ", ".join(config["colors"])
            color = f"linear-gradient(90deg, {colors})" if len(
                config["colors"]) > 1 else config["colors"][0]
        else:
            color = config["colors"][0]

        # Pass the configuration to JavaScript
        self.page().runJavaScript(f"""
            setTrailConfig({{
                shape: '{config["shape"]}',
                color: '{color}',
                size: {config["size"]},
                animation: '{config["animation"]}',
                clickEffect: '{config["clickEffect"]}',
                style: '{config["style"]}',
                amount: {config["amount"]},
                separationDistance: {config["separationDistance"]},
                separationAngle: {config["separationAngle"]}
            }});
        """)


class MainSettingsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Trail Settings")
        self.setGeometry(100, 100, 300, 200)

        # Central widget setup
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        self.layout = QFormLayout(central_widget)

        if not trails:
            raise ValueError("No trails available")

        self.enabled = True
        self.enabledCheckBox = QCheckBox("Enabled")
        self.enabledCheckBox.setChecked(self.enabled)
        self.enabledCheckBox.checkStateChanged.connect(self.toggle)
        self.layout.addWidget(self.enabledCheckBox)

        # Dropdown to select a trail
        self.trail_selector = QComboBox()
        self.trail_selector.addItems(list(trails.keys()))
        self.layout.addRow("Select Trail:", self.trail_selector)

        # Buttons
        self.apply_button = QPushButton("Apply and reset")
        self.customize_button = QPushButton("Customize Trail")
        self.apply_button.clicked.connect(self.apply_settings)
        self.customize_button.clicked.connect(self.open_trail_editor)

        self.layout.addWidget(self.apply_button)
        self.layout.addWidget(self.customize_button)

        self.trail = None
        self._thread = None
        self.screen_trail()

    def screen_trail(self):
        if not self.trail:
            trail = ScreenTrail(trails.get(
                self.trail_selector.currentText(), ""))
            self.trail = trail
        if not self._thread:
            self._thread = QThread()
            self.trail.moveToThread(self._thread)
            self._thread.start()

    def toggle(self):
        self.enabled = self.enabledCheckBox.isChecked()
        if self.enabled:
            self.apply_button.setEnabled(True)
            self.customize_button.setEnabled(True)
            self.trail_selector.setEnabled(True)
        else:
            self.apply_button.setEnabled(False)
            self.customize_button.setEnabled(False)
            self.trail_selector.setEnabled(False)
        self.trail.enabled = self.enabled

    def apply_settings(self):
        selected_trail = self.trail_selector.currentText()
        print("Settings applied:", selected_trail)
        if selected_trail.isupper():
            self.trail.load_custom_trail(trails.get(selected_trail))
        else:
            trail_path = trails.get(selected_trail)
            if trail_path and self.enabled:
                self.trail.setUrl(QUrl.fromLocalFile(trail_path))

    def open_trail_editor(self):
        global trails
        editor = TrailEditor(self)
        if editor.exec():
            for trail in glob.glob("./custom_trails/*.json"):
                trails.update({os.path.basename(trail).split(
                    ".")[0].upper(): os.path.join(os.path.dirname(__file__), trail)})
                self.trail_selector.clear()
                self.trail_selector.addItems(list(trails.keys()))


class TrailEditor(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Trail Editor")
        self.setGeometry(200, 200, 400, 500)
        self._layout = QVBoxLayout(self)

        # Shape Selector
        self.shape_selector = QComboBox()
        self.shape_selector.editTextChanged.connect(self.updateUI)
        self.shape_selectorL = QLabel("Shape:", self.shape_selector)
        self.shape_selector.addItems(["Circle", "Square", "Star"])
        self._layout.addWidget(self.shape_selectorL)
        self._layout.addWidget(self.shape_selector)

        # Color Picker
        self.color_list = []
        self.color_list_widget = QListWidget()
        self.add_color_button = QPushButton("Add Color")
        self.add_color_button.clicked.connect(self.add_color)
        self._layout.addWidget(QLabel("Trail Colors:"))
        self._layout.addWidget(self.add_color_button)
        self._layout.addWidget(self.color_list_widget)

        # color pick type Selector
        self.color_pick_type_selector = QComboBox()
        self.color_pick_type_selector.editTextChanged.connect(self.updateUI)
        self.color_pick_type_selectorL = QLabel(
            "Color Pick Type:", self.color_pick_type_selector)
        self.color_pick_type_selector.addItems(["random", "gradient"])
        self._layout.addWidget(self.color_pick_type_selectorL)
        self._layout.addWidget(self.color_pick_type_selector)

        # Size Slider
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.sliderMoved.connect(self.updateUI)
        self.size_slider.setRange(1, 25)
        self.size_sliderL = QLabel("Size:", self.size_slider)
        self._layout.addWidget(self.size_sliderL)
        self._layout.addWidget(self.size_slider)

        # Amount Slider
        self.amount_slider = QSlider(Qt.Horizontal)
        self.amount_slider.sliderMoved.connect(self.updateUI)
        self.amount_slider.setRange(1, 75)
        self.amount_sliderL = QLabel("Amount:", self.amount_slider)
        self._layout.addWidget(self.amount_sliderL)
        self._layout.addWidget(self.amount_slider)

        # Animation Selector
        self.animation_selector = QComboBox()
        self.animation_selector.editTextChanged.connect(self.updateUI)
        self.animation_selector.addItems(["None", "Fade", "Expand", "Rotate"])
        self.animation_selectorL = QLabel(
            "Animation:", self.animation_selector)
        self._layout.addWidget(self.animation_selectorL)
        self._layout.addWidget(self.animation_selector)

        # Click Effect Selector
        self.click_effect_selector = QComboBox()
        self.click_effect_selector.editTextChanged.connect(self.updateUI)
        self.click_effect_selector.addItems(
            ["None", "Burst", "Ripple", "Glow"])
        self.click_effect_selectorL = QLabel(
            "Click Effect:", self.click_effect_selector)
        self._layout.addWidget(self.click_effect_selectorL)
        self._layout.addWidget(self.click_effect_selector)

        # Trail Style Selector
        self.trail_style_selector = QComboBox()
        self.trail_style_selector.editTextChanged.connect(self.updateUI)
        self.trail_style_selector.addItems(["Solid", "Dashed", "Gradient"])
        self.trail_style_selectorL = QLabel(
            "Trail Style:", self.trail_style_selector)
        self._layout.addWidget(self.trail_style_selectorL)
        self._layout.addWidget(self.trail_style_selector)

        # Separation distance Selector
        self.separationDistanceSelector = QSlider(Qt.Horizontal)
        self.separationDistanceSelector.sliderMoved.connect(self.updateUI)
        self.separationDistanceSelector.setRange(1, 15)
        self.separationDistanceSelectorL = QLabel(
            "Separation Distance:", self.separationDistanceSelector)
        self._layout.addWidget(self.separationDistanceSelectorL)
        self._layout.addWidget(self.separationDistanceSelector)

        # Separation angle Selector
        self.separationAngleSelector = QSlider(Qt.Horizontal)
        self.separationAngleSelector.sliderMoved.connect(self.updateUI)
        self.separationAngleSelector.setRange(1, 4)
        self.separationAngleSelectorL = QLabel(
            "Separation Angle:", self.separationAngleSelector)
        self._layout.addWidget(self.separationAngleSelectorL)
        self._layout.addWidget(self.separationAngleSelector)

        # Save Button
        self.save_button = QPushButton("Save Trail")
        self.save_button.clicked.connect(self.save_trail)
        self._layout.addWidget(self.save_button)
        self.updateUI()

    def add_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.color_list.append(color.name())
            self.color_list_widget.addItem(color.name())
            self.updateUI()

    def updateUI(self):
        # update all the labels to match there current values
        self.shape_selectorL.setText(
            f"Shape: {self.shape_selector.currentText()}")
        self.size_sliderL.setText(f"Size: {self.size_slider.value()}")
        self.amount_sliderL.setText(f"Amount: {self.amount_slider.value()}")
        self.animation_selectorL.setText(
            f"Animation: {self.animation_selector.currentText()}")
        self.click_effect_selectorL.setText(
            f"Click Effect: {self.click_effect_selector.currentText()}")
        self.trail_style_selectorL.setText(
            f"Trail Style: {self.trail_style_selector.currentText()}")
        self.color_pick_type_selectorL.setText(
            f"Color Pick Type: {self.color_pick_type_selector.currentText()}")
        self.separationDistanceSelectorL.setText(
            f"Separation Distance: {self.separationDistanceSelector.value()}")
        self.separationAngleSelectorL.setText(
            f"Separation Angle: {self.separationAngleSelector.value()}")

    def save_trail(self):
        if len(self.color_list) == 0:
            QMessageBox.warning(self, "Error", "No colors selected")
            return
        config = {
            "shape": self.shape_selector.currentText(),
            "colors": self.color_list,
            "size": self.size_slider.value(),
            "animation": self.animation_selector.currentText(),
            "clickEffect": self.click_effect_selector.currentText(),
            "style": self.trail_style_selector.currentText(),
            "amount": self.amount_slider.value(),
            "colorPickType": self.color_pick_type_selector.currentText(),
            "separationDistance": self.separationDistanceSelector.value(),
            "separationAngle": self.separationAngleSelector.value(),
        }

        # Save the configuration to a file under a user inputted name (like `input(">>>")`)
        answer = QInputDialog.getText(self, "Save Trail", "Filename:")
        if answer[1]:
            filename = answer[0]
        else:
            return
        os.makedirs("custom_trails", exist_ok=True)
        with open(f"custom_trails/{filename}.json", 'w') as f:
            json.dump(config, f, indent=4)
        self.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_ForceRasterWidgets)
    main_window = MainSettingsWindow()
    main_window.show()
    sys.exit(app.exec())
