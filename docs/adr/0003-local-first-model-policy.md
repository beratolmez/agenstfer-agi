# ADR-0003: Local-first model politikası

- Durum: Accepted
- Tarih: 2026-07-13

## Bağlam

Şirket SaaS istemiyor ve veri güvenliği öncelikli. Model kalitesi donanıma göre değişebilir.

## Karar

Varsayılan model gateway Ollama'dır. `local-balanced` başlangıçta `qwen3.5:9b`, `local-strong` `qwen3.5:27b` profiline eşlenir; bu eşleme config'tedir. Cloud tamamen kapalı gelir. Açılırsa admin opt-in, host allowlist, classification, redaction ve audit birlikte zorunludur.

## Sonuçlar

Kurulum internet olmadan çalışabilir. Donanım ve model yaşam döngüsü müşteriye aittir. Model seçimi genel benchmark ile değil sentetik/kuruma özel golden eval ile yapılır; 9B kalite kapısını geçmezse 27B denenir.

## Alternatifler

Cloud-first daha kolay operasyon sağlar fakat güvenlik hedefiyle çelişir. Tek modele hard-code etmek upgrade ve donanım esnekliğini bozar.

