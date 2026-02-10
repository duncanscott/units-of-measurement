import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

function loadJsonl(filename) {
  return readFileSync(join(__dirname, 'json', filename), 'utf-8')
    .trim()
    .split('\n')
    .map(JSON.parse);
}

/**
 * Load a units of measurement dataset.
 * @param {string} [dataset='units_of_measurement'] - One of 'units_of_measurement', 'si_units', or 'uom'
 * @returns {Object[]} Array of unit objects
 */
export function load(dataset = 'units_of_measurement') {
  const valid = ['units_of_measurement', 'si_units', 'uom'];
  if (!valid.includes(dataset)) {
    throw new Error('Unknown dataset "' + dataset + '". Choose from: ' + valid.join(', '));
  }
  return loadJsonl(dataset + '.jsonl');
}
