import React, { Component } from 'react';
import PropTypes from 'prop-types';
import Plot from './Plot.jsx';
import { connect } from 'react-redux';
import { fetchCourseStatistics } from '../fetchers.js';

class HistogramAll extends Component {
  constructor() {
    super();
    this.state = { error: false };
  }

  static propTypes = {
    courseAggregates: PropTypes.object
  };

  componentDidMount(props) {
    this.props.onGenerateCourseResults(1);
  }
  //    try {
  //      this.exerciseKey= document.getElementsByTagName('div')[0].getAttribute('exercisekey')  || false
  //     } catch (error) {
  //      this.exerciseKey = false
  //   }

  render() {
    var ag = this.props.courseAggregates;
    if (!this.props.courseAggregates) {
      return <div />;
    }
    var lisall = ag.toJS();
    //console.log("SUMMARY = ", lisall.summary )
    var image_answers = lisall.summary['image_answers'];
    //console.log("IMAGE_ANSWSERS = ", image_answers )

    var lis_all = lisall.all;
    var xvars_all = lis_all.map((item) => Object.keys(item)[0]);
    var yvars_all = lis_all.map((item) => Object.values(item)[0]);

    var lis_required = lisall.required;
    var xvars_required = lis_required.map((item) => Object.keys(item)[0]);
    var yvars_required = lis_required.map((item) => Object.values(item)[0]);

    var lis_bonus = lisall.bonus;
    var xvars_bonus = lis_bonus.map((item) => Object.keys(item)[0]);
    var yvars_bonus = lis_bonus.map((item) => Object.values(item)[0]);

    var lis_aibased = lisall.aibased;
    var xvars_aibased = lis_aibased.map((item) => Object.keys(item)[0]);
    var yvars_aibased = lis_aibased.map((item) => Object.values(item)[0]);

    var lis_optional = lisall.optional;
    var xvars_optional = lis_optional.map((item) => Object.keys(item)[0]);
    var yvars_optional = lis_optional.map((item) => Object.values(item)[0]);

    var i = 0;
    var y_bonus = [];
    var bonustot = 0;
    while (i < xvars_all.length) {
      var j = xvars_bonus.indexOf(xvars_all[i]);
      if (j > 0) {
        y_bonus.push(yvars_bonus[j]);
        bonustot += yvars_bonus[j];
      } else {
        y_bonus.push(0);
      }
      i++;
    }


    var i = 0;
    var y_aibased = [];
    var aibasedtot = 0;
    while (i < xvars_all.length) {
      var j = xvars_aibased.indexOf(xvars_all[i]);
      if (j > 0) {
        y_aibased.push(yvars_aibased[j]);
        aibasedtot += yvars_aibased[j];
      } else {
        y_aibased.push(0);
      }
      i++;
    }





    var i = 0;
    var y_required = [];
    var requiredtot = 0;
    while (i < xvars_all.length) {
      var j = xvars_required.indexOf(xvars_all[i]);
      if (j > 0) {
        y_required.push(yvars_required[j]);
        requiredtot += yvars_required[j];
      } else {
        y_required.push(0);
      }
      i++;
    }

    var i = 0;
    var y_optional = [];
    var optionaltot = 0;
    while (i < xvars_all.length) {
      var j = xvars_optional.indexOf(xvars_all[i]);
      if (j > 0) {
        y_optional.push(yvars_optional[j]);
        optionaltot += yvars_optional[j];
      } else {
        y_optional.push(0);
      }
      i++;
    }
    //console.log("lens = ", y_bonus.length, y_optional.length, y_required.length)
    var totall = bonustot + requiredtot + optionaltot;

    var data_required = { x: xvars_all, y: y_required, type: 'bar', name: 'required: ' + requiredtot, color: 'blue' };
    var data_optional = { x: xvars_all, y: y_optional, type: 'bar', name: 'optional: ' + optionaltot, color: 'green' };
    var data_bonus = { x: xvars_all, y: y_bonus, type: 'bar', name: 'bonus: ' + bonustot, color: 'orange' };
    var data_aibased = { x: xvars_all, y: y_aibased, type: 'bar', name: 'aibased: ' + aibasedtot, color: 'red' };

    var image_answers = lisall.summary['image_answers'];
    var activityRange = lisall.summary['activityRange'];
    var audits = lisall.summary['audits'];

    var data = [data_required, data_bonus, data_optional, data_aibased];
    var layout = {
      barmode: 'stack',
      title:
        'latest ' +
        activityRange +
        ': ' +
        totall +
        ' total answers ' +
        image_answers +
        ' image answers ' +
        audits +
        ' audits'
    };
    var config = { staticPlot: false }
    return (
      <article className="uk-article">
        <Plot plotkey={'allPlot'} data={data} layout={layout} config={config} />
      </article>
    );
    return <div />;
  }
}

const mapDispatchToProps = (dispatch) => ({
  onGenerateCourseResults: (activeCourse) => {
    dispatch(fetchCourseStatistics(activeCourse));
  }
});

const mapStateToProps = (state) => {
  return {
    courseAggregates: state.getIn(['statistics', 'course_aggregates'])
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(HistogramAll);
