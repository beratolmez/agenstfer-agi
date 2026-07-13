# Web Console Tasarım Sistemi

Uygulama iki üretim konseptini kaynak kabul eder:

- `dashboard-concept.png` — ana dashboard, evidence ve approval yoğunluğu.
- `workflow-editor-concept.png` — node catalog, typed DAG canvas ve inspector.

## Görsel kararlar

- Background: true cool light gray `#f7f9fb`; work surface: white `#ffffff`.
- Ink/navy: `#10213f`; muted slate: `#617086`; border: `#d9e0e8`.
- Primary teal: `#007f88`; verified green: `#249748`; pending amber: `#c57900`.
- Radius 5–10 px; 1 px crisp border; yalnız drawer/node için çok hafif shadow.
- Sistem fontu: Segoe UI Variable → Segoe UI → Inter fallback. Dış font isteği yoktur.
- Page heading 31–43 px; section 16 px; UI chrome 10–14 px.

## Container modeli

Dashboard, kart grid'i değil; sidebar + topbar + açık ana çalışma yüzeyi, tek metric strip,
ranking table, sağ action rail ve altta evidence/activity band kullanır. Workflow; catalog rail,
canvas, inspector ve status bar kullanır. Her alan için yeni nested card eklenmez.

## Kilitli ilk ekran metni

`Growth Intelligence`, `Genel Bakış`, `Bilgi Bankası`, `Fırsatlar`, `İş Akışları`,
`Onay Merkezi`, `Veri Kaynakları`, `Ayarlar`, `Büyüme Özeti`,
`Tanıyı yeniden çalıştır`, `Öncelikli fırsatlar`, `30 günlük plan`.

## Etkileşim ve responsive

- Evidence yüzdesi source ID + locator drawer'ını açar.
- Workflow node seçimi inspector'ı; validate/dry-run toolbar'ı status bar'ı günceller.
- Desktop kaynak viewport 1536×1024.
- 820 px altında sidebar yatay icon rail'e dönüşür; metric strip tek kolondur.
- Geniş ranking table yalnız kendi container'ında yatay kayar; document taşmaz.
- `prefers-reduced-motion` desteklenir ve tüm kontroller focus-visible taşır.

## İkonlar

Lucide outline ikonları, 1.65–1.8 stroke; navigation 21 px, toolbar 15–18 px.
Brand mark tek code-native SVG ve `currentColor` kullanır. Raster konsept UI olarak ship edilmez.

