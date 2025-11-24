//import React, { Component } from 'react';
//import PropTypes from 'prop-types';
//import { connect } from 'react-redux';
//
//
//
//
//import ReactDOM from "react-dom";
//import { ContextMenu, MenuItem, ContextMenuTrigger } from "react-contextmenu";
//
//class SimpleMenu extends Component  {
//
//
//handleClick = (e, data)  => {
//  console.log(data);
//  }
//  render() {
//  console.log("this.props.folderName = ", this.props.folderPath)
//  return (
//    <div>
//      {/* NOTICE: id must be unique between EVERY <ContextMenuTrigger> and <ContextMenu> pair */}
//      {/* NOTICE: inside the pair, <ContextMenuTrigger> and <ContextMenu> must have the same id */}
//
//      <ContextMenuTrigger id={this.props.folderName}>
//        <div className="well">Right click to see the menu</div>
//      </ContextMenuTrigger>
//
//      <ContextMenu id={this.props.folderName}>
//        <MenuItem data={{lift: this.props.folderPath}} onClick={this.handleClick}>
//          Move {this.props.folderName}
//        </MenuItem>
//        <MenuItem data={{drop: this.props.folderPath}} onClick={this.handleClick}>
//          Drop {this.props.folderName}
//        </MenuItem>
//        <MenuItem divider />
//        <MenuItem data={{foo: 'bar3'}} onClick={this.handleClick}>
//          ContextMenu Item 3
//        </MenuItem>
//      </ContextMenu>
//
//    </div>
//  );
// }
//}
//
//const mapStateToProps = (state) => {
//  const defaultLanguage = state.getIn(['course', 'languages', 0], 'en')
//    return {
//      language: state.get('lang', defaultLanguage)
//    };
// }
//
// export {SimpleMenu};
