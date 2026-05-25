<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml" encoding="UTF-8" indent="yes"/>

<xsl:template match="/">
  <Classes>
    <xsl:for-each select="Classes/class">
      <class>
        <编号><xsl:value-of select="id"/></编号>
        <名称><xsl:value-of select="name"/></名称>
        <学时><xsl:value-of select="score"/></学时>
        <教师><xsl:value-of select="teacher"/></教师>
        <地点><xsl:value-of select="location"/></地点>
        <学分><xsl:value-of select="time"/></学分>
      </class>
    </xsl:for-each>
  </Classes>
</xsl:template>
</xsl:stylesheet>
