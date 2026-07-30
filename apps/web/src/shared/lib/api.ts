/** Единственный путь к данным: web никогда не ходит в БД напрямую. */
const BASE = process.env.API_INTERNAL_URL ?? "http://api:8000";

export type Project = {
  slug: string;
  title: string;
  summary: string;
  cover_url: string | null;
  stack: string[];
};

/**
 * Деградация вместо падения. Три сценария, где API недоступен:
 *   1. сборка в CI — там бэкенда нет вообще;
 *   2. rolling deploy — api перезапускается на несколько секунд;
 *   3. авария на проде.
 * Во всех трёх статика обязана продолжать отдаваться (HLD §3).
 * fetch бросает исключение при DNS/сетевой ошибке, поэтому одной
 * проверки res.ok недостаточно — нужен try/catch.
 */
export async function listProjects(locale: string): Promise<Project[]> {
  try {
    const res = await fetch(`${BASE}/api/v1/projects?locale=${locale}`, {
      next: { revalidate: 300, tags: ["projects"] },
      signal: AbortSignal.timeout(5000),
    });
    if (!res.ok) {
      console.error("api.projects.bad_status", res.status);
      return [];
    }
    const data = (await res.json()) as { items: Project[] };
    return data.items;
  } catch (error) {
    console.error("api.projects.unreachable", error);
    return [];
  }
}
