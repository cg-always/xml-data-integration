<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml" encoding="UTF-8" indent="yes"/>

<xsl:template match="/">
  <Choices>
    <xsl:for-each select="Choices/choice">
      <choice>
        <Sno><xsl:value-of select="sid"/></Sno>
        <Cno><xsl:value-of select="cid"/></Cno>
        <Grd><xsl:value-of select="score"/></Grd>
      </choice>
    </xsl:for-each>
  </Choices>
</xsl:template>
</xsl:stylesheet>
