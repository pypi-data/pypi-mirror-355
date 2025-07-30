import os
import random
import sqlite3

from faker import Faker

# 设置中文环境
fake = Faker('zh_CN')

# 确保中文显示正常
os.environ['PYTHONIOENCODING'] = 'utf-8'


def generate_student_info(num_students=100):
    """生成随机学生信息"""
    students = []

    # 班级列表
    classes = [f"{random.randint(2020, 2023)}级{random.choice(['计算机', '软件', '人工智能', '数据科学', '网络工程'])}专业{random.randint(1, 5)}班" for _ in range(10)]

    # 生成学生信息
    for i in range(1, num_students + 1):
        gender = random.choice(['男', '女'])
        birth_year = random.randint(2000, 2005)
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)  # 简化处理，避免月份天数问题

        student = {
            'id': i,
            'student_id': f"{random.randint(2020, 2023)}{random.randint(100000, 999999)}",
            'name': fake.name_male() if gender == '男' else fake.name_female(),
            'gender': gender,
            'birth_date': f"{birth_year}-{birth_month:02d}-{birth_day:02d}",
            'class_name': random.choice(classes),
            'phone': fake.phone_number(),
            'email': fake.email(),
            'address': fake.address().replace('\n', ' ')
        }
        students.append(student)

    return students


def generate_grades(students, num_semesters=4):
    """为每个学生生成多学期的成绩数据"""
    subjects = [
        "高等数学", "大学物理", "程序设计基础", "数据结构", "计算机组成原理",
        "操作系统", "计算机网络", "软件工程", "数据库原理", "人工智能基础"
    ]

    grades = []
    grade_id = 1

    for student in students:
        for semester in range(1, num_semesters + 1):
            # 每个学期随机选择3-7门课程
            num_subjects = random.randint(3, 7)
            selected_subjects = random.sample(subjects, num_subjects)

            for subject in selected_subjects:
                # 生成成绩，60-100分，保留1位小数
                score = round(random.uniform(60, 100), 1)

                grade = {
                    'id': grade_id,
                    'student_id': student['student_id'],
                    'semester': f"{2020 + (semester - 1) // 2}-{2020 + semester // 2}学年第{semester % 2 + 1}学期",
                    'subject': subject,
                    'score': score,
                    'credit': random.choice([2.0, 2.5, 3.0, 3.5, 4.0]),
                    'exam_date': f"{2020 + (semester - 1) // 2}-{(semester % 2 + 1) * 6 + random.randint(1, 10)}-{random.randint(10, 30)}"
                }
                grades.append(grade)
                grade_id += 1

    return grades


def create_database(students, grades, db_path='student_database.db'):
    """创建SQLite数据库并导入数据"""
    # 连接到数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 创建学生信息表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY,
        student_id TEXT UNIQUE,
        name TEXT,
        gender TEXT,
        birth_date TEXT,
        class_name TEXT,
        phone TEXT,
        email TEXT,
        address TEXT
    )
    ''')

    # 创建成绩表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS grades (
        id INTEGER PRIMARY KEY,
        student_id TEXT,
        semester TEXT,
        subject TEXT,
        score REAL,
        credit REAL,
        exam_date TEXT,
        FOREIGN KEY (student_id) REFERENCES students (student_id)
    )
    ''')

    # 插入学生信息
    for student in students:
        cursor.execute('''
        INSERT INTO students (id, student_id, name, gender, birth_date, class_name, phone, email, address)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            student['id'],
            student['student_id'],
            student['name'],
            student['gender'],
            student['birth_date'],
            student['class_name'],
            student['phone'],
            student['email'],
            student['address']
        ))

    # 插入成绩数据
    for grade in grades:
        cursor.execute('''
        INSERT INTO grades (id, student_id, semester, subject, score, credit, exam_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            grade['id'],
            grade['student_id'],
            grade['semester'],
            grade['subject'],
            grade['score'],
            grade['credit'],
            grade['exam_date']
        ))

    # 提交更改并关闭连接
    conn.commit()
    conn.close()

    print(f"数据库已创建：{os.path.abspath(db_path)}")
    print(f"学生表记录数：{len(students)}")
    print(f"成绩表记录数：{len(grades)}")


def main():
    # 生成学生信息
    print("正在生成学生信息...")
    students = generate_student_info(num_students=100)

    # 生成成绩数据
    print("正在生成成绩数据...")
    grades = generate_grades(students, num_semesters=4)

    # 创建数据库
    print("正在创建SQLite数据库...")
    create_database(students, grades)

    print("任务完成！")


if __name__ == "__main__":
    main()