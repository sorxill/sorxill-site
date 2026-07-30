/** Единственный путь к данным: web никогда не ходит в БД напрямую. */
const BASE = process.env.API_INTERNAL_URL ?? "http://api:8000";

export type Project = {
  slug: string;
  title: string;
  summary: string;
  cover_url: string | null;
  stack: string[];
};

export async function listProjects(locale: string): Promise<Project[]> {
  const res = await fetch(`${BASE}/api/v1/projects?locale=${locale}`, {
    next: { revalidate: 300, tags: ["projects"] },
  });
  if (!res.ok) {
    // Деградация вместо падения страницы: статика важнее динамики.
    console.error("api.projects.failed", res.status);
    return [];
  }
  const data = (await res.json()) as { items: Project[] };
  return data.items;
}
