# GitHub 협업 스프린트 실습 시나리오

이 문서는 Flask 서버와 React 프론트엔드를 활용하여 4명의 개발자가 GitHub으로 협업하는 스프린트 실습 시나리오를 제공합니다. 모든 단계는 초보자도 쉽게 따라할 수 있도록 구성되었습니다.

## 목차
1. [사전 준비](#1-사전-준비)
2. [프로젝트 초기화 (PM: dev1)](#2-프로젝트-초기화-pm-dev1)
3. [개발자 환경 설정](#3-개발자-환경-설정)
4. [스프린트 계획 및 이슈 등록](#4-스프린트-계획-및-이슈-등록)
5. [개발 및 협업 워크플로우](#5-개발-및-협업-워크플로우)
6. [코드 충돌 해결 시나리오](#6-코드-충돌-해결-시나리오)
7. [프로젝트 빌드 및 최종 배포](#7-프로젝트-빌드-및-최종-배포)

## 1. 사전 준비

### 1.1 Docker 컨테이너 접속 정보
- **dev1 (PM)**: `ssh dev1@localhost -p 22` (비밀번호: dev1)
- **dev2**: `ssh dev2@localhost -p 22` (비밀번호: dev2)
- **dev3**: `ssh dev3@localhost -p 22` (비밀번호: dev3)
- **dev4**: `ssh dev4@localhost -p 22` (비밀번호: dev4)

### 1.2 GitHub 계정 및 개인 액세스 토큰
1. GitHub 계정이 없다면 [GitHub 회원가입](https://github.com/signup)에서 생성합니다.
2. [GitHub 개인 액세스 토큰 생성](https://github.com/settings/tokens):
   - GitHub 웹사이트 우측 상단 프로필 아이콘 → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - "Generate new token" 클릭 → "Generate new token (classic)" 선택
   - Note: "GitHub 협업 실습 토큰"
   - 권한 설정: `repo`, `workflow` 체크
   - "Generate token" 클릭 → 생성된 토큰을 안전한 곳에 복사해 둡니다.

## 2. 프로젝트 초기화 (PM: dev1)

### 2.1 GitHub 저장소 생성 (웹 인터페이스에서 수행)

1. GitHub에 로그인 → "+" 아이콘 클릭 → "New repository" 선택
2. 저장소 설정:
   - Repository name: `audio-transcription-app`
   - Description: `Whisper를 활용한 실시간 음성 인식 애플리케이션`
   - Visibility: Public 또는 Private 선택
   - Initialize this repository with: README 체크
   - .gitignore: Node 선택
   - License: MIT 선택
3. "Create repository" 클릭

### 2.2 GitHub Actions Secrets 설정 (웹 인터페이스에서 수행)

1. 생성된 저장소 페이지 → "Settings" 탭 → 좌측 "Secrets and variables" → "Actions"
2. "New repository secret" 클릭
3. Name: `NGROK_AUTH_TOKEN`
4. Value: ngrok에서 발급받은 인증 토큰
5. "Add secret" 클릭

### 2.3 GitHub 프로젝트 생성 (웹 인터페이스에서 수행)

1. GitHub 저장소 페이지 → "Projects" 탭 → "Create project" 클릭
2. "Board" 템플릿 선택 → "Create" 클릭
3. 프로젝트 이름: "음성인식 앱 스프린트 1"
4. 기본 생성된 칼럼: "Todo", "In progress", "Done"으로 유지

### 2.4 브랜치 생성 (웹 인터페이스에서 수행)

1. GitHub 저장소 페이지 → "Code" 탭 → 브랜치 선택 드롭다운 클릭
2. "New branch" 입력란에 `develop` 입력 → "Create branch: develop" 클릭

### 2.5 PM 초기 개발 환경 설정 (dev1 계정)

```bash
# dev1 사용자로 Docker 컨테이너에 접속 (VSCode Remote-SSH 또는 PuTTY 사용)
# 작업 디렉토리 생성
mkdir -p ~/audio-app
cd ~/audio-app

# 저장소 클론
git clone https://github.com/{GitHub사용자명}/audio-transcription-app.git .
# 프롬프트에 GitHub 사용자명과 개인 액세스 토큰 입력

# develop 브랜치로 전환
git checkout develop

# 프로젝트 디렉토리 구조 생성
mkdir -p backend/www frontend

# Flask 백엔드 코드 작성
cat > backend/app.py << 'EOF'
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
EOF

# 프론트엔드 초기화 (React)
cd ~/audio-app/frontend
npx create-react-app audio-client

# 백엔드 www 디렉토리 생성
mkdir -p ~/audio-app/backend/www

# 초기 index.html 생성
cat > ~/audio-app/backend/www/index.html << 'EOF'
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>음성 인식 앱</title>
</head>
<body>
    <h1>음성 인식 앱 - 초기 설정 완료</h1>
    <p>프로젝트가 성공적으로 초기화되었습니다!</p>
</body>
</html>
EOF

# GitHub Actions CI/CD 워크플로우 설정
mkdir -p ~/audio-app/.github/workflows

cat > ~/audio-app/.github/workflows/ci-cd.yml << 'EOF'
name: CI/CD 파이프라인

on:
  push:
    branches: [ main, develop, feature/* ]
  pull_request:
    branches: [ main, develop ]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Python 설정
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    
    - name: Python 의존성 설치
      run: |
        python -m pip install --upgrade pip
        pip install flask flask-cors flask-sock torch soundfile numpy
        pip install git+https://github.com/openai/whisper.git
    
    - name: Node.js 설정
      uses: actions/setup-node@v2
      with:
        node-version: '18'
    
    - name: 프론트엔드 의존성 설치
      run: |
        cd frontend/audio-client
        npm install
    
    - name: 프론트엔드 빌드
      run: |
        cd frontend/audio-client
        npm run build
        mkdir -p ../../backend/www
        cp -r build/* ../../backend/www/
    
    - name: ngrok 설치
      run: |
        wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
        tar xvzf ngrok-v3-stable-linux-amd64.tgz
        chmod +x ngrok
    
    - name: 애플리케이션 실행 및 ngrok 터널 열기
      env:
        NGROK_AUTH_TOKEN: ${{ secrets.NGROK_AUTH_TOKEN }}
      run: |
        ./ngrok config add-authtoken $NGROK_AUTH_TOKEN
        cd backend
        python app.py &
        sleep 5
        ../ngrok http 3000 --log=stdout > ngrok.log &
        sleep 5
        NGROK_URL=$(grep -o 'https://.*\.ngrok-free\.app' ngrok.log | head -n 1)
        echo "애플리케이션이 다음 URL에서 5분간 접속 가능합니다: $NGROK_URL"
        echo "NGROK_URL=$NGROK_URL" >> $GITHUB_ENV
    
    - name: 테스트 URL 출력
      run: |
        echo "애플리케이션 URL: ${{ env.NGROK_URL }}"
        echo "5분 후 URL은 만료됩니다. 테스트를 서둘러 진행해 주세요."
        sleep 300
EOF

# 백엔드 요구사항 명시
cat > ~/audio-app/backend/requirements.txt << 'EOF'
flask
flask-cors
flask-sock
openai-whisper
torch
soundfile
numpy
EOF

# 변경사항 커밋
cd ~/audio-app
git add .
git commit -m "초기 프로젝트 구조 설정 및 CI/CD 워크플로우 구성"
git push origin develop

# main 브랜치에 초기 프로젝트 구조 병합 (중요: 초기 설정만 병합)
git checkout main
git merge develop
git push origin main
```

## 3. 개발자 환경 설정

### 3.1 개발자 공통 환경 설정 (모든 개발자)

> **참고**: 각 개발자(dev1~dev4)는 동일한 과정을 통해 개발 환경을 설정합니다.

```bash
# 개발자 계정으로 Docker 컨테이너에 접속 (VSCode Remote-SSH 사용)

# 작업 디렉토리 생성
mkdir -p ~/audio-app
cd ~/audio-app

# 저장소 클론
git clone https://github.com/{GitHub사용자명}/audio-transcription-app.git .
# 프롬프트에 GitHub 사용자명과 개인 액세스 토큰 입력

# develop 브랜치로 전환
git checkout develop

# Node.js 의존성 설치 (프론트엔드 개발자만 필요)
cd ~/audio-app/frontend/audio-client
npm install

# VS Code에서 프로젝트 열기
# VS Code Remote-SSH 확장을 사용하여 각 개발자 계정에 접속 후
# "File" > "Open Folder" > ~/audio-app 선택
```

## 4. 스프린트 계획 및 이슈 등록

### 4.1 스프린트 계획 회의 (PM: dev1)

PM은 팀원들과 함께 스프린트 계획 회의를 진행하고, 다음과 같이 작업을 할당합니다.

1. **dev1 (PM)**: 
   - 프로젝트 초기화 및 CI/CD 설정
   - 최종 통합 및 배포 감독

2. **dev2**:
   - 백엔드 설정 및 오디오 처리 기능 구현
   - Flask 서버 최적화

3. **dev3**:
   - 프론트엔드 기본 구조 설정
   - React 앱 UI 컴포넌트 구현

4. **dev4**:
   - 프론트엔드-백엔드 통합 및 WebSocket 연결
   - 테스트 및 문서화

### 4.2 GitHub 이슈 등록 (PM: dev1, 웹 인터페이스에서 수행)

1. GitHub 저장소 페이지 → "Issues" 탭 → "New issue" 클릭
2. 다음 이슈 생성:

**이슈 1: 백엔드 설정 및 오디오 처리 기능 구현**
- 제목: "백엔드 설정 및 오디오 처리 기능 구현"
- 설명:
  ```
  Flask 서버를 설정하고 WebSocket을 통한 오디오 처리 기능을 구현합니다.
  
  할 일:
  - Flask 서버 구성 최적화
  - Whisper 모델 설정 확인
  - 오디오 스트림 처리 로직 검증
  - 오류 처리 및 로깅 추가
  
  담당자: @dev2
  ```
- Assignee: dev2
- Labels: "backend", "enhancement"
- Project: "음성인식 앱 스프린트 1" 선택 → "Todo" 상태로 설정

**이슈 2: 프론트엔드 기본 구조 설정**
- 제목: "프론트엔드 기본 구조 설정"
- 설명:
  ```
  React 앱의 기본 구조를 설정하고 UI 컴포넌트를 구현합니다.
  
  할 일:
  - React 프로젝트 설정
  - AppBar 및 UI 컴포넌트 구현
  - 레이아웃 및 스타일링
  
  담당자: @dev3
  ```
- Assignee: dev3
- Labels: "frontend", "enhancement"
- Project: "음성인식 앱 스프린트 1" 선택 → "Todo" 상태로 설정

**이슈 3: 프론트엔드-백엔드 통합 및 WebSocket 연결**
- 제목: "프론트엔드-백엔드 통합 및 WebSocket 연결"
- 설명:
  ```
  React 앱과 Flask 서버 간의 WebSocket 연결을 구현합니다.
  
  할 일:
  - WebSocket 연결 구현
  - 오디오 녹음 및 전송 기능
  - 응답 처리 및 표시
  - 테스트 및 문서화
  
  담당자: @dev4
  ```
- Assignee: dev4
- Labels: "integration", "enhancement"
- Project: "음성인식 앱 스프린트 1" 선택 → "Todo" 상태로 설정

### 4.3 이슈 알림 (PM: dev1)

PM은 각 팀원에게 할당된 이슈를 이메일 또는 메시지로 알립니다. GitHub에서는 자동으로 이슈가 할당되면 해당 개발자에게 이메일을 보냅니다.

## 5. 개발 및 협업 워크플로우

### 5.1 개발자별 브랜치 생성 및 작업

#### 5.1.1 백엔드 개발자 (dev2) 작업

```bash
# dev2 계정으로 접속 후
cd ~/audio-app

# 현재 develop 브랜치인지 확인
git branch

# 기능 브랜치 생성 및 전환
git checkout -b feature/backend-setup

# 이슈 상태 변경 (웹 인터페이스에서)
# "음성인식 앱 스프린트 1" 프로젝트에서 해당 이슈를 "In progress"로 드래그

# 백엔드 코드 수정 (VS Code에서 편집)
# app.py 파일을 열고 주석 추가 및 로깅 기능 개선

cd ~/audio-app/backend
# 코드 검증 및 테스트
conda activate whisper_env
python app.py
# 브라우저에서 http://localhost:3000 접속하여 테스트

# 변경사항 커밋
git add .
git commit -m "백엔드 설정 최적화 및 로깅 추가"
git push origin feature/backend-setup

# Pull Request 생성 (웹 인터페이스에서)
# GitHub 저장소 페이지 → "Pull requests" 탭 → "New pull request"
# base: develop ← compare: feature/backend-setup 선택
# 제목: "백엔드 설정 및 오디오 처리 기능 구현"
# 설명에 "Closes #1" 추가하여 이슈 연결
# "Create pull request" 클릭

# 이슈 상태 변경 (웹 인터페이스에서)
# "음성인식 앱 스프린트 1" 프로젝트에서 해당 이슈를 "Done"으로 드래그
```

#### 5.1.2 프론트엔드 기본 구조 개발자 (dev3) 작업

```bash
# dev3 계정으로 접속 후
cd ~/audio-app

# 기능 브랜치 생성 및 전환
git checkout -b feature/frontend-setup

# 이슈 상태 변경 (웹 인터페이스에서)
# "음성인식 앱 스프린트 1" 프로젝트에서 해당 이슈를 "In progress"로 드래그

# 프론트엔드 코드 작성
cd ~/audio-app/frontend/audio-client

# App.js 파일 수정
cat > src/App.js << 'EOF'
import React, { useState, useRef, useEffect } from 'react';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Container from '@mui/material/Container';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import TextField from '@mui/material/TextField';
import './App.css';

function App() {
  // 현재 접속한 URL을 기반으로 WebSocket URL 자동 생성
  const getDefaultWebsocketUrl = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    return `${protocol}//${host}/audio`;
  };

  const [isRecording, setIsRecording] = useState(false);
  const [transcriptions, setTranscriptions] = useState([]);
  const [websocketUrl, setWebsocketUrl] = useState(getDefaultWebsocketUrl());
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const socketRef = useRef(null);

  const handleWebSocketUrlChange = (event) => {
    setWebsocketUrl(event.target.value);
  };

  const handleStartRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorderRef.current = new MediaRecorder(stream);

    mediaRecorderRef.current.ondataavailable = (event) => {
      audioChunksRef.current.push(event.data);
    };

    mediaRecorderRef.current.onstop = () => {
      sendAudioData();
    };

    mediaRecorderRef.current.start();
    setIsRecording(true);
  };

  const handleStopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const sendAudioData = () => {
    const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
    const reader = new FileReader();
    reader.onloadend = () => {
      const audioArrayBuffer = reader.result;
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.send(audioArrayBuffer);
      }
      audioChunksRef.current = [];
    };
    reader.readAsArrayBuffer(audioBlob);
  };

  const setupWebSocket = () => {
    socketRef.current = new WebSocket(websocketUrl);

    socketRef.current.onopen = () => {
      console.log('WebSocket is connected.');
    };

    socketRef.current.onmessage = (event) => {
      setTranscriptions((prev) => [...prev, event.data]);
    };

    socketRef.current.onclose = (event) => {
      console.log('WebSocket is closed.', event);
    };

    socketRef.current.onerror = (error) => {
      console.log('WebSocket error:', error);
    };
  };

  useEffect(() => {
    setupWebSocket();
    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [websocketUrl]);

  return (
    <Container>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6">Audio Recorder</Typography>
        </Toolbar>
      </AppBar>
      <Box mt={2}>
        <TextField
          label="WebSocket URL"
          variant="outlined"
          fullWidth
          value={websocketUrl}
          onChange={handleWebSocketUrlChange}
          style={{ marginBottom: 16 }}
        />
        <Button
          variant="contained"
          color="primary"
          onClick={handleStartRecording}
          disabled={isRecording}
        >
          Start Recording
        </Button>
        <Button
          variant="contained"
          color="secondary"
          onClick={handleStopRecording}
          disabled={!isRecording}
          style={{ marginLeft: 16 }}
        >
          Stop Recording
        </Button>
      </Box>
      <div className="transcription-container">
        {transcriptions.map((text, index) => (
          <div
            key={index}
            className="chat-bubble"
          >
            {text}
          </div>
        ))}
      </div>
    </Container>
  );
}

export default App;
EOF

# CSS 스타일 추가
cat > src/App.css << 'EOF'
.transcription-container {
  margin-top: 20px;
  max-height: 400px;
  overflow-y: auto;
}

.chat-bubble {
  background-color: #f1f0f0;
  border-radius: 10px;
  padding: 10px 15px;
  margin: 10px 0;
  max-width: 80%;
  word-wrap: break-word;
}
EOF

# package.json 수정 - Material UI 의존성 추가
npm install @mui/material @emotion/react @emotion/styled

# 코드 테스트
npm start
# 브라우저에서 http://localhost:3000 접속하여 테스트

# 변경사항 커밋
git add .
git commit -m "프론트엔드 기본 구조 및 UI 컴포넌트 구현"
git push origin feature/frontend-setup

# Pull Request 생성 (웹 인터페이스에서)
# GitHub 저장소 페이지 → "Pull requests" 탭 → "New pull request"
# base: develop ← compare: feature/frontend-setup 선택
# 제목: "프론트엔드 기본 구조 설정"
# 설명에 "Closes #2" 추가하여 이슈 연결
# "Create pull request" 클릭

# 이슈 상태 변경 (웹 인터페이스에서)
# "음성인식 앱 스프린트 1" 프로젝트에서 해당 이슈를 "Done"으로 드래그
```

#### 5.1.3 프론트엔드-백엔드 통합 개발자 (dev4) 작업

```bash
# dev4 계정으로 접속 후
cd ~/audio-app

# 기능 브랜치 생성 및 전환 (PR이 merge된 후 진행)
git checkout develop
git pull  # 최신 변경사항 가져오기
git checkout -b feature/integration

# 이슈 상태 변경 (웹 인터페이스에서)
# "음성인식 앱 스프린트 1" 프로젝트에서 해당 이슈를 "In progress"로 드래그

# 프론트엔드 빌드 및 백엔드 통합
cd ~/audio-app/frontend/audio-client
npm run build

# 빌드 결과물을 백엔드 static 폴더로 복사
mkdir -p ~/audio-app/backend/www
cp -r build/* ~/audio-app/backend/www/

# 통합 테스트
cd ~/audio-app/backend
conda activate whisper_env
python app.py
# 브라우저에서 http://localhost:3000 접속하여 테스트

# 변경사항 커밋
git add .
git commit -m "프론트엔드-백엔드 통합 및 테스트 완료"
git push origin feature/integration

# Pull Request 생성 (웹 인터페이스에서)
# GitHub 저장소 페이지 → "Pull requests" 탭 → "New pull request"
# base: develop ← compare: feature/integration 선택
# 제목: "프론트엔드-백엔드 통합 및 WebSocket 연결"
# 설명에 "Closes #3" 추가하여 이슈 연결
# "Create pull request" 클릭

# 이슈 상태 변경 (웹 인터페이스에서)
# "음성인식 앱 스프린트 1" 프로젝트에서 해당 이슈를 "Done"으로 드래그
```

### 5.2 PR 리뷰 및 승인 (PM: dev1)

PM은 각 PR을 검토하고 승인합니다. 웹 인터페이스에서 진행합니다.

1. GitHub 저장소 페이지 → "Pull requests" 탭
2. 각 PR 클릭 → "Files changed" 탭에서 코드 검토
3. 코드 검토 완료 후 "Review changes" → "Approve" 선택 → "Submit review"
4. "Merge pull request" 클릭 → "Confirm merge" 클릭

## 6. 코드 충돌 해결 시나리오

다음은 여러 개발자가 동시에 작업할 때 발생할 수 있는 코드 충돌 시나리오와 해결 방법입니다.

### 6.1 충돌 시나리오 설정

개발자 2명(dev3, dev4)이 동시에 App.js 파일을 수정하는 상황을 가정합니다.

#### 6.1.1 dev3의 작업

```bash
# dev3 계정으로 접속 후
cd ~/audio-app
git checkout develop
git pull  # 최신 변경사항 가져오기
git checkout -b feature/ui-improvements

# App.js 파일 수정 (타이틀 및 버튼 스타일 변경)
# VS Code에서 frontend/audio-client/src/App.js 파일 열기
# AppBar의 타이틀을 "Audio Transcription App"으로 변경
# 버튼 스타일 개선

# 변경사항 커밋
git add .
git commit -m "UI 타이틀 및 버튼 스타일 개선"
git push origin feature/ui-improvements

# Pull Request 생성 (웹 인터페이스에서)
```

#### 6.1.2 dev4의 작업

```bash
# dev4 계정으로 접속 후
cd ~/audio-app
git checkout develop
git pull  # 최신 변경사항 가져오기
git checkout -b feature/websocket-improvements

# App.js 파일 수정 (WebSocket 연결 로직 개선)
# VS Code에서 frontend/audio-client/src/App.js 파일 열기
# setupWebSocket 함수 내 오류 처리 개선

# 변경사항 커밋
git add .
git commit -m "WebSocket 연결 및 오류 처리 개선"
git push origin feature/websocket-improvements

# Pull Request 생성 (웹 인터페이스에서)
```

### 6.2 충돌 해결 과정

dev3의 PR이 먼저 승인되고 병합된 후, dev4가 PR을 생성하면 충돌이 발생합니다.

#### 6.2.1 충돌 해결 (dev4)

```bash
# dev4 계정으로 접속 후
cd ~/audio-app
git checkout feature/websocket-improvements
git fetch origin
git merge origin/develop

# 충돌 해결 (VS Code에서 충돌 마커 확인 및 수정)
# 충돌이 있는 파일 편집 후 저장

# 충돌 해결 후 커밋
git add .
git commit -m "충돌 해결: WebSocket 개선 + UI 개선 병합"
git push origin feature/websocket-improvements

# Pull Request 업데이트 (웹 인터페이스에서 충돌 해결 확인)
```

## 7. 프로젝트 빌드 및 최종 배포

### 7.1 develop에서 main으로 최종 병합 (PM: dev1)

```bash
# dev1 계정으로 접속 후
cd ~/audio-app
git checkout develop
git pull  # 최신 변경사항 가져오기

# develop 브랜치 최종 검증
cd backend
conda activate whisper_env
python app.py
# 브라우저에서 http://localhost:3000 접속하여 최종 테스트

# Release 브랜치 생성
git checkout -b release/v1.0
git push origin release/v1.0

# Pull Request 생성 (웹 인터페이스에서)
# base: main ← compare: release/v1.0 선택
# 제목: "릴리스 v1.0: 음성 인식 앱 첫 버전"
# "Create pull request" 클릭
```

### 7.2 릴리스 및 배포 (웹 인터페이스에서 수행)

1. GitHub 저장소 페이지 → "Pull requests" 탭 → release PR 클릭
2. PR 검토 및 승인 → "Merge pull request" → "Confirm merge"
3. GitHub 저장소 페이지 → "Actions" 탭 → CI/CD 워크플로우 실행 확인
4. 워크플로우 로그에서 ngrok URL 확인하여 배포된 앱 테스트

### 7.3 릴리스 태그 생성 (웹 인터페이스에서 수행)

1. GitHub 저장소 페이지 → "Code" 탭 → "Releases" 섹션 → "Create a new release"
2. Tag version: "v1.0.0"
3. Target: main 브랜치
4. Release title: "음성 인식 앱 v1.0.0"
5. 설명 작성:
   ```
   첫 번째 정식 릴리스 버전입니다.
   
   주요 기능:
   - 실시간 음성 인식 및 텍스트 변환
   - WebSocket을 통한 오디오 스트리밍
   - 사용자 친화적인 UI
   
   이 릴리스는 스프린트 1의 모든 목표를 달성했습니다.
   ```
6. "Publish release" 클릭

## 결론

이 스프린트 시나리오를 통해 4명의 개발자가 GitHub을 활용하여 협업하는 전체 과정을 실습했습니다. 참여자들은 이슈 관리, 브랜치 생성, 코드 리뷰, 충돌 해결, CI/CD 파이프라인 구성, 최종 배포까지의 전체 과정을 경험했습니다. 

이러한 실습은 실제 개발 환경에서 팀 협업 방식을 이해하는 데 큰 도움이 될 것입니다.
