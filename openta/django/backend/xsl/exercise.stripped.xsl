<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="html"/>

<xsl:template match="@* | node()">
  <xsl:copy>
    <xsl:apply-templates select="@* | node()"/>
  </xsl:copy>
</xsl:template>


<xsl:template match="/">
 <html>
<head>
	<script><xsl:attribute name="src"><xsl:text>/xsl/load-mathjax.js</xsl:text></xsl:attribute></script>
</head>
<xsl:apply-templates />
<body width="80%" align="left">
</body>

  </html>
</xsl:template>

<xsl:template match="text">
<p style="padding: 10px; border: 2px solid green;">
   <xsl:apply-templates  />
   </p>
</xsl:template>

<xsl:template match="exercisename">
<p style="padding: 10px; border: 2px solid purple;">
  <xsl:value-of select="." />
   </p>
</xsl:template>



<xsl:template match="question">
<div style="background:#ffaa00">
QUESTION:
<xsl:apply-templates select="text" />
 <xsl:apply-templates select="expression" />
<xsl:apply-templates select="choice" />
</div>
</xsl:template>



<xsl:template match="figure">
  <div style="color:#00ff00">
	  <img>
	  <xsl:attribute name="src"><xsl:value-of select="." /></xsl:attribute>
  </img>
  </div>
</xsl:template>


<xsl:template match="expression">
  <div style="color:#0000ff">
	  ANSWER:
$ <xsl:value-of select="."/> $
  </div>
  </xsl:template>

 <xsl:template match="choice">
  <div style="color:#ff00ff">
<xsl:value-of select="."/>
  </div>
  </xsl:template>



<xsl:template match="right">
  <p> right:
   <xsl:value-of select="."/>
  </p>
</xsl:template>


<xsl:template match="global">
<div style="color:#0000ff">
   <xsl:value-of select="."/>
   </div>
</xsl:template>


</xsl:stylesheet>
