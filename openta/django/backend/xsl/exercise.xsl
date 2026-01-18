<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:output method="html"/>
  <xsl:template match="@* | node()">
    <xsl:copy>
      <xsl:apply-templates select="@* | node()"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="/">
    <html>
      <head>
	      <link rel="stylesheet" href="/xsl/bootstrap.min.css" crossorigin="anonymous"/>
	      <script src="/xsl/jquery-3.4.1.slim.min.js" crossorigin="anonymous"/>
	      <script src="/xsl/popper.min.js" crossorigin="anonymous"/>
	      <script src="/xsl/bootstrap.min.js"  crossorigin="anonymous"/>
      </head>
      <body>
      <div class="d-flex justify-content-center" margin="auto;">
        <div class="w-75 p-3 bg-light">
          <xsl:apply-templates/>
        </div>
      </div>
      </body>
    </html>
  </xsl:template>
  <xsl:template match="text">
    <p/>
    <xsl:apply-templates/>

  </xsl:template>
  <xsl:template match="exercisename">
    <div style="color:#0000ff">
	    <h5>  Name:   <xsl:apply-templates />
		     <span class="float-right"><a href="./exercise.xml"> XML </a>
		     <a href="./"> Assets </a> </span>
	    </h5>
    </div>
  </xsl:template> 


  <xsl:template match="question">
    <p/>
    <p/>
    <div style="color:#0000ff"><h5> Question   </h5> 
	key: <em><xsl:value-of select="@key"/></em>
	type : <em><xsl:value-of select="@type"/></em>
</div>
    <div style="background:#e0e0e0">
      <xsl:apply-templates select="text"/>
<xsl:apply-templates select="istrue"/>
      <xsl:apply-templates select="expression"/>
      <xsl:apply-templates select="choice"/>

    </div>
  </xsl:template>
  <xsl:template match="figure">
    <div style="color:#ffff00">
      <img style="max-width: 50%">
        <xsl:attribute name="src">
		 <xsl:value-of select="normalize-space()"/>
        </xsl:attribute>
      </img>
    </div>
  </xsl:template>

  <xsl:template match="alt">
	  <div class="p-2 border small text-success">
	[ <em> <xsl:value-of select="@lang"/> 
	</em> ] 
	<xsl:apply-templates/>
	</div>
  </xsl:template>

  <xsl:template match="solution">
	  <div class="p-2 border border-primary ">
	  <h6> Solution </h6>
	  <xsl:apply-templates select="text" />
	  <xsl:apply-templates select="asset"/>
  </div>
  </xsl:template>


    <xsl:template match="hidden">
	  <div class="p-2 border border-primary ">
	  <h6> Hidden</h6>
	  <xsl:apply-templates select="asset"/>
	  <xsl:apply-templates select="code"/>
  </div>
  </xsl:template>

  <xsl:template match="code">
	  <div class="p-2 small border-primary ">
		  <h6> Code </h6>
	 <pre>
	 <xsl:value-of select="."/>	
 </pre>
  </div>
  </xsl:template>



  <xsl:template match="asset">
	  <div class="text-warning">
	<a><xsl:attribute name="href"><xsl:value-of select="."/></xsl:attribute> <h6> <xsl:value-of select="@name"/> [ <xsl:value-of select="."/> ] </h6> </a>
	</div>
  </xsl:template>



  <xsl:template match="expression">
    <p/>
    <div style="color:#0000ff"> Answer: 
	<div class="float-right"> 
		<xsl:value-of select="."/> ]
  	</div>
    </div>
  </xsl:template>


  <xsl:template match="istrue">
    <p/>
    <div style="color:#0000ff">
	  IsTrue: 
</div><div>
<pre>
<xsl:value-of select="."/> 
</pre>
  </div>
  </xsl:template>




  <xsl:template match="choice">
    <div>
      <xsl:choose>
        <xsl:when test="@correct!='false'">
          <span class="text-success">
            <span class="margin-left-xl">
              <xsl:value-of select="."/>
            </span>
            <span class="float-right">
		    <img src="/xsl/check-circle-fill.svg"/>
            </span>
          </span>
        </xsl:when>
        <xsl:otherwise>
          <span class="text-danger">
            <xsl:value-of select="."/>
            <span class="float-right">
		    <img src="/xsl/x-circle.svg"/>
            </span>
          </span>
        </xsl:otherwise>
      </xsl:choose>
    </div>
  </xsl:template>

   <xsl:template match="right">
	   <xsl:apply-templates select="figure"/>
  </xsl:template>

   <xsl:template match="var">
	<div>
	<xsl:apply-templates select="token"/>
 	<xsl:apply-templates select="tex"/>
	<xsl:apply-templates select="value"/>
	</div>
  </xsl:template>

  
   <xsl:template match="token">
	    <xsl:value-of select="."/> 
  </xsl:template>

   <xsl:template match="tex">
	    $ \rightarrow  <xsl:value-of select="."/> $ 
  </xsl:template>

   <xsl:template match="value">
	    := <xsl:value-of select="."/>  
  </xsl:template>





  <xsl:template match="global">
    <div style="color:#0000ff">
      <h5> Globals </h5>
      <pre>
     <xsl:value-of select="text()"/>
</pre>
    </div>
   <xsl:apply-templates select="var"/>
  </xsl:template>

 <xsl:template match="macros">
    <div style="color:#0000ff">
      <h5> Macros </h5>
      <pre>
        <xsl:value-of select="."/>
      </pre>
    </div>
  </xsl:template>
</xsl:stylesheet>
