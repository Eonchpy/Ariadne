import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('should allow a user to login', async ({ page }) => {
    // Mock the login API call
    await page.route('**/api/v1/auth/login', async (route) => {
      const json = {
        access_token: 'fake-access-token',
        refresh_token: 'fake-refresh-token',
        token_type: 'Bearer',
        expires_in: 3600,
        user: {
          id: '123',
          email: 'test@example.com',
          name: 'Test User',
          roles: ['user'],
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
        },
      };
      await route.fulfill({ json });
    });

    // Go to login page
    await page.goto('/login');

    // Check if we are on the login page
    // Note: My AuthLayout title is just "Ariadne" and text "Enterprise Metadata Management".
    // The form doesn't have a visible title "Sign in to your account" in my implementation of LoginPage.tsx.
    // I should check for the "Ariadne" title instead.
    await expect(page.getByText('Enterprise Metadata Management')).toBeVisible();

    // Fill in credentials
    await page.getByPlaceholder('Email').fill('test@example.com');
    await page.getByPlaceholder('Password').fill('password');

    // Click sign in
    await page.getByRole('button', { name: 'Sign in' }).click();

    // Should redirect to dashboard (root)
    await expect(page).toHaveURL('/');
    
    // Check for dashboard placeholder text
    await expect(page.getByText('Dashboard Placeholder')).toBeVisible();
    
    // Check if user name is displayed in header
    await expect(page.getByText('Test User')).toBeVisible();
  });

  test('should show error on invalid credentials', async ({ page }) => {
    // Mock failure
    await page.route('**/api/v1/auth/login', async (route) => {
      await route.fulfill({
        status: 401,
        json: {
          error: {
            code: 'INVALID_CREDENTIALS',
            message: 'Invalid email or password.',
          },
        },
      });
    });

    await page.goto('/login');
    await page.getByPlaceholder('Email').fill('wrong@example.com');
    await page.getByPlaceholder('Password').fill('wrongpassword');
    await page.getByRole('button', { name: 'Sign in' }).click();

    // Should stay on login page
    await expect(page).toHaveURL('/login');
    
    // Antd message should appear
    // My client.ts intercepts 401 and shows 'Session expired or invalid credentials'
    await expect(page.getByText('Session expired or invalid credentials')).toBeVisible();
  });
});
