import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('ExcursionLens Canonical Journey & Accessibility', () => {
  test('complete canonical investigation flow and accessibility scan', async ({ page }, testInfo) => {
    // 1. Navigate to application root
    await page.goto('/');

    // 2. Verify branding and initial case overview
    await expect(page.locator('header')).toContainText('ExcursionLens');
    await expect(page.locator('header')).toContainText('Synthetic Benchmark');
    await expect(page.locator('main')).toContainText('NMB-204');
    await expect(page.locator('main')).toContainText('2.0°C to 8.0°C');
    await expect(page.locator('main')).toContainText('42 min Out-of-Range Window');

    // 3. Accessibility Scan in Ready State
    const readyAxeResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .disableRules(['color-contrast']) // Color contrast evaluated in design review
      .analyze();
    expect(readyAxeResults.violations).toEqual([]);

    // 4. Test accessible table toggle
    const tableBtn = page.getByRole('button', { name: /Show Accessible Table/i });
    await tableBtn.click({ force: true });
    await expect(page.locator('#telemetry-table')).toBeAttached();
    await expect(page.locator('#telemetry-table tr')).toHaveCount(52); // Header + 51 readings

    // 5. Trigger Excursion Investigation
    const investigateBtn = page.getByRole('button', { name: /Investigate Excursion/i }).first();
    await investigateBtn.click();

    // 6. Wait for investigation completion
    await expect(page.locator('main')).toContainText('Investigation complete', { timeout: 15000 });
    await expect(page.locator('text=QUARANTINE PENDING QUALIFIED REVIEW').first()).toBeVisible();

    // 7. Verify Competing Hypotheses rendered
    await expect(page.locator('text=Transfer Staging Ambient Heat Penetration').first()).toBeVisible();
    await expect(page.locator('text=Reefer Auxiliary Power Circuit Interruption').first()).toBeVisible();
    await expect(page.locator('text=Surface Logger Displacement').first()).toBeVisible();

    // 8. Verify Skeptic Critique rendered
    await expect(page.locator('text=Adversarial Skeptic Pass').first()).toBeVisible();
    await expect(page.locator('text=Reefer power loss hypothesis is directly contradicted').first()).toBeVisible();

    // 9. Verify Provider Proof Panel rendered
    await expect(page.locator('text=Sponsor Integration Proof Panel').first()).toBeVisible();
    await expect(page.locator('text=Nebius Token Factory').first()).toBeVisible();
    await expect(page.locator('text=Tavily Authoritative Search API').first()).toBeVisible();

    // 10. Click evidence badge to open Evidence Drawer
    const obsBadge = page.locator('button:has-text("OBS-EXCURSION-01")').first();
    if (await obsBadge.isVisible()) {
      await obsBadge.click({ force: true });
      await expect(page.locator('text=Evidence Item').first()).toBeVisible();
      await page.getByRole('button', { name: /Close/i }).first().click({ force: true });
    }

    // 11. Run Counterfactual Simulation
    const replayBtn = page.getByRole('button', { name: /Replay Counterfactual/i });
    await replayBtn.click({ force: true });
    await expect(page.locator('text=Simulation Completed').first()).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=Simulated Excursion: 0.0m').first()).toBeVisible();

    // 12. Open Review Packet Modal
    const reviewBtn = page.getByRole('button', { name: /Review Packet/i }).first();
    await reviewBtn.click({ force: true });
    await expect(page.locator('text=ExcursionLens Quality Review Packet').first()).toBeVisible();
    await expect(page.locator('text=Mandatory Quality Boundary').first()).toBeVisible();

    // 13. Accessibility Scan in Completed / Modal State
    const modalAxeResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .disableRules(['color-contrast'])
      .analyze();
    expect(modalAxeResults.violations).toEqual([]);

    // Close modal
    await page.keyboard.press('Escape');
  });
});
