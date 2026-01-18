// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

function loadXMLDoc(filename)
{
if ( window.ActiveXObject)
  {
  xhttp = new ActiveXObject("Msxml2.XMLHTTP");
  }
else 
  {
  xhttp = new XMLHttpRequest();
  }
xhttp.open("GET", filename, false);
xhttp.send("");
return xhttp.responseXML;
}

function displayResult()
{
var location = document.location.pathname;
p = location.match(/(.*)[\/\\]/)[1]||''
var xmlLocation = p + '/exercise.xml'
var xml = loadXMLDoc(xmlLocation);
//var fullUrl = script.src;
console.log("pg = ", pq )
var xsl = loadXMLDoc(pq + "/exercise.xsl")
// pq obtained from global set in ex.html
// code for IE
//ex = xml.transformNode(xsl);
if ( window.ActiveXObject || xhttp.responseType == "msxml-document")
  {
  ex = xml.transformNode(xsl);
  document.getElementById("txt").innerHTML = ex;
  }
// code for Chrome, Firefox, Opera, etc.
else if (document.implementation && document.implementation.createDocument)
  {
  xsltProcessor = new XSLTProcessor();
  xsltProcessor.importStylesheet(xsl);
  resultDocument = xsltProcessor.transformToFragment(xml, document);
  document.getElementById("txt").appendChild(resultDocument);
  }
}
