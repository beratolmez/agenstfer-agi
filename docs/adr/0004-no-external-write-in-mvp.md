# ADR-0004: MVP'de harici write aksiyonu yok

- Durum: Accepted
- Tarih: 2026-07-13

## Bağlam

Gerçek CRM/ERP ve şirket süreçleri henüz bilinmiyor. Yanlış otomatik aksiyon müşteri verisini veya iş ilişkisini bozabilir.

## Karar

MVP connector interface'i yalnız `test_connection`, `discover_schema`, `preview`, `sync(cursor)` ve `health` içerir. CRM/ERP update, email/call/send/delete capability'si derlenmiş üründe bulunmaz. OKF active bundle merge'i bile insan approval ister.

## Sonuçlar

İlk pilot düşük riskle read-only yürür. UI'daki onay kontrolü atlatılsa bile adapter write yapamaz. Gelecekte write için yeni ADR, capability, consent/privacy incelemesi, idempotency, kill switch ve ayrıntılı audit gerekir.

## Alternatifler

Gizli feature flag veya yalnız UI disable güvenli sınır değildir; capability'nin varlığı saldırı ve yanlış yapılandırma yüzeyini korur.

