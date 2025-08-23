const { createClient } = require('redis');
const host = process.env.REDIS_HOST || 'redis';
const client = createClient({ url: `redis://${host}:6379` });
const timeout = setTimeout(() => {
  console.error('Redis healthcheck timeout');
  process.exit(1);
}, 5000);
client.on('error', () => {
  clearTimeout(timeout);
  process.exit(1);
});
client.connect()
  .then(() => client.ping())
  .then(() => {
    clearTimeout(timeout);
    return client.quit();
  })
  .then(() => process.exit(0))
  .catch(() => {
    clearTimeout(timeout);
    process.exit(1);
  });
