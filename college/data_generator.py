"""Data generator for college databases.

Generates 50 students, 10 courses, and ~250 enrollments (5 per student)
for each college educational management system.

Data is written to the respective DBMS:
  - College A: Microsoft SQL Server
  - College B: Oracle Database
  - College C: MySQL
"""

import json
import os
import random

from sqlalchemy import text

from college.db import get_engine, init_db, _tn, _cols

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


def _drop_tables(engine, config):
    """Drop all existing tables for a clean start."""
    tables_cfg = config['tables']
    db_type = config['database']['type']

    with engine.connect() as conn:
        for key in ['enrollment', 'course', 'student', 'account']:
            tn = tables_cfg[key]['name']

            if db_type == 'mssql':
                conn.execute(
                    text(f"IF OBJECT_ID('dbo.\"{tn}\"', 'U') IS NOT NULL "
                         f"DROP TABLE \"{tn}\""))
            elif db_type == 'oracle':
                try:
                    conn.execute(text(f'DROP TABLE "{tn}"'))
                    conn.commit()
                except Exception:
                    pass  # Table doesn't exist
            elif db_type == 'mysql':
                conn.execute(text(f'DROP TABLE IF EXISTS `{tn}`'))
            else:
                conn.execute(text(f'DROP TABLE IF EXISTS "{tn}"'))
        conn.commit()


def generate_college_data():
    """Generate test data for all three colleges.

    IMPORTANT: This will DELETE all existing data and recreate tables.
    """
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    for col_name in ['A', 'B', 'C']:
        config_path = os.path.join(
            base, 'college', 'configs', f'college_{col_name.lower()}.json')
        with open(config_path, encoding='utf-8') as f:
            config = json.load(f)

        print(f'[学院{col_name}] 连接到 {config["dbms"]} ({config["database"]["host"]}:'
              f'{config["database"]["port"]})...')

        # Ensure database and tables exist first
        init_db(config)

        # Get a fresh engine (init_db may have recreated it for mssql)
        engine = get_engine(config)

        # Drop existing tables and recreate
        _drop_tables(engine, config)
        init_db(config)
        engine = get_engine(config)

        with engine.connect() as conn:
            tables = config['tables']

            # ---- Insert admin account ----
            ac = tables['account']
            ac_c = ac['columns']
            conn.execute(
                text(f'INSERT INTO "{ac["name"]}" '
                     f'("{ac_c["account_id"]}", "{ac_c["password"]}", '
                     f'"{ac_c["role"]}") VALUES (:uid, :pw, :role)'),
                {'uid': 'admin', 'pw': 'admin123', 'role': 'admin'}
            )

            # ---- Insert 50 students ----
            sn = tables['student']['name']
            sc = tables['student']['columns']

            students = []
            for i in range(1, 51):
                sid = f'STU{col_name}{i:03d}'
                surname = random.choice(SURNAMES)
                if random.random() < 0.5:
                    given = random.choice(GIVEN_NAMES_MALE)
                    sex = '男'
                else:
                    given = random.choice(GIVEN_NAMES_FEMALE)
                    sex = '女'
                name = surname + given
                major = random.choice(MAJORS)

                students.append({'id': sid, 'name': name,
                                'sex': sex, 'major': major})

                conn.execute(
                    text(f'INSERT INTO "{sn}" ("{sc["student_id"]}", '
                         f'"{sc["name"]}", "{sc["sex"]}", "{sc["major"]}") '
                         f'VALUES (:sid, :nm, :sx, :mj)'),
                    {'sid': sid, 'nm': name, 'sx': sex, 'mj': major}
                )

                # Insert student account
                conn.execute(
                    text(f'INSERT INTO "{ac["name"]}" '
                         f'("{ac_c["account_id"]}", "{ac_c["password"]}", '
                         f'"{ac_c["role"]}") VALUES (:uid, :pw, :role)'),
                    {'uid': sid, 'pw': '123456', 'role': 'student'}
                )

            # ---- Insert 10 courses ----
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

                courses.append({
                    'id': cid, 'name': cname, 'score': score,
                    'teacher': teacher, 'location': location,
                    'time': time_val,
                })

                conn.execute(
                    text(f'INSERT INTO "{cn}" ("{cc["course_id"]}", '
                         f'"{cc["name"]}", "{cc["score"]}", '
                         f'"{cc["teacher"]}", "{cc["location"]}", '
                         f'"{cc["time"]}") '
                         f'VALUES (:cid, :nm, :sc, :tc, :loc, :tm)'),
                    {'cid': cid, 'nm': cname, 'sc': score,
                     'tc': teacher, 'loc': location, 'tm': time_val}
                )

            # ---- Insert enrollments (5 per student) ----
            en = tables['enrollment']
            enn = en['name']
            ec = en['columns']

            enrollment_count = 0
            for student in students:
                selected_courses = random.sample(courses, 5)
                for course in selected_courses:
                    grade = random.randint(60, 100)
                    try:
                        conn.execute(
                            text(f'INSERT INTO "{enn}" '
                                 f'("{ec["student_id"]}", '
                                 f'"{ec["course_id"]}", '
                                 f'"{ec["score"]}") '
                                 f'VALUES (:sid, :cid, :sc)'),
                            {'sid': student['id'],
                             'cid': course['id'],
                             'sc': grade}
                        )
                        enrollment_count += 1
                    except Exception:
                        pass  # Skip duplicates

            conn.commit()

        print(f'  学院{col_name}: {len(students)} 学生, {len(courses)} 课程, '
              f'{enrollment_count} 选课记录 → 已写入 {config["dbms"]}')

    print('\n所有测试数据已生成完成！')
    print('  学院A → SQL Server  (localhost:1433)')
    print('  学院B → Oracle      (localhost:1521)')
    print('  学院C → MySQL       (localhost:3306)')


if __name__ == '__main__':
    generate_college_data()
