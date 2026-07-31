// Next 16 переименовал middleware.ts в proxy.ts. Важно: при наличии
// каталога src/ файл обязан лежать ИМЕННО здесь, а не в корне приложения —
// иначе он молча игнорируется и "/" отдаёт 404 вместо редиректа на /ru.
import createMiddleware from "next-intl/middleware";
import { routing } from "./i18n/routing";

export default createMiddleware(routing);

export const config = {
  matcher: ["/((?!api|_next|_vercel|.*\\..*).*)"],
};
