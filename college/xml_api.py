"""XML API module for college servers.

Handles:
- Exporting data as XML (college-specific format)
- Exporting data as unified XML format
- Importing enrollment data from XML
"""

from lxml import etree
from shared import (
    UNIFIED_STUDENT, UNIFIED_COURSE, UNIFIED_ENROLLMENT,
    UNIFIED_STUDENTS, UNIFIED_COURSES, UNIFIED_ENROLLMENTS,
    UF_SID, UF_SNAME, UF_SSEX, UF_SMAJOR,
    UF_CID, UF_CNAME, UF_CSCORE, UF_CTIME, UF_CTEACHER, UF_CLOCATION,
    UF_E_SID, UF_E_CID, UF_E_SCORE,
)


def _str(v):
    return str(v) if v is not None else ''


def students_to_unified_xml(students):
    """Convert student list to unified XML format."""
    root = etree.Element(UNIFIED_STUDENTS)
    for s in students:
        el = etree.SubElement(root, UNIFIED_STUDENT)
        etree.SubElement(el, UF_SID).text = _str(s['student_id'])
        etree.SubElement(el, UF_SNAME).text = _str(s['name'])
        etree.SubElement(el, UF_SSEX).text = _str(s['sex'])
        etree.SubElement(el, UF_SMAJOR).text = _str(s['major'])
    return etree.tostring(root, encoding='utf-8', xml_declaration=True)


def courses_to_unified_xml(courses):
    """Convert course list to unified XML format."""
    root = etree.Element(UNIFIED_COURSES)
    for c in courses:
        el = etree.SubElement(root, UNIFIED_COURSE)
        etree.SubElement(el, UF_CID).text = _str(c['course_id'])
        etree.SubElement(el, UF_CNAME).text = _str(c['name'])
        etree.SubElement(el, UF_CSCORE).text = _str(c['score'])
        etree.SubElement(el, UF_CTIME).text = _str(c.get('time', 32))
        etree.SubElement(el, UF_CTEACHER).text = _str(c['teacher'])
        etree.SubElement(el, UF_CLOCATION).text = _str(c['location'])
    return etree.tostring(root, encoding='utf-8', xml_declaration=True)


def enrollments_to_unified_xml(enrollments):
    """Convert enrollment list to unified XML format."""
    root = etree.Element(UNIFIED_ENROLLMENTS)
    for e in enrollments:
        el = etree.SubElement(root, UNIFIED_ENROLLMENT)
        etree.SubElement(el, UF_E_SID).text = _str(e['student_id'])
        etree.SubElement(el, UF_E_CID).text = _str(e['course_id'])
        etree.SubElement(el, UF_E_SCORE).text = _str(e.get('score', 0))
    return etree.tostring(root, encoding='utf-8', xml_declaration=True)


def parse_enrollments_xml(xml_data):
    """Parse unified enrollment XML and return list of enrollment dicts."""
    root = etree.fromstring(xml_data)
    enrollments = []
    for el in root.findall(UNIFIED_ENROLLMENT):
        enrollments.append({
            'student_id': el.findtext(UF_E_SID, ''),
            'course_id': el.findtext(UF_E_CID, ''),
            'score': int(el.findtext(UF_E_SCORE, '0') or '0'),
        })
    return enrollments


def parse_delete_enrollment_xml(xml_data):
    """Parse enrollment XML for deletion (only needs sid + cid)."""
    return parse_enrollments_xml(xml_data)
