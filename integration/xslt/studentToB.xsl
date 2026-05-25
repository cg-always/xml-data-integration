<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml" encoding="UTF-8" indent="yes"/>

<xsl:template match="/">
  <Students>
    <xsl:for-each select="Students/student">
      <student>
        <编号><xsl:value-of select="id"/></编号>
        <名字><xsl:value-of select="name"/></名字>
        <性别><xsl:value-of select="sex"/></性别>
        <专业><xsl:value-of select="major"/></专业>
      </student>
    </xsl:for-each>
  </Students>
</xsl:template>
</xsl:stylesheet>
