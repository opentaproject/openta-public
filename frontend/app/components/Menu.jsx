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

var menuTree = immutable.fromJS({
  menuItems: {
    exercises: {
      name: 'Exercises',
      key: 'exercises',
      reqGroup: [],
    },
    results: {
      name: 'Results',
      key: 'results',
      reqGroup: [],
    },
    activeExercise: {
      invisible: true,
      name: 'Exercise',
      key: 'activeExercise',
      reqGroup: [],
      menuItems: {
        xmlEditor: {
          name: 'XML Editor',
          key: 'xmlEditor',
          reqGroup: 'Author'
        },
        options: {
          name: 'Options',
          key: 'options',
          reqGroup: 'Admin'
        },
        statistics: {
          name: 'Statistics',
          key: 'statistics',
          reqGroup: 'View'
        }
      }
    }
  }
});

function traverse(menuPath) {
  var fullPath = immutable.List([])
  if(menuPath.size > 0) {
    fullPath = menuPath.pop().reduce(
    (acc, next) => acc.push(next).push('menuItems'), immutable.List([])
  ).push(menuPath.last()).insert(0, 'menuItems');
  }
  return menuTree.getIn(fullPath)
}

const BaseMenu = ({menuPath, menuClick, leafDefaults}) => {
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
  var breadcrumbs = nonLeafBreadcrumbs.map( item => (<li key={item.name}><a onClick={e => menuClick(item.path)}>{item.name}</a></li>) )
  var subMenu = subItems.filter( item => !item.get('invisible', false)).map( (item, key) => {
    var cssclass = "uk-button uk-button-primary" + (menuPath.last() === key ? " uk-active" : "");
    return ( <a key={item.get('name')} className={cssclass} onClick={e => menuClick((leaf ? menuPath.butLast() : menuPath).push(item.get('key')), leafDefaults.get(key))}>{item.get('name')}</a> )
  }).toArray();
  return (
    <span>
    <ul className="uk-breadcrumb uk-display-inline-block uk-vertical-align-middle">
      {menuPath.size > 0 && !(menuPath.size == 1 && leaf) && breadcrumbs}
    </ul>
      <div className="uk-button-group uk-margin-left">
      {subMenu}
      </div>
    </span>
  )
};

const mapStateToProps = state => {
  //console.dir(['menuLeafDefaults'].concat(state.get('menuPath').toArray()))
  return ({
  menuPath: state.get('menuPath'),
  leafDefaults: state.getIn(['menuLeafDefaults'].concat(state.get('menuPath').toArray()), immutable.Map({}))
});
}

const mapDispatchToProps = dispatch => ({
  menuClick: (path, defaultLeaf) => {
    console.dir(traverse(path).toJS())
    if(!traverse(path).has('menuItems'))
      dispatch(updateMenuLeafDefaults(path.butLast().toJS(), path.last()))
    if(defaultLeaf)
      dispatch(updateMenuPath(path.push(defaultLeaf)))
    else
      dispatch(updateMenuPath(path))
  }
});

function menuPositionUnder(menuPath, pathArray) {
  return menuPath.take(pathArray.length).equals(immutable.List(pathArray));
}
function menuPositionAt(menuPath, pathArray) {
  return menuPath.equals(immutable.List(pathArray));
}

export default connect(mapStateToProps, mapDispatchToProps)(BaseMenu)
export { menuPositionUnder, menuPositionAt }
