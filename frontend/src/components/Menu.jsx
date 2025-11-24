// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import React from 'react';
import { connect } from 'react-redux';
import {} from '../fetchers.js';

import immutable from 'immutable';
import { traverse, navigateMenuArray } from '../menu.js';

const BaseMenu = ({ menuPath, menuClick, groups, backupstatus }) => {
  var currentItem = traverse(menuPath);
  var leaf = !currentItem.has('menuItems');
  var subItems = currentItem.get('menuItems', traverse(menuPath.butLast()).get('menuItems'));
  var breadcrumbsData = menuPath.reduce(
    (acc, curr) =>
      acc.push({
        name: traverse(acc.last().path.push(curr)).get('name'),
        path: acc.last().path.push(curr)
      }),
    immutable.List([
      {
        name: 'Home',
        path: immutable.List([])
      }
    ])
  );
  var nonLeafBreadcrumbs = breadcrumbsData.filter((item) => traverse(item.path).has('menuItems'));
  var breadcrumbs = nonLeafBreadcrumbs.map((item) => {
    var liClass = '';
    var content = (
      <a className="uk-padding-remove" onClick={(e) => menuClick(item.path)}>
        {item.name}
      </a>
    );
    if (item.path.equals(menuPath) || (leaf && item.path.equals(menuPath.butLast()))) {
      content = <span>{item.name}</span>;
      liClass = 'uk-active';
    }
    return (
      <li key={item.name} className={liClass}>
        {content}
      </li>
    );
  });
  var hasReqGroup = (reqGroups) => {
    if (reqGroups.isEmpty()) {
      return true;
    }
    return reqGroups.map((reqGroup) => groups.includes(reqGroup)).reduce((prev, current) => prev || current);
  };
  var colors =  (item ) => {
	  var ret = 'uk-button-primary'
	  switch( item ) {
	  case "Export exercises" :
		ret =  backupstatus.getIn(["course_exercises_export"],false)  ? 'uk-button-primary': 'uk-button-danger' ;
		break;
	  case 'Course' :
	  	ret =  backupstatus.getIn(["course_exercises_export"],false)  ? 'uk-button-primary': 'uk-button-danger' ;
		break;
	  case 'Server' :
	  	ret = backupstatus.getIn(["course_export"],false)  ? 'uk-button-primary': 'uk-button-danger' ;
		break;
	  case 'Export' :
	  	ret =  backupstatus.getIn(["course_export"],false)  ? 'uk-button-primary': 'uk-button-danger' ;
		break;
	  default:
		ret = "uk-button-primary"
  	}
     return ret
    };

  var subMenu = subItems
    .filter((item) => !item.get('invisible', false) && hasReqGroup(item.get('reqGroup', immutable.List([]))))
    .map((item, key) => {
      var itemname = item.get('name');
      var cssclass =
        'uk-button uk-button-small ' + colors( itemname)  + ' ' + itemname + (menuPath.last() === key ? ' uk-active' : '');
      var tooltip = ( colors(itemname) == 'uk-button-danger' ) ? 'Click here to back up ' : '' 
      return (
        <a
          key={item.get('name')}
          className={cssclass}
          onClick={(e) => menuClick((leaf ? menuPath.butLast() : menuPath).push(item.get('key')))}
          data-uk-tooltip
	  title={tooltip} >
          {item.get('name')}
        </a>
      );
    })
    .toArray();
  return (
    <div className="uk-flex uk-flex-column uk-flex-middle">
      <div className="uk-button-group uk-margin-left">{subMenu}</div>
      {false && menuPath.size > 0 && !(menuPath.size == 1 && leaf) && (
        <ul className="uk-breadcrumb uk-display-inline-block uk-vertical-align-middle">{breadcrumbs}</ul>
      )}
    </div>
  );
};

const mapStateToProps = (state) => {
  return {
    groups: state.getIn(['login', 'groups'], immutable.List([])),
    menuPath: state.get('menuPath'),
    backupstatus: state.getIn(['login', 'backupstatus'], immutable.List([])),

  };
};

const mapDispatchToProps = (dispatch) => ({
  menuClick: (path) => dispatch(navigateMenuArray(path.toJS()))
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseMenu);
