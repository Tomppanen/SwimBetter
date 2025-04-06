import subprocess

input_path = '/Users/tommimosconi/Downloads/GH010528.mov'
output_path = '/Users/tommimosconi/Downloads/GH010528.mp4'

subprocess.run([
    'ffmpeg',
    '-i', input_path,
    '-vcodec', 'libx264',
    '-acodec', 'aac',
    output_path
])