import os
import json
import numpy as np
import subprocess
import cv2
import cred

input_folder = cred.path
all_files = [f for f in os.listdir(input_folder) if f.endswith(".json")]

for filename in all_files:
    filepath = os.path.join(input_folder, filename)
    with open(filepath) as f:
        data = json.load(f)

    left_time = np.array([entry["leftTime"] for entry in data])
    right_time = np.array([entry["rightTime"] for entry in data])
    left_total = np.clip(np.array([entry["leftTotal"] for entry in data]), -8, 8)
    right_total = np.clip(np.array([entry["rightTotal"] for entry in data]), -8, 8)

    window_ms = 1000  
    target_fps = 30
    frame_interval_ms = 1000 / target_fps

    max_time = int(left_time[-1])
    frame_times = np.arange(0, max_time, frame_interval_ms).astype(int)

    left_interp = np.interp(frame_times, left_time, left_total)
    right_interp = np.interp(frame_times, right_time, right_total)

    width, height = 1280, 720
    ymin, ymax = -8, 8

    output_dir = cred.opath
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"st_{os.path.splitext(filename)[0]}.mp4")

    ffmpeg_cmd = [
        'ffmpeg', '-y',
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-pix_fmt', 'bgr24',
        '-s', f'{width}x{height}',
        '-r', str(target_fps),
        '-i', '-',
        '-an',
        '-vcodec', 'libx264',
        '-pix_fmt', 'yuv420p',
        output_file
    ]
    pipe = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

    for i, t in enumerate(frame_times):
        img = np.ones((height, width, 3), dtype=np.uint8) * 255
        start_time = max(0, t - window_ms)
        mask = (frame_times >= start_time) & (frame_times <= t)
        time_window = frame_times[mask]
        left_window = left_interp[mask]
        right_window = right_interp[mask]

        if len(time_window) < 2:
            continue

        # Normalize for drawing
        time_sec = (time_window - time_window[0]) / 1000
        time_norm = np.interp(time_sec, (0, time_sec[-1]), (100, width - 100))
        left_norm = np.interp(left_window, (ymin, ymax), (height - 100, 100))
        right_norm = np.interp(right_window, (ymin, ymax), (height - 100, 100))

        # Draw lines
        for j in range(1, len(time_norm)):
            pt1 = (int(time_norm[j - 1]), int(left_norm[j - 1]))
            pt2 = (int(time_norm[j]), int(left_norm[j]))
            cv2.line(img, pt1, pt2, (255, 0, 0), 2)

            pt1 = (int(time_norm[j - 1]), int(right_norm[j - 1]))
            pt2 = (int(time_norm[j]), int(right_norm[j]))
            cv2.line(img, pt1, pt2, (0, 0, 255), 2)

        # Labels
        cv2.putText(img, "Left (blue)", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        cv2.putText(img, "Right (red)", (200, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(img, f"Time: {t/1000:.2f}s", (width - 250, height - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,0), 2)
        filename_text = os.path.splitext(filename)[0]
        cv2.putText(img, filename_text, (500, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

        for val in np.linspace(ymin, ymax, 5):
            y_tick = int(np.interp(val, (ymin, ymax), (height - 100, 100)))
            cv2.line(img, (90, y_tick), (100, y_tick), (0, 0, 0), 1)
            cv2.putText(img, f"{val:.1f}", (40, y_tick + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)


        pipe.stdin.write(img.tobytes())

    pipe.stdin.close()
    pipe.wait()
    print(f"Video saved as: {output_file}")