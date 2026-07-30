import { getTranslations } from "next-intl/server";
import { listProjects } from "@/shared/lib/api";

export const revalidate = 300;

export default async function HomePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const t = await getTranslations("hero");
  const projects = await listProjects(locale);

  return (
    <main style={{ maxWidth: "75rem", margin: "0 auto", padding: "4rem 2rem" }}>
      <p style={{ fontFamily: "var(--font-mono)", color: "var(--color-accent)" }}>
        {t("eyebrow")}
      </p>
      <h1 style={{ fontSize: "clamp(2.4rem,5vw,4.25rem)", fontWeight: 500, lineHeight: 1.1 }}>
        {t("title")}
      </h1>
      <ul>
        {projects.map((p) => (
          <li key={p.slug}>
            {p.title} — {p.summary}
          </li>
        ))}
      </ul>
      {projects.length === 0 && (
        <p style={{ color: "var(--color-muted)" }}>
          API недоступен — страница продолжает работать (graceful degradation).
        </p>
      )}
    </main>
  );
}
