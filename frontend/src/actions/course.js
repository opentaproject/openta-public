// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

function updateCourse(data) {
  return {
    type: 'UPDATE_COURSE',
    data: data
  };
}

function setActiveCourse(course) {
  return {
    type: 'SET_ACTIVE_COURSE',
    data: course
  };
}

function updateCourses(data) {
  return {
    type: 'UPDATE_COURSES',
    data: data
  };
}

export { updateCourse, updateCourses, setActiveCourse };
