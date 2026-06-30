import { test, expect } from '@playwright/test';

test.describe('SAF-53: Flujo completo frontend SafeRoute Lima', () => {

  test('CP-E2E-01: La pagina carga correctamente con titulo y formulario', async ({ page }) => {
    await page.goto('http://localhost:5173');

    await expect(page.getByText('SafeRoute Lima')).toBeVisible();

    const inputs = page.getByPlaceholder('Buscar dirección o hacer click en el mapa');
    await expect(inputs).toHaveCount(2);

    await expect(page.getByRole('button', { name: 'Buscar Ruta Segura' })).toBeVisible();

    await expect(page.locator('.leaflet-container')).toBeVisible();
  });

  test('CP-E2E-02: Formulario sin puntos muestra alerta de validacion', async ({ page }) => {
    await page.goto('http://localhost:5173');

    await expect(page.getByText('SafeRoute Lima')).toBeVisible();

    page.once('dialog', async dialog => {
      await expect(dialog.message()).toBe('Por favor selecciona origen y destino');
      await dialog.accept();
    });

    await page.getByRole('button', { name: 'Buscar Ruta Segura' }).click();
  });

  test('CP-E2E-03: Campo de busqueda muestra sugerencias de Nominatim', async ({ page }) => {
    await page.goto('http://localhost:5173');

    await expect(page.getByText('SafeRoute Lima')).toBeVisible();

    const inputOrigen = page.getByPlaceholder('Buscar dirección o hacer click en el mapa').first();
    await inputOrigen.click();
    await inputOrigen.fill('Miraflores');

    await page.waitForSelector('.suggestions-list', { timeout: 5000 });

    const sugerencias = page.locator('.suggestions-list li');
    await expect(sugerencias.first()).toBeVisible();
  });

});
