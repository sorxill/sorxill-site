// Next.js 16 переименовал middleware.ts в proxy.ts, чтобы сетевая граница
// приложения была явной. Со старым именем локали молча перестают работать.
import createMiddleware from "next-intl/middleware";
import { routing } from "./src/i18n/routing";

export default createMiddleware(routing);

export const config = {
  matcher: ["/((?!api|_next|_vercel|.*\\..*).*)"],
};
