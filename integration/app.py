"""Integration Server — Central hub for cross-college course sharing.

Handles:
- Aggregating shared courses from all three colleges (A, B, C)
- Cross-college enrollment (student from College A enrolls in College B's course)
- Cross-college course withdrawal
- Unified statistics across all colleges
- XML-based data exchange and XSLT transformation
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify
import requests
from lxml import etree

# ---- Configuration ----

COLLEGES = {
    'A': {'name': '学院A', 'port': 5001, 'dbms': 'SQL Server'},
    'B': {'name': '学院B', 'port': 5002, 'dbms': 'Oracle'},
    'C': {'name': '学院C', 'port': 5003, 'dbms': 'MySQL'},
}

INTEGRATION_PORT = 5000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
XSLT_DIR = os.path.join(BASE_DIR, 'xslt')

app = Flask(__name__, template_folder='templates')
app.secret_key = 'integration_server_secret_2024'


# ---- XSD Validation ----

SCHEMA_DIR = os.path.join(BASE_DIR, 'schema')

def validate_xml_against_xsd(xml_data, xsd_filename):
    """Validate XML data against an XSD schema file.

    Returns (is_valid, error_message).
    """
    xsd_path = os.path.join(SCHEMA_DIR, xsd_filename)
    if not os.path.exists(xsd_path):
        return False, f'Schema file not found: {xsd_filename}'

    try:
        xml_doc = etree.fromstring(
            xml_data.encode('utf-8') if isinstance(xml_data, str) else xml_data)
        xsd_doc = etree.parse(xsd_path)
        schema = etree.XMLSchema(xsd_doc)
        schema.assertValid(xml_doc)
        return True, None
    except etree.DocumentInvalid as e:
        return False, str(e)
    except etree.XMLSyntaxError as e:
        return False, f'XML parse error: {e}'


# ---- XSLT Helpers ----

def xslt_transform(xml_data, xslt_filename):
    """Apply XSLT transformation to XML data."""
    xslt_path = os.path.join(XSLT_DIR, xslt_filename)
    if not os.path.exists(xslt_path):
        return xml_data  # Return original if XSLT not found

    xml_doc = etree.fromstring(xml_data.encode('utf-8') if isinstance(xml_data, str) else xml_data)
    xslt_doc = etree.parse(xslt_path)
    transform = etree.XSLT(xslt_doc)
    result = transform(xml_doc)
    return str(result)


def fetch_college_native_via_xslt(college_name, data_type, timeout=5):
    """Fetch native XML from a college and transform to unified format via XSLT.

    data_type: 'students', 'courses', or 'enrollments'
    """
    # Map data type to native endpoint, XSLT file, and XSD schema
    mapping = {
        'students': ('/api/xml/native/students', 'formatStudent.xsl', 'student.xsd'),
        'courses': ('/api/xml/native/courses', 'formatClass.xsl', 'class.xsd'),
        'enrollments': ('/api/xml/native/enrollments', 'formatChoice.xsl', 'choice.xsd'),
    }
    if data_type not in mapping:
        return None

    endpoint, xslt_file, xsd_file = mapping[data_type]
    native_xml = fetch_college_xml(college_name, endpoint, timeout)
    if not native_xml:
        return None

    # Apply XSLT to convert from native to unified format
    unified_xml = xslt_transform(native_xml, xslt_file)

    # Validate the transformed XML against XSD schema
    is_valid, error = validate_xml_against_xsd(unified_xml, xsd_file)
    if not is_valid:
        print(f'[XSD 验证失败] {college_name}/{data_type}: {error}')

    return unified_xml


def fetch_college_xml(college_name, endpoint, timeout=5):
    """Fetch XML data from a college server."""
    cfg = COLLEGES[college_name]
    url = f'http://127.0.0.1:{cfg["port"]}{endpoint}'
    try:
        resp = requests.get(url, timeout=timeout)
        resp.encoding = 'utf-8'
        return resp.text
    except requests.RequestException as e:
        return None


def fetch_college_json(college_name, endpoint, timeout=5):
    """Fetch JSON data from a college server."""
    cfg = COLLEGES[college_name]
    url = f'http://127.0.0.1:{cfg["port"]}{endpoint}'
    try:
        resp = requests.get(url, timeout=timeout)
        return resp.json()
    except requests.RequestException:
        return None


def post_college_xml(college_name, endpoint, xml_data, timeout=5):
    """POST XML data to a college server."""
    cfg = COLLEGES[college_name]
    url = f'http://127.0.0.1:{cfg["port"]}{endpoint}'
    try:
        if isinstance(xml_data, str):
            xml_data = xml_data.encode('utf-8')
        resp = requests.post(url, data=xml_data,
                           headers={'Content-Type': 'application/xml'},
                           timeout=timeout)
        return resp.text, resp.status_code
    except requests.RequestException as e:
        return str(e), 500


def parse_courses_from_xml(xml_data, college):
    """Parse unified course XML into list of dicts with college info."""
    if not xml_data:
        return []
    root = etree.fromstring(xml_data.encode('utf-8'))
    courses = []
    for el in root.findall('class'):
        courses.append({
            'course_id': el.findtext('id', ''),
            'name': el.findtext('name', ''),
            'score': el.findtext('score', '0'),
            'time': el.findtext('time', '32'),
            'teacher': el.findtext('teacher', ''),
            'location': el.findtext('location', ''),
            'shared': el.findtext('shared', '1'),
            'college': college,
            'college_name': COLLEGES[college]['name'],
            'dbms': COLLEGES[college]['dbms'],
        })
    return courses


def parse_students_from_xml(xml_data, college):
    """Parse unified student XML into list of dicts."""
    if not xml_data:
        return []
    root = etree.fromstring(xml_data.encode('utf-8'))
    students = []
    for el in root.findall('student'):
        students.append({
            'student_id': el.findtext('id', ''),
            'name': el.findtext('name', ''),
            'sex': el.findtext('sex', ''),
            'major': el.findtext('major', ''),
            'college': college,
            'college_name': COLLEGES[college]['name'],
        })
    return students


def parse_enrollments_with_course(xml_data, college):
    """Parse unified enrollment XML and return list with course details.

    Each enrollment includes student_id, course_id, score, and college info.
    """
    if not xml_data:
        return []
    root = etree.fromstring(xml_data.encode('utf-8'))
    enrollments = []
    for el in root.findall('choice'):
        enrollments.append({
            'student_id': el.findtext('sid', ''),
            'course_id': el.findtext('cid', ''),
            'score': el.findtext('score', '0'),
            'college': college,
            'college_name': COLLEGES[college]['name'],
        })
    return enrollments


def build_enrollment_xml(student_id, course_id, score=0):
    """Build unified enrollment XML for sending to colleges."""
    root = etree.Element('Choices')
    choice = etree.SubElement(root, 'choice')
    etree.SubElement(choice, 'sid').text = str(student_id)
    etree.SubElement(choice, 'cid').text = str(course_id)
    etree.SubElement(choice, 'score').text = str(score)
    return etree.tostring(root, encoding='utf-8', xml_declaration=True)


# ---- Routes ----

@app.route('/')
def index():
    """Main dashboard."""
    return render_template('integrated_dashboard.html', colleges=COLLEGES)


@app.route('/courses/shared')
def shared_courses():
    """Display all shared courses from all colleges via XSLT transformation."""
    all_courses = []
    for col_key in COLLEGES:
        # Use XSLT to fetch native XML and transform to unified format
        xml_data = fetch_college_native_via_xslt(col_key, 'courses')
        if xml_data:
            courses = parse_courses_from_xml(xml_data, col_key)
            # Filter only shared courses
            shared = [c for c in courses if c.get('shared', '1') == '1']
            all_courses.extend(shared)
    return render_template('integrated_dashboard.html',
                         colleges=COLLEGES,
                         all_courses=all_courses,
                         active_tab='courses')


@app.route('/students/all')
def all_students():
    """Display all students from all colleges via XSLT."""
    all_students_list = []
    for col_key in COLLEGES:
        xml_data = fetch_college_native_via_xslt(col_key, 'students')
        if xml_data:
            students = parse_students_from_xml(xml_data, col_key)
            all_students_list.extend(students)
    return render_template('integrated_dashboard.html',
                         colleges=COLLEGES,
                         all_students=all_students_list,
                         active_tab='students')


@app.route('/statistics')
def statistics():
    """Unified statistics across all colleges."""
    stats = {'total_students': 0, 'total_courses': 0, 'total_enrollments': 0}
    college_details = {}

    for col_key, col_info in COLLEGES.items():
        data = fetch_college_json(col_key, '/api/stats')
        if data:
            college_details[col_key] = {
                'name': col_info['name'],
                'dbms': col_info['dbms'],
                'students': data.get('student_count', 0),
                'courses': data.get('course_count', 0),
                'enrollments': data.get('enrollment_count', 0),
            }
            stats['total_students'] += data.get('student_count', 0)
            stats['total_courses'] += data.get('course_count', 0)
            stats['total_enrollments'] += data.get('enrollment_count', 0)
        else:
            college_details[col_key] = {
                'name': col_info['name'],
                'dbms': col_info['dbms'],
                'students': '离线',
                'courses': '离线',
                'enrollments': '离线',
            }

    return render_template('integrated_dashboard.html',
                         colleges=COLLEGES,
                         stats=stats,
                         college_details=college_details,
                         active_tab='stats')


@app.route('/enroll', methods=['GET', 'POST'])
def cross_college_enroll():
    """Cross-college enrollment page."""
    message = None
    message_type = None

    # Load all courses for display via XSLT
    all_courses = []
    for col_key in COLLEGES:
        xml_data = fetch_college_native_via_xslt(col_key, 'courses')
        if xml_data:
            courses = parse_courses_from_xml(xml_data, col_key)
            all_courses.extend(courses)

    if request.method == 'POST':
        student_id = request.form.get('student_id', '').strip()
        course_id = request.form.get('course_id', '').strip()

        if not student_id or not course_id:
            message = '请输入学号和课程编号'
            message_type = 'error'
        else:
            # Determine which college the course belongs to
            target_college = None
            for col_key in COLLEGES:
                if course_id.startswith(f'COU{col_key}'):
                    target_college = col_key
                    break

            if not target_college:
                message = '无法识别课程编号，请检查后重试'
                message_type = 'error'
            else:
                # Determine which college the student belongs to
                student_college = None
                for col_key in COLLEGES:
                    if student_id.startswith(f'STU{col_key}'):
                        student_college = col_key
                        break

                if not student_college:
                    message = '无法识别学号，请检查后重试'
                    message_type = 'error'
                else:
                    # Verify student exists
                    student_info = fetch_college_json(
                        student_college, f'/api/student/{student_id}')

                    if not student_info or not student_info.get('found'):
                        message = f'学号 {student_id} 不存在于{COLLEGES[student_college]["name"]}'
                        message_type = 'error'
                    else:
                        # Send enrollment XML to the target college
                        xml_data = build_enrollment_xml(student_id, course_id)
                        result_text, status_code = post_college_xml(
                            target_college, '/api/xml/enrollments/import', xml_data)

                        try:
                            result_root = etree.fromstring(
                                result_text.encode('utf-8') if isinstance(result_text, str)
                                else result_text)
                            status = result_root.findtext('status', 'error')
                            if status == 'ok':
                                imported = result_root.findtext('imported', '0')
                                if int(imported) > 0:
                                    message = (f'选课成功！学生 {student_id} ({student_info["name"]}) '
                                             f'已选修 {COLLEGES[target_college]["name"]} '
                                             f'的课程 {course_id}')
                                    message_type = 'success'
                                else:
                                    message = '选课失败，可能已选过该课程'
                                    message_type = 'error'
                            else:
                                message = f'选课失败: {result_root.findtext("message", "未知错误")}'
                                message_type = 'error'
                        except Exception:
                            message = f'服务器响应异常: {result_text}'
                            message_type = 'error'

    return render_template('integrated_dashboard.html',
                         colleges=COLLEGES,
                         all_courses=all_courses,
                         message=message,
                         message_type=message_type,
                         active_tab='enroll')


@app.route('/withdraw', methods=['GET', 'POST'])
def cross_college_withdraw():
    """Cross-college course withdrawal page."""
    message = None
    message_type = None

    if request.method == 'POST':
        student_id = request.form.get('student_id', '').strip()
        course_id = request.form.get('course_id', '').strip()

        if not student_id or not course_id:
            message = '请输入学号和课程编号'
            message_type = 'error'
        else:
            # Determine the target college from the course ID
            target_college = None
            for col_key in COLLEGES:
                if course_id.startswith(f'COU{col_key}'):
                    target_college = col_key
                    break

            if not target_college:
                message = '无法识别课程编号'
                message_type = 'error'
            else:
                # Build delete enrollment XML
                xml_data = build_enrollment_xml(student_id, course_id)
                result_text, status_code = post_college_xml(
                    target_college, '/api/xml/enrollments/delete', xml_data)

                try:
                    result_root = etree.fromstring(
                        result_text.encode('utf-8') if isinstance(result_text, str)
                        else result_text)
                    status = result_root.findtext('status', 'error')
                    if status == 'ok':
                        deleted = result_root.findtext('deleted', '0')
                        if int(deleted) > 0:
                            message = (f'退课成功！学生 {student_id} 已退出 '
                                     f'{COLLEGES[target_college]["name"]} 的课程 {course_id}')
                            message_type = 'success'
                        else:
                            message = '退课失败，未找到对应选课记录'
                            message_type = 'error'
                    else:
                        message = f'退课失败: {result_root.findtext("message", "未知错误")}'
                        message_type = 'error'
                except Exception:
                    message = f'服务器响应异常: {result_text}'
                    message_type = 'error'

    return render_template('integrated_dashboard.html',
                         colleges=COLLEGES,
                         message=message,
                         message_type=message_type,
                         active_tab='withdraw')


@app.route('/my-courses', methods=['GET', 'POST'])
def my_cross_college_courses():
    """Query a student's cross-college enrollments across all colleges."""
    enrollments = None
    student_id = None
    message = None
    message_type = None

    if request.method == 'POST':
        student_id = request.form.get('student_id', '').strip()
        if not student_id:
            message = '请输入学号'
            message_type = 'error'
        else:
            # Determine student's home college
            student_college = None
            for col_key in COLLEGES:
                if student_id.startswith(f'STU{col_key}'):
                    student_college = col_key
                    break

            if not student_college:
                message = '无法识别学号，请检查后重试'
                message_type = 'error'
            else:
                # Fetch enrollments from all colleges via XSLT
                all_enrollments = []
                for col_key in COLLEGES:
                    xml_data = fetch_college_native_via_xslt(col_key, 'enrollments')
                    if xml_data:
                        parsed = parse_enrollments_with_course(xml_data, col_key)
                        all_enrollments.extend(parsed)

                # Filter for this student
                enrollments = [e for e in all_enrollments
                             if e['student_id'] == student_id]

                # Separate home college courses and cross-college courses
                home_courses = []
                cross_courses = []
                for e in enrollments:
                    if e['college'] == student_college:
                        home_courses.append(e)
                    else:
                        cross_courses.append(e)

                # Enrich with course names
                all_courses_map = {}
                for col_key in COLLEGES:
                    xml_data = fetch_college_native_via_xslt(col_key, 'courses')
                    if xml_data:
                        for c in parse_courses_from_xml(xml_data, col_key):
                            all_courses_map[c['course_id']] = c

                for e in enrollments:
                    c = all_courses_map.get(e['course_id'], {})
                    e['course_name'] = c.get('name', '未知课程')
                    e['teacher'] = c.get('teacher', '')
                    e['score_credit'] = c.get('score', '')

                enrollments = cross_courses  # Show only cross-college courses

                if not enrollments:
                    enrollments = []
                    message = f'学生 {student_id} 暂无跨院选课记录'
                    message_type = 'info'

    return render_template('integrated_dashboard.html',
                         colleges=COLLEGES,
                         enrollments=enrollments,
                         student_id=student_id,
                         message=message,
                         message_type=message_type,
                         active_tab='mycourses')


@app.route('/api/colleges')
def api_colleges():
    """Return college status as JSON."""
    result = {}
    for col_key, col_info in COLLEGES.items():
        stats = fetch_college_json(col_key, '/api/stats')
        result[col_key] = {
            'name': col_info['name'],
            'dbms': col_info['dbms'],
            'port': col_info['port'],
            'online': stats is not None,
            'stats': stats,
        }
    return jsonify(result)


if __name__ == '__main__':
    print(f'[集成服务器] 启动于 http://127.0.0.1:{INTEGRATION_PORT}')
    print(f'  - 学院A: http://127.0.0.1:5001')
    print(f'  - 学院B: http://127.0.0.1:5002')
    print(f'  - 学院C: http://127.0.0.1:5003')
    app.run(host='127.0.0.1', port=INTEGRATION_PORT, debug=False)
