import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Ярослав Бритов — Python Backend Engineer",
  description:
    "Асинхронные HTTP API и микросервисы на FastAPI и asyncio. Шлюз на 500+ RPS, уведомления на 100k+ сообщений в сутки.",
};

/** Тема ставится до первой отрисовки: иначе вспышка светлой темы. */
const themeScript = `
(function(){try{
  var m=document.cookie.match(/theme=(light|dark)/);
  var t=m?m[1]:(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');
  document.documentElement.dataset.theme=t;
}catch(e){}})();`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body>{children}</body>
    </html>
  );
}
