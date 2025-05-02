from flask import Flask, render_template
from flask_cors import CORS
from flask_sock import Sock
import ssl
import whisper
import io
import numpy as np
import torch
import soundfile as sf

app = Flask(__name__,
    template_folder='./www',
    static_folder='./www',
    static_url_path='/'
)
CORS(app)  # 모든 도메인에서의 접근을 허용
sock = Sock(app)
model = whisper.load_model("base")

@app.route('/')
def index():
    return render_template('index.html')

@sock.route('/audio')
def handle_audio(ws):
    while True:
        data = ws.receive()
        if data is None:
            break
        
        audio_stream = io.BytesIO(data)
        audio_stream.seek(0)  # 스트림의 시작으로 이동

        try:
            # 오디오 데이터를 .wav 파일로 저장
            with open('received_audio.wav', 'wb') as f:
                f.write(audio_stream.read())

            # Whisper 모델에 .wav 파일을 전달하여 인식
            result = model.transcribe('received_audio.wav')
            ws.send(result['text'])
        except Exception as e:
            print(f'Error: {e}')
            ws.send('Error processing audio')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
