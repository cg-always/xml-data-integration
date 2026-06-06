"""Database helper for college educational management systems.

Handles connections to three different DBMS:
  - College A: Microsoft SQL Server (via pymssql)
  - College B: Oracle Database (via oracledb thin mode)
  - College C: MySQL (via pymysql)

Uses SQLAlchemy Core as the unified abstraction layer while
preserving each college's heterogeneous table/column naming.
"""

from sqlalchemy import (
    create_engine, MetaData, Table, Column,
    String, Integer, Text, Unicode, text, inspect,
    PrimaryKeyConstraint,
)
from sqlalchemy.exc import IntegrityError
from urllib.parse import quote_plus
import time


# ---------------------------------------------------------------------------
# Engine & connection management
# ---------------------------------------------------------------------------

_engines = {}


def _build_url(config):
    """Build SQLAlchemy connection URL from college database config."""
    db = config['database']
    db_type = db['type']
    driver = db['driver']
    user = quote_plus(db['user'])
    password = quote_plus(db['password'])
    host = db['host']
    port = db['port']

    if db_type == 'mssql':
        # SQL Server: mssql+pymssql://sa:pass@host:port/dbname?charset=utf8
        # Note: tds_version is passed via connect_args in get_engine()
        return (f"mssql+pymssql://{user}:{password}@{host}:{port}"
                f"/{db['name']}?charset=utf8")

    elif db_type == 'oracle':
        # Oracle: oracle+oracledb://user:pass@host:port/?service_name=XEPDB1
        svc = db.get('service_name', 'XEPDB1')
        return (f"oracle+oracledb://{user}:{password}@{host}:{port}"
                f"/?service_name={svc}")

    elif db_type == 'mysql':
        # MySQL: mysql+pymysql://user:pass@host:port/dbname?charset=utf8mb4
        return (f"mysql+pymysql://{user}:{password}@{host}:{port}"
                f"/{db['name']}?charset=utf8mb4")

    else:
        raise ValueError(f"Unsupported database type: {db_type}")


def get_engine(config):
    """Get or create a SQLAlchemy engine for the given college config."""
    col_name = config['name']
    if col_name not in _engines:
        url = _build_url(config)
        db_type = config['database']['type']

        engine_kwargs = {
            'echo': False,
            'pool_size': 5,
            'pool_pre_ping': True,
            'pool_recycle': 1800,
        }

        # pymssql 2.3+ requires explicit tds_version
        if db_type == 'mssql':
            engine_kwargs['connect_args'] = {'tds_version': '7.0'}

        # MySQL: enable ANSI_QUOTES so double-quoted identifiers work
        if db_type == 'mysql':
            engine_kwargs['connect_args'] = {
                'init_command': "SET SESSION sql_mode='ANSI_QUOTES'"
            }

        _engines[col_name] = create_engine(url, **engine_kwargs)
    return _engines[col_name]


def get_conn(config):
    """Get a database connection (raw DBAPI connection).

    Retained for compatibility; new code should use get_engine().
    """
    engine = get_engine(config)
    return engine.raw_connection()


# ---------------------------------------------------------------------------
# Schema helpers
# ---------------------------------------------------------------------------

def _col(table_obj, logical_name):
    """Get actual column name from logical name."""
    return table_obj['columns'][logical_name]


def _tn(config, table_key):
    """Get actual table name."""
    return config['tables'][table_key]['name']


def _cols(config, table_key):
    """Get columns dict for table."""
    return config['tables'][table_key]['columns']


# ---------------------------------------------------------------------------
# Table initialization
# ---------------------------------------------------------------------------

def init_db(config):
    """Initialize database schema for a college.

    Creates the database (if needed) and all required tables
    with college-specific table/column names.
    """
    db_type = config['database']['type']
    engine = get_engine(config)

    # --- Oracle: tables go into user schema; CREATE TABLE IF NOT EXISTS ---
    if db_type == 'oracle':
        _init_tables_oracle(engine, config)
        return

    # --- SQL Server / MySQL: ensure database exists, then create tables ---
    if db_type == 'mssql':
        _ensure_database_mssql(config)
    # MySQL database is pre-created by docker-compose

    # Re-create engine pointing to the target database
    url = _build_url(config)
    engine_kwargs = {
        'echo': False,
        'pool_size': 5,
        'pool_pre_ping': True,
        'pool_recycle': 1800,
    }
    if db_type == 'mssql':
        engine_kwargs['connect_args'] = {'tds_version': '7.0'}
    if db_type == 'mysql':
        engine_kwargs['connect_args'] = {
            'init_command': "SET SESSION sql_mode='ANSI_QUOTES'"
        }
    engine = create_engine(url, **engine_kwargs)
    _engines[config['name']] = engine

    metadata = MetaData()
    tables_cfg = config['tables']

    # Account table
    ac = tables_cfg['account']
    Table(ac['name'], metadata,
          Column(ac['columns']['account_id'], Unicode(50), primary_key=True),
          Column(ac['columns']['password'], Unicode(100), nullable=False),
          Column(ac['columns']['role'], Unicode(20), nullable=False),
          )

    # Student table
    st = tables_cfg['student']
    Table(st['name'], metadata,
          Column(st['columns']['student_id'], Unicode(50), primary_key=True),
          Column(st['columns']['name'], Unicode(100), nullable=False),
          Column(st['columns']['sex'], Unicode(10), nullable=False),
          Column(st['columns']['major'], Unicode(100), nullable=False),
          )

    # Course table
    co = tables_cfg['course']
    Table(co['name'], metadata,
          Column(co['columns']['course_id'], Unicode(50), primary_key=True),
          Column(co['columns']['name'], Unicode(200), nullable=False),
          Column(co['columns']['score'], Integer, nullable=False),
          Column(co['columns']['teacher'], Unicode(100), nullable=False),
          Column(co['columns']['location'], Unicode(200), nullable=False),
          Column(co['columns']['time'], Integer, default=32),
          )

    # Enrollment table (composite PK)
    en = tables_cfg['enrollment']
    Table(en['name'], metadata,
          Column(en['columns']['student_id'], Unicode(50), nullable=False),
          Column(en['columns']['course_id'], Unicode(50), nullable=False),
          Column(en['columns']['score'], Integer, default=0),
          PrimaryKeyConstraint(
              en['columns']['student_id'],
              en['columns']['course_id'],
              name=f"pk_{en['name']}"),
          )

    metadata.create_all(engine, checkfirst=True)


def _ensure_database_mssql(config):
    """Create the SQL Server database if it doesn't exist, with UTF-8 collation."""
    db_cfg = config['database']
    db_name = db_cfg['name']
    user = quote_plus(db_cfg['user'])
    pw = quote_plus(db_cfg['password'])
    master_url = (f"mssql+pymssql://{user}:{pw}"
                  f"@{db_cfg['host']}:{db_cfg['port']}/master"
                  f"?charset=utf8")
    master_engine = create_engine(master_url, echo=False,
                                  pool_pre_ping=True, pool_recycle=1800,
                                  connect_args={'tds_version': '7.0'})

    with master_engine.connect() as conn:
        conn.execute(text(
            f"IF DB_ID('{db_name}') IS NULL "
            f"CREATE DATABASE [{db_name}] "
            f"COLLATE Latin1_General_100_CI_AS_SC_UTF8"
        ))
        conn.commit()

    master_engine.dispose()


def _init_tables_oracle(engine, config):
    """Create tables for Oracle using PL/SQL exception handling.

    Oracle doesn't support IF NOT EXISTS in standard CREATE TABLE,
    so we catch ORA-00955 (table already exists) gracefully.
    """
    tables_cfg = config['tables']

    table_defs = []

    # Account table
    ac = tables_cfg['account']
    ac_c = ac['columns']
    table_defs.append(f'''
        CREATE TABLE "{ac['name']}" (
            "{ac_c['account_id']}" VARCHAR2(50) PRIMARY KEY,
            "{ac_c['password']}" VARCHAR2(100) NOT NULL,
            "{ac_c['role']}" VARCHAR2(20) NOT NULL
        )''')

    # Student table
    st = tables_cfg['student']
    sc = st['columns']
    table_defs.append(f'''
        CREATE TABLE "{st['name']}" (
            "{sc['student_id']}" VARCHAR2(50) PRIMARY KEY,
            "{sc['name']}" VARCHAR2(100) NOT NULL,
            "{sc['sex']}" VARCHAR2(10) NOT NULL,
            "{sc['major']}" VARCHAR2(100) NOT NULL
        )''')

    # Course table
    co = tables_cfg['course']
    cc = co['columns']
    table_defs.append(f'''
        CREATE TABLE "{co['name']}" (
            "{cc['course_id']}" VARCHAR2(50) PRIMARY KEY,
            "{cc['name']}" VARCHAR2(200) NOT NULL,
            "{cc['score']}" NUMBER(10) NOT NULL,
            "{cc['teacher']}" VARCHAR2(100) NOT NULL,
            "{cc['location']}" VARCHAR2(200) NOT NULL,
            "{cc['time']}" NUMBER(10) DEFAULT 32
        )''')

    # Enrollment table (composite PK without constraint name)
    en = tables_cfg['enrollment']
    ec = en['columns']
    table_defs.append(f'''
        CREATE TABLE "{en['name']}" (
            "{ec['student_id']}" VARCHAR2(50) NOT NULL,
            "{ec['course_id']}" VARCHAR2(50) NOT NULL,
            "{ec['score']}" NUMBER(10) DEFAULT 0,
            PRIMARY KEY ("{ec['student_id']}", "{ec['course_id']}")
        )''')

    with engine.connect() as conn:
        for ddl in table_defs:
            try:
                conn.execute(text(ddl))
                conn.commit()
            except Exception as e:
                # ORA-00955: name is already used by an existing object
                if 'ORA-00955' in str(e) or 'already exists' in str(e).lower():
                    pass  # Table exists, skip
                else:
                    raise


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def verify_login(config, username, password):
    """Verify login credentials. Returns (success, role) or (False, None)."""
    engine = get_engine(config)
    t = config['tables']['account']
    tn = t['name']
    cn_id = t['columns']['account_id']
    cn_pw = t['columns']['password']
    cn_role = t['columns']['role']

    with engine.connect() as conn:
        result = conn.execute(
            text(f'SELECT "{cn_role}" FROM "{tn}" '
                 f'WHERE "{cn_id}" = :uid AND "{cn_pw}" = :pwd'),
            {'uid': username, 'pwd': password}
        )
        row = result.fetchone()
    if row:
        return True, row[0]
    return False, None


# ---------------------------------------------------------------------------
# Student operations
# ---------------------------------------------------------------------------

def get_student(config, student_id):
    """Get student by ID."""
    engine = get_engine(config)
    t = config['tables']['student']
    tn = t['name']
    sc = t['columns']

    with engine.connect() as conn:
        result = conn.execute(
            text(f'SELECT "{sc["student_id"]}", "{sc["name"]}", '
                 f'"{sc["sex"]}", "{sc["major"]}" '
                 f'FROM "{tn}" WHERE "{sc["student_id"]}" = :sid'),
            {'sid': student_id}
        )
        row = result.fetchone()
    if row:
        return {
            'student_id': row[0], 'name': row[1],
            'sex': row[2], 'major': row[3]
        }
    return None


def get_all_students(config):
    """Get all students."""
    engine = get_engine(config)
    t = config['tables']['student']
    tn = t['name']
    sc = t['columns']

    with engine.connect() as conn:
        result = conn.execute(
            text(f'SELECT "{sc["student_id"]}", "{sc["name"]}", '
                 f'"{sc["sex"]}", "{sc["major"]}" FROM "{tn}"')
        )
        rows = result.fetchall()
    return [{'student_id': r[0], 'name': r[1],
             'sex': r[2], 'major': r[3]} for r in rows]


# ---------------------------------------------------------------------------
# Course operations
# ---------------------------------------------------------------------------

def get_course(config, course_id):
    """Get course by ID."""
    engine = get_engine(config)
    t = config['tables']['course']
    tn = t['name']
    cc = t['columns']

    with engine.connect() as conn:
        result = conn.execute(
            text(f'SELECT "{cc["course_id"]}", "{cc["name"]}", '
                 f'"{cc["score"]}", "{cc["teacher"]}", '
                 f'"{cc["location"]}", "{cc["time"]}" '
                 f'FROM "{tn}" WHERE "{cc["course_id"]}" = :cid'),
            {'cid': course_id}
        )
        row = result.fetchone()
    if row:
        return {
            'course_id': row[0], 'name': row[1], 'score': row[2],
            'teacher': row[3], 'location': row[4], 'time': row[5]
        }
    return None


def get_all_courses(config):
    """Get all courses."""
    engine = get_engine(config)
    t = config['tables']['course']
    tn = t['name']
    cc = t['columns']

    with engine.connect() as conn:
        result = conn.execute(
            text(f'SELECT "{cc["course_id"]}", "{cc["name"]}", '
                 f'"{cc["score"]}", "{cc["teacher"]}", '
                 f'"{cc["location"]}", "{cc["time"]}" FROM "{tn}"')
        )
        rows = result.fetchall()
    return [{'course_id': r[0], 'name': r[1], 'score': r[2],
             'teacher': r[3], 'location': r[4], 'time': r[5]} for r in rows]


# ---------------------------------------------------------------------------
# Enrollment operations
# ---------------------------------------------------------------------------

def get_enrollments(config, student_id=None):
    """Get enrollments, optionally filtered by student."""
    engine = get_engine(config)
    t = config['tables']['enrollment']
    tn = t['name']
    ec = t['columns']

    with engine.connect() as conn:
        if student_id:
            result = conn.execute(
                text(f'SELECT "{ec["student_id"]}", "{ec["course_id"]}", '
                     f'"{ec["score"]}" FROM "{tn}" '
                     f'WHERE "{ec["student_id"]}" = :sid'),
                {'sid': student_id}
            )
        else:
            result = conn.execute(
                text(f'SELECT "{ec["student_id"]}", "{ec["course_id"]}", '
                     f'"{ec["score"]}" FROM "{tn}"')
            )
        rows = result.fetchall()
    return [{'student_id': r[0], 'course_id': r[1], 'score': r[2]}
            for r in rows]


def add_enrollment(config, student_id, course_id, score=0):
    """Add an enrollment record."""
    engine = get_engine(config)
    t = config['tables']['enrollment']
    tn = t['name']
    ec = t['columns']

    with engine.connect() as conn:
        try:
            conn.execute(
                text(f'INSERT INTO "{tn}" ("{ec["student_id"]}", '
                     f'"{ec["course_id"]}", "{ec["score"]}") '
                     f'VALUES (:sid, :cid, :sc)'),
                {'sid': student_id, 'cid': course_id, 'sc': score}
            )
            conn.commit()
            ok = True
        except IntegrityError:
            conn.rollback()
            ok = False
        except Exception:
            conn.rollback()
            ok = False
    return ok


def delete_enrollment(config, student_id, course_id):
    """Delete an enrollment record."""
    engine = get_engine(config)
    t = config['tables']['enrollment']
    tn = t['name']
    ec = t['columns']

    with engine.connect() as conn:
        result = conn.execute(
            text(f'DELETE FROM "{tn}" '
                 f'WHERE "{ec["student_id"]}" = :sid '
                 f'AND "{ec["course_id"]}" = :cid'),
            {'sid': student_id, 'cid': course_id}
        )
        conn.commit()
        affected = result.rowcount
    return affected > 0


# ---------------------------------------------------------------------------
# Joined queries
# ---------------------------------------------------------------------------

def get_student_courses(config, student_id):
    """Get courses with enrollment details for a specific student."""
    engine = get_engine(config)
    t_en = config['tables']['enrollment']
    t_co = config['tables']['course']
    en = t_en['name']
    cn = t_co['name']
    ec = t_en['columns']
    cc = t_co['columns']

    with engine.connect() as conn:
        result = conn.execute(
            text(f'SELECT c."{cc["course_id"]}", c."{cc["name"]}", '
                 f'c."{cc["score"]}", c."{cc["teacher"]}", '
                 f'c."{cc["location"]}", e."{ec["score"]}" '
                 f'FROM "{en}" e JOIN "{cn}" c '
                 f'ON e."{ec["course_id"]}" = c."{cc["course_id"]}" '
                 f'WHERE e."{ec["student_id"]}" = :sid'),
            {'sid': student_id}
        )
        rows = result.fetchall()
    return [{'course_id': r[0], 'name': r[1], 'score': r[2],
             'teacher': r[3], 'location': r[4], 'grade': r[5]} for r in rows]


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def get_college_stats(config):
    """Get statistics for this college."""
    engine = get_engine(config)
    t_st = config['tables']['student']
    t_co = config['tables']['course']
    t_en = config['tables']['enrollment']
    stn = t_st['name']
    con = t_co['name']
    enn = t_en['name']

    with engine.connect() as conn:
        result = conn.execute(text(f'SELECT COUNT(*) FROM "{stn}"'))
        student_count = result.fetchone()[0]

        result = conn.execute(text(f'SELECT COUNT(*) FROM "{con}"'))
        course_count = result.fetchone()[0]

        result = conn.execute(text(f'SELECT COUNT(*) FROM "{enn}"'))
        enrollment_count = result.fetchone()[0]

    return {
        'student_count': student_count,
        'course_count': course_count,
        'enrollment_count': enrollment_count,
    }
