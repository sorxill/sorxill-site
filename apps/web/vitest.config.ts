import { defineConfig } from "vitest/config";

// Плагин @vitejs/plugin-react появится в M2 вместе с первыми тестами
// на компоненты. Пока тесты только на модулях без JSX, и лишняя
// зависимость с жёстким peer на vite не нужна.
export default defineConfig({
  test: {
    environment: "jsdom",
    globals: true,
    include: ["src/**/*.test.{ts,tsx}"],
  },
});
