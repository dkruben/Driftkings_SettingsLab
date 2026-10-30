'use strict';
// Discover every frontend suite; a newly added test must not need a manual require.
var fs = require('fs'), path = require('path');
var groups = ['settings', 'battle', 'lobby'], total = 0;
groups.forEach(function (group) {
    var folder = path.join(__dirname, 'frontend', group);
    var files = fs.readdirSync(folder).filter(function (name) { return /^test_.*\.js$/.test(name); }).sort();
    if (!files.length) { throw new Error('No frontend tests in ' + group); }
    files.forEach(function (name) { require(path.join(folder, name)); total++; });
});
console.log('Frontend suites executed: ' + total);
