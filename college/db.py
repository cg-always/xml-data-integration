"""Database helper for college educational management systems.

Handles SQLite database initialization with college-specific schemas,
and provides CRUD operations using logical column names.
"""

import sqlite3
import json
import os


def get_col_db_path(config):
    """Get absolute path to college DB file."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, config['db_path'])


def init_db(config):
    """Initialize database with college-specific schema."""
    db_path = get_col_db_path(config)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    tables = config['tables']

    # Account table
    ac = tables['account']
    an = ac['name']
    ac_cols = ac['columns']
    c.execute(f'''CREATE TABLE IF NOT EXISTS "{an}" (
        "{ac_cols["account_id"]}" TEXT PRIMARY KEY,
        "{ac_cols["password"]}" TEXT NOT NULL,
        "{ac_cols["role"]}" TEXT NOT NULL
    )''')

    # Student table
    st = tables['student']
    sn = st['name']
    sc = st['columns']
    c.execute(f'''CREATE TABLE IF NOT EXISTS "{sn}" (
        "{sc["student_id"]}" TEXT PRIMARY KEY,
        "{sc["name"]}" TEXT NOT NULL,
        "{sc["sex"]}" TEXT NOT NULL,
        "{sc["major"]}" TEXT NOT NULL
    )''')

    # Course table
    co = tables['course']
    cn = co['name']
    cc = co['columns']
    c.execute(f'''CREATE TABLE IF NOT EXISTS "{cn}" (
        "{cc["course_id"]}" TEXT PRIMARY KEY,
        "{cc["name"]}" TEXT NOT NULL,
        "{cc["score"]}" INTEGER NOT NULL,
        "{cc["teacher"]}" TEXT NOT NULL,
        "{cc["location"]}" TEXT NOT NULL,
        "{cc["time"]}" INTEGER DEFAULT 32,
        "{cc["shared"]}" INTEGER DEFAULT 1
    )''')

    # Enrollment table
    en = tables['enrollment']
    enn = en['name']
    ec = en['columns']
    c.execute(f'''CREATE TABLE IF NOT EXISTS "{enn}" (
        "{ec["student_id"]}" TEXT NOT NULL,
        "{ec["course_id"]}" TEXT NOT NULL,
        "{ec["score"]}" INTEGER DEFAULT 0,
        PRIMARY KEY ("{ec["student_id"]}", "{ec["course_id"]}")
    )''')

    conn.commit()
    conn.close()


def get_conn(config):
    """Get database connection."""
    return sqlite3.connect(get_col_db_path(config))


def _col(table_obj, logical_name):
    """Get actual column name from logical name."""
    return table_obj['columns'][logical_name]


def _tn(config, table_key):
    """Get actual table name."""
    return config['tables'][table_key]['name']


def _cols(config, table_key):
    """Get columns dict for table."""
    return config['tables'][table_key]['columns']


def verify_login(config, username, password):
    """Verify login credentials. Returns (success, role) or (False, None)."""
    conn = get_conn(config)
    c = conn.cursor()
    t = config['tables']['account']
    tn = t['name']
    cn_id = t['columns']['account_id']
    cn_pw = t['columns']['password']
    cn_role = t['columns']['role']
    c.execute(f'SELECT "{cn_role}" FROM "{tn}" WHERE "{cn_id}"=? AND "{cn_pw}"=?',
              (username, password))
    row = c.fetchone()
    conn.close()
    if row:
        return True, row[0]
    return False, None


def get_student(config, student_id):
    """Get student by ID."""
    conn = get_conn(config)
    c = conn.cursor()
    t = config['tables']['student']
    tn = t['name']
    sc = t['columns']
    c.execute(f'SELECT "{sc["student_id"]}", "{sc["name"]}", "{sc["sex"]}", "{sc["major"]}" '
              f'FROM "{tn}" WHERE "{sc["student_id"]}"=?', (student_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            'student_id': row[0], 'name': row[1],
            'sex': row[2], 'major': row[3]
        }
    return None


def get_all_students(config):
    """Get all students."""
    conn = get_conn(config)
    c = conn.cursor()
    t = config['tables']['student']
    tn = t['name']
    sc = t['columns']
    c.execute(f'SELECT "{sc["student_id"]}", "{sc["name"]}", "{sc["sex"]}", "{sc["major"]}" '
              f'FROM "{tn}"')
    rows = c.fetchall()
    conn.close()
    return [{'student_id': r[0], 'name': r[1], 'sex': r[2], 'major': r[3]} for r in rows]


def get_course(config, course_id):
    """Get course by ID."""
    conn = get_conn(config)
    c = conn.cursor()
    t = config['tables']['course']
    tn = t['name']
    cc = t['columns']
    c.execute(f'SELECT "{cc["course_id"]}", "{cc["name"]}", "{cc["score"]}", '
              f'"{cc["teacher"]}", "{cc["location"]}", "{cc["time"]}", '
              f'"{cc["shared"]}" '
              f'FROM "{tn}" WHERE "{cc["course_id"]}"=?', (course_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            'course_id': row[0], 'name': row[1], 'score': row[2],
            'teacher': row[3], 'location': row[4], 'time': row[5],
            'shared': row[6],
        }
    return None


def get_all_courses(config):
    """Get all courses."""
    conn = get_conn(config)
    c = conn.cursor()
    t = config['tables']['course']
    tn = t['name']
    cc = t['columns']
    c.execute(f'SELECT "{cc["course_id"]}", "{cc["name"]}", "{cc["score"]}", '
              f'"{cc["teacher"]}", "{cc["location"]}", "{cc["time"]}", '
              f'"{cc["shared"]}" FROM "{tn}"')
    rows = c.fetchall()
    conn.close()
    return [{'course_id': r[0], 'name': r[1], 'score': r[2],
             'teacher': r[3], 'location': r[4], 'time': r[5],
             'shared': r[6]} for r in rows]


def get_shared_courses(config):
    """Get only courses marked as shared."""
    conn = get_conn(config)
    c = conn.cursor()
    t = config['tables']['course']
    tn = t['name']
    cc = t['columns']
    c.execute(f'SELECT "{cc["course_id"]}", "{cc["name"]}", "{cc["score"]}", '
              f'"{cc["teacher"]}", "{cc["location"]}", "{cc["time"]}", '
              f'"{cc["shared"]}" FROM "{tn}" WHERE "{cc["shared"]}"=1')
    rows = c.fetchall()
    conn.close()
    return [{'course_id': r[0], 'name': r[1], 'score': r[2],
             'teacher': r[3], 'location': r[4], 'time': r[5],
             'shared': r[6]} for r in rows]


def get_enrollments(config, student_id=None):
    """Get enrollments, optionally filtered by student."""
    conn = get_conn(config)
    c = conn.cursor()
    t = config['tables']['enrollment']
    tn = t['name']
    ec = t['columns']
    if student_id:
        c.execute(f'SELECT "{ec["student_id"]}", "{ec["course_id"]}", "{ec["score"]}" '
                  f'FROM "{tn}" WHERE "{ec["student_id"]}"=?', (student_id,))
    else:
        c.execute(f'SELECT "{ec["student_id"]}", "{ec["course_id"]}", "{ec["score"]}" '
                  f'FROM "{tn}"')
    rows = c.fetchall()
    conn.close()
    return [{'student_id': r[0], 'course_id': r[1], 'score': r[2]} for r in rows]


def add_enrollment(config, student_id, course_id, score=0):
    """Add an enrollment record."""
    conn = get_conn(config)
    c = conn.cursor()
    t = config['tables']['enrollment']
    tn = t['name']
    ec = t['columns']
    try:
        c.execute(f'INSERT INTO "{tn}" ("{ec["student_id"]}", "{ec["course_id"]}", '
                  f'"{ec["score"]}") VALUES (?, ?, ?)', (student_id, course_id, score))
        conn.commit()
        ok = True
    except sqlite3.IntegrityError:
        ok = False
    conn.close()
    return ok


def delete_enrollment(config, student_id, course_id):
    """Delete an enrollment record."""
    conn = get_conn(config)
    c = conn.cursor()
    t = config['tables']['enrollment']
    tn = t['name']
    ec = t['columns']
    c.execute(f'DELETE FROM "{tn}" WHERE "{ec["student_id"]}"=? AND '
              f'"{ec["course_id"]}"=?', (student_id, course_id))
    conn.commit()
    affected = c.rowcount
    conn.close()
    return affected > 0


def get_student_courses(config, student_id):
    """Get courses with details for a specific student."""
    conn = get_conn(config)
    c = conn.cursor()
    t_en = config['tables']['enrollment']
    t_co = config['tables']['course']
    en = t_en['name']
    cn = t_co['name']
    ec = t_en['columns']
    cc = t_co['columns']
    c.execute(f'SELECT c."{cc["course_id"]}", c."{cc["name"]}", c."{cc["score"]}", '
              f'c."{cc["teacher"]}", c."{cc["location"]}", e."{ec["score"]}" '
              f'FROM "{en}" e JOIN "{cn}" c ON e."{ec["course_id"]}" = c."{cc["course_id"]}" '
              f'WHERE e."{ec["student_id"]}"=?', (student_id,))
    rows = c.fetchall()
    conn.close()
    return [{'course_id': r[0], 'name': r[1], 'score': r[2],
             'teacher': r[3], 'location': r[4], 'grade': r[5]} for r in rows]


def get_college_stats(config):
    """Get statistics for this college."""
    conn = get_conn(config)
    c = conn.cursor()
    t_st = config['tables']['student']  # noqa: F841
    t_co = config['tables']['course']
    t_en = config['tables']['enrollment']
    stn = t_st['name']
    sc = t_st['columns']
    con = t_co['name']
    enn = t_en['name']

    c.execute(f'SELECT COUNT(*) FROM "{stn}"')
    student_count = c.fetchone()[0]

    c.execute(f'SELECT COUNT(*) FROM "{con}"')
    course_count = c.fetchone()[0]

    c.execute(f'SELECT COUNT(*) FROM "{enn}"')
    enrollment_count = c.fetchone()[0]

    conn.close()
    return {
        'student_count': student_count,
        'course_count': course_count,
        'enrollment_count': enrollment_count,
    }
