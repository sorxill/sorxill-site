// Без этого файла Tailwind v4 не запускается вообще: Next не знает, что CSS
// надо прогнать через PostCSS. Директивы @import "tailwindcss" и @theme
// доезжают до браузера сырыми, браузер их отбрасывает — и в собранном CSS
// не остаётся ни утилит, ни preflight, ни определений токенов в :root.
// Симптом обманчивый: тёмная тема при этом работает, потому что
// [data-theme="dark"] — обычное CSS-правило, а @theme — нет.
const config = {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};

export default config;
