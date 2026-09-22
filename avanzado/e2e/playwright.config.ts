import { defineConfig } from '@playwright/test';

// Config del nivel avanzado. La app FastAPI se levanta aparte con
// `uvicorn app.main:app --port 8010 --reload` parado en `avanzado/` y sirve en el 8010 (el 8000 lo tiene tomado Docker).
//
// `headless: false` es a proposito: en la capacitacion el punto de Playwright
// es que se vea el navegador abriendose. Para CI va en true.
export default defineConfig({
  testDir: './tests',
  use: {
    baseURL: 'http://localhost:8010',
    headless: false,
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  reporter: [['list'], ['html', { open: 'never' }]],
});
