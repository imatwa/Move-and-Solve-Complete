import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks import python
from Detectors import JumpCounter, SquatCounter, BendCounter, HandUpDetector
from mediapipe.framework.formats import landmark_pb2

class GestureEngine:
    def __init__(self, model_path="pose_landmarker_full.task"):
        with open(model_path, "rb") as f:
            model_buffer = f.read()

        base_options = python.BaseOptions(model_asset_buffer=model_buffer)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_poses=3,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )

        self.detector = vision.PoseLandmarker.create_from_options(options)
        self.people_data = []
        self.all_hands_up = False

    def process_frame(self, frame_rgb):
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=frame_rgb
        )

        result = self.detector.detect(mp_image)

        total_jumps = total_squats = total_bends = 0
        hands_up_count = 0

        if result.pose_landmarks:
            if len(self.people_data) != len(result.pose_landmarks):
                self.people_data = [
                    {
                        "jump": JumpCounter(),
                        "squat": SquatCounter(),
                        "bend": BendCounter(),
                        "hand": HandUpDetector()
                    }
                    for _ in result.pose_landmarks
                ]

            for i, landmarks in enumerate(result.pose_landmarks):
                pdata = self.people_data[i]

                total_jumps += pdata["jump"].update(landmarks)
                total_squats += pdata["squat"].update(landmarks)
                total_bends += pdata["bend"].update(landmarks)

                if pdata["hand"].detect_hand_up(landmarks):
                    hands_up_count += 1

        all_up = (
            len(result.pose_landmarks) > 0
            and hands_up_count == len(result.pose_landmarks)
        )

        points = total_jumps + 5 * total_bends + 10 * total_squats

        return {
            "jumps": total_jumps,
            "squats": total_squats,
            "bends": total_bends,
            "points": points,
            "all_hands_up": all_up
        }

    def close(self):
        self.detector.close()
