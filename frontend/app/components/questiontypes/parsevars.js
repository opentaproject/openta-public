import mathjs from 'mathjs'

var gettexsubs = ( questionData ) => {
	return getkeysubs( questionData, 'var', 'tex' )
	};

var insertimplicitsubscript = (asciitext) => {
      var re, implicitsubscripts = [/([a-zA-Z]+)([0-9]+)/g ] ;
      var nasciitext = asciitext;
      for(re of implicitsubscripts){
		nasciitext = nasciitext.replace(re,'$1_{$2} ');
	};
      return nasciitext;
     }


var absify = ( sstr ) => {
    var l = sstr.length;
    var i = 0 ; 
    var s = '';
    var depth = 0;
    while( i < l ){
            var c = sstr[i];
            if(  c == '|'  ){
                 if( depth == 0  ){
                        s += " norm( ";
                        depth =  - 1;
                  } else if ( depth == -1 ){
                        depth = 0;
                        }
           } else {
                s += sstr[i];
            }
            if(  c == '|' && depth == 0   ){
                    s += " ) ";
            }
       // console.log(i,s,depth, s );
       i += 1;
     } 
    if( depth == 0 ){
    	return s;
 	} else {
	return sstr }
}

var braketify = (sstr) => { 
     //console.log("sstr = ", sstr);
     var snew = sstr.replace(/\<([^<|]+)\|([^|>]+)\>/g, 'Braket($1, $2)');
     var snew = snew.replace(/\<([^<|]+)\|([^|]+)\|([^|>]+)\>/g, 'Braket($1, $2,$3)');
     var snew = snew.replace(/\|([^>]+)\>([\S^\<]+)\<([^|]+)\|/g,'KetBra($1,$2,$3)'); 
     var snew = snew.replace(/\|([^>]+)\>\S*<([^|]+)\|/g,'KetBra($1,$2)');
    
     //console.log("snew = ", snew );
     //snew = snew.replace(/<([^|]*)|([^|]*)|([^>|]*)>)/g , "Braket( $1 , $2, $3 )");
    return snew;
    }




var absify2 = ( sstr ) => {
    var l = sstr.length;
    var i = 0 ; 
    var s = '';
    var depth = 0;
    while( i < l ){
            var c = sstr[i];
            if(  c == '|'  ){
                 if( depth == 0  ){
                        s += "<";
                        depth =  - 1;
                  } else if ( depth == -1 ){
                        depth = 0;
                        }
           } else {
                s += sstr[i];
            }
            if(  c == '|' && depth == 0   ){
                    s += ">";
            }
       // console.log(i,s,depth, s );
       i += 1;
     }
    return s;
}




var getkeysubs = ( questionData , varn, key ) => {
  var vars = {};
  try{
  var OBglobals =  (questionData.getIn(['global']) );
  if( OBglobals !== undefined ){ 
  var globalvars =  questionData.getIn(['global',varn],'$');
  
  if( globalvars != '$' ){
  // console.log("All extra variables ",  questionData.getIn(['global','var','token','$'],'$') );;
  // console.log("All extra variables 2 ",  globalvars.getIn(['token','$'],'$') );
  // console.log( "properties ", Object.getOwnPropertyNames( globalvars) );
  // console.log( "tex = ", globalvars.getIn(['tex','$'],'$' ) );
  var JSglobalvars = globalvars.toJS();
  // var gg = Object.keys(getvalsubs( questionData ) )
  //console.log("gg = ");
  //console.dir(gg);
  //console.log("JSglobalvars = ");
  //console.dir(JSglobalvars);
 
  // console.log( "JSglobalvars", JSglobalvars );
  var newdefs = {};
  var ind,JSObj;
  var ArrayOfJSglobalvars = [] ;
  
  try{

  if( JSglobalvars instanceof Array ){
	ArrayOfJSglobalvars = JSglobalvars } else {
	ArrayOfJSglobalvars[0] = JSglobalvars;
	}
  for( ind in ArrayOfJSglobalvars ){
	JSObj = ArrayOfJSglobalvars[ind]
	//console.log( "ind = ", JSObj );
	if( JSObj.token !== undefined ){
	    vars[ JSObj.token.$] = ( JSObj.token.$  );
	   if( JSObj[key] !== undefined  ){
		vars[ JSObj.token.$] = ( JSObj[key].$  );
		//console.log("token = ", JSObj.token.$ );
		//console.log("tex  = ", JSObj.tex.$ );
	     }	}
	   }
   //console.log("FINISHED ALL TEX ASSIGNMENTS")
   } 
  catch(e){
  console.log("ERROR IN getkeysubs" )
  console.log(e.toString())
  }

     }
  //console.log("GOT TO HERE A")
   }
  //console.log("GOT TO HERE B")
  var arr = []; 
//  var ind, varsList = Object.keys(( getvalsubs( questionData ) )); 
// var ind, varsList = Object.keys( questionData.vars); 
 //console.log("GOT HERE TO C")
 // console.dir( questionData.vars)
 var ind, varsList = Object.keys( questionData.vars )
 //console.log("varsList = " )
 //console.log( varsList);
 var txt = ''
 if( key === 'tex'){
 try{
     for( ind in varsList ){
        txt = varsList[ind];
	arr[varsList[ind]] = insertimplicitsubscript( txt);
	}
   } 
 catch(e){
    console.log("ERROR in ", ind.toString(), txt )
   }
 }


  for( ind in vars ){ arr[ ind  ] =  vars[ind]; }
  //console.log("arr = ", arr );
  return arr ;
  }

  catch(e){
	console.log("error in getkeysubs" + e);
	return [];
     }
  }

var getvalsubs = ( questionData ) => {
  // ERRORS RESULT WHEN XML FILE IS BEING ALTERED
  // THESE MUST BE CAUGHT IN ORDER TO AVOID CRASHING A SAVE
  // console.log("ET 2VALSUBS")
  try{
  var OBglobals =  (questionData.getIn(['global']) );
  //var unitsubs = {kg: mathjs.random() , meter: mathjs.random(), second: mathjs.random() };
  var unitsubs = {kg: 7 , meter: 8 , second: 9 };
  //console.log("ENTERING GETVALSUBS")
  //console.log(unitsubs)
  //console.log("THIS WAS UNITSUBS")
  //unitsubs['kg'] = 1;
  //unitsubs['meter'] = 1;
  //unitsubs['second'] = 1;
  if( OBglobals !== undefined ){ 
  var variableString = (questionData.getIn(['global','$'], ''));
  //console.log("VARIABLE STRING",variableString)
  var expressions = variableString.split(';')
  //console.log(expressions)
  var key,line,entry,res
  var vars = unitsubs
  //console.log("UNITSUBS")
  //console.dir(unitsubs)
  // HAVE TO GO THROUTH THE GLOBAL $ CAREFULLY TO EVALUATE DEPENDENT
  // EXPRESSIONS 
  // SINCE THERE IS NO GUARANTEE THAT THE XML WILL BE LOADED IN ORDER
  //  
  for( key in expressions){
        line = expressions[key].trim()
        if( line !== ''){
                entry = line.split('=').map( entry => entry.trim() )
                if( entry.length > 2 ){
                        console.log("MISSING SEMICOLON");
                        throw "missing semicolon in xml:  " + line;
                        }
                if( entry.length <= 1 ){
                        console.log("MISSING = sign");
                        throw "missing equal sign in xml:  " + line;
                        }
                //console.log("entry = ", entry) 
                try{
                        res = mathjs.eval( entry[1], vars);
                        vars[ entry[0].trim() ] = res;
                   }
                catch(e){
                        var es = e.toString();
                        console.log(" A ERROR PARSING INPUT STRING" )
                        //console.log("ERROR WITH ")
                        //console.log(entry)
                        console.log( es)
                        var hint = '  Unable to valuate xml variables to numerical values ; variables in RHS must be defined before used'
                        if( es.indexOf("TypeError") >= 0 ){
                                hint = "   Unable to reduce defined variables to known units or numbers. .... Likely wrong symbol for kg,meter or second in spite of the error showing up on another line"
                                }
                        throw "EA : Error in xml line:"  + line  + "......"+  e.toString() + hint;
                        }
                //console.log(vars)
                }
        }
  //console.log("VARS = ")
  //console.dir(vars)
  //var stringvars = variableString.trim()
   //   .split(';')
    //  .filter(str => str !== "")
     // .map( str => str.split('=') )
    //  .map( entry => ( vars[ entry[0].trim() ]  =  mathjs.eval( entry[1], unitsubs) ) ) // STOP TRYING TO PARSE UNITS
    //  //.map( entry => ( vars[ entry[0].trim() ]  = ( ( entry[1] ).trim() ) ).replace(/kg/m,'1') )
  //console.log("legacy vars  = ", vars );
  var globalvars =  questionData.getIn(['global','var'],'$');
  if( globalvars != '$' ){
  // console.log("All extra variables ",  questionData.getIn(['global','var','token','$'],'$') );;
  // console.log("All extra variables 2 ",  globalvars.getIn(['token','$'],'$') );
  // console.log( "properties ", Object.getOwnPropertyNames( globalvars) );
  // console.log( "val = ", globalvars.getIn(['val','$'],'$' ) );
  var JSglobalvars = globalvars.toJS();
  //console.log( "JSglobalvars", JSglobalvars );
  var newdefs = {};
  var ind,JSObj;
  var ArrayOfJSglobalvars = [] ;
  if( JSglobalvars instanceof Array ){
	ArrayOfJSglobalvars = JSglobalvars } else {
	ArrayOfJSglobalvars[0] = JSglobalvars;
	}
  var token,val,varsym;
  for( ind in ArrayOfJSglobalvars ){
	JSObj = ArrayOfJSglobalvars[ind]
	//console.log( "ind = ", JSObj );
	if( JSObj.token !== undefined && JSObj.val !== undefined  ){
		//vars[ JSObj.token.$] = ( JSObj.val.$  ).replace(/([*/\s])*(kg|meter|second)/m,'');
		//console.log("token = ", JSObj.token.$ );
		//console.log("val  = ", JSObj.val.$ );
                try{
                        varsym = JSObj.token.$
                        if( vars[varsym] == undefined){
                                res = mathjs.eval( ( JSObj.val.$  ), vars);
		                vars[ JSObj.token.$] = res ;
                         } else {
                                throw "xml errors: multiple definition of " + varsym
                                //console.log("REDEFINING VARIABLE " + varsym )
                           }
                        }
                catch(e){
                        console.log("B- ERROR PARSING INPUT STRING" )
                        console.log("ERROR WITH ")
                        console.log( JSObj.val.$ )
                        console.log( JSObj.token.$ )
                        throw "EB " + e.toString();
                        }
 
                //vars[ JSObj.token.$] = ( JSObj.val.$  ); //  XXX  DO MATHJS VERSION IF ERRORS APPEAR
		// vars[ JSObj.token.$] = mathjs.random(); // STOP TRYING TO PARSE UNITS
		}
	}
     }
   }
  var arr = []; 
  for( ind in vars ){ arr[ ind  ] =  vars[ind]; }
  // console.log("parsevars: vals  ", arr );
  } 
  catch(e){
   console.log("parsvars error for broken xml");
   console.log(expressions)
   console.log(e)
   var arr = []; 
   for( ind in vars ){ arr[ ind  ] =  vars[ind]; }
   throw "EC " + e;
    }
  return arr ;
  }

var insertimplicitmultiply = (asciitext) => {
      //
      // first token[space]token ; then [space]integers[paren] ; then [blanks][numbers][token] ; then )[space*](
      // The reason for the complexity is that mathjs is even more lenient with implicit multiplies; 3x is treated as 3*x
      // That is a nuisance which makes the parsing more difficult to comply with
      //
      // console.log("IMPLICIT MULTIPLY" + asciitext)
      var re, implicitmultiplies = [
        /([0-9]+)\s+([0-9]+)/g,    // [int] [int] => [int]*[int]
	/(\w+)\s+(\w+)/g,    // [token] [token] => [token]*[token]
	/(\s+[0-9]+)([(])/g, 	// [space][integers]( => [integer] * ( 
	/(\W+[0-9]+)([A-Za-z]+)/g, // [nonword][integers][token] => [nonword][integers] * token
	/(\w+)\s+([(])/g,           // [token][space]( => [token] * (
	/([)])\s*(\w+)/g, 	    // )[space][token] => ) * [token]
	/([)])\s*([(])/g ];         // )[space*]( => ) * (
      var nasciitext = ' '+asciitext + ' ';
      for(re of implicitmultiplies){
		nasciitext = nasciitext.replace(re,'$1 * $2');
	};
      return nasciitext;
     }



export {gettexsubs, getvalsubs,getkeysubs,insertimplicitsubscript,insertimplicitmultiply,absify,absify2,braketify}
