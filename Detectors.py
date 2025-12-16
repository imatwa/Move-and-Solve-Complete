import numpy as np

class JumpCounter:
    def __init__(self):
        # Прыжки
        self.jump_count = 0

        # Сейчас в воздухе?
        self.is_in_air = False

        # Высота, когда стоит на земле
        self.start_height = None

        # Пороги для определения прыжка
        # Минимальная высота прыжка
        self.JUMP_HEIGHT_THRESHOLD = 0.04

        # Порог для определения, что человек на земле
        self.GROUND_HEIGHT_THRESHOLD = 0.01

    def calculate_hip_height(self, landmarks):
        # Левое бедро
        left_hip = landmarks[23]

        # Правое бедро
        right_hip = landmarks[24]

        # Среднее положение бедер по y-координате
        hip_y = (left_hip.y + right_hip.y) / 2
        return hip_y

    def detect_jump(self, current_height):
        # Если это первый кадр, иницилизируем начальную высоту
        if self.start_height is None:
            self.start_height = current_height
            return False

        # Находим разницу высот
        height_diff = self.start_height - current_height

        # Если человек стоит на земле, обновляем начанльную высоту
        if abs(height_diff) < self.GROUND_HEIGHT_THRESHOLD:
            self.start_height = current_height
            self.is_in_air = False

        # Если человек был не в воздухе (то есть этот прыжок еще не был посчитан)
        # и сейчас он находится на высоте прыжка,
        # то возвращаем, что человек находится в прыжке
        if not self.is_in_air and height_diff > self.JUMP_HEIGHT_THRESHOLD:
            self.is_in_air = True
            return True

        # Если человек находился в воздухе и сейчас он находится на земле,
        # то записываем, что он находится не в прыжке
        if self.is_in_air and abs(height_diff) < self.GROUND_HEIGHT_THRESHOLD:
            self.is_in_air = False

        # Возвращаем, что человек не в прыжке, если условие того,
        # что он в прыжке, не выполнилось
        return False

    def update(self, landmarks):
        # Находим высоту, на которой сейчас человек
        current_height = self.calculate_hip_height(landmarks)

        # Если человек новом (не посчитанном) прыжке,
        # то добавляем его к итоговому кол-ву
        if self.detect_jump(current_height):
            self.jump_count += 1
        return self.jump_count

class SquatCounter:
    def __init__(self):
        # Счетчик приседаний
        self.squat_count = 0

        # Сейчас в приседе?
        self.is_down = False

        # Пороги для определения приседа
        # Максимальный угол в коленях в приседе
        self.SQUAT_ANGLE_THRESHOLD = 100

        # Минимальный угол в коленях, когда человек стоит
        self.STAND_ANGLE_THRESHOLD = 160

    def calculate_angle(self, a, b, c):
        # Получаем координаты точек
        a = np.array([a.x, a.y])
        b = np.array([b.x, b.y])
        c = np.array([c.x, c.y])

        # Вычислем вектора от колена до лодыжки и от колена до бедра
        ba = a - b
        bc = c - b

        # Находим косинус угла, с помощью деления скалярного
        # произведения векторов на длины этих векторов
        cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))

        # Считаем угл с помощью арккосинуса и возращаем его в градусах
        angle = np.arccos(cos_angle)
        return np.degrees(angle)

    def update(self, landmarks):
        # Угол в левом колене
        left_knee_angle = self.calculate_angle(landmarks[23], landmarks[25], landmarks[27])

        # Угол в правом колене
        right_knee_angle = self.calculate_angle(landmarks[24], landmarks[26], landmarks[28])

        # Находим усредненное значение углов в коленях
        sr_angle = (left_knee_angle + right_knee_angle) / 2

        # Если человек был не в приседе, а сейчас угол в коленях меньше максимального угла
        # в коленях при приседе, то меняеем статус на "в приседе"
        if not self.is_down and sr_angle < self.SQUAT_ANGLE_THRESHOLD:
            self.is_down = True

        # Если человек был в приседе, а сейчас угол в коленях больше минимального угла
        # в коленях, когда человек стоит, то меняем статус на "не в приседе" и засчитываем приседание
        elif self.is_down and sr_angle > self.STAND_ANGLE_THRESHOLD:
            self.is_down = False
            self.squat_count += 1

        return self.squat_count

class BendCounter:
    def __init__(self):
        # Счетчик Наклонов
        self.bend_count = 0

        # Сейчас в наклоне?
        self.is_bend = False

        # Пороги для определения наклона
        # Максимальный угол в бедрах при наклоне
        self.BEND_HIP_ANGLE_THRESHOLD = 70

        # Минимальный угол в коленях при наклоне
        self.BEND_KNEE_ANGLE_THRESHOLD = 150

        # Минимальный угол в бедрах, когда человек стоит
        self.STAND_ANGLE_THRESHOLD = 100

    def calculate_angle(self, a, b, c):
        # Получаем координаты точек
        a = np.array([a.x, a.y])
        b = np.array([b.x, b.y])
        c = np.array([c.x, c.y])

        # Вычислем вектора от плеча до бедра и от бедра до колена (для угла в бедрах)
        # Вычислем вектора от колена до лодыжки и от колена до бедра (для угла в коленях)
        ba = a - b
        bc = c - b

        # Находим косинус угла, с помощью деления скалярного
        # произведения векторов на длины этих векторов
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))

        # Считаем угл с помощью арккосинуса и возращаем его в градусах
        angle = np.arccos(cosine_angle)
        return np.degrees(angle)

    def update(self, landmarks):
        # Угол в левом бедре
        left_hip_angle = self.calculate_angle(landmarks[11], landmarks[23], landmarks[25])

        # Угол в правом бедре
        right_hip_angle = self.calculate_angle(landmarks[12], landmarks[24], landmarks[26])

        # Находим усредненное значение углов в бедрах
        avg_hip_angle = (left_hip_angle + right_hip_angle) / 2

        # Угол в левом колене
        left_knee_angle = self.calculate_angle(landmarks[23], landmarks[25], landmarks[27])

        # Угол в правом колене
        right_knee_angle = self.calculate_angle(landmarks[24], landmarks[26], landmarks[28])

        # Находим усредненное значение углов в коленях
        avg_knee_angle = (left_knee_angle + right_knee_angle) / 2

        # Если человек был не в наклоне, а сейчас угол в бедрах меньше максимального угла
        # в бедрах при наклоне и угол в коленях больше минимального угла в коленях при наклоне,
        # то меняеем статус на "в наклоне"
        if (not self.is_bend and avg_hip_angle < self.BEND_HIP_ANGLE_THRESHOLD
                and avg_knee_angle > self.BEND_KNEE_ANGLE_THRESHOLD):
            self.is_bend = True

        # Если человек был в наклоне, а сейчас угол в бедрах больше минимального угла
        # в бедрах, когда человек стоит, то меняем статус на "не в наклоне" и засчитываем наклон
        elif self.is_bend and avg_hip_angle > self.STAND_ANGLE_THRESHOLD:
            self.is_bend = False
            self.bend_count += 1

        return self.bend_count

class HandUpDetector:
    def __init__(self):
        # Пороги для определения поднятой руки
        # Рука считается поднятой, если запястье выше плеча на это число
        self.HAND_UP_THRESHOLD = 0.1

    def detect_right_hand_up(self, landmarks):
        # Правое плечо
        right_shoulder = landmarks[12]

        # Правое запястье
        right_wrist = landmarks[16]

        # Проверяем, что запястье выше плеча
        return right_wrist.y < right_shoulder.y - self.HAND_UP_THRESHOLD


    def detect_left_hand_up(self, landmarks):
        # Левое плечо
        left_shoulder = landmarks[11]

        # Левое запястье
        left_wrist = landmarks[15]

        # Проверяем, что запястье выше плеча
        return left_wrist.y < left_shoulder.y - self.HAND_UP_THRESHOLD

    def detect_hand_up(self, landmarks):
        # Если одна из рук поднята, то возвращается True
        return self.detect_right_hand_up(landmarks) or self.detect_left_hand_up(landmarks)