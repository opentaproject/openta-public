import React, { PropTypes, Component } from 'react';
import uniqueId from 'lodash/uniqueId';
import HelpCompareNumeric from './HelpCompareNumeric.jsx'
import MathSpan from '../MathSpan'

export default class HelpDevLinearAlgebra extends Component {
  render = () => (
  <span>
<a data-uk-toggle={"{target:'#" + this.id + "'}"}><i className="uk-icon uk-text-warning uk-icon-small uk-icon-question-circle-o uk-margin-small-left"/></a>
<div id={this.id} className="uk-hidden">
  <p>Skriv in ditt svar i rutan och tryck på <i className="uk-icon uk-icon-send uk-margin-small-left uk-margin-small-right"/> för att kontrollera. Under tiden som du skriver in uttrycket får du löpande information om eventuella syntaxfel.</p>
  Förutom syntax i vanliga svarsfält (<HelpCompareNumeric/>) så finns det här även vektoroperatorer som skrivs på funktionsform: kryssprodukt <code>cross(v1, v2)</code>, skalärprodukt <code>dot(v1, v2)</code> och storlek av en vektor <code>norm(v)</code> (eller <code>abs(v)</code>).
    <hr/>
    T.ex kan uttrycket <MathSpan message="$(\vec{u}+\vec{v}) \times \vec{w}$"></MathSpan> skrivas som <code>cross(u+v,w)</code> 
    <hr/>
    Variabler i uppgiften kan beteckna vektorer/matriser (skall framgå av uppgiftsformulering) och skrivs in som vanligt. Vektorer och matriser kan även skrivas in explicit med hakparanteser: <MathSpan message="$\begin{pmatrix} x \\ y \end{pmatrix}$"/> skrivs in som <code>[x,y]</code>, <MathSpan message="$\begin{pmatrix} a & b \\ c & d \end{pmatrix}$"/> skrivs som <code>[[a,b],[c,d]]</code>. 
  </div>
  </span>
);

  componentWillMount = () => {
    this.id = uniqueId('help');
  } 
}
