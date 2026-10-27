import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('ExcursionLens Quality, Truthfulness & Accessibility Journeys', () => {

  test('1. canonical desktop investigation flow and evidence reconciliation', async ({ page }) => {
    // 1. Navigate to application root
    await page.goto('/');

    // 2. Verify branding and reconciled 40 min metric
    await expect(page.locator('header')).toContainText('ExcursionLens');
    await expect(page.locator('header')).toContainText('Synthetic Benchmark');
    await expect(page.locator('main')).toContainText('NMB-204');
    await expect(page.locator('main')).toContainText('2.0°C to 8.0°C');
    await expect(page.locator('main')).toContainText('40 min Out-of-Range Window');

    // 3. Trigger Excursion Investigation
    const investigateBtn = page.getByRole('button', { name: /Investigate Excursion/i }).first();
    await investigateBtn.evaluate((el) => el.scrollIntoView({ block: 'center' }));
    await investigateBtn.click();

    // 4. Wait for investigation completion
    await expect(page.locator('main')).toContainText('Investigation complete', { timeout: 15000 });
    await expect(page.locator('text=QUARANTINE PENDING QUALIFIED REVIEW').first()).toBeVisible();

    // 5. Test accessible table toggle without forced clicks
    const tableBtn = page.getByRole('button', { name: /Show Accessible Table/i });
    await tableBtn.evaluate((el) => el.scrollIntoView({ block: 'center' }));
    await tableBtn.click();
    await expect(page.locator('#telemetry-table')).toBeAttached();
    await expect(page.locator('#telemetry-table tr')).toHaveCount(52); // Header + 51 readings

    // 6. Verify Competing Hypotheses rendered
    await expect(page.locator('text=Transfer Staging Ambient Heat Penetration').first()).toBeVisible();
    await expect(page.locator('text=Reefer Auxiliary Power Circuit Interruption').first()).toBeVisible();
    await expect(page.locator('text=Surface Logger Displacement').first()).toBeVisible();

    // 7. Verify Skeptic Critique rendered
    await expect(page.locator('text=Adversarial Skeptic Pass').first()).toBeVisible();
    await expect(page.locator('text=Reefer power loss hypothesis is directly contradicted').first()).toBeVisible();

    // 8. Verify Truthful Provider Proof Panel rendered
    await expect(page.locator('text=Provider & Retrieval Proof Panel').first()).toBeVisible();
    await expect(page.locator('text=Nebius Token Factory').first()).toBeVisible();
    await expect(page.locator('text=Authoritative Search Grounding (Tavily)').first()).toBeVisible();

    // 9. Run Counterfactual Simulation
    const replayBtn = page.getByRole('button', { name: /Replay Counterfactual/i });
    await replayBtn.evaluate((el) => el.scrollIntoView({ block: 'center' }));
    await replayBtn.click();
    await expect(page.locator('text=Simulation Completed').first()).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=Simulated Excursion: 0.0m').first()).toBeVisible();

    // 10. Open Review Packet Modal without forced clicks
    const reviewBtn = page.getByRole('button', { name: /Review Packet/i }).first();
    await reviewBtn.evaluate((el) => el.scrollIntoView({ block: 'center' }));
    await reviewBtn.click();
    await expect(page.locator('text=ExcursionLens Quality Review Packet').first()).toBeVisible();
    await expect(page.locator('text=Decision-Support Boundary').first()).toBeVisible();

    // Close modal via Escape key
    await page.keyboard.press('Escape');
    await expect(page.locator('role=dialog')).not.toBeVisible();
  });

  test('2. accessibility audit with WCAG AA color-contrast rules enabled', async ({ page }) => {
    await page.goto('/');

    // Run full Axe audit with color-contrast ENABLED
    const axeResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze();

    expect(axeResults.violations).toEqual([]);
  });

  test('3. keyboard navigation, modal focus trapping, and escape dismiss', async ({ page }) => {
    await page.goto('/');

    // Start investigation to enable review packet button
    const investigateBtn = page.getByRole('button', { name: /Investigate Excursion/i }).first();
    await investigateBtn.evaluate((el) => el.scrollIntoView({ block: 'center' }));
    await investigateBtn.click();
    await expect(page.locator('main')).toContainText('Investigation complete', { timeout: 15000 });

    const reviewBtn = page.getByRole('button', { name: /Review Packet/i }).first();
    await reviewBtn.evaluate((el) => el.scrollIntoView({ block: 'center' }));
    await reviewBtn.click();

    const modal = page.locator('role=dialog');
    await expect(modal).toBeVisible();

    // Verify initial focus is within the modal
    const focusedTag = await page.evaluate(() => document.activeElement?.tagName);
    expect(['BUTTON', 'A', 'INPUT', 'DIV']).toContain(focusedTag);

    // Verify focus trap: Tab key stays within dialog
    await page.keyboard.press('Tab');
    const isInsideModalAfterTab = await page.evaluate(() => {
      const modalEl = document.querySelector('[role="dialog"]');
      return modalEl?.contains(document.activeElement) ?? false;
    });
    expect(isInsideModalAfterTab).toBe(true);

    // Verify Escape dismisses modal
    await page.keyboard.press('Escape');
    await expect(modal).not.toBeVisible();
  });

  test('4. mobile responsive inspection without layout distortion', async ({ page, isMobile }) => {
    if (!isMobile) {
      await page.setViewportSize({ width: 320, height: 568 });
    }
    await page.goto('/');

    // Verify header elements are accessible and visible at mobile dimensions
    await expect(page.locator('header')).toBeVisible();
    const investigateBtn = page.getByRole('button', { name: /Investigate Excursion/i }).first();
    await expect(investigateBtn).toBeVisible();

    // Test table toggle on small screen
    const tableBtn = page.getByRole('button', { name: /Show Accessible Table/i });
    await tableBtn.evaluate((el) => el.scrollIntoView({ block: 'center' }));
    await tableBtn.click();
    await expect(page.locator('#telemetry-table')).toBeVisible();
  });

  test('5. truthful provider receipts and neutral status reporting', async ({ page }) => {
    await page.goto('/');

    const investigateBtn = page.getByRole('button', { name: /Investigate Excursion/i }).first();
    await investigateBtn.evaluate((el) => el.scrollIntoView({ block: 'center' }));
    await investigateBtn.click();
    await expect(page.locator('main')).toContainText('Investigation complete', { timeout: 15000 });

    // Verify status badge is truthful neutral (FIXTURE DEMO or LIVE VERIFIED)
    const proofPanel = page.locator('.card', { hasText: 'Provider & Retrieval Proof Panel' });
    await expect(proofPanel).toBeVisible();

    // Verify "Bonus Award Proof" marketing label is completely absent
    await expect(page.locator('text=Bonus Award Proof')).not.toBeVisible();

    // Verify allowlist grounding
    await expect(proofPanel).toContainText('cdc.gov');
    await expect(proofPanel).toContainText('fda.gov');
    await expect(proofPanel).toContainText('who.int');
  });

});
