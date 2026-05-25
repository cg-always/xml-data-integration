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

from flask import Flask, render_template, request, redirect, url_for, session, Response
from lxml import etree

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

    @app.route('/student')
    @login_required
    def student():
        student_id = session['user']
        student_info = get_student(config, student_id)
        if not student_info:
            return '学生信息不存在', 404

        enrolled_courses = get_student_courses(config, student_id)
        all_courses = get_all_courses(config)
        enrolled_ids = {c['course_id'] for c in enrolled_courses}
        available_courses = [c for c in all_courses if c['course_id'] not in enrolled_ids]

        return render_template('student_dashboard.html',
                             config=config,
                             student=student_info,
                             enrolled=enrolled_courses,
                             available=available_courses)

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
