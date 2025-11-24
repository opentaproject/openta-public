// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

'use strict'; // It is recommended to use strict javascript for easier debugging

import { all, create } from 'mathjs';
const math = create(all);

import { asciiMathToMathJS, insertCursor } from '../mathrender/string_parse.js';
function precheck(pvalue) {
  var not_syntaxerror = true;
  not_syntaxerror = not_syntaxerror && (pvalue.match(/\(/g) || []).length == (pvalue.match(/\)/g) || []).length;
  not_syntaxerror = not_syntaxerror && (pvalue.match(/\[/g) || []).length == (pvalue.match(/\]/g) || []).length;
  not_syntaxerror = not_syntaxerror && (pvalue.match(/\|/g) || []).length % 2 == 0;
  var syntaxerror = !not_syntaxerror;
  return syntaxerror;
}

function postcheck(res) {
  var renderedMath = res.out;
  var not_syntaxerror = !res.syntaxerror;
  not_syntaxerror = not_syntaxerror && !renderedMath.includes('orange') && !renderedMath.includes('red');
  return { out: renderedMath, warnings: res.warnings, syntaxerror: !not_syntaxerror };
}

export const external_renderAsciiMath = (asciitext, thiss) => {
  var ignore_undefined = false;
  var syntaxerror = precheck(asciitext);
  var cursorComplete = false;
  var cursorPos = thiss.state.cursor;
  thiss.mathjserror = /(\/|\*|\+|-|\^)\W*$/.test(asciitext);
  thiss.mathjswarning = thiss.mathjserror ? 'unterminated operator on right' : '';
  if (/\s\^/.test(asciitext)) {
    thiss.mathjserror = true;
    thiss.mathjswarning += ' : interior dangling caret';
  }
  if (cursorPos > asciitext.length) {
    cursorPos = asciitext.length;
  }
  var preParsed = asciiMathToMathJS(insertCursor(asciitext, cursorPos));
  if (preParsed.warnings) {
    thiss.mathjswarning += preParsed.warnings;
  }
  var parsed = preParsed.out;
  var reg = /(#|\$|&)/;
  if (asciitext.match(reg)) {
    parsed = parsed.replace(reg, '\\color{red}{\\$1}');
    return postcheck({ out: parsed, warnings: preParsed.warnings, syntaxerror: syntaxerror });
  }

  parsed = parsed.replace(/\)\.\(/g, ')**(', parsed);
  try {
    //var syntaxerror = false
    var mParsed = math.parse(parsed).toTex({
      parenthesis: 'keep', // The keep options keeps parenthesis from input expression, seems to work best.
      handler: thiss.customLatex, // Custom latex node handler
      ignore_undefined: ignore_undefined
    });
    mParsed = mParsed.replace(/prime}~ /g, 'prime}');
    mParsed = mParsed.replace(/}~ /g, '}');
    if (typeof mParsed === 'string' && mParsed !== 'undefined') {
      thiss.lastParsable = mParsed.replace(/\\\\end{bmatrix}/g, 'end{bmatrix}'); // MathJS outputs an extra \\ which KaTeX interprets as a new line
    }
    return postcheck({ out: thiss.lastParsable, warnings: preParsed.warnings, syntaxerror: syntaxerror });
  } catch (e) {
    //console.log("CAUGHT ERROR ", e )
    var syntaxerror = true;
    var redchar = '';
    var last = thiss.lastParsable;
    var outtex = parsed;
    var lastchar = parsed.charAt(parsed.length - 2);
    if (RegExp('fail').test(parsed)) {
      var redchar = parsed.match(/fail\(\"(.)\"\)/)[1];
      var outtex = parsed.replace(/fail\(\"(.)\"\)/, '{\\color{red}{$1} }');
      //syntaxerror = false
    } else if (RegExp('unclosed').test(parsed)) {
      thiss.isUnclosed = false;
      var outtex = parsed.replace(/unclosed\(\).*/, '');
      //syntaxerror = false
    }
    var chardict = {
      '%': '\\%',
      '#': 'hash',
      '^': '\\hat{}',
      '"': "''",
      '@': '@',
      '\\': '\\backslash',
      '?': '?',
      $: '\\$'
    };
    for (var cd in chardict) {
      if (lastchar == cd) {
        thiss.isUnclosed = false;
        var redchar = chardict[cd];
        //syntaxerror = false
        var outtex = last + '\\color{red}{ \\large{  ' + redchar + '}}';
      }
    }
    thiss.mathjswarning = ' : Unparsable  ' + (thiss.mathswarning ? thiss.mathjswarning : '');
    return postcheck({
      out: outtex,
      warnings: preParsed.warnings,
      error: 'MathJS parse/toTex error',
      syntaxerror: syntaxerror
    });
  }
};
