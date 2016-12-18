import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import {
} from '../fetchers.js';
import {
  setTableSortField,
  setTableSortReverse
} from '../actions.js';
import Spinner from './Spinner.jsx';
import Badge from './Badge.jsx';
import Plot from './Plot.jsx';

import immutable from 'immutable';
import moment from 'moment';
import {SUBPATH} from '../settings.js';

const BaseTable = ({ data, fields, keyIndex, onSort, sortField, sortReverse, onItem }) => {
  var sorted = data;
  if(sortField && !sortReverse)
    sorted = data.sortBy( item => item.get(sortField) )
  if(sortField && sortReverse)
    sorted = data.sortBy( item => item.get(sortField) ).reverse()

  const renderFields = (item, fields) => fields.map( field => 
                                                    (
                                                      <td key={field.index} className={field.index === sortField ? 'uk-text-bold uk-text-primary' : ''}>
                                                        {item.get(field.index)}
                                                      </td>
                                                    )
                                                   );
  var rows = sorted.map( item => (
    <tr key={item.get(keyIndex)} onClick={() => onItem(item.get(keyIndex))}>
      {renderFields(item, fields)}
    </tr>
  ));
  return (
    <table className="uk-table uk-table-hover uk-table-condensed">
      <thead>
        <tr>
          { fields.map( field => (<th key={field.name}><a onClick={() => onSort(field.index, sortField, sortReverse)}>{field.name}</a></th>)) }
        </tr>
      </thead>
      <tbody>
        { rows }
      </tbody>
    </table>
  );
}

const mapStateToProps = (state, ownProps) => ({
  //data: state.getIn(ownProps.dataPath, []),
  sortField: state.getIn(['tables', ownProps.tableId, 'sortField'], null),
  sortReverse: state.getIn(['tables', ownProps.tableId, 'sortReverse'], false)
});

const mapDispatchToProps = (dispatch, ownProps) => ({
  onSort: (field, current, reverse) =>  {
    dispatch(setTableSortField(ownProps.tableId, field))
    if(field === current)
      dispatch(setTableSortReverse(ownProps.tableId, !reverse))
  }
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseTable)
