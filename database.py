"""만능 봇 DB 공통 연결 파일

1차 분리에서는 기존 bot_legacy.py가 DB 생성/마이그레이션을 계속 담당합니다.
다음 단계에서 테이블 생성 코드와 마이그레이션 함수를 이 파일로 옮기면 됩니다.
"""

import sqlite3
import threading

from config import DATABASE_PATH


DB_MUTEX = threading.RLock()
conn = sqlite3.connect(DATABASE_PATH, timeout=30, check_same_thread=False)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=NORMAL")
conn.execute("PRAGMA busy_timeout=30000")
conn.execute("PRAGMA foreign_keys=ON")
conn.execute("PRAGMA temp_store=MEMORY")
c = conn.cursor()


def commit() -> None:
    with DB_MUTEX:
        conn.commit()
