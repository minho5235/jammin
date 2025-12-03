# 🤖 Jammin AI - PyQt6 기반 데스크탑 챗봇

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![PyQt6](https://img.shields.io/badge/PyQt-6.0-green)
![Gemini API](https://img.shields.io/badge/API-Google%20Gemini-orange)

**Jammin AI**는 Google의 **Gemini Pro/Flash 모델**을 활용한 데스크탑 기반의 AI 채팅 애플리케이션입니다.
PyQt6를 사용하여 모던하고 직관적인 UI를 구현하였으며, 스레딩(Threading) 기술을 통해 API 통신 중에도 끊김 없는 사용자 경험을 제공합니다.

## 📸 실행 화면
*(여기에 실행한 앱의 스크린샷 이미지를 캡처해서 붙여넣으세요. 예: `assets/screenshot.png`)*
> ![실행 화면 예시](https://via.placeholder.com/600x400?text=App+Screenshot+Here)

## ✨ 주요 기능
- **실시간 AI 대화**: Google Gemini API와 연동하여 자연스러운 대화가 가능합니다.
- **모던 UI 디자인**: CSS 스타일시트를 적용한 둥근 모서리와 깔끔한 채팅 인터페이스.
- **마크다운 렌더링**: AI의 답변에 포함된 볼드체, 리스트 등의 마크다운 문법을 HTML로 변환하여 깔끔하게 표시합니다.
- **비동기 처리 (Async)**: `QThread`를 사용하여 네트워크 통신 중 UI 멈춤(Freezing) 현상을 방지했습니다.
- **보안**: `.env` 파일을 통해 API Key를 안전하게 관리합니다.

## 🛠 사용 기술 (Tech Stack)
- **Language**: Python 3.9+
- **GUI Framework**: PyQt6 (Qt Designer 활용)
- **AI Model**: Google Gemini-1.5-flash (또는 Gemini-Pro)
- **Environment Management**: python-dotenv

## 🚀 설치 및 실행 방법 (Getting Started)
# 필요한 라이브러리 한번에 설치하기
pip install -r requirements.txt

### 1. 프로젝트 클론 (Clone)
```bash
git clone [https://github.com/](https://github.com/)[본인아이디]/jammin-ai.git
cd jammin-ai# jammin
