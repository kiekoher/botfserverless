// =================================================================
// ==              MÓDULO DE CLIENTE REDIS                        ==
// =================================================================
// Gestiona la conexión a la base de datos de memoria Redis.
// =================================================================

import { createClient } from 'redis';
import 'dotenv/config';

const redisUrl = process.env.REDIS_URL || 'redis://redis:6379';
const redisClient = createClient({
    url: redisUrl
});

redisClient.on('error', (err) => console.error('Error en el Cliente de Redis', err));

try {
    await redisClient.connect();
    console.log('✅ Conectado exitosamente a la base de datos de memoria (Redis).');
} catch (err) {
    console.error('No se pudo conectar a Redis:', err);
    process.exit(1);
}

export default redisClient;
