import { describe, expect, it, vi, afterEach } from "vitest";
import { listProjects } from "./api";

afterEach(() => vi.restoreAllMocks());

describe("listProjects", () => {
  it("возвращает проекты при успешном ответе", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ items: [{ slug: "a", title: "A", summary: "s", cover_url: null, stack: [] }] }),
    }));
    await expect(listProjects("ru")).resolves.toHaveLength(1);
  });

  it("деградирует до пустого списка, когда API недоступен", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("ENOTFOUND")));
    vi.spyOn(console, "error").mockImplementation(() => {});
    await expect(listProjects("ru")).resolves.toEqual([]);
  });

  it("деградирует при 500 от API", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 500 }));
    vi.spyOn(console, "error").mockImplementation(() => {});
    await expect(listProjects("ru")).resolves.toEqual([]);
  });
});
