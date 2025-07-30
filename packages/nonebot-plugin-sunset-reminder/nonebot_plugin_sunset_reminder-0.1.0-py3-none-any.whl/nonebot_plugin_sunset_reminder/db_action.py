import sqlite3
from typing import List, Dict, Tuple
from .config import DATA_DIR

DB_FILE = DATA_DIR / "sunset_reminder.db"


def init_database() -> None:
    """初始化数据库并创建表"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sunset_remind (
            id INTEGER,
            type TEXT,
            activate BOOLEAN,
            UNIQUE(id, type)
        )
    """)
    conn.commit()
    conn.close()


def add_data(id_: int, type_: str, activate: bool = False) -> None:
    """添加或更新群组/用户激活状态"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO sunset_remind (id, type, activate)
        VALUES (?, ?, ?)
        ON CONFLICT(id, type) DO UPDATE SET activate=excluded.activate
        """,
        (id_, type_, activate)
    )
    conn.commit()
    conn.close()


def remove_data(id_: int, type_: str) -> None:
    """删除群组/用户"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """
        DELETE FROM sunset_remind WHERE id=? AND type=?
        """,
        (id_, type_)
    )
    conn.commit()
    conn.close()


def load_data() -> List[Dict[Tuple[int, str], bool]]:
    """加载所有群组/用户激活状态"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, type, activate FROM sunset_remind")
    rows = cursor.fetchall()
    conn.close()
    return [{(id_, type_): bool(activate)} for id_, type_, activate in rows]
