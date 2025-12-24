import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout, QStackedWidget)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFontDatabase, QFont, QImage, QPixmap
from PyQt6.QtWidgets import QHBoxLayout
from random import choice, choices, randint
import cv2
import logic as game_logic


class CameraWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.score_label = QLabel("Счёт:")
        self.score_label.setFont(QFont(font_settings, 40))
        self.score_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.correct_answer = 0
        self.answer_frozen = False
        self.frozen_points = 0
        self.current_points = 0

        self.verdict_label = QLabel("")
        self.verdict_label.setFont(QFont(font_settings, 20))
        self.verdict_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        left_panel = QVBoxLayout()
        left_panel.addWidget(self.score_label)
        left_panel.addWidget(self.verdict_label)
        left_panel.addStretch()

        main_layout = QHBoxLayout()
        main_layout.addLayout(left_panel, stretch=1)
        main_layout.addWidget(self.video_label, stretch=4)

        self.setLayout(main_layout)
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

    def start(self):
        if self.cap is None:
            self.cap = cv2.VideoCapture(0)
        QTimer.singleShot(300, lambda: self.timer.start(30))

    def stop(self):
        self.timer.stop()
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def update_frame(self):
        if self.cap is None:
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        frame, points, all_hands_up = game_logic.movements_counter(
            external_frame=frame,
            return_data=True
        )

        if self.answer_frozen:
            display_points = self.frozen_points
            self.score_label.setText(f"Счёт:\n{display_points}")
        else:
            self.current_points = points

            if points > self.correct_answer:
                self.freeze_answer(points)
                self.show_verdict(success=False, reason="Ответ больше нужного")
            elif all_hands_up:
                self.freeze_answer(points)
                success = points == self.correct_answer
                self.show_verdict(success)

            self.score_label.setText(f"Счёт:\n{self.current_points}")

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        img = QImage(frame.data, w, h, ch * w, QImage.Format.Format_RGB888)
        img = img.scaled(
            self.video_label.width(),
            self.video_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio
        )
        self.video_label.setPixmap(QPixmap.fromImage(img))

    def reset_round(self):
        self.answer_frozen = False
        self.frozen_points = 0
        self.current_points = 0

        game_logic.reset_counters()

        self.score_label.setText("Счёт:\n0")
        self.verdict_label.setText("")
        self.score_label.repaint()

    def freeze_answer(self, points):
        self.answer_frozen = True
        self.frozen_points = points

    def show_verdict(self, success, reason=None):
        if reason:
            text = (
                f"{reason}\n\n"
                f"Ответ команды: {self.frozen_points}\n"
                f"Правильный ответ: {self.correct_answer}"
            )
        elif success:
            text = (
                f"Верно!\n\n"
                f"Ответ команды: {self.frozen_points}\n"
                f"Правильный ответ: {self.correct_answer}"
            )
        else:
            text = (
                f"Неверно\n\n"
                f"Ответ команды: {self.frozen_points}\n"
                f"Правильный ответ: {self.correct_answer}"
            )

        self.verdict_label.setText(text)
        QTimer.singleShot(4000, self.start_new_round)

    def start_new_round(self):
        self.reset_round()

        parent = self.parent()
        while parent and not hasattr(parent, "update_problems"):
            parent = parent.parent()

        if parent:
            parent.update_problems()


class MenuScreen(QWidget):
    def __init__(self, switch_to_game, switch_to_rules, exit_app):
        super().__init__()
        layout = QVBoxLayout()
        title = QLabel("Меню")
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_play = QPushButton("Играть")
        btn_play.setFont(button_font)
        btn_rules = QPushButton("Правила")
        btn_rules.setFont(button_font)
        btn_exit = QPushButton("Выход")
        btn_exit.setFont(button_font)
        btn_play.clicked.connect(switch_to_game)
        btn_rules.clicked.connect(switch_to_rules)
        btn_exit.clicked.connect(exit_app)

        layout.addWidget(title)
        layout.addWidget(btn_play)
        layout.addWidget(btn_rules)
        layout.addWidget(btn_exit)

        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Move and Solve")
        self.showFullScreen()
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.menu_screen = MenuScreen(switch_to_game=self.show_game_screen, switch_to_rules=self.show_rules_screen,
                                      exit_app=self.close)
        self.game_screen = GameScreen(back_to_menu=self.show_menu_screen)
        self.rules_screen = RulesScreen(back_to_menu=self.show_menu_screen)

        self.stack.addWidget(self.menu_screen)
        self.stack.addWidget(self.game_screen)
        self.stack.addWidget(self.rules_screen)

        self.stack.setCurrentIndex(0)

    def show_menu_screen(self):
        self.stack.setCurrentIndex(0)

    def show_game_screen(self):
        self.game_screen.camera.reset_round()
        self.game_screen.update_problems()
        self.stack.setCurrentIndex(1)

    def show_rules_screen(self):
        self.stack.setCurrentIndex(2)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


def simple_problem_generator():
    types = ['+', '-', '*', '/']
    operation = choice(types)
    if operation == '+':
        number_1 = randint(0, 100)
        number_2 = randint(0, 100)
    elif operation == '-':
        number_1 = randint(50, 110)
        number_2 = randint(0, 50)
    elif operation == '*':
        number_1 = randint(0, 10)
        number_2 = randint(0, 10)
    else:
        number_1 = randint(0, 100)
        number_2 = randint(1, 100)
        while number_1 % number_2 != 0:
            number_1 = randint(0, 100)
            number_2 = randint(1, 100)

    return f'{number_1} {operation} {number_2}'


def complicated_problem_generator():
    default = simple_problem_generator()
    types = ['+', '-']
    operation = choice(types)
    base = int(eval(default))
    if operation == '+':
        number = randint(0, 100)
    else:
        if base < 0:
            base = abs(base)
        number = randint(0, base)

    return f'{default} {operation} {number}'


class GameScreen(QWidget):
    def __init__(self, back_to_menu):
        super().__init__()
        layout = QVBoxLayout()
        label = QLabel("Экран игры")
        label.setFont(title_font)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.problem1_label = QLabel()
        self.problem2_label = QLabel()
        self.problem1_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera = CameraWidget()
        self.camera.setMinimumSize(800, 600)

        btn_menu = QPushButton("В меню")
        btn_menu.setFont(back_to_menu_font)
        btn_menu.clicked.connect(back_to_menu)
        layout.addWidget(label)
        layout.addWidget(self.problem1_label)
        layout.addWidget(self.camera, stretch=4)
        layout.addWidget(btn_menu)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)
        self.update_problems()

    def showEvent(self, event):
        self.camera.reset_round()
        self.camera.start()
        super().showEvent(event)

    def hideEvent(self, event):
        self.camera.stop()
        super().hideEvent(event)

    def update_problems(self):
        self.camera.reset_round()

        choice_type = choices(['simple', 'complicated'], weights=[70, 30], k=1)[0]
        if choice_type == 'simple':
            problem_text = simple_problem_generator()
        else:
            problem_text = complicated_problem_generator()

        self.problem1_label.setFont(problem_font)
        self.problem1_label.setText(problem_text)
        self.problem1_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        answer = int(eval(problem_text))
        self.camera.correct_answer = answer


class RulesScreen(QWidget):
    def __init__(self, back_to_menu):
        super().__init__()
        layout = QVBoxLayout()

        title = QLabel("Правила игры")
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        rules_text = QLabel(
            "Ученики разбиваются на несколько команд, в каждой из которых должно быть 3 человека.\n\n"
            "По очереди команды подходят к камере и получают пример, который необходимо решить. "
            "В примере используются такие вычислительные операции как сложение, вычитание, умножение и деление.\n\n"
            "Ученики, принимая различные позы, набирают очки:\n"
            "• Прыжок — 1 очко\n"
            "• Наклон — 5 очков\n"
            "• Приседание — 10 очков\n\n"
            "Дети должны набрать такое количество очков, которое является ответом на полученный пример.\n\n"
            "Нюансы игры:\n"
            "• Наклоны выполняются боком, а приседания глубоко.\n"
            "• Если количество очков в какой-то момент превысило правильный ответ, "
            "пример автоматически аннулируется и команда не получает балл.\n"
            "• После того как команда набрала нужное количество очков, ответ необходимо подтвердить — "
            "все члены команды должны поднять руки вверх.\n\n"
            "Если команда правильно решила пример, она получает балл. "
            "Команды соревнуются между собой, повышая мотивацию к игре."
        )

        rules_text.setFont(QFont(font_settings, 18))
        rules_text.setWordWrap(True)
        rules_text.setAlignment(Qt.AlignmentFlag.AlignTop)

        btn_menu = QPushButton("В меню")
        btn_menu.setFont(back_to_menu_font)
        btn_menu.clicked.connect(back_to_menu)

        layout.addWidget(title)
        layout.addWidget(rules_text)
        layout.addStretch()
        layout.addWidget(btn_menu)

        self.setLayout(layout)


app = QApplication(sys.argv)
font_id = QFontDatabase.addApplicationFont("static/Vincendo-Regular.otf")
font_settings = QFontDatabase.applicationFontFamilies(font_id)[0]
title_font = QFont(font_settings, 60)
button_font = QFont(font_settings, 30)
problem_font = QFont(font_settings, 40)
back_to_menu_font = QFont(font_settings, 20)

w = MainWindow()
w.show()
app.exec()