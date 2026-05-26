"""XML Schema definitions for validating the unified XML format."""

STUDENT_XSD = '''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="Students">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="student" minOccurs="0" maxOccurs="unbounded">
          <xs:complexType>
            <xs:sequence>
              <xs:element name="id" type="xs:string"/>
              <xs:element name="name" type="xs:string"/>
              <xs:element name="sex" type="xs:string"/>
              <xs:element name="major" type="xs:string"/>
            </xs:sequence>
          </xs:complexType>
        </xs:element>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>'''

COURSE_XSD = '''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="Classes">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="class" minOccurs="0" maxOccurs="unbounded">
          <xs:complexType>
            <xs:sequence>
              <xs:element name="id" type="xs:string"/>
              <xs:element name="name" type="xs:string"/>
              <xs:element name="score" type="xs:unsignedByte"/>
              <xs:element name="time" type="xs:unsignedByte"/>
              <xs:element name="teacher" type="xs:string"/>
              <xs:element name="location" type="xs:string"/>
              <xs:element name="shared" type="xs:unsignedByte"/>
            </xs:sequence>
          </xs:complexType>
        </xs:element>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>'''

ENROLLMENT_XSD = '''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="Choices">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="choice" minOccurs="0" maxOccurs="unbounded">
          <xs:complexType>
            <xs:sequence>
              <xs:element name="sid" type="xs:string"/>
              <xs:element name="cid" type="xs:string"/>
              <xs:element name="score" type="xs:unsignedByte"/>
            </xs:sequence>
          </xs:complexType>
        </xs:element>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>'''

XSD_MAP = {
    'students': STUDENT_XSD,
    'courses': COURSE_XSD,
    'enrollments': ENROLLMENT_XSD,
}
