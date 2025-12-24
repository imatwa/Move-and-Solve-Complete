import cv2
import mediapipe as mp
from Detectors import JumpCounter, SquatCounter, BendCounter, HandUpDetector
from mediapipe.tasks.python import vision
from mediapipe.tasks import python

MODEL_PATH = "pose_landmarker_full.task"

with open(MODEL_PATH, "rb") as f:
    model_buffer = f.read()

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose


def create_detector():
    base_options = python.BaseOptions(model_asset_buffer=model_buffer)
    options = vision.PoseLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO,
        num_poses=3,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5
    )
    return vision.PoseLandmarker.create_from_options(options)


detector = create_detector()
time_cadr = 0

people_data = []
all_hands_up = False
round_points = 0


def reset_counters():
    global people_data, all_hands_up, round_points, time_cadr, detector

    people_data = []
    all_hands_up = False
    round_points = 0
    time_cadr = 0

    detector.close()
    detector = create_detector()


def movements_counter(external_frame=None, return_data=False):
    global people_data, all_hands_up, time_cadr, round_points, detector

    if external_frame is None:
        return None, round_points, False

    frame = external_frame
    time_cadr += 1

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

    detect_result = detector.detect_for_video(mp_image, time_cadr)

    total_jumps = 0
    total_squats = 0
    total_bends = 0
    hands_up_count = 0

    if detect_result.pose_landmarks:
        num_people = len(detect_result.pose_landmarks)

        while len(people_data) < num_people:
            people_data.append({
                'jump_counter': JumpCounter(),
                'squat_counter': SquatCounter(),
                'bend_counter': BendCounter(),
                'hand_up_detector': HandUpDetector(),
            })

        for person_id in range(num_people):
            landmarks = detect_result.pose_landmarks[person_id]
            person = people_data[person_id]

            jumps = person['jump_counter'].update(landmarks)
            squats = person['squat_counter'].update(landmarks)
            bends = person['bend_counter'].update(landmarks)

            total_jumps += jumps
            total_squats += squats
            total_bends += bends

            if person['hand_up_detector'].detect_hand_up(landmarks):
                hands_up_count += 1

            from mediapipe.framework.formats import landmark_pb2
            lm_proto = landmark_pb2.NormalizedLandmarkList()
            lm_proto.landmark.extend([
                landmark_pb2.NormalizedLandmark(
                    x=l.x, y=l.y, z=l.z, visibility=l.visibility
                ) for l in landmarks
            ])

            mp_drawing.draw_landmarks(
                frame,
                lm_proto,
                mp_pose.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2),
                mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2)
            )

        frame_points = total_jumps + (5 * total_bends) + (10 * total_squats)

        if frame_points > round_points:
            round_points = frame_points

        all_hands_up = (num_people > 0 and hands_up_count == num_people)

    else:
        all_hands_up = False

    if return_data:
        return frame, round_points, all_hands_up

    cv2.imshow("Camera", frame)


if __name__ == "__main__":
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        movements_counter(frame)
        if cv2.waitKey(1) == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    detector.close()
