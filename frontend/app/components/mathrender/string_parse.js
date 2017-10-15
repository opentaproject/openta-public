"use strict";
//Returns a new string where the character at pos in str is replaced with newstring
function replaceAt(str, pos, newString) {
  return str.slice(0,pos) + newString + str.slice(pos+1);
}

function insertAfter(str, pos, newString) {
  if(pos + 1 < str.length-1)
    return str.slice(0,pos+1) + newString + str.slice(pos+1);
  else
    return str + newString;
}

function insertBefore(str, pos, newString) {
  return str.slice(0,pos) + newString + str.slice(pos);
}

//Parse Bra,Ket,BraKet and KetBra expressions for QM.
var braketify = (sstr) => { 
 if( sstr != undefined ){
  var snew = sstr.replace(/\<([^<|]+)\|([^|>]+)\>/g, 'Braket($1, $2)');
  snew = snew.replace(/\<([^<|]+)\|([^|]+)\|([^|>]+)\>/g, 'Braket($1, $2,$3)');
  snew = snew.replace(/\|([^>]+)\>([^\<]+)\<([^|]+)\|/g,'KetBra($1,$2,$3)'); 
  snew = snew.replace(/\|([^>]+)\>\S*<([^|]+)\|/g,'KetBra($1,$2)');
  return snew;
 }
  else return "UNDEFINED PASSED TO braketify"
}

var absify = (expression) => {//{{{
    var l = expression.length;
    var i = 0; 
    var s = ''
    var depth = 0
    while(i < l) {
            var c = expression[i]
            if(c === '|'){
                 if(depth == 0) {
                        s += "Norm("
                        depth = -1
                 }
                 else if(depth == -1)
                        depth = 0
            }
            else {
                s += expression[i]
            }
            if(c === '|' && depth == 0)
                    s += ")"
            i += 1
    }
    if(depth == 0)
        return s
    else
        return expression
}//}}}

//An alpha character followed by a number should be rendered in subscript
const insertImplicitSubscript = (asciitext) => {
  var re = /([a-zA-Z]+)([0-9]+)/g;
  return asciitext.replace(re,'$1_$2');
}

//Uses a number of regexp rules to insert implicit multiplication.
var insertImplicitMultiply = (asciitext) => {//{{{
  //
  // first token[space]token ; then [space]integers[paren] ; then [blanks][numbers][token] ; then )[space*](
  // The reason for the complexity is that mathjs is even more lenient with implicit multiplies; 3x is treated as 3*x
  // That is a nuisance which makes the parsing more difficult to comply with
  //
  var re, implicitmultiplies = [
    /([0-9]+)\s+([0-9]+)/g,    // [int] [int] => [int]*[int]
    /([\w~]+)\s+([\w~]+)/g,    // [token] [token] => [token]*[token]
    /([0-9]+)\s+([0-9]+)/g,    // [int] [int] => [int]*[int]
    /([\w~]+)\s+([\w~]+)/g,    // [token] [token] => [token]*[token]
    /(\s+[0-9]+)([(])/g, 	// [space][integers]( => [integer] * ( 
    /(\W+[0-9]+)([A-Za-z]+)/g, // [nonword][integers][token] => [nonword][integers] * token
    /(\w+)\s+([\[(])/g,           // [token][space]( => [token] * (
    /([)\]])\s*([\w~]+)/g, 	    // )[space][token] => ) * [token]
    /([)\]])\s*([(\[])/g ];         // )[space*]( => ) * (
    var nasciitext = ' '+asciitext + ' ';
    for(re of implicitmultiplies){
      nasciitext = nasciitext.replace(re, '$1 * $2');
    };
    return nasciitext;
}//}}}

// Finds unmatched delimiters and inserts metainformation for the MathJS rendering as custom functions
function fixDelimiters(str) {//{{{
  var starts = ['(', '['];
  var ends = [')', ']'];
  var stack = [];
  var i = 0;
  var warnings = [];
  // Traverse the string one char at a time
  while(i < str.length) {
    // Loop through all delimiters
    for(var j = 0; j < starts.length; j++) {
      // Push on stack if open
      if(str[i] == starts[j])stack.push({delim: j, pos: i});
      // Is the char a closing delimiter?
      if(str[i] == ends[j]) {
        // Compare ending delimiter with the last opened on the stack
        if(stack.length > 0) {
          var {delim, pos} = stack.pop();
          if(delim != j) {
            str = replaceAt(str, pos, ' fail("' + starts[delim] + '") ')
            i = i + 10;
            str = replaceAt(str, i, ' fail("' + ends[j] + '") ')
            i = i + 10;
          }
        } 
        // If there was nothing on the stack then there is no corresponding open delimiter
        else {
          str = replaceAt(str, i, ' fail("' + ends[j] + '") ')
          i = i + 10;
        }
      }
    }
    i++;
  }
  // If there are any remaining items in the stack this means there are unmatched opened delimiters. Fix them in reverse so that the position of subsequent items is still valid after the string update
  for(let open of stack.reverse()) {
    if(starts[open.delim] === '(')
      str = str + ' unclosed() ' + ends[open.delim];
    else {
      str = str + ends[open.delim] /*+ ' smalltext("] fattas") '*/;
      warnings.push("\"]\" fattas")
    }
  }
  return {out: str, warnings: warnings};
}//}}}

// Insert the special "~" (bitNot) operator to handle cursor positioning.
// Strategy: Find the opening parenthesis on the same level, if this is not a function call then return the string with the ~ inserted before.
// Example: 1 + ( a + [cursor here]b) => 1 + ~( a + b )
// If its a function call then place the bitNot before the function.
// Example: 1 + sin( a + [cursor here]b) => 1 + ~sin( a + b)
const insertCursor = (str, pos) => {//{{{
    var left = pos;
    var done = false;
    var depth = 0;
    if(left === 0)return str;
    while(!done && left > 0) {
        left--;
        if(left === 0 && depth > 0)
            return str
        if(str[left] === ')')depth++;
        if(str[left] === '(' ) {
            if(depth === 0) {
                while(left > 0 && str[left-1].match(/[a-zA-Z0-9]/g))
                    left--;
                return insertBefore(str, left, ' ~');
            }
            depth--;
        }
    }
    return str;
}//}}}

/**
* @param {string} str - Asciimath string
* @return {object} {out: {string} - Parsed output, warnings: {string} - Warnings}
*/
const asciiMathToMathJS = (str) => {
	
    var parsed = str;
    parsed = insertImplicitMultiply(parsed);
    // parsed = insertImplicitSubscript(parsed);  // DELETED THIS
    parsed = braketify(parsed);
    parsed = fixDelimiters(parsed);
    // console.log("DEV_LINEAR_ALGEBRA parsed = ", parsed )
    return parsed
}

export {asciiMathToMathJS, insertCursor, braketify, absify, insertImplicitMultiply, insertImplicitSubscript, fixDelimiters}
