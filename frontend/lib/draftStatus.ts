import type { TranslationKey } from "@/lib/i18n";

// Taslak durumu → çeviri anahtarı ve renk eşlemeleri. DraftPanel (taslak
// kartındaki rozet) ve DraftOutcomeChart (analitik sayfasındaki dağılım
// grafiği) aynı dört durumu aynı renklerle göstermeli — tanım burada tek yer.
export const DRAFT_STATUS_LABEL_KEYS: Record<string, TranslationKey> = {
  pending: "draftPanel.statusPending",
  approved: "draftPanel.statusApproved",
  edited: "draftPanel.statusEdited",
  rejected: "draftPanel.statusRejected",
};

// Rozet (pill) için: yumuşak arka plan + okunur metin çifti.
export const DRAFT_STATUS_PILL_CLASSES: Record<string, string> = {
  pending: "bg-status-open-bg text-status-open-fg",
  approved: "bg-status-done-bg text-status-done-fg",
  edited: "bg-status-wait-bg text-status-wait-fg",
  rejected: "bg-surface-2 text-muted",
};

// Dağılım çubuğu dilimi için: tek renkli, dolgun yüzey (bkz.
// lib/categories.ts categorySwatchClass deseni).
export const DRAFT_STATUS_SWATCH_CLASSES: Record<string, string> = {
  pending: "bg-status-open-fg",
  approved: "bg-status-done-fg",
  edited: "bg-status-wait-fg",
  rejected: "bg-border-strong",
};
