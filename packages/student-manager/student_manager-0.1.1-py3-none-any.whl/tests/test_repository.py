import unittest
import os
import sqlite3
from student_manager.repository import StudentRepository

TEST_DB_PATH = "test_students.db"


class TestStudentRepository(unittest.TestCase):
    # 每个测试用例执行之前自动调用，用于准备测试环境或初始化资源。比如创建数据库连接、初始化变量、准备测试数据等。
    def setUp(self):
        # 初始化测试数据库
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
        conn = sqlite3.connect(TEST_DB_PATH)
        conn.execute("""
            CREATE TABLE students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                score INTEGER
            )
        """)
        conn.commit()
        conn.close()

        # 替换 repository 中默认数据库连接（需要配合 database.py 让其读取自定义路径）
        self.repo = StudentRepository(TEST_DB_PATH)
        # self.repo.db.db_path = TEST_DB_PATH
        # self.repo.conn = sqlite3.connect(TEST_DB_PATH)

    # 每个测试用例执行之后自动调用，用于清理测试环境或释放资源。比如关闭数据库连接、删除临时文件、清理数据等
    def tearDown(self):
        self.repo.close()
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

    def test_insert_and_fetch(self):
        self.repo.insert_student("Alice", 90)
        self.repo.insert_student("Bob", 80)
        results = self.repo.fetch_all()
        self.assertEqual(len(results), 2)
        self.assertIn(("Alice", 90), results)
        self.assertIn(("Bob", 80), results)

    def test_update_score(self):
        self.repo.insert_student("Alice", 90)
        self.repo.update_score("Alice", 95)
        results = dict(self.repo.fetch_all())
        self.assertEqual(results["Alice"], 95)

    def test_delete_student(self):
        self.repo.insert_student("Alice", 90)
        self.repo.delete_student("Alice")
        results = self.repo.fetch_all()
        self.assertEqual(len(results), 0)

    def test_average_score(self):
        self.repo.insert_student("A", 80)
        self.repo.insert_student("B", 100)
        avg = self.repo.average_score()
        self.assertAlmostEqual(avg, 90)

    def test_max_min_score(self):
        self.repo.insert_student("A", 60)
        self.repo.insert_student("B", 100)
        max_stu, min_stu = self.repo.max_min_score()
        self.assertEqual(max_stu[1], 100)
        self.assertEqual(min_stu[1], 60)


if __name__ == '__main__':
    unittest.main()
