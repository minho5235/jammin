🤖 Jammin AI - PyQt6 & MySQL 기반 데스크탑 챗봇
Jammin AI는 Google의 Gemini Pro/Flash 모델을 활용한 데스크탑 기반의 지능형 채팅 애플리케이션입니다. PyQt6로 구현된 직관적인 인터페이스와 MySQL 데이터베이스를 연동하여 대화 내용을 영구적으로 저장하고 관리할 수 있습니다.


✨ 주요 기능
💾 대화 자동 저장 (DB 연동): MySQL과 연동하여 모든 대화 내용이 실시간으로 저장됩니다. 프로그램을 껐다 켜도 이전 대화를 불러올 수 있습니다.

🗂 세션 관리 사이드바: 왼쪽 사이드바에서 과거 대화 목록을 확인하고, 클릭하여 즉시 불러올 수 있습니다.

🗑 대화 삭제 기능: 불필요한 대화는 사이드바에서 즉시 삭제할 수 있으며, DB에서도 안전하게 제거됩니다.

🏷 자동 제목 생성: 첫 메시지를 보내는 순간, 내용을 분석하여 대화방 제목이 자동으로 설정됩니다.

⚡ 비동기 처리 (Threading): QThread를 사용하여 AI가 답변을 생성하는 동안에도 UI가 멈추지 않고 부드럽게 작동합니다.

🎨 마크다운(Markdown) 지원: AI의 답변(코드 블럭, 볼드체, 리스트 등)을 깔끔한 서식으로 렌더링합니다.

🛠 사용 기술 (Tech Stack)
Language: Python 3.9+

GUI: PyQt6 (Qt Designer jammin.ui 연동)

Database: MySQL (mysql-connector-python)

AI Model: Google Gemini-2.5-flash

Utils: python-dotenv (환경변수 관리)

🚀 설치 및 실행 방법 (Getting Started)
1. 사전 준비 (Prerequisites)
Python 3.9 이상 설치

MySQL Server 설치 및 실행

2. 프로젝트 클론 (Clone)
Bash
git clone https://github.com/minho5253/jammin-ai.git
cd jammin-ai

3. 라이브러리 설치
Bash
pip install -r requirements.txt
(만약 requirements.txt가 없다면 아래 명령어로 설치)

Bash
pip install google-generativeai PyQt6 mysql-connector-python markdown python-dotenv

4. 데이터베이스 설정 (중요!)
MySQL 워크벤치나 터미널에서 아래 명령어를 입력하여 데이터베이스를 생성해주세요. (테이블은 프로그램 실행 시 자동 생성됩니다.)

SQL
CREATE DATABASE jammin_db;

5. 환경 변수 설정 (.env)
프로젝트 루트 경로에 .env 파일을 생성하고 아래 내용을 입력하세요.

Ini, TOML

# Google Gemini API Key
GOOGLE_API_KEY=당신의_구글_API_키

# MySQL Database Info
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=당신의_DB_비밀번호
DB_NAME=jammin_db
6. 실행 (Run)
Bash

python main.py
📂 프로젝트 구조
jammin-ai/
├── main.py             # 메인 로직 (DB연동, GUI실행, 스레드)
├── jammin.ui           # Qt Designer로 만든 UI 파일
├── .env                # API 키 및 DB 정보 (비공개)
├── README.md           # 설명 파일
└── requirements.txt    # 의존성 목록
📝 License
This project is for educational purposes.
