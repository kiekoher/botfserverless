const { Client, LocalAuth } = require('whatsapp-web.js');
const pino = require('pino');
const logger = pino();

// This healthcheck script is designed to verify the actual connection status
// of the WhatsApp client. It uses the same session data as the main bot
// to provide an accurate health status.

const SESSION_PATH = process.env.WHATSAPP_SESSION_PATH || '/app/session';

// Set a timeout for the entire healthcheck process to prevent it from hanging.
const healthcheckTimeout = setTimeout(() => {
    logger.error('Healthcheck timed out after 10 seconds.');
    process.exit(1);
}, 10000); // 10 seconds timeout

let client;
try {
    client = new Client({
        authStrategy: new LocalAuth({ dataPath: SESSION_PATH }),
        puppeteer: {
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox'],
        }
    });
} catch (e) {
    logger.error('Failed to instantiate WhatsApp client:', e.message);
    clearTimeout(healthcheckTimeout);
    process.exit(1);
}

// The most reliable way to check health is to initialize the client and get its state.
// We add a listener for the 'ready' event and a timeout.
client.on('ready', () => {
    logger.info('Healthcheck: Client is ready.');
    clearTimeout(healthcheckTimeout);
    process.exit(0); // Success
});


// Handle disconnection events during initialization
client.on('disconnected', () => {
    logger.error('Healthcheck: Client is disconnected.');
    clearTimeout(healthcheckTimeout);
    process.exit(1); // Failure
});

// Initialize the client to check the connection status
client.initialize().catch(err => {
    logger.error('Healthcheck: Client initialization failed.', err.message);
    clearTimeout(healthcheckTimeout);
    process.exit(1); // Failure
});

// In some cases, if the client is already authenticated, it might not emit 'ready'.
// We can also check the state after a short delay.
setTimeout(async () => {
    try {
        const state = await client.getState();
        if (state === 'CONNECTED') {
            logger.info('Healthcheck: Client state is CONNECTED.');
            clearTimeout(healthcheckTimeout);
            process.exit(0);
        } else {
            logger.error(`Healthcheck: Client state is '${state}'.`);
            clearTimeout(healthcheckTimeout);
            process.exit(1);
        }
    } catch (e) {
        logger.error('Healthcheck: Failed to get client state.', e.message);
        clearTimeout(healthcheckTimeout);
        process.exit(1);
    }
}, 5000); // Check state after 5 seconds as a fallback
