import { test, expect } from "@playwright/test";

test("homepage has title", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveTitle(/Expo/);
});

test("app loads successfully", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("text=Open up App.tsx to start working on your app!")).toBeVisible();
});
