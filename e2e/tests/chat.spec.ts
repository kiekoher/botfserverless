import { test, expect, Page } from '@playwright/test';

const TEST_USER_EMAIL = process.env.TEST_USER_EMAIL;
const TEST_USER_PASSWORD = process.env.TEST_USER_PASSWORD;

if (!TEST_USER_EMAIL || !TEST_USER_PASSWORD) {
  throw new Error('TEST_USER_EMAIL and TEST_USER_PASSWORD environment variables are required for E2E tests.');
}

// Helper function to log in, reused from the RAG test
async function login(page: Page) {
  await page.goto('/login');
  await page.fill('input[name="email"]', TEST_USER_EMAIL!);
  await page.fill('input[name="password"]', TEST_USER_PASSWORD!);
  await page.click('button[type="submit"]');
  await page.waitForURL('/dashboard', { timeout: 15000 });
}

test.describe('Basic Chat Flow E2E Test', () => {
  let page: Page;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
    await login(page);
  });

  test.afterAll(async () => {
    await page.close();
  });

  test('should send a message and receive a non-empty response', async () => {
    // 1. Navigate to the main dashboard page where the chat is located
    await page.goto('/dashboard');
    await page.waitForSelector('h1:has-text("Mis Agentes")');

    // 2. Find the chat input, type a message, and send it
    const chatInput = page.locator('textarea[placeholder*="Escribe tu mensaje aquí..."]');
    await chatInput.fill('Hola, ¿quién eres?');
    await page.keyboard.press('Enter');

    // 3. Wait for the bot's response to appear.
    // We expect two '.prose' elements: one for the user's message and one for the bot's response.
    const responseLocator = page.locator('.prose').nth(1); // nth(1) gets the second element

    await expect(responseLocator).toBeVisible({ timeout: 45000 }); // Generous timeout for the full pipeline

    // 4. Assert that the response has content
    const responseText = await responseLocator.innerText();
    expect(responseText.trim()).not.toBe('');

    console.log(`Basic Chat E2E Test Passed. Bot response: "${responseText}"`);
  });
});
