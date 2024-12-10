from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QSlider, QPushButton, QRadioButton, QHBoxLayout
from PySide6.QtCore import Qt
import subprocess
import sys
import re

class LUMI(QWidget):
    def __init__(self):
        super().__init__()

        self.display_name = "DP-1"

        self.config_file = "settings.txt"
        
        self.save_initial_gamma()
        self.load_config()

        self.setWindowTitle("LUMI")
        self.setGeometry(100, 100, 400, 250)

        layout = QVBoxLayout()

        self.label = QLabel("Color temperature: neutral", self)
        layout.addWidget(self.label)

        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setRange(0, 100)
        self.slider.setValue(self.slider_value)
        self.slider.valueChanged.connect(self.update_filter)
        layout.addWidget(self.slider)

        radio_layout = QVBoxLayout()
        self.radio_warm = QRadioButton("Warm")
        self.radio_cool = QRadioButton("Cold")
        
        if self.filter_type == "warm":
            self.radio_warm.setChecked(True)
        else:
            self.radio_cool.setChecked(True)

        self.radio_warm.toggled.connect(lambda: self.apply_filter("warm"))
        self.radio_cool.toggled.connect(lambda: self.apply_filter("cool"))
        
        radio_layout.addWidget(self.radio_warm)
        radio_layout.addWidget(self.radio_cool)
        layout.addLayout(radio_layout)

        self.reset_button = QPushButton("Reset initial gamma", self)
        self.reset_button.clicked.connect(self.restore_initial_gamma)
        layout.addWidget(self.reset_button)

        self.setLayout(layout)
        self.update_filter()

    def save_initial_gamma(self):
        result = subprocess.run(f"xrandr --verbose | grep -A 5 '{self.display_name}'", shell=True, capture_output=True, text=True)
        match = re.search(r"Gamma:\s+([\d.]+):([\d.]+):([\d.]+)", result.stdout)
        if match:
            red_gamma, green_gamma, blue_gamma = match.groups()
            with open(self.config_file, "w") as file:
                file.write(f"initial_gamma={red_gamma},{green_gamma},{blue_gamma}\n")
                file.write("slider_value=50\n")
                file.write("filter_type=neutral\n")
            print("Initial gamma:", red_gamma, green_gamma, blue_gamma)
        else:
            print("Can't find initial gamma values.")

    def restore_initial_gamma(self):
        try:
            with open(self.config_file, "r") as file:
                lines = file.readlines()
                initial_gamma = [line.split('=')[1].strip() for line in lines if "initial_gamma" in line][0]
                red_gamma, green_gamma, blue_gamma = initial_gamma.split(",")
            reset_command = f"xrandr --output {self.display_name} --gamma {red_gamma}:{green_gamma}:{blue_gamma}"
            subprocess.run(reset_command, shell=True)
            self.label.setText("Reset original gamma")
            print("Original gamma recovered:", red_gamma, green_gamma, blue_gamma)
        except Exception as e:
            print("Error to recover initial gamma:", e)

    def update_filter(self):
        slider_value = self.slider.value()
        if self.radio_warm.isChecked():
            red_gamma = 1.0
            green_gamma = max(0.5, 1.0 - (slider_value / 200))
            blue_gamma = max(0.3, 1.0 - (slider_value / 100))
        elif self.radio_cool.isChecked():
            red_gamma = max(0.3, 1.0 - (slider_value / 100))
            green_gamma = max(0.5, 1.0 - (slider_value / 200))
            blue_gamma = 1.0
        else:
            red_gamma = green_gamma = blue_gamma = 1.0

        gamma_command = f"xrandr --output {self.display_name} --gamma {red_gamma}:{green_gamma}:{blue_gamma}"
        subprocess.run(gamma_command, shell=True)

        self.label.setText(f"Color temperature: {slider_value}%")
        self.save_config(slider_value, "warm" if self.radio_warm.isChecked() else "cool")

    def apply_filter(self, filter_type):
        self.update_filter()

    def save_config(self, slider_value, filter_type):
        with open(self.config_file, "r") as file:
            lines = file.readlines()
        
        with open(self.config_file, "w") as file:
            for line in lines:
                if "slider_value" in line:
                    file.write(f"slider_value={slider_value}\n")
                elif "filter_type" in line:
                    file.write(f"filter_type={filter_type}\n")
                else:
                    file.write(line)

    def load_config(self):
        try:
            with open(self.config_file, "r") as file:
                lines = file.readlines()
                for line in lines:
                    if "slider_value" in line:
                        self.slider_value = int(line.split('=')[1].strip())
                    elif "filter_type" in line:
                        self.filter_type = line.split('=')[1].strip()
        except FileNotFoundError:
            self.slider_value = 50
            self.filter_type = "neutral"
            print("No configuration found. Default settings applied.")

app = QApplication(sys.argv)
LUMI().show()
sys.exit(app.exec())

