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

"""conn = pymysql.connect(
                host='bitnmeta2.synology.me',
                user='iyrc',
                passwd='Dodan1004!',
                db='gemini_ai',
                charset='utf8',
                port=3307,
                cursorclass=pymysql.cursors.DictCursor
            )"""

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

    def search_sessions(self, keyword):
        """[검색 기능] 제목이나 내용에 키워드가 포함된 세션 찾기"""
        if not self.conn: return []
        # 제목이나 메시지 내용에 검색어가 포함된 방을 찾음
        query = """
            SELECT DISTINCT s.id, s.title, s.created_at 
            FROM chat_sessions s
            LEFT JOIN chat_messages m ON s.id = m.session_id
            WHERE s.title LIKE %s OR m.content LIKE %s
            ORDER BY s.id DESC
        """
        search_pattern = f"%{keyword}%"
        self.cursor.execute(query, (search_pattern, search_pattern))
        return self.cursor.fetchall()

    def get_messages(self, session_id):
        if not self.conn: return []
        self.cursor.execute("SELECT sender, content FROM chat_messages WHERE session_id = %s ORDER BY id ASC", (session_id,))
        return self.cursor.fetchall()

    def update_session_title(self, session_id, title):
        if not self.conn: return
        self.cursor.execute("UPDATE chat_sessions SET title = %s WHERE id = %s", (title, session_id))
        self.conn.commit()


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
        self.current_session_id = None
        
        # [수정됨] 검색 버튼(btn_search)과 엔터키에만 이벤트 연결
        if hasattr(self, 'btn_search'):
            self.btn_search.clicked.connect(self.run_search)
        
        if hasattr(self, 'search_input'):
            self.search_input.returnPressed.connect(self.run_search)

        # UI 이벤트 연결
        self.btn_send.clicked.connect(self.send_message)
        self.input_text.returnPressed.connect(self.send_message)
        
        if hasattr(self, 'session_list'):
            self.session_list.itemClicked.connect(self.load_past_chat)
        
        if hasattr(self, 'btn_new_chat'):
            self.btn_new_chat.clicked.connect(self.reset_chat)

        if hasattr(self, 'btn_delete'):
            self.btn_delete.clicked.connect(self.delete_current_chat)

        # 시작 시 전체 목록 불러오기
        self.refresh_session_list()
        
        if self.session_list.count() > 0:
            self.session_list.setCurrentRow(0)
            item = self.session_list.currentItem()
            self.load_past_chat(item)
        else:
            self.start_new_session_ui()

    def start_new_session_ui(self):
        self.current_session_id = None
        self.chat_display.clear()
        self.chat_display.setHtml('<html><head/><body><p><span style=" font-size:18pt; font-weight:600; color:#444746;">안녕하세요, Jammin입니다.</span></p></body></html>')
        self.session_list.clearSelection()
        self.statusbar.showMessage("새로운 대화 시작")

    def run_search(self):
        """검색 버튼 누르면 호출되는 함수"""
        if not hasattr(self, 'search_input'): return
        keyword = self.search_input.text().strip()
        
        if keyword:
            print(f"🔍 검색 시작: {keyword}")
            self.refresh_session_list(keyword) # 키워드 전달
        else:
            print("🔄 검색어 없음 -> 전체 목록 조회")
            self.refresh_session_list() # 전체 조회

    def refresh_session_list(self, keyword=None):
        if not hasattr(self, 'session_list'): return
        
        self.session_list.clear()

        # 키워드가 있으면 검색, 없으면 전체
        if keyword:
            sessions = self.db.search_sessions(keyword)
        else:
            sessions = self.db.get_all_sessions()

        # 결과가 없으면 알림
        if not sessions and keyword:
            self.statusbar.showMessage(f"'{keyword}' 검색 결과가 없습니다.")
            return

        for sess in sessions:
            s_id, s_title, s_date = sess
            if not s_title: s_title = "새로운 대화"
            
            item = QListWidgetItem(f"{s_title}")
            item.setData(Qt.ItemDataRole.UserRole, s_id) 
            self.session_list.addItem(item)

        if keyword:
            self.statusbar.showMessage(f"검색 결과: {len(sessions)}개")

    def delete_current_chat(self):
        item = self.session_list.currentItem()
        if item is None or self.current_session_id is None:
            self.statusbar.showMessage("삭제할 대화가 없습니다.")
            return
            
        session_id = item.data(Qt.ItemDataRole.UserRole)
        row = self.session_list.row(item)
        
        confirm = QMessageBox.question(self, "삭제 확인", "이 대화를 영구적으로 삭제하시겠습니까?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
            if self.db.delete_session(session_id):
                self.session_list.takeItem(row)
                if self.session_list.count() > 0:
                    new_row = min(row, self.session_list.count() - 1)
                    next_item = self.session_list.item(new_row)
                    self.session_list.setCurrentItem(next_item)
                    self.load_past_chat(next_item)
                else:
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
        self.start_new_session_ui()
        if hasattr(self, 'search_input'):
            self.search_input.clear()
            self.refresh_session_list() # 검색어 지웠으니 전체 목록 다시 보여주기

    def send_message(self):
        text = self.input_text.text()
        if not text.strip(): return

        if self.current_session_id is None:
            short_title = text[:15] + "..." if len(text) > 15 else text
            self.current_session_id = self.db.create_session(short_title)
            self.refresh_session_list()
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