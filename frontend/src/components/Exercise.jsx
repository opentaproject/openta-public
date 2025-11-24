// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

'use strict';
import InnerHTML from 'dangerously-set-html-content'
import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import ReactDOM from 'react-dom';
import Alert from './Alert.jsx';
import QMath from './QMath.jsx';
import AsciiMath from './AsciiMath.jsx';
import immutable from 'immutable';
import moment from 'moment';
import DOMPurify from 'dompurify';
import ExerciseImageUpload from './ExerciseImageUpload.jsx';
import T from './Translation.jsx';
import t from '../translations.js';
import Badge from './Badge.jsx';
import Plot from './Plot.jsx';
import Assets from './Assets.jsx';
import { SUBPATH ,  user_permissions ,use_sidecar ,sidecar_url } from '../settings.js';
import classNames from 'classnames';
import uniqueId from 'lodash/uniqueId';
import { navigateMenuArray } from '../menu.js';
import Question from './Question.jsx';
import ReactDOMServer from 'react-dom/server';
import xml2js from 'xml2js';
import { all, create } from 'mathjs';
const math = create(all, {} )


var XMLParser = new xml2js.Parser({
  trim: true,
  explicitArray: false,
  explicitCharkey: true,
  charkey: '$',
  attrkey: '@attr',
  explicitChildren: true,
  preserveChildrenOrder: true,
  charsAsChildren: true,
  childkey: '$children$',
  strict: true,
  async: false, // set to true caused fail in v421
  chunkSize: 1000
});

import { fetchAssets } from '../fetchers.js';

var unstableKey = 0;
const nextUnstableKey = () => unstableKey++
var nextplotkey = 0
var nextidkey = 0


/* const range = ( xbeg, xend , length) =>  {
       return (
    		Array.from({
      		length: length + 1
    		}, (_, i) => (xbeg + i * ((xend - xbeg) / length))))
		};
		*/
/* const StringToHtml = () =>{
  const [html, setHtml] = useState("");
  useEffect(() => {
    setHtml("<div>Html stored as a string</div>")
  }, [html])
  return(
      <div>{html}</div>
  )
}
*/

class BaseExercise extends Component {
  constructor(props) {
    super(props);
    this.state = {
	    qkeys: Array([]), 
	    oldkeys: Array([]),
	    warn_for_deletion: false,
    	};
    this.exerciseRef = React.createRef();
    this.itemDispatch = {
      exercisename: this.renderName,
      text: this.renderText,
      figure: this.renderFigure,
      question: this.renderQuestion,
      jscript: this.renderScript,
      html: this.renderScript,
      snippet: this.renderScript,
      qmath: this.renderQuestionMath,
      asciimath: this.renderAsciiMath,
      solution: this.renderSolution,
      hidden: this.renderHidden,
      asset: this.renderAsset,
      p: this.renderHTMLElement(),
      i: this.renderHTMLElement(),
      b: this.renderHTMLElement(),
      strong: this.renderHTMLElement(),
      em: this.renderHTMLElement(),
      pre: this.renderTag('<pre>', '</pre>'),
      code: this.renderTag('<pre><code>', '</code></pre>'),
      h3: this.renderHTMLElement(),
      h2: this.renderHTMLElement(),
      h1: this.renderHTMLElement(),
      hr: this.renderHTMLElementHR(),
      br: this.renderHTMLElementBR(),
      ul: this.renderHTMLElement('uk-list'),
      li: this.renderHTMLElement(),
      table: this.renderHTMLElement(),
      tr: this.renderHTMLElement(),
      thead: this.renderHTMLElement(),
      tbody: this.renderHTMLElement(),
      td: this.renderHTMLElement(),
      th: this.renderHTMLElement(),
      a: this.renderHTMLElementA(),
      plot: this.renderPlot,
      right: this.renderRight,
      __text__: this.renderBareText,
      alt: this.renderAltText
    };

  }

  static propTypes = {
    admin: PropTypes.bool,
    exerciseKey: PropTypes.string.isRequired,
    onQuestionInputKeyUp: PropTypes.func,
    exerciseState: PropTypes.object,
    //pendingState: PropTypes.object,
    onHome: PropTypes.func,
    locked: PropTypes.bool
  };


  renderQuestion = (itemjson, json, meta, exerciseKey) => {
    var questions = json.getIn(['exercise', 'question'], immutable.List([]));
    var question = itemjson;
    var questionRenderText = (itemjson) => this.renderText(itemjson, json, meta, exerciseKey);
    var locked = this.props.locked && !this.props.author;
    var duplicate = questions.filter((q) => q.getIn(['@attr', 'key']) == question.getIn(['@attr', 'key'])).count() > 1;
    var duplicatew = questions.filter((q) => q.getIn(['@attr', 'type']) == 'webworks' ).count() > 1;
    var quid = question.getIn(['@attr', 'key']);
    var questionKey = duplicate ? uniqueId('duplicate-id') : question.getIn(['@attr', 'key']);
    var qkeys =   questions.map((q) => q.getIn(['@attr', 'key']) ) 
    if ( this.state.qkeys.size > 0  && ! this.state.warn_for_deletion ) {
    	let difference = qkeys.filter(x => !this.state.qkeys.includes(x));
	if ( difference.size> 0 ){
		if ( ! this.state.warn_for_deletion ){
			var missing =  this.state.qkeys.filter(x => !qkeys.includes(x));
			this.state.oldkeys =  missing ;
			var s = String( missing.first() );
			alert("WARNING do you really need to change this key? The key is arbitrary and can be any string. But if you change it,  all previous student work for this question will lost. Click OK to proceed with no further warning. Either set it back to " + s + " or change it to something else.  You can do a browser page reload  if you don\'t care about losing your edits.   After Save, the change is irrevocable. " )
		};
    		this.state.warn_for_deletion = true
	}
    }
    this.state.qkeys = qkeys;
    return (

      <div key={questionKey}>
	{/* this.state.warn_for_deletion && this.props.admin && (
          <Alert
            message={
              'Warning: you are modifying key ' + this.state.oldkeys[0] + ' ! If you do this, all student answers will be lost'
            }
            type="error"
          />
        )*/}

        {duplicate && ! duplicatew && this.props.admin && (
          <Alert
            message={
              'Duplicate question key ' + quid + ' ! (If you copied a question you must change the key attribute)'
            }
            type="error"
          />
        )}
    {duplicatew && this.props.admin && (
          <Alert
            message={
              'Only one webworks question per exercise.'
            }
            type="error"
          />
        )}


        {!duplicate && (
          <form key={question.getIn(['@attr', 'key'])} className="uk-form" onSubmit={(event) => event.preventDefault()}>
            <Question
              exerciseKey={this.props.exerciseKey}
              locked={locked}
              renderText={questionRenderText}
              questionKey={questionKey}
	      assets={["assetstub"]}
	      exerciseState={this.props.exerciseState}
	      submits='0'
            />
          </form>
        )}
      </div>
    );
  };

   renderTag =
    (tagopen = '<pre>', tagclose = '</pre>', extraAttrs = []) =>
    (itemjson, json, meta, exerciseKey) => {
      var children = itemjson
        .get('$children$', immutable.List([]))
        .filter((item) => item.get('#name') === 'figure')
        .map((child) => this.dispatchElement(child, json, meta, exerciseKey))
        .toSeq();
      var txt = itemjson.get('$')
      //txt = txt.trimLeft('<![CDATA[/').trimRight(']]>')
      //textArea.innerText = txt;
      //txt = textArea.innerHTML;
      txt = txt.replace(/</g,'&lt;')
      txt = txt.replace(/</g,'&gt;')
      return (
        <span className="uk-clearfix" key={'text'}>
          <span className="uk-align-right">{children}</span>
          <span dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(tagopen + txt + tagclose) }} />
        </span>
      );
    };



  brokenrenderTag =
    (tagopen = '<pre>', tagclose = '</pre>', extraAttrs = []) =>
    (itemjson, json, meta, exerciseKey) => {
      var children = itemjson
        .get('$children$', immutable.List([]))
        .filter((item) => item.get('#name') === 'figure')
        .map((child) => this.dispatchElement(child, json, meta, exerciseKey, nextidkey ++ ))
        .toSeq();
      var tagname = itemjson.get("#name")
      var xml = String( this.props.exerciseState.getIn(['activeXML']) );
      var parser = new DOMParser();
      var xmlDoc = parser.parseFromString(xml,"text/xml")
      var js = xmlDoc.getElementsByTagName(tagname)[0]
      var txt = js.innerHTML 
      var textArea = document.createElement('textarea'); //  TRICK TO ESCAPE SPECIAL CHARACTERS
      txt = txt.trimLeft('<![CDATA[/').trimRight(']]>')
      textArea.innerText = txt;
      txt = textArea.innerHTML;
      txt = txt.replace(/&amp;lt;/,'<')
      txt = txt.replace(/&amp;gt;/,'>')
      return (
        <span className="uk-clearfix" key={'text'}>
          <span className="uk-align-right">{children}</span>
          <span dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(tagopen + txt + tagclose) }} />
        </span>
      );
    };

  renderQuestionMath = (itemjson, json, meta, exerciseKey) => {
    var question = itemjson;
    var type = question.getIn(['@attr', 'type'], 'default');
    return (
      <span key={'qmath' + nextUnstableKey()}>
        <QMath exerciseKey={exerciseKey} questionType={'basic'} expression={itemjson.get('$', '')} />
      </span>
    );
  };

  renderAsciiMath = (itemjson, json, meta, exerciseKey) => {
    return (
      <span key={'asciimath' + nextUnstableKey()}>
        <AsciiMath>{itemjson.get('$', '')}</AsciiMath>
      </span>
    );
  };

  renderLegacyText = (itemjson, json, meta, exerciseKey) => {
    var children = itemjson
      .get('$children$', immutable.List([]))
      .filter((item) => item.get('#name') === 'figure')
      .map((child) => this.dispatchElement(child, json, meta, exerciseKey, nextidkey++))
      .toSeq();
    return (
      <div className="uk-clearfix" key={'text'}>
        <div className="uk-align-medium-right">{children}</div>
        <span
          key={uniqueId('dangeroursly-se')}
          dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(itemjson.get('$')) }}
        />
      </div>
    );
  };

  filterLanguage = (children) => {
    var filtered = children.filter((item) => item.getIn(['@attr', 'lang'], undefined) === this.props.language);
    if (filtered.size > 0) {
      return filtered;
    } else {
      return children.filter((item) => !item.hasIn(['@attr', 'lang']));
    }
  };

  renderAltText = (itemjson, json, meta, exerciseKey) => {
    if (itemjson) {
      var className = itemjson.getIn(['@attr', 'class'], '');
      var childrenList = this.filterLanguage(itemjson.get('$children$', immutable.List([])));

      if (childrenList.filter((item) => item.get('#name', '') === 'figure').size == 1 && childrenList.size == 2) {
        return this.renderLegacyText(itemjson, json, meta, exerciseKey);
      }
      var children = childrenList.map((child) => this.dispatchElement(child, json, meta, exerciseKey, nextidkey ++ )).toSeq();
      XMLParser.reset();
      var xml = this.props.exerciseState.getIn(['activeXML']);
      var parser = new DOMParser();
      var xmlDoc = parser.parseFromString(xml, 'text/xml');
      var alts = xmlDoc.getElementsByTagName('alt');
      var htmlstring = ReactDOMServer.renderToStaticMarkup(children);
      var hashkey = itemjson.getIn(['@attr', 'hashkey']);
      var lang = itemjson.getIn(['@attr', 'lang']);
      var s = '';
      for (var i = 0; i < alts.length; i++) {
        var _hashkey = alts[i].getAttribute('hashkey');
        var _lang = alts[i].getAttribute('lang');
        if (_lang == lang && _hashkey == hashkey) {
          var childnodes = alts[i].childNodes;
          for (var j = 0; j < childnodes.length; j++) {
            var node = childnodes[j];
            var nodename = node.nodeName;
            if (nodename == '#text') {
              s = s + childnodes[j].textContent;
            } else {
              s = s + '<' + nodename + '>' + childnodes[j].textContent + '</' + nodename + '>';
            }
          }
        }
      }

      var translation_key = '[' + hashkey + ',' + lang + '] ';
      return (
        <div className={'uk-clearfix ' + className} key={'text' + nextUnstableKey()}>
          {' '}
          {children}{' '}
        </div>

        //<div className={"uk-clearfix " + className } key={"text" + nextUnstableKey()}>
        //  {children}
        //</div>
      );
    } else {
      return <Badge className={'uk-badge uk-text-medium uk-badge-danger'}> Text missing ! </Badge>;
    }
  };


  restoreXML =  (itemjson, json, meta, exerciseKey, nextid , level = 0 ) => {
      var spacing = '    '.repeat(level)
      var spacing = ''
      level = level + 1 ;
      if( itemjson ){
      var childrenList = this.filterLanguage(itemjson.get('$children$', immutable.List([])));
      var children = childrenList.map((child) => this.restoreXML(child, json, meta, exerciseKey, nextidkey ++ , level ))
      var tagname = itemjson.get("#name")
      var attributes = itemjson.getIn(['@attr'],immutable.List([])).toJS() 
      if( childrenList.size ==  0 ) {
	      var contents = ""
	      if ( tagname == "__text__" ){
		      contents = itemjson.getIn(['$'] ).trim()  + '\n'
	      		} else {
				var keys = Object.keys( attributes)
      				var s =  ( keys.map( (o) => String(  o ) + '=\'' +  String( attributes[o] ) + '\''   ) ).join(' ')
      				if( s ) { s = ' ' + s } ;
			  	var contents = ( spacing + '<' + tagname +  ( s ).trimRight()  +  '/>')
			}
	      return( contents )
      }
      var keys = Object.keys( attributes)
      var s = keys.map( (o) => String(  o ) + '=\"' +  String( attributes[o] ) + '\"'   ).join(' ')
      if( s ) { s = ' ' + s } ;
      var leafstring  = ( spacing + '<' + tagname +  ( s ).trimRight()  +  '>' + ( children ).join('')   +  spacing + '  </' + tagname + '>'  )
      return ( leafstring )
    }
  }
	


  renderText = (itemjson, json, meta, exerciseKey) => {
    if (itemjson) {
      var className = itemjson.getIn(['@attr', 'class'], '');
      var childrenList = this.filterLanguage(itemjson.get('$children$', immutable.List([])));

      if (childrenList.filter((item) => item.get('#name', '') === 'figure').size == 1 && childrenList.size == 2) {
        return this.renderLegacyText(itemjson, json, meta, exerciseKey);
      }
      var children = childrenList.map((child) => this.dispatchElement(child, json, meta, exerciseKey, nextidkey ++ )).toSeq();
      return (
        <div className={'uk-clearfix ' + className} key={'text' + nextUnstableKey()}>
          {children}
        </div>
      );
    } else {
      return <Badge className={'uk-badge uk-text-medium uk-badge-danger'}> Text missing ! </Badge>;
    }
  };

  renderFigure = (itemjson, json, meta, exerciseKey) => {
    var figure = itemjson.get('$', '');
    var size = itemjson.getIn(['@attr', 'size'], 'small');
    var sizeClass = {
      'uk-thumbnail': true,
      'uk-thumbnail-small': size == 'small' || !(size in ['small', 'medium', 'large']),
      'uk-thumbnail-medium': size == 'medium',
      'uk-thumbnail-large': size == 'large'
    };

    return (
      <a
        className={classNames(sizeClass)}
        key={'figure' + figure}
        href={SUBPATH + '/exercise/' + exerciseKey + '/asset/' + figure.trim()}
        data-uk-lightbox
        data-lightbox-type="image"
      >
        <img src={SUBPATH + '/exercise/' + this.props.exerciseKey + '/asset/' + figure.trim()} alt="" />
        {itemjson.has('caption') && <div className="uk-thumbnail-caption">{itemjson.getIn(['caption', '$'])}</div>}
      </a>
    );
  };


    /*renderLiteral= (itemjson,json ) => {
	var id = String( itemjson.getIn(['@attr','id'])) 
	var tag = String( itemjson.get("#name"))
	var xml = this.restoreXML(itemjson, json,this.props.exercisemeta, this.props.exerciseKey, 0  ) 
	var parser = new DOMParser();
	var xmlDoc = parser.parseFromString(xml,"text/xml");
	var js = xmlDoc.getElementById(id)
	var html = js.innerHTML.relace(/</g,"&lt;")
	var html = js.innerHTML.relace(/</g,"&gt;")
	return ("")
	}
	*/

	




    renderScript = (itemjson,json ) => {
	try { 
	// var id = String( itemjson.getIn(['@attr','id'])) 
	var tag = String( itemjson.get("#name"))
	//if ( false && this.props.author ){ 
	//	var xml = String( this.props.exerciseState.getIn(['activeXML'],'')  )
	//} else { 
	var xml = this.restoreXML(itemjson, json,this.props.exercisemeta, this.props.exerciseKey, 0  ) 
	//       }
	var parser = new DOMParser();
	var xmlDoc = parser.parseFromString(xml,"text/xml");
	var js = xmlDoc.getElementsByTagName(tag)[0]
	var children = js.childNodes
	var inorder = true
	var foundscript = false
	var child_not_in_order = null
	var edom = ''
	for ( let child of children ) {
		var n = child.nodeName;
		var foundscript = ( n == 'script' ) ? true : foundscript
		if ( n != 'script' && n != '#text' && foundscript ){
			inorder = false 
			child_not_in_order = child

		  }
	      }
	if ( child_not_in_order ){
		var msg = "The script " + child_not_in_order.outerHTML + " is out of order; it must be last"
		var edom = (  <Badge className={'uk-badge uk-text-medium uk-badge-danger'}> {msg}  </Badge> )
	      }
        //var jss = xmlDoc.getElementsByTagName(tag)
	//var i = 0
	//for ( let v of jss ){ if ( v.id == id  ){ i ++ } }
	//var duplicate = ( i > 1 )
	var meta = this.props.exercisemeta
	var links =  js.getElementsByTagName('script')
	for ( let link of links ){
		try {
   			eval(link.innerHTML)
			} catch (e) {
   		var msg = 'Invalid css  ' +  e.toString()  +    link.innerHTML ;
		var edom = (  <Badge className={'uk-badge uk-text-medium uk-badge-danger'}> {msg}  </Badge> )
		}
		
		if ( link.attributes.src ){ 
			var src = link.attributes.src.nodeValue
			if ( ! src.includes('/')  ){
				link.setAttribute('src','/exercise/' + this.props.exerciseKey + '/asset/' + src )
			     }	

		}
	}

	var links =  js.getElementsByTagName('link')
	for ( let link of links ){
		try {
   			eval(link.innerHTML)
			} catch (e) {
   		var msg = 'Invalid style link: ' +  e.toString()  +    link.innerHTML ;
		var edom = (  <Badge className={'uk-badge uk-text-medium uk-badge-danger'}> {msg}  </Badge> )
		}
		
		if ( link.attributes.href){ 
			var href= link.attributes.href.nodeValue
			if ( ! href.includes('/')  ){
				link.setAttribute('href','/exercise/' + this.props.exerciseKey + '/asset/' + href)
			     }	

		}
	}

	var html = js.innerHTML
	//if ( duplicate ){
        //		var edom =  <Badge className={'uk-badge uk-text-medium uk-badge-danger'}> Duplicate id {id}  </Badge>
        //		}
	return ( 
		<div key={"script-" + nextidkey  }>
		{edom}
 		<InnerHTML html={html} />
		</div>
	 )
	} catch (e ) {
		return ( <div> <Alert message= {e.toString()}  type="error" />  { this.renderHTMLElement( itemjson, json , this.props.exercisemeta, this.props.ExerciseKey ) } </div>
		)
	}
    }

    renderPlot = (itemjson, json, meta, exerciseKey) => {
    this.plotkey = 'plot-' + nextplotkey++;
    if (itemjson) {
      var className = itemjson.getIn(['@attr', 'class'], '');
      var is_plotly =  ! ( itemjson.getIn(['data']  ) == null )
      if (is_plotly ){
      	var datastring =   itemjson.getIn(['data','$' ] ) 
      	var layoutstring  = itemjson.getIn(['layout','$'] )
	var varstring = itemjson.getIn( ['vars','$'],'')
	var configstring = itemjson.getIn( ['config','$'],'{ staticPlot: true }')
      	var trace1 = null
      	var layout = null
	var vars = null
	var config = null
          try { 
          	eval( "vars = " + varstring + ";")
    	} catch (err ){ trace1 = [{}]   ;  layout = {title: 'Error in vars ' +  err.message  } }
          try { 
          	eval( "layout = " + layoutstring + ";")
    	} catch (err ){ trace1 = [{}]   ; layout = {title: "Error in layout \n" + err.message }  }
           
          try { 
          	eval( "trace1 = " + datastring  + ";")
    	} catch (err ){ trace1 = [{}]   ; layout = {title: 'Error in data ' +  err.message  } }

          try { 
          	eval( "config = " + configstring + ";")
    	} catch (err ){ trace1 = [{}]   ; layout = {title: 'Error in config ' +  err.message  } }


          var data = trace1;
          try { 
	      var ret = ( <div key={'abc' + this.plotkey}>
    	     <Plot   plotkey={this.plotkey} data={data} layout={layout} config={config}   /> 
    	     </div>
          		) } catch( err ) {
    			var ret = <div> Error </div>
    		}
          return ret 

	  } 
    
        } else {
          var ret = ( <div > <Badge className={'uk-badge uk-text-medium uk-badge-danger'}> Plot data missing ! </Badge> </div> )
        }
    return ( ret )
  }




  renderSolution = (itemjson, json, meta, exerciseKey) => {
    var children = itemjson
      .get('$children$', immutable.List([]))
      .map((child) => this.dispatchElement(child, json, meta, exerciseKey, nextidkey ++ ))
      .toSeq();
    var canViewXML = this.props.author || this.props.view;
    var hiddentxt = t('Hidden for students.  ');
    var showtxt = t('Show solution for students by checking solution in exercise options. ');
    return (
      <div className="uk-margin-bottom uk-text-center" key={'solution' + nextUnstableKey()}>
        {this.props.solution && children}

        {!this.props.solution && this.props.view && (
          <div className="uk-block uk-block-muted uk-padding-remove uk-text-warning">
            {hiddentxt}
            {canViewXML && <span>{showtxt} </span>}
          </div>
        )}
        {!this.props.solution && this.props.view && (
          <div className="uk-block uk-block-muted uk-padding-remove">{children}</div>
        )}
      </div>
    );
  };

  renderHidden = (itemjson, json, meta, exerciseKey) => {
    var label = itemjson.getIn(['@attr', 'label'], 'hidden');
    var children = itemjson
      .get('$children$', immutable.List([]))
      .map((child) => this.dispatchElement(child, json, meta, exerciseKey, nextidkey ++ ))
      .toSeq();
    var style =
      'uk-icon uk-icon-medium uk-text-primary uk-text-small uk-icon-life-ring uk-margin-small-left uk-text-middle';
    var subClass = 'uk-hidden uk-text-muted uk-background-secondary uk-text-small';
    var labelClass = 'uk-padding uk-padding-remove-vertical uk-text-danger';
    var id = uniqueId('hiddenItem');
    if (this.props.view) {
      return (
        <span key={id}>
          <a className="uk-button  uk-button-link" data-uk-toggle={"{target:'#" + id + "'}"}>
            <i className={style} />
            <span key={'hidden1' + nextUnstableKey()} className={labelClass}>
              {' '}
              {label}{' '}
            </span>{' '}
          </a>
          <div id={id} className={subClass}>
            <div
              className="uk-margin-bottom uk-text-left uk-panel uk-panel-box uk-panel-box-primary"
              key={'hidden' + nextUnstableKey()}
            >
              {children}
            </div>
          </div>
        </span>
      );
    } else {
      return <span />;
    }
  };

  renderAsset = (itemjson, json, meta, exerciseKey) => {
    try {
      return (
        <a
          key={'asset' + itemjson.get('$')}
          className="uk-button uk-button-small"
          target="_blank"
	  referrerPolicy="origin-when-cross-origin"
	  referrer="origin-when-cross-origin"
          href={SUBPATH + '/exercise/' + exerciseKey + '/asset/' + itemjson.get('$', '').trim()}
        >
          {t(itemjson.getIn(['@attr', 'name']))}
        </a>
      );
    } catch (err) {
      return (
        <Badge className={'uk-badge uk-text-medium uk-badge-danger'}>
          {' '}
          Asset error; perhaps you wanted to use tag figure.
        </Badge>
      );
    }
  };

  renderName = (itemjson, json, meta, exerciseKey) => {
    var deadlineDate = meta.get('deadline_date')
    var deadlineTime = meta.get('deadline_time')
    var deadlineDateFormat = '';
    if (deadlineDate) {
      if (deadlineTime) {
        deadlineDateFormat = moment(deadlineDate + ' ' + deadlineTime).format('D MMM HH:mm');
      } else {
        deadlineDateFormat = moment(deadlineDate).format('D MMM');
      }
    } else {
	deadlineDateFormat = 'none';
	deadlineDate = '';
	   }
    var obligatorisk = meta.get('required', false);
    var bonus = meta.get('bonus', false);
    var translations = this.filterLanguage(itemjson.get('$children$', immutable.List([])));
    var canViewXML = this.props.author || this.props.view;
    try {
      var name = translations.first().get('$');
    } catch (error) {
      var name = 'name missing';
    }
    var view_xml = ( user_permissions == "view_xml")

    var sidecar_count = this.props.sidecar_count
    try { 
    var c0 = sidecar_count.get('sidecar_count',-1)
    var c2 = sidecar_count.get('unread').includes( this.props.exerciseKey )
    var c1 = sidecar_count.get('exercises_with_posts').includes( this.props.exerciseKey )
    var sc = c2 ?  2 : ( c1 ? 1 : c0  )
    }  catch {
	    c2 = false;
	    c1 = false;
	    sc = -1;
    }


    if ( sc <  0  ){ var sidecar_icon = ''
  	} else if ( sc ==  1  ){
	  var sidecar_icon = "https://storage.googleapis.com/opentaproject-cdn-bucket/icons/sscircle.png" 
  	} else  if ( sc == 2 ){ 
	  var sidecar_icon = "https://storage.googleapis.com/opentaproject-cdn-bucket/icons/ss.png" 
  	} else { var sidecar_icon = "https://storage.googleapis.com/opentaproject-cdn-bucket/icons/s.ico" }

    var sidecar_class = ['uk-icon-pencil','uk-icon uk-icon-circle-o','uk-text-danger uk-icon uk-icon-circle' ]
    if ( sc > -1 ){
    	var sidecar_icon = sidecar_class[ sc ]
    }

 
	
    //var sc = sidecar_count.get('sidecar_count')
    var sidecar_text = String( sc )
    sidecar_text = ''



    return (
      <div key={name}>
        <h1 className="uk-article-title">
          {name} { view_xml && ( 
	   <a className={'uk-button'} href={'/exercise/' +  exerciseKey + '/download_assets'}>
            <i className="uk-icon-download" title="Download entire exercise as zip. " />{' '}
          </a>) }
	     { use_sidecar != 'False' &&  sc >= 0 && (
	    <a title="Open Sidecar" href={"/launch_sidecar?filter_key=" + exerciseKey } className="button-link"> 
		      <i className={sidecar_icon}  style={{ 'marginLeft' : '10px' , 'fontSize' : '20px' }} > </i>

<button className="uk-button uk-button-link"> { sidecar_text} </button>  </a>
	     )}

          {deadlineDate && (
            <div className="uk-badge uk-badge-danger uk-margin-small-left">
              <a
                data-uk-tooltip
                title="You can still submit answers and pictures after deadline but they will be marked late. The date of the first correct answer is used to determine if the problem timestamp, so you can continue to experiment with answers after deadline without being marked late. "
              >
                Deadline: {deadlineDateFormat}
                <i className="uk-icon uk-icon-small uk-icon-question-circle-o uk-margin-small-left" />
              </a>
            </div>
          )}
          {obligatorisk && <div className="uk-badge uk-margin-small-left">Obligatory</div>}
          {bonus && <div className="uk-badge uk-badge-warning uk-margin-small-left">Bonus</div>}
          {canViewXML && !meta.get('published') && (
            <div className="uk-badge uk-badge-danger uk-margin-small-left">
              <T>Unpublished</T>
            </div>
          )}
        </h1>
      </div>
    );
  };

  renderHTMLElementA = () => (itemjson, json, meta, exerciseKey) => {
    var children = itemjson
      .get('$children$', immutable.List([]))
      .map((child) => this.dispatchElement(child, json, meta, exerciseKey, nextidkey ++ ))
      .toList();
    return (
      <a href={itemjson.getIn(['@attr', 'href'])} target="_blank" key={nextUnstableKey()}>
        {children}
      </a>
    );
  };

  renderHTMLElementHR = () => (itemjson, json, meta, exerciseKey) => {
    return (
      <div key={nextUnstableKey()}>
        {' '}
        <hr />{' '}
      </div>
    );
  };

  renderHTMLElementBR = () => (itemjson, json, meta, exerciseKey) => {
    return (
      <div key={nextUnstableKey()}>
        {' '}
        <br />{' '}
      </div>
    );
  };

  renderHTMLElement =
    (className = '', extraAttrs = []) =>
    (itemjson, json, meta, exerciseKey) => {
	    var attrs = {};
	    for (let attr of extraAttrs) {
        attrs[attr] = itemjson.getIn(['@attr', attr]);
      }

      var children = itemjson
        .get('$children$', immutable.List([]))
        .map((child) => this.dispatchElement(child, json, meta, exerciseKey, nextidkey ++ ))
        .toList();
      var itemDOM = React.createElement(
        itemjson.get('#name'),
        {
          className: className + ' ' + itemjson.getIn(['@attr', 'class']),
          style: itemjson.getIn(['@attr', 'style']),
          key: nextUnstableKey(),
          ...attrs
        },
        children
      );
      return itemDOM;
    };

  renderBareText = (itemjson, json, meta, exerciseKey) => (
    <span key={nextUnstableKey()} dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(itemjson.get('$')) }} />
  );

  renderRight = (itemjson, json, meta, exerciseKey) => (
    <div className="uk-align-medium-right" key={nextUnstableKey()}>
      {itemjson
        .get('$children$', immutable.List([]))
        .map((child) => this.dispatchElement(child, json, meta, exerciseKey, nextidkey ++ ))
        .toList()}
    </div>
  );

  dispatchElement = (element, json, meta, exerciseKey, idkey ) => {
    if (element.get('#name') in this.itemDispatch) {
      return this.itemDispatch[element.get('#name')](element, json, meta, exerciseKey, idkey ++ );
    } else {
      return null;
    }
  };

  basename = (path) => {
    if (!path == '') {
      return path.split('/').reverse()[0];
    } else {
      return '';
    }
  };

  render() {
    try{ 
    unstableKey = 1921993  // SET UNSTABLE KEY FOR EXERCISE TO AVOID REDRAWING
    nextplotkey = 0
    nextidkey = 0
    var sidecar_count = this.props.sidecar_count
    try { 
    	var c2 = sidecar_count.get('unread').includes( this.props.exerciseKey )
    	var c1 = sidecar_count.get('exercises_with_posts').includes( this.props.exerciseKey )
	var sc = c2 ?  2 : ( c1 ? 1 : 0  )
    } catch {
	    var c1 = false;
	    var c2 = false;
	    var sc = -1;
    }

    	if ( sc <  0  ){ var sidecar_icon = '' } 
	else if ( sc ==  0  ){ var sidecar_icon = "https://storage.googleapis.com/opentaproject-cdn-bucket/icons/s.ico" }
	else  if ( sc == 1 ){ var sidecar_icon = "https://storage.googleapis.com/opentaproject-cdn-bucket/icons/sscircle.png" } 
	else  if ( sc == 2 ){ var sidecar_icon = "https://storage.googleapis.com/opentaproject-cdn-bucket/icons/ss.png" } 
	else { var sidecar_icon = "https://storage.googleapis.com/opentaproject-cdn-bucket/icons/s.ico" }
    var sidecar_class = ['uk-icon uk-icon-circle','uk-icon uk-icon-circle-o','uk-text-danger uk-icon uk-icon-circle' ]
    if ( sc > 0 ){
    	var sidecar_icon = sidecar_class[ sc ]
    }
 

    /* var sc = c2 ?  2 : ( c1 ? 1 : -1  )
    if ( sc <  0  ){
	  var sidecar_icon = ''
  	} else if ( sc ==  0  ){
	  var sidecar_icon = "https://storage.googleapis.com/opentaproject-cdn-bucket/icons/s.ico" 
  	} else  { 
	  var sidecar_icon = "https://storage.googleapis.com/opentaproject-cdn-bucket/icons/ss.png" 
  	}
	*/

    var exerciseKey = this.props.exerciseKey;
    var key = exerciseKey;
    var state = this.props.exerciseState;
    var exerciseState = this.props.exerciseState;
    //////////////////
    //var locked = true
    //if ( this.props.exercisemeta.size > 0 ){
    //   var locked = this.props.exercisemeta.first().getIn(['meta'],{} ).getIn(['locked'],true)
    //  }
    var locked = this.props.locked && !this.props.author;
    //var pendingState = this.props.pendingState;
    var filename = ( this.basename(state.getIn(['path'], '/')) ).toString();
    var json = state.get('json', immutable.Map({}));
    var error = json.get('error', null);
    var response_awaits = Number(state.getIn(['response_awaits'], 0));
    var meta = state.get('meta', immutable.Map({}));
    var image = this.props.exerciseState.getIn(['meta', 'image']);
    if (meta === null) {
      meta = immutable.Map({});
    }
    var items = json
      .getIn(['exercise', '$children$'], immutable.List([]))
      .map((child) => this.dispatchElement(child, json, meta, key, nextidkey ++ ))
      .toSeq();
    var filename_and_key = filename + " key=  " + key 
    var canViewXML = this.props.author || this.props.view;
    var canUpload = !this.props.view || this.props.admin || this.props.author;
    var showResponseAwaits = response_awaits > 0;
    // I CANT FIGURE OUT WHY I CANT PUT {filenam} into filenameDOM if blank
    var filenameDOM = (
      <span key={'filename-dom'} className="uk-text-bold uk-text-primary">
        Exercise:  {filename_and_key} 
      </span>
    );
    var exerciseDOM = (
      <div className="uk-width-1-1">
        {' '}
        <article
          className="uk-article uk-margin-top uk-margin-small-right uk-margin-small-left"
          ref={this.exerciseRef}
          key={key}
        >
          {canViewXML && showResponseAwaits && (
            <i className="uk-text-danger uk-margin-small-left uk-icon uk-icon uk-icon-envelope" />
          )}
          {error && canViewXML && <Alert message={error} type="error" />}
          {false && canViewXML && filenameDOM}
          {meta.get('student_assets') && <Assets locked={locked} />}
          {canUpload && image && (
            <div className="uk-float-right uk-margin-small-right">
              <ExerciseImageUpload locked={locked} />
            </div>
          )}
          {items}
        </article>{' '}
      </div>
    );

    //if(pendingState.getIn(['exercises', key, 'loadingJSON'], false)) {
    //  return (<Spinner/>);
    //}
    return exerciseDOM;
   } catch ( error ) {
    return (
	 " xml error; edit in XML and assets to avoid this message "
       )

    }
  }

  componentDidMount(props, state, root) {
    this.props.getAssets();
    this.componentDidUpdate(props, state, root);
  }
  componentDidUpdate(props, state, root) {
    var node = this.exerciseRef.current;
    if (node !== null) {
      renderMathInElement(node, {
        delimiters: [
          { left: '$', right: '$', display: false },
          { left: '\\[', right: '\\]', display: true }
        ]
      });
    }
  }
}

const mapStateToProps = (state) => {
  var activeExercise = state.get('activeExercise');
  var activeExerciseState = state.getIn(['exerciseState', state.get('activeExercise')], immutable.Map({}));
  var exercisemeta = activeExerciseState.getIn(['meta'], immutable.Map({}));
  var locked = true;
  var solution = false;
  if (exercisemeta.size > 0) {
    locked = exercisemeta.getIn(['locked'], true);
    solution = exercisemeta.getIn(['solution'], false);
  }
  const defaultLanguage = state.getIn(['course', 'languages', 0], 'en');
  return {
    author: state.getIn(['login', 'groups'], immutable.List([])).includes('Author'),
    admin: state.getIn(['login', 'groups'], immutable.List([])).includes('Admin'),
    view: state.getIn(['login', 'groups'], immutable.List([])).includes('View'),
    sidecar_count :  state.getIn(['login', 'sidecar_count'], immutable.List([])),
    language: state.get('lang', defaultLanguage),
    exerciseKey: state.get('activeExercise'),
    exerciseState: activeExerciseState,
    //pendingState: state.get('pendingState'),
    locked: locked,
    solution: solution
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    onQuestionInputKeyUp: (event, exercise, question) => handleQuestionInputKeyUp(dispatch, event, exercise, question),
    getAssets: () => dispatch(fetchAssets()),
    onHome: () => dispatch(navigateMenuArray([]))
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(BaseExercise);
