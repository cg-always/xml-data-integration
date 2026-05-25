<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml" encoding="UTF-8" indent="yes"/>

<xsl:template match="/">
  <Classes>
    <xsl:for-each select="Classes/class">
      <class>
        <Cno><xsl:value-of select="id"/></Cno>
        <Cnm><xsl:value-of select="name"/></Cnm>
        <Cpt><xsl:value-of select="score"/></Cpt>
        <Tec><xsl:value-of select="teacher"/></Tec>
        <Pla><xsl:value-of select="location"/></Pla>
        <time><xsl:value-of select="time"/></time>
      </class>
    </xsl:for-each>
  </Classes>
</xsl:template>
</xsl:stylesheet>
