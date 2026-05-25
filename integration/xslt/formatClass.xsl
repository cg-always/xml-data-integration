<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml" encoding="UTF-8" indent="yes"/>

<!-- Convert college-specific course XML to unified format -->
<xsl:template match="/">
  <Classes>
    <xsl:for-each select="Classes/class">
      <class>
        <id>
          <xsl:choose>
            <xsl:when test="课程编号"><xsl:value-of select="课程编号"/></xsl:when>
            <xsl:when test="编号"><xsl:value-of select="编号"/></xsl:when>
            <xsl:when test="Cno"><xsl:value-of select="Cno"/></xsl:when>
          </xsl:choose>
        </id>
        <name>
          <xsl:choose>
            <xsl:when test="课程名称"><xsl:value-of select="课程名称"/></xsl:when>
            <xsl:when test="名称"><xsl:value-of select="名称"/></xsl:when>
            <xsl:when test="Cnm"><xsl:value-of select="Cnm"/></xsl:when>
          </xsl:choose>
        </name>
        <score>
          <xsl:choose>
            <xsl:when test="学分"><xsl:value-of select="学分"/></xsl:when>
            <xsl:when test="学时"><xsl:value-of select="学时"/></xsl:when>
            <xsl:when test="Cpt"><xsl:value-of select="Cpt"/></xsl:when>
          </xsl:choose>
        </score>
        <time>
          <xsl:choose>
            <xsl:when test="学时"><xsl:value-of select="学时"/></xsl:when>
            <xsl:when test="time"><xsl:value-of select="time"/></xsl:when>
            <xsl:otherwise>32</xsl:otherwise>
          </xsl:choose>
        </time>
        <teacher>
          <xsl:choose>
            <xsl:when test="授课教师"><xsl:value-of select="授课教师"/></xsl:when>
            <xsl:when test="教师"><xsl:value-of select="教师"/></xsl:when>
            <xsl:when test="Tec"><xsl:value-of select="Tec"/></xsl:when>
          </xsl:choose>
        </teacher>
        <location>
          <xsl:choose>
            <xsl:when test="授课地点"><xsl:value-of select="授课地点"/></xsl:when>
            <xsl:when test="地点"><xsl:value-of select="地点"/></xsl:when>
            <xsl:when test="Pla"><xsl:value-of select="Pla"/></xsl:when>
          </xsl:choose>
        </location>
      </class>
    </xsl:for-each>
  </Classes>
</xsl:template>
</xsl:stylesheet>
