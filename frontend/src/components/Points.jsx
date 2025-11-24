import React from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';

class Points extends React.Component {
  constructor(props) {
    super(props);
    this.handleChange = this.handleChange.bind(this);
    this.input = React.createRef();
    this.state = { points: '' };
  }

  handleChange(event) {
    this.setState({ points: event.target.value });
    console.log('onSubmit ', this.state.points);
    event.preventDefault();
  }

  render() {
    console.log('AUDIT_DATA = ', JSON.stringify(this.props.auditData));
    return (
      <div>
        MaxPoints:{' '}
        <input
          onChange={(event) => this.handleChange(event)}
          type="text"
          ref={this.input}
          placeholder={this.state.points}
        />
      </div>
    );
  }
}

const mapStateToProps = (state) => {
  var activeAudit = state.getIn(['audit', 'activeAudit'], false);
  //var changedAudit = state.getIn(['audit','activeAuditChanged'], false);
  var auditData = state.getIn(['audit', 'auditdata', activeAudit], immutable.Map({}));
  var activeExercise = state.get('activeExercise');
  return {
    auditData: auditData,
    exerciseState: state.getIn(['exerciseState', activeExercise])
  };
};

export default connect(mapStateToProps, null)(Points);
