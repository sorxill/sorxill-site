import { NextIntlClientProvider, hasLocale } from "next-intl";
import { notFound } from "next/navigation";
import { setRequestLocale } from "next-intl/server";
import { routing } from "@/i18n/routing";

/**
 * Без этого `/wp-config.php` матчится на `/[locale]` с locale="wp-config.php",
 * уходит в рантайм-рендер, next-intl читает заголовки — и Next отдаёт 500
 * ("Page changed from static to dynamic at runtime, reason: headers")
 * вместо 404. Пути с точкой не проходят matcher в proxy.ts, поэтому
 * middleware их не перехватывает. Список из generateStaticParams
 * становится исчерпывающим: всё остальное — сразу 404.
 */
export const dynamicParams = false;

/** Обе локали пререндерятся на билде — это часть стратегии SSG из HLD §6. */
export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!hasLocale(routing.locales, locale)) notFound();

  // Без этого страница уедет в динамический рендеринг и SSG не сработает.
  setRequestLocale(locale);

  return <NextIntlClientProvider>{children}</NextIntlClientProvider>;
}
