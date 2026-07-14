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

## Amendment — 14 July 2026

Qwen 3.5 local typed extraction disables unpersisted reasoning with
`openai_reasoning_effort: none` and `temperature: 0`. Agent v2 uses Pydantic AI PromptedOutput,
bounded representative evidence in model context, and workflow-prefetched capability results; the
complete persisted evidence set remains in PostgreSQL for the final gate. The installed 9B model
passes the probe but failed the first full CPU golden run at Growth Opportunity Analyst, so it is a
development profile until a 20-run qualification passes. No automatic promotion to 27B or cloud is
allowed.

Growth Opportunity Analyst v3 resolves the earlier “up to ten” versus exactly-five typed-contract
conflict and bounds output to five short rationales. A real 9B node call passed in 278.29 seconds,
but this does not qualify the model: a complete successful diagnostic and the 20-run gate remain
mandatory.
