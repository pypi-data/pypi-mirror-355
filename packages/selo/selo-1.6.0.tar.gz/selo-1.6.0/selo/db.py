import sqlite3
from datetime import datetime


class Db:
    def __init__(self, db_path=None, create_table_sql=None):
        """
        初始化数据库类
        :param db_path: 数据库路径
        :param create_table_sql: 建表语句
        """
        self.db_path = db_path
        self.db_table = create_table_sql
        self.conn = None
        self.task_id = 0
        self.step_sequence = 1

    def set_db_path(self, db_path):
        """
        设置数据库路径
        """
        self.db_path = db_path

    def set_db_table(self, create_table_sql):
        """
        设置建表语句
        """
        self.db_table = create_table_sql

    def connect_db(self):
        """
        连接数据库，如果表结构存在则创建
        """
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            if self.db_table:
                self.create_tables_if_not_exist(self.db_table)
        except sqlite3.Error as e:
            print(f"数据库连接失败: {e}")
            self.close()

    def create_tables_if_not_exist(self, create_table_sql):
        """
        创建数据库表
        """
        try:
            with self.conn:
                self.conn.executescript(create_table_sql)
        except sqlite3.Error as e:
            print(f"建表失败: {e}")

    def close(self):
        """
        关闭数据库连接
        """
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # ====================== 通用操作 ======================

    def get_latest_task_id(self):
        """
        获取当前最新任务ID
        """
        try:
            with self.conn as conn:
                cursor = conn.execute("SELECT id FROM task ORDER BY id DESC LIMIT 1")
                row = cursor.fetchone()
                if row:
                    self.task_id = row["id"] + 1
                else:
                    self.task_id = 1
        except sqlite3.Error as e:
            print(f"获取最新任务ID失败: {e}")

    def insert_task(self, name, start_time=None, task_type='步骤'):
        """
        插入一个任务
        """
        try:
            start_time = start_time or datetime.now().isoformat()
            with self.conn as conn:
                cursor = conn.execute("""
                    INSERT INTO task (name, start_time, status)
                    VALUES (?, ?, ?)
                """, (name, start_time, task_type))
                self.task_id = cursor.lastrowid
                return self.task_id
        except sqlite3.Error as e:
            print(f"插入任务失败: {e}")
            return None

    def insert_step(self, task_id, step_name, sequence, step_type='', log='', error_message=''):
        """
        插入步骤
        """
        try:
            now = datetime.now().isoformat()
            with self.conn:
                self.conn.execute("""
                    INSERT INTO step (task_id, step_name, sequence, start_time, status, log, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (task_id, step_name, sequence, now, step_type, log, error_message))
        except sqlite3.Error as e:
            print(f"插入步骤失败: {e}")

    def update_task(self, task_id, status, result='', error_message=''):
        """
        更新任务状态、结束时间和结果
        """
        try:
            now = datetime.now().isoformat()
            with self.conn:
                self.conn.execute("""
                    UPDATE task
                    SET end_time = ?, status = ?, result = ?, error_message = ?
                    WHERE id = ?
                """, (now, status, result, error_message, task_id))
        except sqlite3.Error as e:
            print(f"更新任务失败: {e}")

    def query_tasks(self, status=None):
        """
        查询所有任务，按时间倒序
        """
        try:
            query = "SELECT * FROM task"
            params = ()
            if status:
                query += " WHERE status = ?"
                params = (status,)
            query += " ORDER BY start_time DESC"
            cursor = self.conn.execute(query, params)
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"查询任务失败: {e}")
            return []

    def delete_task(self, task_id):
        """
        删除指定任务及其相关步骤
        """
        try:
            with self.conn:
                self.conn.execute("DELETE FROM step WHERE task_id = ?", (task_id,))
                self.conn.execute("DELETE FROM task WHERE id = ?", (task_id,))
        except sqlite3.Error as e:
            print(f"删除任务失败: {e}")

    def query_steps(self, task_id):
        """
        查询指定任务的步骤
        """
        try:
            cursor = self.conn.execute(
                "SELECT * FROM step WHERE task_id = ? ORDER BY sequence", (task_id,))
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"查询步骤失败: {e}")
            return []

    # ====================== 日志封装函数 ======================

    def log_step(self, step_name, step_type='', log='', error_message=''):
        """
        插入日志步骤（自动序号）
        """
        self.insert_step(
            task_id=self.task_id,
            step_name=step_name,
            sequence=self.step_sequence,
            step_type=step_type,
            log=log,
            error_message=error_message
        )
        self.step_sequence += 1

    def log_success(self, step_name, msg):
        """
        记录成功步骤
        """
        self.log_step(step_name, step_type="success", log=msg)

    def log_fail(self, step_name, msg, error_message=""):
        """
        记录失败步骤
        """
        self.log_step(step_name, step_type="fail", log=msg, error_message=error_message)

# 示例
# db_path = 'example.db'
# # 初始化和连接数据库
# db = Db(db_path=db_path, create_table_sql=create_table_sql)
# db.set_db_table(create_table_sql)
# db.connect_db()
# # 插入一个任务
# task_name = "数据处理任务"
# task_id = db.insert_task(name=task_name)
# db.task_id = task_id  # 设置当前 task_id（便于 log_step 使用）
# # 记录步骤（成功）
# db.log_success("加载数据", "从本地加载成功")
# # 记录步骤（失败）
# db.log_fail("清洗数据", "执行清洗失败", "字段缺失")
# # 查询所有任务
# tasks = db.query_tasks()
# print("任务列表：")
# for task in tasks:
#     print(dict(task))
# # 查询某个任务的步骤
# steps = db.query_steps(task_id)
# print(f"\n任务 {task_id} 的步骤：")
# for step in steps:
#     print(dict(step))
# # 更新任务状态为完成
# db.update_task(task_id=task_id, status="完成", result="部分成功", error_message="清洗失败")
# # 删除任务（包含步骤）
# # db.delete_task(task_id)
# # 关闭数据库连接
# db.close()