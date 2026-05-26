"""Data generator for college databases.

Generates 50 students, 10 courses, and ~250 enrollments (5 per student)
for each college educational management system.
"""

import sqlite3
import json
import os
import random

# Chinese names for data generation
SURNAMES = '赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜'
GIVEN_NAMES_MALE = ['伟', '强', '磊', '军', '勇', '明', '杰', '涛', '斌', '浩',
                    '鹏', '超', '飞', '刚', '平', '辉', '宁', '峰', '毅', '亮']
GIVEN_NAMES_FEMALE = ['芳', '敏', '静', '丽', '娜', '婷', '雪', '玲', '娟', '艳',
                      '红', '霞', '慧', '梅', '兰', '云', '燕', '秀', '萍', '文']
MAJORS = ['计算机科学', '软件工程', '数据科学', '人工智能', '网络工程',
          '电子信息', '通信工程', '自动化', '数学', '物理']

COURSE_NAMES = [
    '高等数学', '线性代数', '概率论', '离散数学',
    '数据结构', '操作系统', '计算机网络', '数据库原理',
    '软件工程', '人工智能导论', '编译原理', '计算机组成原理',
    '算法设计与分析', '面向对象编程', 'Web开发技术',
]

TEACHERS = [
    '张教授', '李教授', '王教授', '赵教授', '陈教授',
    '刘副教授', '周副教授', '吴讲师', '郑讲师', '孙讲师',
]

LOCATIONS = [
    '教学楼A101', '教学楼A102', '教学楼B201', '教学楼B202',
    '实验楼C301', '实验楼C302', '主楼D401', '主楼D402',
    '综合楼E501', '综合楼E502',
]


def generate_college_data():
    """Generate test data for all three colleges."""
    # Import here to avoid circular imports
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    for col_name in ['A', 'B', 'C']:
        config_path = os.path.join(base, 'college', 'configs', f'college_{col_name.lower()}.json')
        with open(config_path, encoding='utf-8') as f:
            config = json.load(f)

        db_path = os.path.join(base, config['db_path'])
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Remove existing DB and recreate
        if os.path.exists(db_path):
            os.remove(db_path)

        from college.db import init_db, get_conn
        init_db(config)
        conn = get_conn(config)
        c = conn.cursor()

        tables = config['tables']

        # Insert admin account
        ac = tables['account']
        an = ac['name']
        ac_c = ac['columns']
        c.execute(f'INSERT INTO "{an}" ("{ac_c["account_id"]}", "{ac_c["password"]}", "{ac_c["role"]}") '
                  f'VALUES (?, ?, ?)', ('admin', 'admin123', 'admin'))

        # Insert student accounts and students
        sn = tables['student']['name']
        sc = tables['student']['columns']

        students = []
        for i in range(1, 51):
            sid = f'STU{col_name}{i:03d}'
            # Generate Chinese name
            surname = random.choice(SURNAMES)
            if random.random() < 0.5:
                given = random.choice(GIVEN_NAMES_MALE)
                sex = '男'
            else:
                given = random.choice(GIVEN_NAMES_FEMALE)
                sex = '女'
            name = surname + given
            major = random.choice(MAJORS)

            students.append({'id': sid, 'name': name, 'sex': sex, 'major': major})

            c.execute(f'INSERT INTO "{sn}" ("{sc["student_id"]}", "{sc["name"]}", '
                      f'"{sc["sex"]}", "{sc["major"]}") VALUES (?, ?, ?, ?)',
                      (sid, name, sex, major))

            # Insert student account
            c.execute(f'INSERT INTO "{an}" ("{ac_c["account_id"]}", "{ac_c["password"]}", '
                      f'"{ac_c["role"]}") VALUES (?, ?, ?)', (sid, '123456', 'student'))

        # Insert courses
        cn = tables['course']['name']
        cc = tables['course']['columns']

        courses = []
        for i in range(1, 11):
            cid = f'COU{col_name}{i:03d}'
            cname = COURSE_NAMES[(i - 1) % len(COURSE_NAMES)]
            score = random.choice([2, 3, 4])
            teacher = random.choice(TEACHERS)
            location = random.choice(LOCATIONS)
            time_val = random.choice([32, 48, 64])

            courses.append({'id': cid, 'name': cname, 'score': score,
                          'teacher': teacher, 'location': location, 'time': time_val})

            shared = 1 if random.random() < 0.6 else 0  # 60% courses are shared
            c.execute(f'INSERT INTO "{cn}" ("{cc["course_id"]}", "{cc["name"]}", '
                      f'"{cc["score"]}", "{cc["teacher"]}", "{cc["location"]}", '
                      f'"{cc["time"]}", "{cc["shared"]}") VALUES (?, ?, ?, ?, ?, ?, ?)',
                      (cid, cname, score, teacher, location, time_val, shared))

        # Insert enrollments (each student takes 5 courses)
        en = tables['enrollment']
        enn = en['name']
        ec = en['columns']

        enrollment_count = 0
        for student in students:
            selected_courses = random.sample(courses, 5)
            for course in selected_courses:
                grade = random.randint(60, 100)
                try:
                    c.execute(f'INSERT INTO "{enn}" ("{ec["student_id"]}", '
                              f'"{ec["course_id"]}", "{ec["score"]}") VALUES (?, ?, ?)',
                              (student['id'], course['id'], grade))
                    enrollment_count += 1
                except sqlite3.IntegrityError:
                    pass

        conn.commit()
        conn.close()

        print(f'学院{col_name}: {len(students)} 学生, {len(courses)} 课程, '
              f'{enrollment_count} 选课记录 已生成')

    print('所有测试数据已生成完成！')


if __name__ == '__main__':
    generate_college_data()
