<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml" encoding="UTF-8" indent="yes"/>

<xsl:template match="/">
  <Classes>
    <xsl:for-each select="Classes/class">
      <class>
        <课程编号><xsl:value-of select="id"/></课程编号>
        <课程名称><xsl:value-of select="name"/></课程名称>
        <学分><xsl:value-of select="score"/></学分>
        <授课教师><xsl:value-of select="teacher"/></授课教师>
        <授课地点><xsl:value-of select="location"/></授课地点>
        <学时><xsl:value-of select="time"/></学时>
      </class>
    </xsl:for-each>
  </Classes>
</xsl:template>
</xsl:stylesheet>
