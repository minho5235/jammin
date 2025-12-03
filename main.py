import sys
import os
import google.generativeai as genai
import markdown  # 마크다운을 HTML로 변환하기 위해 필요
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6 import uic
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from dotenv import load_dotenv # 추가

# .env 파일 활성화
load_dotenv()

# --- 설정 ---
# 여기에 발급받은 Google Gemini API Key를 입력하세요
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    print("오류: .env 파일을 찾을 수 없거나 GOOGLE_API_KEY가 없습니다.")
    # 프로그램 종료 처리 등...
else:
    genai.configure(api_key=API_KEY)

# 모델 설정 (gemini-pro 사용)
model = genai.GenerativeModel('gemini-2.5-flash')

# UI 파일 로드
form_class = uic.loadUiType("jammin.ui")[0]

# --- 1. 백그라운드 워커 스레드 (API 통신용) ---
class GeminiWorker(QThread):
    # 사용자 정의 시그널: 작업 완료 시 (결과 텍스트)를 메인 스레드로 보냄
    finished_signal = pyqtSignal(str)

    def __init__(self, user_input):
        super().__init__()
        self.user_input = user_input

    def run(self):
        try:
            # 여기서 API를 호출 (시간이 걸리는 작업)
            response = model.generate_content(self.user_input)
            self.finished_signal.emit(response.text)
        except Exception as e:
            self.finished_signal.emit(f"오류가 발생했습니다: {str(e)}")

# --- 2. 메인 윈도우 ---
class MainWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # 이벤트 연결
        self.btn_send.clicked.connect(self.send_message)
        self.input_text.returnPressed.connect(self.send_message)
        
        # 스레드 변수 초기화
        self.worker = None

    def send_message(self):
        text = self.input_text.text()
        
        # 빈 문자열 방지
        if not text.strip():
            return

        # 1. 내 메시지를 UI에 표시 (우측 정렬)
        my_html = f'''
        <div style="text-align: right; margin: 10px;">
            <span style="background-color: #e3f2fd; padding: 10px 15px; border-radius: 15px; color: #333; display: inline-block;">
                {text}
            </span>
        </div>
        '''
        self.chat_display.append(my_html)
        self.input_text.clear()
        
        # 로딩 표시 (선택 사항)
        self.statusbar.showMessage("Gemini가 생각 중입니다...")
        
        # 2. 스레드 생성 및 시작
        self.worker = GeminiWorker(text)
        self.worker.finished_signal.connect(self.receive_response) # 끝났을 때 실행할 함수 연결
        self.worker.start()

    # 스레드로부터 응답을 받는 함수 (Slot)
    def receive_response(self, response_text):
        # Gemini는 마크다운(**굵게** 등)을 반환하므로 HTML로 변환
        html_text = markdown.markdown(response_text)

        # AI 메시지를 UI에 표시 (좌측 정렬)
        ai_html = f'''
        <div style="text-align: left; margin: 10px;">
            <span style="background-color: #f0f4f9; padding: 10px 15px; border-radius: 15px; color: #333; display: inline-block;">
                <b style="color: #1a73e8;">Jammin:</b><br>
                {html_text}
            </span>
        </div>
        '''
        self.chat_display.append(ai_html)
        
        # 상태바 초기화 및 스크롤 내리기
        self.statusbar.showMessage("준비")
        self.scroll_to_bottom()

    def scroll_to_bottom(self):
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    my_window = MainWindow()
    my_window.show()
    sys.exit(app.exec())