"""College Educational Management System — Flask Application.

This module serves as the configurable Flask app for each college (A, B, C).
It adapts its database schema, templates, and behavior based on the college
configuration file.

Each college runs independently with its own database schema simulating
different DBMS implementations (SQL Server, Oracle, MySQL).
"""

import json
import os
import sys
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, Response, jsonify
from lxml import etree
import requests as http_requests

# Add parent dir to path for shared imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from college.db import (
    init_db, verify_login, get_student, get_all_students,
    get_course, get_all_courses, get_enrollments, get_student_courses,
    add_enrollment, delete_enrollment, get_college_stats,
)
from college.xml_api import (
    students_to_unified_xml, courses_to_unified_xml,
    enrollments_to_unified_xml, parse_enrollments_xml, parse_delete_enrollment_xml,
)
from shared.xml_schemas import XSD_MAP


def create_college_app(config_path):
    """Create and configure a Flask app for a specific college."""
    # Load config
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)

    app = Flask(__name__, template_folder='templates')
    app.secret_key = f'college_{config["name"]}_secret_key_2024'

    # Initialize database
    init_db(config)

    # ---- Authentication decorators ----

    def login_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user' not in session:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated

    def admin_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user' not in session or session.get('role') != 'admin':
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated

    # ---- Routes ----

    @app.route('/')
    def index():
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        error = None
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            if username and password:
                ok, role = verify_login(config, username, password)
                if ok:
                    session['user'] = username
                    session['role'] = role
                    if role == 'admin':
                        return redirect(url_for('admin'))
                    return redirect(url_for('student'))
                error = '用户名或密码错误'
            else:
                error = '请输入用户名和密码'
        return render_template('login.html', config=config, error=error)

    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))

    def _fetch_external_enrollments(student_id):
        """Fetch cross-college enrollment records for a student from other colleges."""
        my_college = config['name']
        all_colleges = {
            'A': {'name': '学院A', 'port': 5001},
            'B': {'name': '学院B', 'port': 5002},
            'C': {'name': '学院C', 'port': 5003},
        }
        external_courses = []
        for col_key, col_info in all_colleges.items():
            if col_key == my_college:
                continue
            try:
                # Get all enrollments from the target college
                resp = http_requests.get(
                    f'http://127.0.0.1:{col_info["port"]}/api/xml/enrollments',
                    timeout=5)
                resp.encoding = 'utf-8'
                root = etree.fromstring(resp.text.encode('utf-8'))
                # Find enrollments for this student
                student_enrolled_cids = []
                for el in root.findall('choice'):
                    sid = el.findtext('sid', '')
                    cid = el.findtext('cid', '')
                    if sid == student_id and cid:
                        student_enrolled_cids.append(cid)

                # Get course details for each enrolled course
                for cid in student_enrolled_cids:
                    try:
                        course_resp = http_requests.get(
                            f'http://127.0.0.1:{col_info["port"]}/api/xml/courses',
                            timeout=5)
                        course_resp.encoding = 'utf-8'
                        course_root = etree.fromstring(course_resp.text.encode('utf-8'))
                        for cel in course_root.findall('class'):
                            if cel.findtext('id', '') == cid:
                                external_courses.append({
                                    'course_id': cid,
                                    'name': cel.findtext('name', ''),
                                    'score': cel.findtext('score', '0'),
                                    'teacher': cel.findtext('teacher', ''),
                                    'location': cel.findtext('location', ''),
                                    'grade': 0,
                                    'college': col_key,
                                    'college_name': col_info['name'],
                                    'is_external': True,
                                })
                                break
                    except Exception:
                        pass
            except Exception:
                pass
        return external_courses

    @app.route('/student')
    @login_required
    def student():
        student_id = session['user']
        student_info = get_student(config, student_id)
        if not student_info:
            return '学生信息不存在', 404

        # Local enrolled courses
        enrolled_courses = get_student_courses(config, student_id)

        # Cross-college enrolled courses from other colleges
        external_courses = _fetch_external_enrollments(student_id)

        # Combine local and external enrolled courses
        all_enrolled = enrolled_courses + external_courses

        all_courses = get_all_courses(config)
        enrolled_ids = {c['course_id'] for c in all_enrolled}
        available_courses = [c for c in all_courses if c['course_id'] not in enrolled_ids]

        return render_template('student_dashboard.html',
                             config=config,
                             student=student_info,
                             enrolled=all_enrolled,
                             available=available_courses)

    @app.route('/student/cross-college')
    @login_required
    def cross_college_courses():
        """Display courses from other colleges for cross-college enrollment."""
        student_id = session['user']
        student_info = get_student(config, student_id)
        if not student_info:
            return '学生信息不存在', 404

        # Get ALL enrolled courses (local + external) to exclude already-enrolled
        local_enrolled = get_student_courses(config, student_id)
        external_enrolled = _fetch_external_enrollments(student_id)
        all_enrolled_ids = {c['course_id'] for c in local_enrolled + external_enrolled}

        # Determine which colleges are "other" colleges
        my_college = config['name']
        other_colleges = {
            k: v for k, v in {
                'A': {'name': '学院A', 'port': 5001},
                'B': {'name': '学院B', 'port': 5002},
                'C': {'name': '学院C', 'port': 5003},
            }.items() if k != my_college
        }

        # Fetch courses from other colleges
        all_external_courses = []
        college_errors = []
        for col_key, col_info in other_colleges.items():
            try:
                resp = http_requests.get(
                    f'http://127.0.0.1:{col_info["port"]}/api/xml/courses',
                    timeout=5)
                resp.encoding = 'utf-8'
                root = etree.fromstring(resp.text.encode('utf-8'))
                for el in root.findall('class'):
                    cid = el.findtext('id', '')
                    if cid not in all_enrolled_ids:
                        all_external_courses.append({
                            'course_id': cid,
                            'name': el.findtext('name', ''),
                            'score': el.findtext('score', '0'),
                            'teacher': el.findtext('teacher', ''),
                            'location': el.findtext('location', ''),
                            'time': el.findtext('time', '32'),
                            'college': col_key,
                            'college_name': col_info['name'],
                        })
            except Exception as e:
                college_errors.append(f'{col_info["name"]}: {str(e)}')

        message = request.args.get('message')
        message_type = request.args.get('message_type')

        return render_template('student_dashboard.html',
                             config=config,
                             student=student_info,
                             cross_college=True,
                             external_courses=all_external_courses,
                             other_colleges=other_colleges,
                             college_errors=college_errors,
                             message=message,
                             message_type=message_type)

    @app.route('/student/cross-college/enroll', methods=['POST'])
    @login_required
    def cross_college_enroll():
        """Enroll in a course from another college."""
        student_id = session['user']
        course_id = request.form.get('course_id', '').strip()

        if not course_id:
            return redirect(url_for('cross_college_courses',
                                    message='请输入课程编号',
                                    message_type='error'))

        # Determine target college from course ID
        target_college = None
        target_port = None
        all_colleges = {
            'A': 5001, 'B': 5002, 'C': 5003,
        }
        for col_key, port in all_colleges.items():
            if course_id.startswith(f'COU{col_key}'):
                target_college = col_key
                target_port = port
                break

        if not target_college:
            return redirect(url_for('cross_college_courses',
                                    message='无法识别课程编号',
                                    message_type='error'))

        # Build enrollment XML
        xml_root = etree.Element('Choices')
        choice = etree.SubElement(xml_root, 'choice')
        etree.SubElement(choice, 'sid').text = student_id
        etree.SubElement(choice, 'cid').text = course_id
        etree.SubElement(choice, 'score').text = '0'
        xml_data = etree.tostring(xml_root, encoding='utf-8', xml_declaration=True)

        # Send to target college
        try:
            resp = http_requests.post(
                f'http://127.0.0.1:{target_port}/api/xml/enrollments/import',
                data=xml_data,
                headers={'Content-Type': 'application/xml'},
                timeout=5)
            result_root = etree.fromstring(resp.text.encode('utf-8')
                                          if isinstance(resp.text, str)
                                          else resp.text)
            status = result_root.findtext('status', 'error')
            if status == 'ok':
                imported = result_root.findtext('imported', '0')
                if int(imported) > 0:
                    college_names = {'A': '学院A', 'B': '学院B', 'C': '学院C'}
                    return redirect(url_for('cross_college_courses',
                                            message=f'跨院选课成功！已选修{college_names.get(target_college, target_college)}的课程 {course_id}',
                                            message_type='success'))
                else:
                    return redirect(url_for('cross_college_courses',
                                            message='选课失败，可能已选过该课程',
                                            message_type='error'))
            else:
                msg = result_root.findtext('message', '未知错误')
                return redirect(url_for('cross_college_courses',
                                        message=f'选课失败: {msg}',
                                        message_type='error'))
        except Exception as e:
            return redirect(url_for('cross_college_courses',
                                    message=f'请求失败: {str(e)}',
                                    message_type='error'))

    @app.route('/admin')
    @login_required
    @admin_required
    def admin():
        stats = get_college_stats(config)
        students = get_all_students(config)
        courses = get_all_courses(config)
        return render_template('admin_dashboard.html',
                             config=config,
                             stats=stats,
                             students=students,
                             courses=courses)

    # ---- XML API endpoints (for integration server) ----

    @app.route('/api/xml/students')
    def api_xml_students():
        """Export all students as unified XML."""
        students = get_all_students(config)
        xml_data = students_to_unified_xml(students)

        # Add college source attribute
        root = etree.fromstring(xml_data)
        root.set('college', config['name'])
        xml_data = etree.tostring(root, encoding='utf-8', xml_declaration=True)

        return Response(xml_data, mimetype='application/xml')

    @app.route('/api/xml/courses')
    def api_xml_courses():
        """Export all courses as unified XML."""
        courses = get_all_courses(config)
        xml_data = courses_to_unified_xml(courses)

        root = etree.fromstring(xml_data)
        root.set('college', config['name'])
        xml_data = etree.tostring(root, encoding='utf-8', xml_declaration=True)

        return Response(xml_data, mimetype='application/xml')

    @app.route('/api/xml/enrollments')
    def api_xml_enrollments():
        """Export all enrollments as unified XML."""
        enrollments = get_enrollments(config)
        xml_data = enrollments_to_unified_xml(enrollments)

        root = etree.fromstring(xml_data)
        root.set('college', config['name'])
        xml_data = etree.tostring(root, encoding='utf-8', xml_declaration=True)

        return Response(xml_data, mimetype='application/xml')

    @app.route('/api/xml/schema/<data_type>')
    def api_xml_schema(data_type):
        """Serve XSD schema for validation."""
        if data_type in XSD_MAP:
            return Response(XSD_MAP[data_type], mimetype='application/xml')
        return 'Schema not found', 404

    @app.route('/api/xml/enrollments/import', methods=['POST'])
    def api_import_enrollments():
        """Import enrollment data from unified XML.

        Receives enrollment XML, parses it, and inserts into local DB.
        Used when a student from another college enrolls in this college's course.
        """
        try:
            xml_data = request.data
            enrollments = parse_enrollments_xml(xml_data)
            imported = 0
            for enr in enrollments:
                if add_enrollment(config, enr['student_id'],
                                enr['course_id'], enr['score']):
                    imported += 1
            return f'<result><status>ok</status><imported>{imported}</imported></result>', 200
        except Exception as e:
            return f'<result><status>error</status><message>{str(e)}</message></result>', 400

    @app.route('/api/xml/enrollments/delete', methods=['POST'])
    def api_delete_enrollments():
        """Delete enrollment data from unified XML.

        Used for course withdrawal in the integrated environment.
        """
        try:
            xml_data = request.data
            enrollments = parse_delete_enrollment_xml(xml_data)
            deleted = 0
            for enr in enrollments:
                if delete_enrollment(config, enr['student_id'], enr['course_id']):
                    deleted += 1
            return f'<result><status>ok</status><deleted>{deleted}</deleted></result>', 200
        except Exception as e:
            return f'<result><status>error</status><message>{str(e)}</message></result>', 400

    @app.route('/api/stats')
    def api_stats():
        """Return college statistics as JSON for the integration server."""
        return get_college_stats(config)

    @app.route('/api/student/<student_id>')
    def api_student_info(student_id):
        """Return student info as JSON — used by integration server to verify students."""
        student = get_student(config, student_id)
        if student:
            return {'found': True, 'name': student['name'],
                    'college': config['name'], 'college_cn': config['name_cn']}
        return {'found': False}

    return app
