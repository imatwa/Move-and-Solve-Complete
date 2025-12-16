import sys
import cv2
from random import choice, choices, randint

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout, QStackedWidget)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFontDatabase, QFont, QImage, QPixmap

import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks import python

from Detectors import JumpCounter, SquatCounter, BendCounter
from game_logic import ScoreCounter


def simple_problem_generator():
    types = ['+', '-', '*', '/']
    operation = choice(types)

    if operation == '+':
        a, b = randint(0, 100), randint(0, 100)
    elif operation == '-':
        a, b = randint(50, 110), randint(0, 50)
    elif operation == '*':
        a, b = randint(0, 10), randint(0, 10)
    else:
        a, b = randint(0, 100), randint(1, 100)
        while a % b != 0:
            a, b = randint(0, 100), randint(1, 100)

    return f"{a} {operation} {b}"


def complicated_problem_generator():
    base = simple_problem_generator()
    result = int(eval(base))
    operation = choice(['+', '-'])

    if operation == '+':
        num = randint(0, 100)
    else:
        num = randint(0, abs(result))

    return f"{base} {operation} {num}"


class CameraWidget(QWidget):
    def __init__(self, game_screen):
        super().__init__()
        self.game_screen = game_screen

        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.video_label)
        self.setLayout(layout)

        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        with open("pose_landmarker_full.task", "rb") as f:
            model_buffer = f.read()

        base_options = python.BaseOptions(model_asset_buffer=model_buffer)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_poses=1
        )
        self.detector = vision.PoseLandmarker.create_from_options(options)

        self.jump_counter = JumpCounter()
        self.squat_counter = SquatCounter()
        self.bend_counter = BendCounter()

    def start(self):
        self.cap = cv2.VideoCapture(0)
        self.timer.start(30)

    def stop(self):
        self.timer.stop()
        if self.cap:
            self.cap.release()
            self.cap = None

    def update_frame(self):
        if not self.cap:
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self.detector.detect(mp_image)

        jumps = squats = bends = 0

        if result.pose_landmarks:
            landmarks = result.pose_landmarks[0]
            jumps = self.jump_counter.update(landmarks)
            squats = self.squat_counter.update(landmarks)
            bends = self.bend_counter.update(landmarks)

            self.game_screen.on_movements(jumps, squats, bends)

        h, w, ch = rgb.shape
        img = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        img = img.scaled(
            self.video_label.width(),
            self.video_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio
        )
        self.video_label.setPixmap(QPixmap.fromImage(img))


class MenuScreen(QWidget):
    def __init__(self, to_game, to_rules, exit_app):
        super().__init__()
        layout = QVBoxLayout()

        title = QLabel("Меню")
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_play = QPushButton("Играть")
        btn_rules = QPushButton("Правила")
        btn_exit = QPushButton("Выход")

        btn_play.setFont(button_font)
        btn_rules.setFont(button_font)
        btn_exit.setFont(button_font)

        btn_play.clicked.connect(to_game)
        btn_rules.clicked.connect(to_rules)
        btn_exit.clicked.connect(exit_app)

        layout.addWidget(title)
        layout.addWidget(btn_play)
        layout.addWidget(btn_rules)
        layout.addWidget(btn_exit)

        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)


class GameScreen(QWidget):
    def __init__(self, back_to_menu):
        super().__init__()

        self.score_counter = ScoreCounter()

        layout = QVBoxLayout()

        self.problem_label = QLabel()
        self.problem_label.setFont(problem_font)
        self.problem_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.score_label = QLabel("Очки: 0")
        self.score_label.setFont(problem_font)
        self.score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.camera = CameraWidget(self)
        self.camera.setMinimumSize(800, 600)

        btn_menu = QPushButton("В меню")
        btn_menu.setFont(back_to_menu_font)
        btn_menu.clicked.connect(back_to_menu)

        layout.addWidget(self.problem_label)
        layout.addWidget(self.score_label)
        layout.addWidget(self.camera, stretch=4)
        layout.addWidget(btn_menu)

        self.setLayout(layout)
        self.update_problem()

    def showEvent(self, event):
        self.score_counter.reset()
        self.score_label.setText("Очки: 0")
        self.camera.start()
        super().showEvent(event)

    def hideEvent(self, event):
        self.camera.stop()
        super().hideEvent(event)

    def update_problem(self):
        kind = choices(['simple', 'complicated'], weights=[70, 30])[0]
        problem = simple_problem_generator() if kind == 'simple' else complicated_problem_generator()
        self.problem_label.setText(problem)
        print(problem, "=", eval(problem))

    def on_movements(self, jumps, squats, bends):
        score = self.score_counter.update(jumps, squats, bends)
        self.score_label.setText(f"Очки: {score}")


class RulesScreen(QWidget):
    def __init__(self, back_to_menu):
        super().__init__()
        layout = QVBoxLayout()

        label = QLabel("Правила игры")
        label.setFont(title_font)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_menu = QPushButton("В меню")
        btn_menu.setFont(back_to_menu_font)
        btn_menu.clicked.connect(back_to_menu)

        layout.addWidget(label)
        layout.addWidget(btn_menu)
        self.setLayout(layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Move and Solve")
        self.showFullScreen()

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.menu = MenuScreen(self.show_game, self.show_rules, self.close)
        self.game = GameScreen(self.show_menu)
        self.rules = RulesScreen(self.show_menu)

        self.stack.addWidget(self.menu)
        self.stack.addWidget(self.game)
        self.stack.addWidget(self.rules)

    def show_menu(self):
        self.stack.setCurrentIndex(0)

    def show_game(self):
        self.game.update_problem()
        self.stack.setCurrentIndex(1)

    def show_rules(self):
        self.stack.setCurrentIndex(2)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()


app = QApplication(sys.argv)

font_id = QFontDatabase.addApplicationFont("static/Vincendo-Regular.otf")
font_family = QFontDatabase.applicationFontFamilies(font_id)[0]

title_font = QFont(font_family, 80)
button_font = QFont(font_family, 30)
problem_font = QFont(font_family, 30)
back_to_menu_font = QFont(font_family, 20)

window = MainWindow()
window.show()
app.exec()
