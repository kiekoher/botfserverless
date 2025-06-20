import { randomInt, sleep } from './helpers.js';

const simulateReading = async (chat) => {
    try {
        await chat.sendSeen();
        await sleep(randomInt(500, 1500));
    } catch (e) { 
        console.error("Error en sendSeen:", e.message); 
    }
};

const simulateTyping = async (chat, responseText) => {
    const typingDuration = Math.max(1000, (responseText.length / randomInt(15, 25)) * 1000);
    try {
        await chat.sendStateTyping();
        await sleep(typingDuration);
        await chat.clearState();
    } catch (e) { 
        console.error("Error en sendStateTyping:", e.message); 
    }
};

export const sendHumanResponse = async (chat, responseText) => {
    await simulateReading(chat);
    await simulateTyping(chat, responseText);
    await sleep(randomInt(200, 500));
    return await chat.sendMessage(responseText);
};
