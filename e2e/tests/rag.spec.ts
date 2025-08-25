import { test, expect, Page } from '@playwright/test';
import path from 'path';

const TEST_USER_EMAIL = process.env.TEST_USER_EMAIL;
const TEST_USER_PASSWORD = process.env.TEST_USER_PASSWORD;
const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:3000';

if (!TEST_USER_EMAIL || !TEST_USER_PASSWORD) {
  throw new Error('TEST_USER_EMAIL and TEST_USER_PASSWORD environment variables are required.');
}

// Helper function to log in
async function login(page: Page) {
  await page.goto('/login');
  await page.fill('input[name="email"]', TEST_USER_EMAIL!);
  await page.fill('input[name="password"]', TEST_USER_PASSWORD!);
  await page.click('button[type="submit"]');
  // Wait for navigation to the dashboard, indicating successful login
  await page.waitForURL('/dashboard', { timeout: 15000 });
}

test.describe('RAG Pipeline E2E Test', () => {
  let page: Page;

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
    await login(page);
  });

  test.afterAll(async () => {
    await page.close();
  });

  test('should upload a document, process it, and answer a question using its content', async () => {
    // 1. Navigate to the Knowledge Base page
    await page.goto('/dashboard/knowledge');
    await page.waitForSelector('h1:has-text("Knowledge Base")');

    // 2. Upload the document
    const filePath = path.join(__dirname, 'fixtures', 'test-doc.txt');
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.getByText(/Drag 'n' drop a file here/i).click();
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles(filePath);

    // 3. Wait for the document to appear in the list and be processed
    await expect(page.getByText('test-doc.txt')).toBeVisible({ timeout: 10000 });
    // Wait for status to be "Processing"
    await expect(page.locator('tr:has-text("test-doc.txt")').getByText('Processing')).toBeVisible({ timeout: 10000 });
    // Wait for status to become "Completed"
    await expect(page.locator('tr:has-text("test-doc.txt")').getByText('Completed')).toBeVisible({ timeout: 120000 }); // 2 minutes timeout for processing

    // 4. Navigate to the main chat page
    await page.goto('/dashboard');
    await page.waitForSelector('h1:has-text("Dashboard")');

    // 5. Ask a question related to the document
    const chatInput = page.locator('textarea[placeholder*="Ask your agent..."]');
    await chatInput.fill('What is the secret code for the blue pineapple?');
    await page.keyboard.press('Enter');

    // 6. Assert the response from the bot
    const responseLocator = page.locator('.prose').last();
    await expect(responseLocator).toBeVisible({ timeout: 30000 });
    const responseText = await responseLocator.innerText();

    // The response should contain the specific information from the document
    expect(responseText).toContain('Omega-7');

    console.log('RAG E2E Test Passed. Bot response:', responseText);
  });
});
