import sys
import os
import google.generativeai as genai
import markdown
import mysql.connector
from PyQt6.QtWidgets import QApplication, QMainWindow, QListWidgetItem, QMessageBox
from PyQt6 import uic
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from dotenv import load_dotenv

load_dotenv()

# --- 설정 ---
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    print("경고: .env 파일 오류")
else:
    genai.configure(api_key=API_KEY)

model = genai.GenerativeModel('gemini-2.5-flash')
UI_PATH = "jammin.ui"
try:
    form_class = uic.loadUiType(UI_PATH)[0]
except:
    print(f"오류: {UI_PATH} 없음")
    sys.exit(1)

# --- DB 매니저 ---
class DatabaseManager:
    def __init__(self):
        self.conn = None
        try:
            self.conn = mysql.connector.connect(
                host=os.getenv("DB_HOST"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME")
            )
            self.cursor = self.conn.cursor()
            self._init_tables()
            print("DB 연결 성공")
        except Exception as e:
            print(f"DB 오류: {e}")

    def _init_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(100) DEFAULT '새로운 대화',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 컬럼 존재 여부 확인 및 추가
        try:
            self.cursor.execute("SELECT title FROM chat_sessions LIMIT 1")
            self.cursor.fetchall()
        except mysql.connector.errors.ProgrammingError:
            self.cursor.execute("ALTER TABLE chat_sessions ADD COLUMN title VARCHAR(100) DEFAULT '새로운 대화' AFTER id")
            self.conn.commit()

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_id INT,
                sender VARCHAR(10),
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
            )
        """)
        self.conn.commit()

    def create_session(self, title="새로운 대화"):
        if not self.conn: return None
        self.cursor.execute("INSERT INTO chat_sessions (title) VALUES (%s)", (title,))
        self.conn.commit()
        return self.cursor.lastrowid

    def delete_session(self, session_id):
        if not self.conn: return False
        try:
            self.cursor.execute("DELETE FROM chat_messages WHERE session_id = %s", (session_id,))
            self.cursor.execute("DELETE FROM chat_sessions WHERE id = %s", (session_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"삭제 오류: {e}")
            return False

    def save_message(self, session_id, sender, content):
        if not self.conn or session_id is None: return
        self.cursor.execute("INSERT INTO chat_messages (session_id, sender, content) VALUES (%s, %s, %s)", 
                            (session_id, sender, content))
        self.conn.commit()

    def get_all_sessions(self):
        if not self.conn: return []
        self.cursor.execute("SELECT id, title, created_at FROM chat_sessions ORDER BY id DESC")
        return self.cursor.fetchall()

    def get_messages(self, session_id):
        if not self.conn: return []
        self.cursor.execute("SELECT sender, content FROM chat_messages WHERE session_id = %s ORDER BY id ASC", (session_id,))
        return self.cursor.fetchall()

# --- 워커 스레드 ---
class GeminiWorker(QThread):
    finished_signal = pyqtSignal(str)

    def __init__(self, user_input):
        super().__init__()
        self.user_input = user_input

    def run(self):
        try:
            response = model.generate_content(self.user_input)
            self.finished_signal.emit(response.text)
        except Exception as e:
            self.finished_signal.emit(f"오류: {e}")

# --- 메인 윈도우 ---
class MainWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.db = DatabaseManager()
        self.current_session_id = None # None이면 아직 DB에 저장되지 않은 상태
        
        # UI 이벤트 연결
        self.btn_send.clicked.connect(self.send_message)
        self.input_text.returnPressed.connect(self.send_message)
        
        if hasattr(self, 'session_list'):
            self.session_list.itemClicked.connect(self.load_past_chat)
        
        if hasattr(self, 'btn_new_chat'):
            self.btn_new_chat.clicked.connect(self.reset_chat)

        if hasattr(self, 'btn_delete'):
            self.btn_delete.clicked.connect(self.delete_current_chat)

        # 시작 시 목록 불러오기
        self.refresh_session_list()
        
        # 만약 목록이 있으면 첫번째 채팅 선택, 없으면 빈 화면 시작
        if self.session_list.count() > 0:
            self.session_list.setCurrentRow(0)
            item = self.session_list.currentItem()
            self.load_past_chat(item)
        else:
            self.start_new_session_ui()

    def start_new_session_ui(self):
        """DB 생성 없이 화면만 초기화 (메시지 보낼 때 생성됨)"""
        self.current_session_id = None
        self.chat_display.clear()
        self.chat_display.setHtml('<html><head/><body><p><span style=" font-size:18pt; font-weight:600; color:#444746;">안녕하세요, Jammin입니다.</span></p></body></html>')
        self.session_list.clearSelection()
        self.statusbar.showMessage("새로운 대화 시작 (메시지를 입력하면 저장됩니다)")

    def refresh_session_list(self):
        if not hasattr(self, 'session_list'): return
        
        # 현재 선택된 ID 기억
        current_selected_id = None
        if self.session_list.currentItem():
            current_selected_id = self.session_list.currentItem().data(Qt.ItemDataRole.UserRole)

        self.session_list.clear()
        sessions = self.db.get_all_sessions()
        
        for sess in sessions:
            s_id, s_title, s_date = sess
            if not s_title: s_title = "새로운 대화"
            
            item = QListWidgetItem(f"{s_title}")
            item.setData(Qt.ItemDataRole.UserRole, s_id) 
            self.session_list.addItem(item)

            if s_id == current_selected_id:
                item.setSelected(True)
                self.session_list.setCurrentItem(item)

    def delete_current_chat(self):
        """현재 선택된 채팅방 삭제"""
        item = self.session_list.currentItem()
        
        # 선택된 게 없거나, 아직 저장도 안 된 '새 채팅' 화면일 경우
        if item is None or self.current_session_id is None:
            self.statusbar.showMessage("삭제할 대화가 없거나 저장되지 않았습니다.")
            # 화면만 초기화
            self.start_new_session_ui()
            return
            
        session_id = item.data(Qt.ItemDataRole.UserRole)
        row = self.session_list.row(item)
        
        confirm = QMessageBox.question(self, "삭제 확인", "이 대화를 영구적으로 삭제하시겠습니까?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
            if self.db.delete_session(session_id):
                # 1. UI 목록에서 즉시 제거
                self.session_list.takeItem(row)
                
                # 2. 삭제 후 다른 채팅방을 보여줄지 결정
                if self.session_list.count() > 0:
                    # 삭제된 위치가 마지막이었다면 그 앞엣놈, 아니면 그 뒷놈 선택
                    new_row = min(row, self.session_list.count() - 1)
                    next_item = self.session_list.item(new_row)
                    self.session_list.setCurrentItem(next_item)
                    self.load_past_chat(next_item) # 그 채팅방 내용 로드
                else:
                    # 다 지워서 남은 게 없으면 빈 화면(새 채팅)으로
                    self.start_new_session_ui()
                
                self.statusbar.showMessage("대화가 삭제되었습니다.")
            else:
                QMessageBox.warning(self, "오류", "삭제에 실패했습니다.")

    def load_past_chat(self, item):
        session_id = item.data(Qt.ItemDataRole.UserRole)
        self.current_session_id = session_id
        self.chat_display.clear()
        
        messages = self.db.get_messages(session_id)
        for sender, content in messages:
            self.display_message(content, sender)
            
        self.statusbar.showMessage(f"대화 불러옴 (ID: {session_id})")

    def reset_chat(self):
        # '새로운 채팅' 버튼 누르면 빈 화면으로
        self.start_new_session_ui()

    def send_message(self):
        text = self.input_text.text()
        if not text.strip(): return

        # [핵심 변경] 첫 메시지 전송 시점에 세션 생성 (Lazy Creation)
        if self.current_session_id is None:
            short_title = text[:15] + "..." if len(text) > 15 else text
            # DB에 방 만들기
            self.current_session_id = self.db.create_session(short_title)
            # 목록 갱신해서 방금 만든 방 보여주기
            self.refresh_session_list()
            # 맨 위(방금 만든 방) 선택 상태로
            if self.session_list.count() > 0:
                self.session_list.setCurrentRow(0)
        
        self.display_message(text, 'user')
        self.db.save_message(self.current_session_id, 'user', text)
        self.input_text.clear()
        
        self.statusbar.showMessage("Gemini 생각 중...")
        self.worker = GeminiWorker(text)
        self.worker.finished_signal.connect(self.receive_response)
        self.worker.start()

    def receive_response(self, response_text):
        self.display_message(response_text, 'ai')
        self.db.save_message(self.current_session_id, 'ai', response_text)
        self.statusbar.showMessage("준비")

    def display_message(self, text, sender):
        if sender == 'user':
            html = f'<div style="text-align: right; margin: 10px;"><span style="background-color: #e3f2fd; padding: 10px 15px; border-radius: 15px; color: #333;">{text}</span></div>'
        else:
            converted_text = markdown.markdown(text)
            html = f'<div style="text-align: left; margin: 10px;"><span style="background-color: #f0f4f9; padding: 10px 15px; border-radius: 15px; color: #333;"><b>Jammin:</b><br>{converted_text}</span></div>'
        
        self.chat_display.append(html)
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())