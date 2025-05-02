# EXAMPLE-Teamwork-Experience

# Git 및 GitHub 협업 실습 환경 구성 및 시나리오

안녕하세요! 요청하신 Flask 서버와 React 프론트엔드를 활용한 Git/GitHub 협업 실습 환경 구성과 시나리오를 정리해드리겠습니다.

## 요청사항 정리

1. **목표**: Git과 GitHub을 처음 사용하는 학생들을 위한 협업 실습 수업 진행
2. **실습 내용**:
   - 제공된 Flask 서버 코드와 React 클라이언트 코드를 바탕으로 협업
   - GitHub의 이슈 트래킹, 프로젝트 관리 기능 활용
   - 스프린트 계획 및 수행, CI/CD 구성, 브랜치 관리 경험
   - 코드 충돌 해결 및 병합 실습

3. **환경 구성**:
   - Windows 개발자 PC에 Docker Desktop 설치
   - 단일 Ubuntu 컨테이너에 4개 사용자 계정 생성 (dev1~dev4)
   - VSCode Remote-SSH로 개발
   - GPU 지원 Docker 이미지 사용
   - GitHub Actions를 활용한 CI/CD 구성
   - ngrok을 통한 임시 서버 가동 및 확인

4. **브랜치 전략**:
   - main: 최종 배포 버전
   - develop: 테스트 검증판
   - feature/: 기능별 개발 브랜치

## 실습 환경 구성 단계

아래 과정을 따라 실습 환경을 구성해보세요.

### 1. Docker 환경 구성

#### Docker Desktop 설치 (Windows)
```
# Windows에서 Docker Desktop을 설치합니다
# https://www.docker.com/products/docker-desktop/ 에서 다운로드 후 설치
```

#### GPU 지원 Ubuntu 컨테이너 생성 및 설정
```bash
# GPU 지원 Ubuntu 이미지 다운로드
docker pull nvidia/cuda:11.4.3-base-ubuntu20.04

# 컨테이너 생성 및 실행 (호스트의 3000번과 22번 포트를 컨테이너에 매핑)
docker run -d --name colab-container -p 3000:3000 -p 22:22 nvidia/cuda:11.4.3-base-ubuntu20.04 tail -f /dev/null

# 컨테이너 접속
docker exec -it colab-container bash

# 기본 패키지 설치
apt-get update
apt-get install -y sudo openssh-server git curl vim python3 python3-pip build-essential

# SSH 서버 설정
mkdir -p /var/run/sshd
echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config
echo 'PasswordAuthentication yes' >> /etc/ssh/sshd_config
service ssh start

# SSH 서버 시작 스크립트 생성
cat > /root/start_ssh.sh << 'EOF'
#!/bin/bash
service ssh start
tail -f /dev/null
EOF

chmod +x /root/start_ssh.sh

# 개발자 계정 생성
for user in dev1 dev2 dev3 dev4; do
  useradd -m -s /bin/bash $user
  echo "$user:$user" | chpasswd
  usermod -aG sudo $user
  
  # 사용자 디렉토리에 .bashrc 설정
  cat >> /home/$user/.bashrc << 'EOF'
# NVM 환경 설정
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
EOF

  # Git 자격 증명 저장 설정
  su - $user -c "git config --global credential.helper store"
  su - $user -c "git config --global user.name \"$user\""
  su - $user -c "git config --global user.email \"$user@example.com\""
done

# Anaconda 설치
curl -O https://repo.anaconda.com/archive/Anaconda3-2023.09-0-Linux-x86_64.sh
bash Anaconda3-2023.09-0-Linux-x86_64.sh -b -p /opt/anaconda3
echo 'export PATH="/opt/anaconda3/bin:$PATH"' >> /etc/profile.d/anaconda.sh
chmod +x /etc/profile.d/anaconda.sh
source /etc/profile.d/anaconda.sh

# 공통 Anaconda 환경 생성
conda create -y -n whisper_env python=3.10
conda activate whisper_env
pip install flask flask-cors flask-sock whisper torch soundfile numpy

# 모든 사용자가 Anaconda 환경에 접근할 수 있도록 설정
echo 'export PATH="/opt/anaconda3/bin:$PATH"' >> /etc/bash.bashrc
echo 'source /opt/anaconda3/etc/profile.d/conda.sh' >> /etc/bash.bashrc
echo 'conda activate whisper_env' >> /etc/bash.bashrc

# 개발자들을 위한 공유 디렉토리 생성
mkdir -p /shared/project
chmod 777 /shared/project
```

### 2. VSCode Remote-SSH 설정 (Windows)

```
# 1. VSCode 설치 (Windows)
# https://code.visualstudio.com/ 에서 다운로드 후 설치

# 2. Remote-SSH 확장 설치
# VSCode 확장 메뉴에서 'Remote - SSH' 검색 후 설치

# 3. SSH 연결 설정
# VSCode에서 F1 키를 누르고 'Remote-SSH: Connect to Host...' 선택
# 'Add New SSH Host...' 선택 후 아래 형식으로 입력:
# ssh dev1@localhost -p 22

# 4. 각 개발자 계정으로 접속
# dev1, dev2, dev3, dev4 계정별로 SSH 연결 구성
# 비밀번호는 계정명과 동일 (dev1, dev2, dev3, dev4)
```

### 3. Node.js 설치 (컨테이너 내 각 개발자 계정에서 실행)

```bash
# 각 개발자 계정으로 접속 후 실행
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | bash
source ~/.bashrc
nvm ls-remote
nvm install 22
```

### 4. GitHub 계정 및 저장소 설정

```
# 1. GitHub 계정 생성 (아직 없는 경우)
# https://github.com/signup 에서 계정 생성

# 2. 개인 액세스 토큰 생성
# GitHub 웹사이트에서 Settings > Developer settings > Personal access tokens > Tokens (classic)
# Generate new token 클릭
# 토큰 권한: repo, workflow 체크
# 생성된 토큰을 안전한 곳에 저장
```

### 5. 저장소 초기화 (GitHub 웹 인터페이스에서)

```
# 1. GitHub 웹사이트에서 새 저장소 생성
# 저장소 이름: audio-transcription-app
# Description: Whisper를 활용한 음성 인식 애플리케이션
# Public 또는 Private 선택
# "Initialize this repository with a README" 체크
# .gitignore: Node 선택
# Create repository 클릭

# 2. GitHub Actions 비밀값 설정
# 저장소 > Settings > Secrets and variables > Actions > New repository secret
# Name: NGROK_AUTH_TOKEN
# Value: ngrok에서 발급받은 인증 토큰
```
