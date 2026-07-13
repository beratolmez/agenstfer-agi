export const locale = "tr-TR" as const;

export const messages = {
  actions: {
    approve: "Onayla",
    reject: "Reddet",
    retry: "Yeniden dene",
    refresh: "Yenile",
    save: "Kaydet",
  },
  states: {
    empty: "Henüz kayıt yok.",
    loading: "Yükleniyor…",
    degradedModel: "Model hazır değil; başka provider'a otomatik geçilmez.",
  },
} as const;

export type MessageCatalog = typeof messages;
