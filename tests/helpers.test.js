import { strict as assert } from 'assert';
import { randomInt } from '../src/utils/helpers.js';

describe('helpers.randomInt', () => {
  it('returns value within provided range', () => {
    for (let i = 0; i < 100; i++) {
      const val = randomInt(1, 3);
      assert.ok(val >= 1 && val <= 3, `value ${val} not within range`);
    }
  });
});
