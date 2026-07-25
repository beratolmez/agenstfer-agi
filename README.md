# Agentic Growth Intelligence

Agentic Growth Intelligence; şirket başına izole kurulup satılan ve güncellemeleri vendor tarafından
sağlanan, dağınık şirket bilgisini
taşınabilir [Open Knowledge Format 0.1](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
bilgi tabanına dönüştüren ve kaynak satırına kadar izlenebilen bir **Growth Diagnostic + 30 günlük
aksiyon planı** üreten local-first üründür. Bu ürün ortak SaaS tenancy varsaymaz; her kurulum tek bir
şirkete hizmet eder.

Kaynak [PRD](./Agentic_Growth_Intelligence_Server_PRD.md) ve
[yönetici mimarisi](./docs/SYSTEM_ARCHITECTURE.md) değiştirilmeden korunur. Güncel kararlar ve gerçek
durum:

- [Project Architecture](./docs/PROJECT_ARCHITECTURE.md)
- [New Architecture Plan](./docs/NEW_ARCHITECTURE_PLAN.md)
- [Product Deployment Plan](./docs/PRODUCT_DEPLOYMENT_PLAN.md)
- [Implementation Status](./docs/IMPLEMENTATION_STATUS.md)
- [Operations Runbook](./docs/OPERATIONS_RUNBOOK.md)
- [Release Checklist](./docs/RELEASE_CHECKLIST.md)

## Mevcut durum

Kod tabanı production-candidate seviyesindedir: ingestion/evidence/OKF, dört typed Pydantic AI
agent, deterministic scoring, Evidence Reviewer, yönetilebilir immutable workflow/agent sürümleri,
durability, Approval Center, kalıcı kurulum sihirbazı, backup/restore, no-egress, SBOM ve güvenlik
kontrolleri uygulanmıştır.

Henüz release değildir. Bu mimaride **Gemini API** entegrasyonu ana model sağlayıcısı olarak kullanılmaktadır. LangGraph orchestrator ile Pydantic AI kullanılarak `mock_data` ingestion ve React UI setup wizard'ı başarıyla entegre edilmiştir. Ayrıntı için
[Implementation Status](./docs/IMPLEMENTATION_STATUS.md) belgesine bakın.

## Yerel başlangıç

Gereksinimler: Docker Desktop/Engine + Compose v2. Hedef: Linux x86-64; önerilen referans ortam
8 CPU, 32 GB RAM ve 50 GB boş disk.

```powershell
Copy-Item .env.example .env
docker compose up -d --build
```

`.env` içindeki PostgreSQL parolasını ve development değerlerini değiştirin. Web:
`http://localhost:8080`; API docs: `http://localhost:8080/api/docs`.

Sadece açık development bypass için:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

Bu overlay production'da kullanılmaz.

## Production overlay

Production session cookie `Secure` olduğu için port 8080'i şirketin HTTPS reverse proxy'sinin
arkasına koyun. Secret dosyalarını üretin ve production overlay'i açın:

```powershell
.\scripts\initialize-secrets.ps1
docker compose -f docker-compose.yml -f docker-compose.production.yml up -d --build
```

Linux karşılığı `./scripts/initialize-secrets.sh` komutudur. `.secrets/` Git tarafından yok sayılır.
İlk admin oluşturulana kadar `bootstrap_token` değerini güvenli bir secret manager'da saklayın.

## Model seçimi

Projenin core LLM provider'ı **Gemini API**'dir.

API key `.env` içine yazılmaz, ortam değişkenleri ile veya `.secrets/cloud_model_api_key` üzerinden sisteme verilir.
`confidential`/`restricted` evidence cloud'a gönderilmez; izinli `internal` içerikte contact
identifier redaksiyonu uygulanır.

Pydantic AI agent'ları Gemini API üzerinden çağrılır. Test ve geliştirme amaçlı olarak FastApi backend'inde fallback mekanizması sağlanmış olabilir ancak production için hedef mimari Gemini'dir.
## Product architecture

The manager target architecture adds customer-isolated AWS deployments, private/local inference,
OpenTelemetry with optional self-hosted Langfuse, and later bounded task orchestration. The current
Compose deployment remains the reference implementation until one AWS runtime, customer update
path, inference network pattern, and observability profile are release-qualified. See
[Product Deployment Plan](./docs/PRODUCT_DEPLOYMENT_PLAN.md) and the ADRs 0009–0012.

## Geliştirme ve doğrulama

```powershell
uv sync --all-groups
npm --prefix apps/web ci
.\scripts\project-check.ps1
```

Canlı health ile `-Live`; no-egress, backup/restore ve release scan için:

```powershell
.\scripts\verify-no-egress.ps1
.\scripts\browser-e2e.ps1
.\scripts\backup.ps1
.\scripts\restore.ps1 .\backups\<timestamp>
.\scripts\release-scan.ps1
```

Linux script karşılıkları `scripts/*.sh` altındadır.

`browser-e2e` modelden bağımsız dashboard, setup/demo sync, Sources, Agent Registry
create/publish ve workflow version/schedule/dry-run akışlarını izole volume'larda doğrular. Gerçek
model diagnostic → citation → approval → export akışı
release için ayrıca çalıştırılmalıdır. Bu akış mevcut bir disposable deployment'a karşı şu wrapper
ile çalıştırılır; secret değerlerini komut satırına yazmayın:

```powershell
$env:AGI_E2E_ADMIN_PASSWORD = "<secret>"
$env:AGI_E2E_BOOTSTRAP_TOKEN = "<one-time-secret>"
.\scripts\browser-real-model-e2e.ps1 -BaseUrl http://127.0.0.1:8080 `
  -AdminEmail release-admin@example.test -ModelProfile local-strong -ConfirmDisposable
```

Nihai dış-host kapısı için Linux x86-64 üzerinde `scripts/release-rehearsal.sh` kullanılır. Script
20-run qualification, gerçek-model browser akışı, aynı LangGraph thread ID'si üzerinde agent/approval
restart, scan, backup/restore, lexical fallback ve qmd rebuild adımlarını birleştirir. Qualification
ve restart kanıtları bağımsız doğrulanır; zorunlu artifact'lar SHA-256 ile manifest'e bağlanır.
Script'in var olması bu kapıların geçtiği anlamına gelmez.

## MVP'nin yaptığı / yapmadığı

Yapar: read-only demo/CSV/XLSX ingest, canonical context ve immutable evidence, OKF 0.1 + Git
candidate lifecycle, evidence-gated Growth Diagnostic pipeline, constrained workflow/LangGraph/approval,
rapor ve portable OKF export. Kurulumda seçilen code-defined model profili immutable workflow
sürümüne pinlenir; Dashboard ve sihirbaz aynı persisted LangGraph run'ını izler. Release raporu üretmek
için ayrıca qualified model profili gerekir.

Yapmaz: gerçek CRM/ERP write-back, dış lead scraping, outreach, inbound/outbound call, finansal işlem,
siber güvenlik operasyonu, rakip otomasyonu veya multi-tenant SaaS. Bu işler yeni ADR, threat model,
consent/legal, capability ve rollback kapıları olmadan eklenmez.

## Repository haritası

```text
apps/api/       FastAPI, domain, Pydantic AI agents, OKF, LangGraph runtime, Chroma RAG, MCP gateway ve event inbox
apps/web/       React + TypeScript web console control plane
apps/services/  Unintegrated legacy microservice stubs (ADR-0016)
knowledge/      Immutable raw vault ve active/candidate OKF bilgi alanı
docs/           Mimari, ADR, plan, eval, threat, operasyon ve release belgeleri
infra/          Nginx, qmd ve allowlisted egress
scripts/        Cross-platform check, backup/restore, eval ve release araçları
```
