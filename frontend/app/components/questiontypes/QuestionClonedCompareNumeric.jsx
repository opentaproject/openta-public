/*
 * This is the presentational part of a question. It contains the javascript and html code that is shown in the front-end to the user.
 * It consists of a React component (see documentation on github for more details).
 */
"use strict"; // It is recommended to use strict javascript for easier debugging
import React, { PropTypes, Component } from 'react'; // React specific import

import { registerQuestionType } from './question_type_dispatch.js' // Register function used at the bottom of this file to let the system know of the question type
import Alert from '../Alert.jsx'; // Another component useful for showing alerts in the form of colored boxes. See below for examples.
import SafeMathAlert from '../SafeMathAlert.jsx'; // Another component useful for showing alerts in the form of colored boxes. See below for examples.
import Badge from '../Badge.jsx'; // Another component useful for showing badges in the form of small colored boxes. See below for examples.
import HelpClonedCompareNumeric from './HelpClonedCompareNumeric.jsx';
import mathjs from 'mathjs';
import {insertimplicitsubscript, insertimplicitmultiply, gettexsubs, getvalsubs,getkeysubs,absify,absify2,braketify} from './parsevars.js';



export default class QuestionClonedCompareNumeric extends Component {
  static propTypes = {
    questionData: PropTypes.object, // Data from exercise XML file, i.e. whats inside the <question> tag
    questionState: PropTypes.object, // Current question state together with response data from server
    submitFunction: PropTypes.func, // Call this function to submit an answer to the server. The only parameter is the answer data which is unconstrained: It could be a simple string as below or a dictionary of values if more information needs to be conveyed.
    questionPending: PropTypes.bool, // Indicates when we are waiting for a server response
    isAuthor: PropTypes.bool, //Indicates if user is an author/content creator.
    canViewSolution: PropTypes.bool, //Indicates if user is allowed to see solution.
  }

  constructor(props) {
    super(props);
    this.state = {
      value: this.props.questionState.getIn(['answer'], ''),
      parsable: '',
      parsableparsed: '',
      cursorbegin: 0,
      cursorend: 1000,
      greenlight : true,
      counter: 0
    };
   //console.log("CONSTRUCTOR")
    if(this.props.canViewSolution)
      this.state.value = this.props.questionData.getIn(['expression','$'], '').replace(/;/g,'');
  }

  handleChange = (event) => {
    this.setState({value: event.target.value, cursorbegin: event.target.selectionStart, cursorend:event.target.selectionEnd});
  }

  componentWillReceiveProps = (newProps) => {
   // console.log("RECEIVE PROPS") // CALLED AFTER EVERY SERVER SUBMIT
   // console.log("COUNTER = ", this.state.counter)
    this.state.counter = 0
    //this.setState({ value: newProps.questionState.getIn(['answer'],'') });
  }

  componentWillMount = () => {
   // console.log("WILL MOUNT")
    this.state.counter = 0;
    //if(vars) {
     // vars.map( v => {
      //  if(AMsymbols.find( item => item.input === v ) === undefined)
    //      newsymbol({input:v,  tag:"mi", output: v, tex: v, ttype:0, val: true});
     // });
    // }
  }
	
  //Helper function for parsing errors from MathJS
  containsAny = ( str, substrings)   => {
    for (var i = 0; i != substrings.length; i++) {
      var substring = substrings[i];
      if (str.indexOf(substring) != - 1) {
        return substring;
      }
    }
    return null; 
  }


  rcontainsAny = ( str, regexes)   => {
    for (var i = 0; i != regexes.length; i++) {
      //if (str.indexOf(substring) != - 1) {
      var reg = new RegExp(regexes[i]);
        if( str.match(reg)){
        return reg;
      }
    }
    return null; 
  }




customlatex = (node, options) =>  {
 // console.log("NODE");
  //console.log( node.type)
  //console.dir(node);
  if ((node.type === 'SymbolNode') && options['texsubs']  ) {
  var key, p = options['texsubs'];
     p['pi'] = "\\pi";
     p['i'] = "\\mathsf{i}"
    //don't forget to pass the options to the toTex functions
     if( node.name === '_'){
	return '_';
	}
    if( p[node.name] ){
        return '\\color{#390}{'+p[node.name]+'} ' // CRUCIAL SPACE
        } else {
	//console.log("B", node.name );
	// console.dir(node.name);
        return '\\color{red}{'+ node.name + '} '  // CRUCIAL SPACE
        } 
    } else if ((node.type === 'FunctionNode') && options['blacklist'] ) {
	var key, blacklist = options['blacklist'];
	var ind, texexp = '';
	var len = node.args.length;
	var texexp = node.args[0].toTex(options);
	for(ind = 1 ; ind < len ; ind ++ ) {
		texexp = texexp + ' , ' + node.args[ind].toTex(options);
		}
	var fprint = ( node.fn.name ).toString();
	//console.log("FPRINT = ", node.fn.name, node.type)
        var symbs = {};
	symbs['cross'] = ' \\times ';
	symbs['dot'] = ' \\bullet ';
	symbs['Braket'] = ' brkt ';
        symbs['KetBra'] = ' ketbra ';
	symbs['exp'] = ' e^'
 	if( blacklist[fprint] && symbs[fprint] === undefined ){ 
		//console.log("1 ", blacklist[fprint] );
		return '\\color{red}{' +  blacklist[fprint] + '}(' +  texexp + ')'
		} else {
		//console.log("FPRINT2 = ", fprint);
		if( fprint === 'Braket'){
			//console.log("BRAKET IT IS");
			}
		if( fprint === 'cross' || fprint === 'dot' ){
			var tex0 = node.args[0].toTex(options);
			var tex1 = node.args[1].toTex(options);
			if( ! ( node.args[0].type === 'SymbolNode' ) ){ tex0 = '(' + tex0 + ')'; }
			if( ! ( node.args[1].type === 'SymbolNode' ) ){ tex1 = '(' + tex1 + ')' ; }
			if( fprint === 'dot' ){
				return  '( ' + tex0 + symbs[fprint] +  tex1 +')'
				} else {
				return  tex0 + symbs[fprint] +  tex1
				}
			}
		else if( fprint === 'Braket'  ){
			//console.log("BRAKET")
			//console.dir( node )
			var tex0 = node.args[0].toTex(options);
			var tex1 = node.args[1].toTex(options);
			if( node.args.length == 2 ){
				return "\\langle  \\,"+ tex0 +"  \\,|  \\," + tex1 + "  \\,\\rangle"
				}
			else {
				var tex2 = node.args[2].toTex(options);
				return "\\langle \\, "+ tex0 +" \\ |  \\," + tex1 + " \\,| \\," + tex2 + " \\, \\rangle"
				}
			}
		
		else if( fprint === 'KetBra'  ){
			//console.log("KETBRA")
			//console.dir( node )
			var tex0 = node.args[0].toTex(options);
			var tex1 = node.args[1].toTex(options);
			if( node.args.length == 2 ){
				return '|\\,' + tex0 +" \\, \\rangle \\langle \\," + tex1 + " \\,|"
				}
			else {
				var tex2 = node.args[2].toTex(options);
				return '|\\,' + tex0 +" \\, \\rangle \\, " + tex1 + "\\, \\langle \\," + tex2 + " \\,|"
				}
			}


		else if( fprint === 'sqrt' ){
			return '\\sqrt{ {' + texexp + '}} ' // CRUCIAL SPACES!
			} 
		
		else if( ( fprint === 'abs' ) || ( fprint === 'norm') ){
			return '|' + texexp.replace(/\((.*)\)/,'$1') + '| ' // CRUCIAL SPACES!
			} 
		
		else  if( symbs[fprint] !== undefined){
			// return '\\color{blue}{' +  fprint + '}(' +  texexp + ')'
			 return ' '+ symbs[fprint]+'{' +  texexp + '}' // CRUCIAL SPACES!
			}
		else {
			// return '\\color{blue}{' +  fprint + '}(' +  texexp + ')'
			 return ' '+ fprint + '(' +  texexp + ')' // CRUCIAL SPACES!
		 	}

		}
	     }
	else  if(node.type == 'OperatorNode'){
                //console.log("OPERATOR NODE")
                //console.dir(node)

        }
        else {
	//console.log("node type = ", node.type);
  	// var v = options['vars'];
  	//console.log("function ", fprint,"v = ");
  	//console.dir(v);
	//console.dir(node);
	}
      };


getblacklist = () => {
 var blacklist = [];
 var blacklistobject =  this.props.questionData.getIn(['global','blacklist','token']);
 if( blacklistobject ){
	blacklistobject = blacklistobject.toJS();
    	try {
    	if( blacklistobject){
		if( !( blacklistobject instanceof Array )){ 
			blacklist  =  new Array(blacklistobject['$'] );
			} else {
			blacklist = ( blacklistobject.map( item =>  ( item['$']  ) ) ) };
			} 
	}
    	catch (e){
		console.log("XML PARSING ERROR IN QUESTIONCLONEDCOMPARENUMERIC");
      		throw("XML PARSING ERROR IN QUESTIONCLONEDCOMPARENUMERIC");

	  }
       }
return blacklist;
}


renderMathJS = (asciitext,vars) => {
    //console.log("2 renderMathJS");
    // console.log("cursorend = ", this.state.cursorend, "length of expression = ", asciitext.length );
    //if( this.state.cursorend === 1000 ){
     //           this.state.cursorend = asciitext.length;
      //          }
    //console.log('asccitext',asciitext.trim());
   // console.log('lasttry', this.state.lasttry);
   // console.log('cursorend', this.state.cursorend);
    //console.log('len', asciitext.length ); 
   var checkingsubexpression = false
   // console.log("RENDER GREENLIGHT", this.state.greenlight)
    if( asciitext.replace(']',')').split(')').length !== asciitext.replace('[','(').split('(').length ){
                // console.log("UNMATCHED PAREN - switch off green")
		this.state.greenlight = false // NEVER GIVE GREEN LIGHT FOR UNMATCHED PARENS
		} 
    if( ( this.state.cursorend === 999 ) ||  
                this.state.cursorend > asciitext.length && 
                this.state.lastparsed && asciitext.trim() === this.state.lasttry ){
		//this.state.greenlight = true;
		//console.log("K greenlight true ");
		//console.log('quick return:', this.state.lastparsed);
		return this.state.lastparsed;
		 }
    var nasciitext = asciitext.trim();  
    if( nasciitext.length === 0 ){
		return '';
		}
     var texsubs = gettexsubs( this.props.questionData);
     //console.log("TEXSUBS = ")
     //console.log(texsubs)
     var blacklist = this.getblacklist();
     var ind, blacklistedvars = [];
     var sub;
     for( ind in  blacklist ){
	blacklistedvars[blacklist[ind]] =  blacklist[ind];
	}
    try{ 
	// FIRST CHECK IF THE INPUT EXPRESSION IS CLEAN
	// AND CAN GENERATE GREEN LIGHT
	var len=asciitext.length;
	var regexes = ['/ *-','\\\\\\\\','\\\\','\\{','\\}','_','%','#','&','\\$','@','\\:','\\?' ];
	var illegals = ['\\','{','}','_','%','#','$','@',':','?','&'];

	var tr = []; tr['\\$'] = ' \\$ '; tr['$'] = ' \\$ '; tr['@'] = '@'; tr['\\:'] = ':';
	tr['\\?'] = '?'; tr['\\}'] = ' \\} '; tr['\\{'] = ' \\{ '; tr['\\\\'] = ' setminus ';
	tr['\\\\\\\\'] = ' setminus setminus '; //console.log(tr); 
        tr['/ *-'] = "/-"
	 //console.log(tr);
	if( this.containsAny(asciitext, illegals) ){
                 console.log("illegal char: switch off green")
                 this.state.greenlight = false;
                }
        // console.log("greenlight status = ", this.state.greenlight );
	if( !(  this.state.cursorend >= len ) && this.state.greenlight){  // XXXXXX
		//console.log("cursorsubstring"); 
		checkingsubexpression = true
		throw("cursorsubstring"); 
		};
	if( this.rcontainsAny(asciitext, regexes) ){
		parsed = asciitext;
		for( var c  of regexes ){
			var reg = new RegExp(c);
			if( ! (  tr[c] !== undefined ) ){ 
                                sub = '\\'+c; } 
                        else { 
                                sub = "underlineLEFTBRACKET"+tr[c]+"RIGHTBRACKET" ; 
                                };
			parsed = parsed.replace(reg,'BEGINRED'+sub+'ENDRED');
			}
		parsed = '\\mathsf{' + parsed + '}';
		parsed = parsed.replace(/setminus/g,'\\setminus').
				replace(/BEGINRED/g,'\\color{red}{\\;\\;').
				replace(/ENDRED/g,'\\;\\;}').
                                replace(/LEFTBRACKET/g,'{').
                                replace(/RIGHTBRACKET/g,'}').
                                replace(/underline/g,'\\underline') ;
		this.state.lastparsed = parsed;
		this.state.lasttry = asciitext;
                // console.log("SWITCH OFF GREENLIGHT because of illegals")
		this.state.greenlight = false;
		//console.log("RETURN 3", parsed );
		return parsed;
		}
	try{ 
                //console.log("VARS = ", vars ) 
                // console.log("nasciitext = ", nasciitext)
                var pnasciitext = insertimplicitmultiply(nasciitext)
                var qnasciitext =  absify( braketify( pnasciitext) )
		var ev = mathjs.eval( qnasciitext, vars ) 
		//console.log("ev = ", ev )
                //console.log( ev.toString() )
    		var undefs = ( ( ev.toString() ).replace(/-?\d*(\.\d+)?/g,'') );
 		//console.log("undefs = ", undefs)
 		undefs = undefs.replace(/\W*[+-]*\W*ei\W*/g,'').trim();  // XXXXXXXXXXXXXXXXXXXX CATCH COMPLEX NUMBERS
                undefs = undefs.replace(/,/g,'').
                                replace(/\]/g,'').
                                replace(/\[/g,'').
                                trim()
		// console.log("undefs = ", undefs)
    		var isnan = isNaN( mathjs.max( mathjs.abs( ev )) ); // Flag error even if mathjs.eval is OK but result is not a number
		if( undefs.length > 0 ){ 
                        console.log( "SWITCH OFF GREENLIGHTS BECAUSE OF undefs")
                        console.log( "undefs = ", undefs)
                        console.log( undefs )
                        this.state.greenlight = false;
                          }
 		if(  isnan  ){
			blacklistedvars[undefs] =   undefs
			blacklist.push(undefs);
			console.log("B greenlight false");
			this.state.greenlight = false;
			} else {
			//console.log("RESET GREENLIGHT TO TRUE ");
			this.state.greenlight = true;
			}
	    	}
	catch(e){
		if( ! checkingsubexpression){
			this.state.greenlight = false;
			//console.log("C greenlight false");
			}
		if( !  ( e instanceof String  ) ){ e = e.toString() ; };
		var er = "Undefined symbol";
 		var n = e.search(er)  ;
 		if(  n >= 0  ){
 			var undefvar = ( e.substring(n  + er.length )).trim();
			blacklist.push(undefvar);
			blacklistedvars[undefvar] =   undefvar;
			}
		}
	var blk = this.containsAny(nasciitext, blacklist);  		//  
	if( blk ){
		//console.log("K greenlight false");
		this.state.greenlight = false;
		};
	// if input contains any blacklisted sysmbol, fail
	// So a clean input expression; no blacklist issues no problems
        var pnasciitext = insertimplicitmultiply(nasciitext)
	var parsed = ' '+ ( mathjs.parse( absify(braketify(pnasciitext)) )).toTex({'parenthesis': '', 'implicit' : 'show', 
		'blacklist': blacklistedvars,
		'handler': this.customlatex, 
		'texsubs': texsubs,
		'vars': vars  } ) + ' '; // keep, auto or all
        parsed = parsed.replace(/\\\\end{bmatrix}/g,'end{bmatrix}');
	//parsed = parsed.replace(/mod/g,'\\%');
	//parsed = parsed.replace('/\\s%/g','\\%');
	// parsed = parsed.replace(/cdot_/g,'_');
	// parsed = parsed.replace('/\\\\cdot\\\\color{\#390}{\\\\_}/g','Q');

	// if (blk ){ throw("THROW:UNDEFINED SYMBOL:"+ blk ) ;}
	if( this.state.greenlight ){
		this.state.parsable = nasciitext;
        	this.state.parsableparsed =  parsed;
		}
	this.state.lastparsed = parsed;
	this.state.lasttry = asciitext;
	return( parsed);
	}
    catch(e){
	if( e instanceof Error ){ 
                //console.log("GREENLIGHT Q")
                this.state.greenlight = false; 
                        }
	if( !( e instanceof String ) ){ e = e.toString(); }
	// console.log("e = ", e );
	//console.log("D greenlight false");
	//this.state.greenlight = false;
	//console.log("A e = ", e );
	//if( e instanceof Error ){
	if( e ){
		// NONE OF THE EASY FIXES WORKED; REVERT TO LAST OK EXPRESSION AND USE ASCII FOR HEAD AND TAIL
		var beg = this.state.cursorend;
		var end = this.state.cursorend;
                // console.log("beg", beg, "end", end )
		//if( beg == len && end == len ){ end --; }
		var depth = 0;
                var squeeze = absify2(asciitext).replace(/\]/g,')').
                                replace(/\[/g,'(').
                                replace(/</g,'(').
                                replace(/>/g,')')

		for( var i = end;   i <= len  &&  depth <= 0   ; i++ ){
                        var c = squeeze[i];
			if(  c  === '(' ){ depth --; };
			if(  c === ')' ){ depth ++; };
			end = i;
			};
		depth = 0;
		for( var i = beg-1  ;   i >= 0  &&  depth >=  0  ; i-- ){
                        var c = squeeze[i];
			if( c  === '('  ){ depth --; };
			if( c  === ')' ){ depth ++; };
			beg = i;
			};
		if( depth === -1 ){ beg ++; };
		var lastchar = '';
		var lastcharlist =  ['-',',',' ','(','/','+','*','_','^'];
                //console.log(" now: beg", beg, "end", end )
		while( this.containsAny( asciitext.slice(beg,end).trim().slice(-1), lastcharlist)){
				lastchar =  asciitext.slice(beg,end).trim().slice(-1);
				end --; }
                // console.log(" revised: beg", beg, "end", end )
		var body = asciitext.slice(beg,end);
		var head = asciitext.slice(0,beg);
		var tail = asciitext.slice(end,len);
		//console.log("E greenlight false");	
		//this.state.greenlight = false;
		tail = insertimplicitmultiply( tail);
		head = insertimplicitmultiply( head );
                tail = tail.replace(/\^/g,'\\hat{}');
                head = head.replace(/\^/g,'\\hat{}');
                //console.log("partition = ")
                //console.log(tail + ">" + body + "<" + tail )
		
		if( ! (head.trim() === '' ) ){ head = '\\mathsf{ \\color{orange}{ '+head+'} \\;  \\;}' };
		if( ! (tail.trim() === '' ) ){ tail = '\\; \\; \\mathsf{ \\color{orange}{ '+tail+'}}' };
		try{
			if( !( body.trim() === '' ) ){
			if( ! (this.containsAny(body,['_']) ) ){
				var parsed = ( mathjs.parse(  absify( braketify(body)) )).toTex({'parenthesis': '', 'implicit' : 'show', 
				'blacklist': blacklistedvars, 'handler': this.customlatex, 
				'texsubs': texsubs, 'vars': vars } ); // keep, auto or all
        			parsed = parsed.replace(/\\\\end{bmatrix}/g,'end{bmatrix}');
				} else {
				parsed = 'b2\\mathsf{ \\color{orange}{ '+body+'}}b2' 
				}
			//console.log("E greenlight false");
			//this.state.greenlight = false;
			parsed = parsed.replace(/mod/g,'%');
			//parsed = parsed.replace(/%/g,'\\%');
			} else {
			parsed = '';
			}
			parsed =  head + parsed + tail;
			//console.log("undefs = ", undefs);
			//console.log("RETURN1 ", parsed );
			if( parsed.indexOf("color{red}") !== -1 ){ // CATCH THE ILLEGAL VARS PUT OUT BY Texparser
				//console.log("KK greenlight false");
				this.state.greenlight = false;
				}
			this.state.lastparsed = parsed;
			this.state.lasttry = asciitext;
			return parsed;
		  }
		catch(e){
			if( !  ( e instanceof String  ) ){ e = e.toString() ; };
			if( ! checkingsubexpression){
				this.state.greenlight = false;
		 		//console.log("H greenlight false");	
				} 
			//console.log(e)
                        body = body.replace(/, *,/g,",\\blacksquare,")   // ADJACENT COMMAS
                        body = body
			var parsed = head + '\\mathsf{ \\color{blue}{'+ body +' }}' + tail;
			this.state.lastparsed = parsed;
			this.state.lasttry = asciitext;
			//console.log("RETURN2", parsed );
			return parsed;
	     		}
	 	return( "FELL OFF THE END");
		}
   	}
   }



 //newparseVariables  = () => {
  //  return  Object.keys(( getvalsubs( this.props.questionData ) )) 
 // }

 //newparseVariables  = () => {
  //  return  Object.keys(( this.props.questionData.vars ) ) 
 // }


  /* render gets called every time the question is shown on screen */
  render() {  
  // Some convenience definitions
  var question = this.props.questionData;
  var state = this.props.questionState;
  var submit = this.props.submitFunction;
  var pending = this.props.questionPending;
  var input = this.state.value;
  // THE WHOLE STRUCTURE OF USING PARSABLE TO PARTIALLY REWRITE 
  // SYNTACTICALLY QUESTIONABLE STRING IS PROBABLY COUNTERPRODUCTIVE
  var parsable = this.state.parsable;
  var parsableparsed = this.state.parsableparsed;
  //console.log(this.state.cursorbegin);
  //console.log(this.state.cursorend);
  //console.log(" RENDER RETURN  state.response ")
  //console.dir(state.getIn(['response']))
 //console.log(" RENDER RETURN props ")
  //console.dir(this.props)
 

  /*var texsub = [];
  try{
  var prop =  this.props.questionData;
  texsub = gettexsubs( prop );
    }
  catch(e){
    console.log("gettexsubs fails", e);
   }
    
*/

  // System state data
  var xmlerror = false
  var xmlwarning = ''

  try{
        //console.log("LOCATION 1: counter = ", this.state.counter)
        if( this.state.counter == 0) {
                //console.log("LOCATION 2")
                //console.log("counter = ", this.state.counter)
                var vars = getvalsubs(this.props.questionData);
                this.props.questionData.vars = vars;
                var texsub =   gettexsubs( this.props.questionData)
                this.props.questionData.texsub =  texsub
                this.props.questionData.newparseVariables = Object.keys(( vars))
                //console.log("DID RESET VARS")
                }
        // System state data
        var xmlerror = false
        var xmlwarning = ''
        var vars = this.props.questionData.vars 
        var texsub =   this.props.questionData.texsub
        this.state.counter = this.state.counter + 1
        //this.setState({ value: newProps.questionState.getIn(['answer'],'') });
        }
  catch(e){
        console.log("xml error", e )
        xmlerror = true
        xmlwarning = e
        }


  var lastAnswer = state.getIn(['answer'], ''); 
  // Last saved answer in database, same format as passed to the submitFunction
  var correct = state.getIn(['response','correct'], false) || state.getIn(['correct'], false); 
  correct = correct && !xmlerror;
  // Boolean indicating if the grader reported correct answer

  // Custom state data
  var latex = state.getIn(['response','latex'], ''); 
  // Custom field containing the latex code obtained from SymPy.
  var error = state.getIn(['response','error']); 
  // Custom field containing error information
  var warning = state.getIn(['response','warning']) 
  //console.dir(state.getIn(['response']));
  //console.log("warning = ", warning)
  if( xmlerror){
        warning = xmlwarning
        }
   // Custom field containing error information
  var status = state.getIn(['response','status'], 'none'); 
   // Custom field containing the overall status of the answer, corresponds to the css class map inputClass above
  if(state.getIn(['response','detail'])){
    //console.log(state.getIn(['response','detail'] ) );
    error = "Du är inte inloggad, tryck på logga ut eller ladda om sidan.";
    }
    //error = state.getIn(['response','detail'])


  // var varsList = this.parseVariables(this.props.questionData.getIn(['global','$'], ''));
  
  if (! xmlerror ){
        var varsList = this.props.questionData.newparseVariables;
        } else {
        var varsList = {}
      }
  //console.log("varsList = ")
  //console.log( varsList )
  var availableVariables = varsList.length ? "(i termer av " + varsList.join(", ") + ")" : "";
  // HTML output defined as JSX code: Contains HTML entities with className instead of class and with javascript code within curly braces.
  // The styling classes are from UIKit, see getuikit.com for available elements.
  var graderResponse = null;
  // input = insertimplicitmultiply( input );
  var splitinput = this.state.value.split('===');
  if( splitinput.length > 1 ){
	console.log("splitinput = ");
	console.log(splitinput);
	this.state.value = splitinput[1];
	}
  var hasChanged = input !== lastAnswer;
  var nonEmpty = input !== "";
  var parsed = '';
  var mathjsError = null;
  var evaluated = (<Alert type="warning" message={ 'not evaluated' }/>);
  var evaluated = '';
  try { 
	parsed = this.renderMathJS(input,vars) ;
  	}
  catch(e) {
      mathjsError = (<Alert type="warning" message={e.toString() }/>);
	parsed =  'input>'+input +'<cannot be parsed';
	}
  if(input === lastAnswer && lastAnswer !== '' && !error) {
    if(correct) { graderResponse = (<Alert message={"$" + parsed + "$" + " är korrekt."} type="success" key="input" hasMath={true}/>); 
	} else {
      // parsed = parsed.replace(/#390/g,'red') 
      //console.log("parsed = ", parsed)
      graderResponse = (<Alert message={"$" + parsed + "$" + " är inte korrekt."} type="warning" key="input" hasMath={true}/>);
        }
     }
  else if(input !== ''){
	//console.log("WHAT THE ");
	//console.log("input = ", input);
        //console.log("lastAnswer", lastAnswer);
	//console.log("parsed", parsed);
	graderResponse = (<SafeMathAlert message={parsed} key="input"/>);
     }
	
  var DEBUGPARSE = true ; // Set to true to get full error message and result of eval on web page
  var mathjsErrorPrint = DEBUGPARSE ? mathjsError : '';
  var evaluatedPrint = DEBUGPARSE ? evaluated : '';
  return (
        <div className="">
          <label className="uk-form-row uk-display-inline-block">{question.getIn(['text','$'],'')} <span className="uk-text-small uk-text-primary">{availableVariables}</span><HelpClonedCompareNumeric/></label>
{ hasChanged && (<Badge message={"föregående: " + lastAnswer} hasMath={false} className="uk-text-small uk-margin-small-left uk-margin-bottom-remove"/>)}
          <div className="uk-grid uk-grid-small">
          <div className="uk-width-5-6">
          <div className="uk-form-icon uk-width-1-1">
          { !pending && <i className="uk-icon-pencil"/> }
          { pending && <i className="uk-icon-cog uk-icon-spin"/> }
            <input className={"uk-width-1-1 "} type="text" value={this.state.value} onSelect={this.handleChange} onChange={this.handleChange} ></input>
          </div>
          </div>
          <div className="uk-width-1-6">
            <a onClick={(event) => submit(input)} className={ "uk-width-1-1 uk-button uk-padding-remove " + ( nonEmpty && hasChanged && this.state.greenlight ? "uk-button-success" : "")}>
              { pending && <i className="uk-icon-cog uk-icon-spin"/> }
              { !pending && <i className="uk-icon uk-icon-send"/> }
            </a>
            </div>
          </div>
          { error && !hasChanged && <Alert message={error} type="error" key="err"/> }
        { warning && !hasChanged && <Alert message={warning} type="warning" key="warning"/> }
        { graderResponse }
      	{ mathjsErrorPrint}
        { evaluatedPrint}
        </div>
  );
}
}

//Register the question component with the system
registerQuestionType('ClonedCompareNumeric', QuestionClonedCompareNumeric);
