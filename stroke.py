import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import subprocess
from io import BytesIO

matplotlib.use("Agg")

with open("Force vs Time Chart.json") as f:
    data = json.load(f)

left_time = np.array([entry["leftTime"] for entry in data])
right_time = np.array([entry["rightTime"] for entry in data])
left_total = np.array([entry["leftTotal"] for entry in data])
right_total = np.array([entry["rightTotal"] for entry in data])

window_ms = 1000  # Scrolling window width
target_fps = 30
frame_interval_ms = 1000 / target_fps

max_time = int(left_time[-1])
frame_times = np.arange(0, max_time, frame_interval_ms).astype(int)

left_interp = np.interp(frame_times, left_time, left_total)
right_interp = np.interp(frame_times, right_time, right_total)

dpi = 100
figsize = (10, 5)
width, height = int(figsize[0] * dpi), int(figsize[1] * dpi)
ymin = min(np.min(left_total), np.min(right_total)) * 1.1
ymax = max(np.max(left_total), np.max(right_total)) * 1.1

ffmpeg_cmd = [
    "ffmpeg", "-y",
    "-f", "image2pipe",
    "-vcodec", "png",
    "-r", str(target_fps),
    "-i", "-",
    "-vcodec", "libx264",
    "-pix_fmt", "yuv420p",
    "scrolling_total_force_realtime.mp4"
]
pipe = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

for i, t in enumerate(frame_times):
    ax.clear()
    start_time = max(0, t - window_ms)
    time_window = frame_times[(frame_times >= start_time) & (frame_times <= t)]
    left_window = left_interp[(frame_times >= start_time) & (frame_times <= t)]
    right_window = right_interp[(frame_times >= start_time) & (frame_times <= t)]

    ax.plot(time_window / 1000, left_window, color="blue", label="Left")
    ax.plot(time_window / 1000, right_window, color="red", label="Right")
    ax.set_xlim(start_time / 1000, t / 1000)
    ax.set_ylim(ymin, ymax)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Total Force")
    ax.set_title("Real-Time Stroke Force")
    ax.legend(loc="upper right")

    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=dpi)
    pipe.stdin.write(buf.getvalue())
    buf.close()

pipe.stdin.close()
pipe.wait()
plt.close(fig)

print(f"Video saved as: scrolling_total_force_realtime.mp4")