// Dashboard talep listesinin URL query-state'i (?q=&category=&page=) için tek
// bir href üretici — CategoryFilterBar ve Pagination ikisi de kullanıyor.
// Bir filtre değiştiğinde diğerleri korunmalı (arama yaparken kategori
// filtresi kalkmamalı, kategori değiştirince arama terimi kaybolmamalı),
// sadece page her filtre değişiminde 1'e sıfırlanır (çağıran taraf `page`
// alanını bilinçli olarak set etmezse öyle kalır).
export function buildDashboardHref(params: { category?: string | null; q?: string | null; page?: number }): string {
  const search = new URLSearchParams();
  if (params.category) search.set("category", params.category);
  if (params.q) search.set("q", params.q);
  if (params.page && params.page > 1) search.set("page", String(params.page));
  const qs = search.toString();
  return qs ? `/dashboard?${qs}` : "/dashboard";
}
