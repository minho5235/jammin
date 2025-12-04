# 🤖 Jammin AI - Python Desktop Chatbot

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![PyQt6](https://img.shields.io/badge/PyQt-6.0-green)
![MySQL](https://img.shields.io/badge/Database-MySQL-00758F)
![Gemini API](https://img.shields.io/badge/API-Google%20Gemini-orange)

**Jammin AI**는 Google의 최신 **Gemini 2.5 Flash 모델**을 탑재한 데스크탑 AI 채팅 애플리케이션입니다.
PyQt6를 활용한 깔끔한 GUI 환경에서 AI와 대화할 수 있으며, MySQL 데이터베이스를 연동하여 대화 내용을 영구적으로 저장하고 관리할 수 있습니다.

## ✨ 주요 기능 (Key Features)

### 1. 💬 강력한 AI 채팅 (Core)
* **Google Gemini 연동**: 구글의 고성능 생성형 AI 모델을 사용하여 자연스럽고 똑똑한 답변을 제공합니다.
* **마크다운(Markdown) 렌더링**: AI가 작성한 코드 블럭, 강조(Bold), 리스트 등을 보기 좋게 변환하여 표시합니다.
* **비동기 처리 (Multi-threading)**: `QThread`를 적용하여 AI가 생각하는 동안에도 프로그램이 멈추지 않고 쾌적하게 작동합니다.

### 2. 🖥️ 사용자 친화적 UI (Interface)
* **모던 디자인**: CSS 스타일시트가 적용된 둥근 모서리 버튼과 입력창, 직관적인 레이아웃을 제공합니다.
* **사이드바 (Sidebar)**: 과거 대화 기록을 한눈에 볼 수 있는 사이드바 인터페이스를 구축했습니다.
* **Qt Designer 연동**: `jammin.ui` 파일을 로드하여 디자인 수정과 유지보수가 용이합니다.

### 3. 💾 데이터베이스 및 세션 관리 (Database)
* **대화 자동 저장**: 모든 채팅 내용은 MySQL DB에 실시간으로 안전하게 저장됩니다.
* **자동 제목 생성**: 첫 메시지 내용을 분석하여 대화방의 제목을 자동으로 요약/설정합니다.
* **이어하기 & 삭제**: 언제든지 이전 대화를 클릭하여 불러오거나, 불필요한 대화방을 삭제할 수 있습니다.

## 🛠 사용 기술 (Tech Stack)
* **Language**: Python 3.9+
* **GUI Framework**: PyQt6
* **Database**: MySQL (mysql-connector-python)
* **AI Model**: Google Gemini-2.5-flash
* **Configuration**: python-dotenv (API 키 및 DB 정보 보안 관리)

## 🚀 설치 및 실행 (Installation)

### 1. 라이브러리 설치
프로젝트 실행에 필요한 파이썬 라이브러리를 설치합니다.
bash
pip install -r requirements.txt

### 2. 데이터베이스 설정
MySQL에 접속하여 프로젝트용 데이터베이스를 생성합니다. (테이블은 앱 실행 시 자동 생성됩니다.)

SQL

CREATE DATABASE jammin_db;
### 3. 환경 변수 설정 (.env)
프로젝트 폴더에 .env 파일을 만들고 아래 정보를 입력하세요.

Ini, TOML

# Google Gemini API Key
GOOGLE_API_KEY=발급받은_API_키_입력

# MySQL 접속 정보
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=설정한_DB_비밀번호
DB_NAME=jammin_db

### 4. 실행하기
Bash

python main.py