'use strict';

const fs = require('fs');
const path = require('path');

function loadJsonl(filename) {
  const filePath = path.join(__dirname, 'json', filename);
  return fs.readFileSync(filePath, 'utf-8')
    .trim()
    .split('\n')
    .map(JSON.parse);
}

/**
 * Load a units of measurement dataset.
 * @param {string} [dataset='units_of_measurement'] - One of 'units_of_measurement', 'si_units', or 'uom'
 * @returns {Object[]} Array of unit objects
 */
function load(dataset) {
  if (dataset === undefined) dataset = 'units_of_measurement';
  const valid = ['units_of_measurement', 'si_units', 'uom'];
  if (!valid.includes(dataset)) {
    throw new Error('Unknown dataset "' + dataset + '". Choose from: ' + valid.join(', '));
  }
  return loadJsonl(dataset + '.jsonl');
}

module.exports = { load };
