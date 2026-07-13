# MVP Uygulama Durumu

Son güncelleme: 13 Temmuz 2026

Bu belge, 14–18 haftalık üretim planı ile repository'de bugün çalışan dikey dilimi birbirinden ayırır. Kaynak PRD ve yönetici mimarisi değiştirilmemiştir.

## Tamamlanan çekirdek

- Faz 0 belgeleri, Mermaid diyagramları ve dört ADR.
- FastAPI + React/TypeScript monorepo iskeleti ve Docker Compose deployment'ı.
- PostgreSQL/Alembic şeması; kullanıcı, rol, audit, evidence, workflow, approval ve run state tabloları.
- OKF 0.1 parser/writer, conformance ve AGI kalite lint'i, link/backlink, index/log, Git diff ve ZIP import/export.
- Immutable raw vault ve source locator üzerinden citation → evidence → ham kaynak çözümleme.
- Tam sayıda sentetik Anka veri seti ve altı bilerek yerleştirilmiş fırsat/veri problemi.
- Dört agent tanımı, local Ollama model gateway'i ve deterministik fallback.
- Built-in Growth Diagnostic, ağırlıklı skor, ilk beş fırsat ve 30 günlük plan.
- Typed workflow DSL, publish validation, immutable sürüm modeli, dry-run ve DBOS durable run/approval akışı.
- Dashboard, Knowledge Explorer, kurulum sihirbazı, Evidence Drawer, Approval Center ve React Flow editörü.
- Backend/frontend testleri, production frontend build'i, Docker image ve container smoke testi.

## Release öncesi tamamlanacak işler

- Hedef Linux sunucuda gerçek Ollama modeliyle golden dataset eval'i ve 9B/27B profil kararı.
- qmd profilinin hedef makinede kurulması, hybrid index/reranker ölçümü ve fallback tatbikatı.
- PostgreSQL üzerinde uzun süreli DBOS restart/approval/idempotency testleri.
- Prompt injection, SSRF, XSS, path traversal, CSV formula injection ve log redaction güvenlik paketi.
- Gerçek backup → boş kurulum restore tatbikatı ve RPO/RTO kaydı.
- İlk tasarım ortağı belirlendikten sonra read-only CRM/ERP connector seçimi.
- Reverse proxy/TLS, secret manager ve kurumun SSO/RBAC politikasıyla production entegrasyonu.

## Bilinçli kapsam dışı

Harici write-back, dış lead discovery, inbound/outbound call, Financial Modules, Cyber Security ve rakip araştırması MVP içinde etkin değildir. Bu yetenekler ayrı threat model, approval ve ADR olmadan açılmamalıdır.

