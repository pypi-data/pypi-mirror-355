import os
import sqlite3
from datetime import datetime


class Db:
    def __init__(self, db_path, create_table_sql):
        """连接数据库，如果不存在则创建"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.task_id = 0
        self.step_sequence = 1
        create_tables = not os.path.exists(db_path)
        try:
            self.conn = sqlite3.connect(db_path)
            self.conn.row_factory = sqlite3.Row  # 方便字典式访问
            if create_tables:
                self.create_tables_if_not_exist(create_table_sql)
        except sqlite3.Error as e:
            print(f"数据库连接失败: {e}")
            self.close()

    def create_tables_if_not_exist(self, create_table_sql):
        """创建任务和步骤表"""
        try:
            self.cursor = self.conn.cursor()
            self.cursor.executescript(create_table_sql)
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"建表失败: {e}")
            self.conn.rollback()

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # ========== 通用增删改查函数 ==========

    def get_latest_task_id(self):
        """获取数据库中最新的 task_id"""
        try:
            self.cursor.execute("SELECT id FROM task ORDER BY id DESC LIMIT 1")
            row = self.cursor.fetchone()
            if row["id"] is not None:
                self.task_id = row["id"] + 1
            else:
                raise ValueError("任务id无效")
        except sqlite3.Error as e:
            print(f"获取最新任务 ID 失败: {e}")
            return None

    # 插入任务
    def insert_task(self, name, start_time=None, task_type='步骤'):
        try:
            if start_time is None:
                start_time = datetime.now().isoformat()
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO task (name, start_time, status)
                VALUES (?, ?, ?)
            """, (name, start_time, task_type))
            self.conn.commit()
            return cursor.lastrowid  # 返回 task_id
        except sqlite3.Error as e:
            print(f"插入任务失败: {e}")
            self.conn.rollback()
            return None

    # 插入步骤
    def insert_step(self, task_id, step_name, sequence, step_type='', log='', error_message=''):
        try:
            now = datetime.now().isoformat()
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO step (task_id, step_name, sequence, start_time, status, log, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (task_id, step_name, sequence, now, step_type, log, error_message))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"插入步骤失败: {e}")
            self.conn.rollback()

    # 更新任务状态和结果
    def update_task(self, task_id, status, result='', error_message=''):
        try:
            now = datetime.now().isoformat()
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE task
                SET end_time = ?, status = ?, result = ?, error_message = ?
                WHERE id = ?
            """, (now, status, result, error_message, task_id))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"更新任务失败: {e}")
            self.conn.rollback()

    # 查询任务列表
    def query_tasks(self, status=None):
        try:
            cursor = self.conn.cursor()
            if status:
                cursor.execute("SELECT * FROM task WHERE status = ? ORDER BY start_time DESC", (status,))
            else:
                cursor.execute("SELECT * FROM task ORDER BY start_time DESC")
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"查询任务失败: {e}")
            return []

    # 删除任务（以及对应步骤）
    def delete_task(self, task_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM step WHERE task_id = ?", (task_id,))
            cursor.execute("DELETE FROM task WHERE id = ?", (task_id,))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"删除任务失败: {e}")
            self.conn.rollback()

    # 查询任务对应的步骤
    def query_steps(self, task_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM step WHERE task_id = ? ORDER BY sequence", (task_id,))
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"查询步骤失败: {e}")
            return []

    def log_step(self, step_name, step_type='', log='', error_message=''):
        self.insert_step(
            task_id=self.task_id,
            step_name=step_name,
            sequence=self.step_sequence,
            step_type=step_type,
            log=log,
            error_message=error_message
        )
        self.step_sequence += 1
    def log_success(self, name, msg):
        self.log_step(
            step_name=name,
            step_type="success",
            log=msg
        )

    def log_fail(self, name, msg, error_message=""):
        self.log_step(
            step_name=name,
            step_type="fail",
            log=msg,
            error_message=error_message
        )
