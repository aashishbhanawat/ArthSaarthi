const React = require('react');

const createIcon = () => React.createElement('div');

// Use a Proxy to dynamically mock any icon import.
// This is more robust than maintaining a static list of exports.
module.exports = new Proxy({}, {
  get: function(target, prop) {
    return createIcon;
  },
});

