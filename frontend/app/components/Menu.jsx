import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import {
} from '../fetchers.js';
import {
  updateMenuPath,
  updateMenuLeafDefaults,
} from '../actions.js';
import Spinner from './Spinner.jsx';
import Badge from './Badge.jsx';

import immutable from 'immutable';
import moment from 'moment';
import {SUBPATH} from '../settings.js';
import { traverse, navigateMenuArray } from '../menu.js';

const BaseMenu = ({menuPath, menuClick, groups}) => {
  var currentItem = traverse(menuPath);
  var leaf = !currentItem.has('menuItems');
  var subItems = currentItem.get('menuItems', traverse(menuPath.butLast()).get('menuItems'))
  var breadcrumbsData = menuPath.reduce(
                                    (acc, curr) => acc.push( {
                                      name: traverse(acc.last().path.push(curr)).get('name'),
                                      path: acc.last().path.push(curr)} ),
                                      immutable.List([ {
                                        name: 'Home',
                                        path: immutable.List([])
                                      } ])
                                   )
  var nonLeafBreadcrumbs = breadcrumbsData.filter( item => traverse(item.path).has('menuItems') );
  var breadcrumbs = nonLeafBreadcrumbs.map( item => {
    var liClass = "";
    var content = (<a className="uk-padding-remove" onClick={e => menuClick(item.path)}>{item.name}</a>);
    if(item.path.equals(menuPath) || (leaf && item.path.equals(menuPath.butLast()))) {
      content = (<span>{item.name}</span>);
      liClass = "uk-active";
    }
    return (
    <li key={item.name} className={liClass}>
      {content}
    </li>);
  })
  var hasReqGroup = reqGroups => {
    if(reqGroups.isEmpty())
      return true;
    return reqGroups.map( reqGroup => groups.includes(reqGroup) ).reduce((prev, current) => prev || current)
  };

  var subMenu = subItems.filter( item => !item.get('invisible', false) && hasReqGroup(item.get('reqGroup', immutable.List([])) ))
    .map( (item, key) => {
    var cssclass = "uk-button uk-button-small uk-button-primary" + (menuPath.last() === key ? " uk-active" : "");
    return ( <a key={item.get('name')} className={cssclass} onClick={e => menuClick((leaf ? menuPath.butLast() : menuPath).push(item.get('key')))}>{item.get('name')}</a> )
  }).toArray();
  return (
    <div className="uk-flex uk-flex-column uk-flex-middle">
    <div className="uk-button-group uk-margin-left">
    {subMenu}
    </div>
    {menuPath.size > 0 && !(menuPath.size == 1 && leaf) &&
    <ul className="uk-breadcrumb uk-display-inline-block uk-vertical-align-middle">
     {breadcrumbs}
    </ul>
    }
    </div>
  )
};

const mapStateToProps = state => {
  return ({
  groups: state.getIn(['login', 'groups'], immutable.List([])),
  menuPath: state.get('menuPath'),
});
}

const mapDispatchToProps = dispatch => ({
  menuClick: (path) => dispatch(navigateMenuArray(path.toJS())),
    
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseMenu)
