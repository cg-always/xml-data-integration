<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml" encoding="UTF-8" indent="yes"/>

<!-- Convert college-specific student XML to unified format -->
<xsl:template match="/">
  <Students>
    <xsl:for-each select="Students/student">
      <student>
        <id>
          <xsl:choose>
            <xsl:when test="学号"><xsl:value-of select="学号"/></xsl:when>
            <xsl:when test="编号"><xsl:value-of select="编号"/></xsl:when>
            <xsl:when test="Sno"><xsl:value-of select="Sno"/></xsl:when>
          </xsl:choose>
        </id>
        <name>
          <xsl:choose>
            <xsl:when test="姓名"><xsl:value-of select="姓名"/></xsl:when>
            <xsl:when test="名字"><xsl:value-of select="名字"/></xsl:when>
            <xsl:when test="Snm"><xsl:value-of select="Snm"/></xsl:when>
          </xsl:choose>
        </name>
        <sex>
          <xsl:choose>
            <xsl:when test="性别"><xsl:value-of select="性别"/></xsl:when>
            <xsl:when test="Sex"><xsl:value-of select="Sex"/></xsl:when>
          </xsl:choose>
        </sex>
        <major>
          <xsl:choose>
            <xsl:when test="院系"><xsl:value-of select="院系"/></xsl:when>
            <xsl:when test="专业"><xsl:value-of select="专业"/></xsl:when>
            <xsl:when test="Sde"><xsl:value-of select="Sde"/></xsl:when>
          </xsl:choose>
        </major>
      </student>
    </xsl:for-each>
  </Students>
</xsl:template>
</xsl:stylesheet>
