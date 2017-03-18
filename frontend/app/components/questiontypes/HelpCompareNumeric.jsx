import React, { PropTypes, Component } from 'react';
import uniqueId from 'lodash/uniqueId';

export default class HelpCompareNumeric extends Component {
  render = () => (
  <span>
<a data-uk-toggle={"{target:'#" + this.id + "'}"}><i className="uk-icon uk-icon-small uk-icon-question-circle-o uk-margin-small-left"/></a>
<div id={this.id} className="uk-hidden">
  <hr/>
  <p>Skriv in ditt svar i rutan och tryck på <i className="uk-icon uk-icon-send uk-margin-small-left uk-margin-small-right"/> för att kontrollera. Under tiden som du skriver in uttrycket får du löpande information om eventuella syntaxfel.</p>
  <p>
I svarsfältet kan man använda de vanliga algebraiska operatorerna * (även mellanslag), /, +, - och ^ tillsammans med paranteser för att gruppera uttryck. Förutom dessa operatorer finns de vanligaste funktionerna: sin, sinh, asin, asinh, cos, cosh, acos, acosh, tan, tanh, atan, atanh, sqrt (kvadratrot), abs (absolutbelopp), ln (naturliga logaritmen) och log.</p>
<p>Argument till funktioner ges med paranteser såsom f(x). Ett exempel på ett typiskt uttryck är</p>
 <pre>(a+b) / sqrt(a^2+b^2) + sin(alpha)</pre>
<p>Ovanför svarsfälten finns en lista med de variabler som kan användas för att skriva ned svaret, notera att dessa ibland har en lite annan form än i själva uppgiftstexten.
  </p>
  <hr/>
</div>
  </span>
);

  componentWillMount = () => {
    this.id = uniqueId('help');
  } 
}
