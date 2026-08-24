// Dashboard talep listesinin URL query-state'i (?q=&category=&answered=&
// channel=&sort=&lead=&page=) için tek bir href üretici — CategoryFilterBar,
// TicketFilterBar ve Pagination üçü de kullanıyor. Bir filtre değiştiğinde
// diğerleri korunmalı (arama yaparken kategori filtresi kalkmamalı, kanal
// değiştirince cevap durumu filtresi kaybolmamalı) — bu yüzden HER çağıran
// kendi değiştirmediği alanları da "mevcut aktif değer" olarak elden geçirip
// iletmeli. Sadece page her filtre değişiminde 1'e sıfırlanır (çağıran taraf
// `page` alanını bilinçli olarak set etmezse öyle kalır).
export function buildDashboardHref(params: {
  category?: string | null;
  q?: string | null;
  answered?: string | null;
  channel?: string | null;
  sort?: string | null;
  lead?: string | null;
  urgent?: string | null;
  page?: number;
}): string {
  const search = new URLSearchParams();
  if (params.category) search.set("category", params.category);
  if (params.q) search.set("q", params.q);
  if (params.answered) search.set("answered", params.answered);
  if (params.channel) search.set("channel", params.channel);
  if (params.sort) search.set("sort", params.sort);
  if (params.lead) search.set("lead", params.lead);
  if (params.urgent) search.set("urgent", params.urgent);
  if (params.page && params.page > 1) search.set("page", String(params.page));
  const qs = search.toString();
  return qs ? `/dashboard?${qs}` : "/dashboard";
}
