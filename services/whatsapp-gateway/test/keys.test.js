const test = require('node:test');
const assert = require('node:assert');
const { qrKey, statusKey } = require('../keys');

test('generates namespaced keys', () => {
  assert.strictEqual(qrKey('user1'), 'whatsapp:user1:qr_code');
  assert.strictEqual(statusKey('user1'), 'whatsapp:user1:status');
});
