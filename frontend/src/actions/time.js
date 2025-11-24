function setTimezone(timezone) {
  return {
    type: 'SET_TIMEZONE',
    data: timezone
  };
}

export { setTimezone };
