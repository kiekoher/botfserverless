import { strict as assert } from 'assert';
import { randomInt, getClarificationMessage } from '../src/utils/helpers.js';

describe('helpers.randomInt', () => {
  it('returns value within provided range', () => {
    for (let i = 0; i < 100; i++) {
      const val = randomInt(1, 3);
      assert.ok(val >= 1 && val <= 3, `value ${val} not within range`);
    }
  });
});

describe('helpers.getClarificationMessage', () => {
  it('returns a non-empty string from the predefined list', () => {
    const allowed = [
      'Disculpa, no estoy seguro de haber entendido. ¿Podrías explicarlo de otra forma?',
      'Perdona, creo que me he perdido. ¿Me lo repites por favor?',
      'Lo siento, ¿puedes aclarar un poco más tu pregunta?',
      'No comprendí bien, ¿podrías detallarlo nuevamente?',
      'Perdón, no entendí. ¿Podrías decirlo de otra manera?'
    ];
    for (let i = 0; i < 10; i++) {
      const msg = getClarificationMessage();
      assert.ok(typeof msg === 'string' && msg.length > 0, 'message should be non-empty string');
      assert.ok(allowed.includes(msg), `unexpected message: ${msg}`);
    }
  });
});
