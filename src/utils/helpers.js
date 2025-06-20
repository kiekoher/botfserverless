// =================================================================
// ==                  MÓDULO DE AYUDANTES (HELPERS)              ==
// =================================================================
// Contiene funciones de utilidad reutilizables en todo el proyecto,
// como pausas y generación de números aleatorios.
// =================================================================

/**
 * Genera un número entero aleatorio dentro de un rango específico.
 * @param {number} min - El valor mínimo (inclusive).
 * @param {number} max - El valor máximo (inclusive).
 * @returns {number} Un número entero aleatorio.
 */
export const randomInt = (min, max) => {
    return Math.floor(Math.random() * (max - min + 1)) + min;
};

/**
 * Realiza una pausa (duerme) durante una cantidad específica de milisegundos.
 * Devuelve una promesa que se resuelve después del tiempo de espera.
 * @param {number} ms - El número de milisegundos para la pausa.
 * @returns {Promise<void>}
 */
export const sleep = (ms) => {
    return new Promise(resolve => setTimeout(resolve, ms));
};
