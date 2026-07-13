# Agentic Growth Intelligence

Agentic Growth Intelligence, tek bir şirketin kendi altyapısında çalışan; dağınık şirket bilgisini taşınabilir bir [Open Knowledge Format (OKF) 0.1](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) bundle'ına dönüştüren ve kanıta bağlı bir **Growth Diagnostic + 30 günlük aksiyon planı** üreten local-first MVP'dir.

Bu repository, mevcut [PRD](./Agentic_Growth_Intelligence_Server_PRD.md) ile [yönetici mimari bağlamını](./ARCHITECTURE_CONTEXT.md) kaynak olarak korur. Güncel MVP kararları [proje mimarisinde](./docs/PROJECT_ARCHITECTURE.md), uygulama sırası [teknik planda](./docs/MVP_IMPLEMENTATION_PLAN.md), günlük çalışma biçimi [sonraki adımlar rehberinde](./docs/NEXT_STEPS_GUIDE.md), çalışan kapsam ile release öncesi kalanlar ise [uygulama durumu](./docs/IMPLEMENTATION_STATUS.md) belgesinde açıklanır. Domain sözleşmeleri, eval, tehdit modeli, operasyon ve release kapıları da `docs/` altında version-controlled tutulur.

## Mevcut durum: çalışan scaffold, tamamlanmamış MVP

Web/API/Docker katmanı ayağa kalkar; ancak ürün henüz gerçek agent tabanlı Growth Diagnostic çalıştırmaz. Bugünkü tanı çıktısı deterministik fixture'dır. Workflow editöründe yalnız doğrulama backend'e bağlıdır; Dry-run/Publish/Run ve Approval/Sources/Settings akışları tamamlanmamıştır. PostgreSQL şeması vardır fakat ürün state'i henüz kalıcı olarak kullanılmamaktadır.

Doğrulanmış ve eksik kapsamın tek kaynağı [Implementation Status](./docs/IMPLEMENTATION_STATUS.md) belgesidir.

## Şu anda doğrulanmış scaffold

- Sentetik “Anka Endüstriyel Otomasyon” şirketi ve deterministik Growth Diagnostic.
- OKF 0.1 concept okuma/yazma, lint, link/backlink ve ZIP round-trip altyapısı.
- Demo evidence referansları içeren sabit fırsat skorları ve 30 günlük plan.
- FastAPI API, React/TypeScript dashboard ve kısıtlı React Flow workflow editörü.
- Typed DAG doğrulaması; cycle, geçersiz port ve izin verilmeyen node reddi.
- PostgreSQL için uygulama/audit/evidence şema iskeleti; ürün akışları henüz bu state'i doldurmaz.
- Docker Compose ile `app`, `postgres`, `ollama`; opsiyonel `qmd`, `jaeger` ve `egress-gateway` profilleri.

Bu MVP henüz canlı CRM/ERP write-back, dış lead toplama, outbound, çağrı, finans, siber güvenlik ya da rakip araştırması yapmaz. Bunlar bilinçli olarak sonraki fazdır.

## Hızlı başlangıç

### Docker Compose

Gereksinimler: Docker Desktop/Engine, Compose v2, x86-64 Linux hedefinde en az 8 CPU, 32 GB RAM ve 50 GB boş disk önerilir.

```bash
cp .env.example .env
docker compose up --build
```

Web arayüzü: `http://localhost:8080`  
API dokümanı: `http://localhost:8080/api/docs`

Ollama modeli ilk çalıştırmada ayrıca indirilmelidir:

```bash
docker compose exec ollama ollama pull qwen3.5:9b
```

Yerel geliştirmede Ollama olmadan sentetik/deterministik demo çalışır.

### Geçici cloud model (Groq veya Mistral)

Cloud model varsayılan kapalıdır ve otomatik fallback değildir. Yönetici Groq veya Mistral profilini production için açıkça seçebilir; yalnız `public` ve policy tarafından izin verilmiş/redakte edilmiş `internal` veri gönderilebilir. `confidential` ve `restricted` veri MVP'de cloud provider'a gönderilemez. Varsayılan Compose dosyası internete çıkmaz.

1. `.env` içinde `AGI_CLOUD_PROVIDER=groq` veya `mistral`, `AGI_CLOUD_API_KEY=...` ve `AGI_MODEL_PROFILE=cloud-balanced` yazın. İsterseniz `AGI_CLOUD_MODEL` ile model adını değiştirin.
2. Allowlist'li proxy profilini başlatın:

```bash
docker compose -f docker-compose.yml -f docker-compose.cloud.yml --profile cloud up -d --build
```

Groq için varsayılan `openai/gpt-oss-20b`, Mistral için `mistral-small-latest` seçilir. API anahtarı yalnızca environment üzerinden okunur; status endpoint'i ve loglar anahtarı döndürmez.

### Yerel geliştirme

Backend (Python 3.12–3.14):

```bash
uv sync --all-groups
uv run uvicorn agi_server.main:app --app-dir apps/api --reload --port 8000
```

Frontend (Node 22+):

```bash
cd apps/web
npm install
npm run dev
```

Test ve kalite kontrolleri:

```bash
uv run pytest
uv run ruff check apps/api
cd apps/web && npm test && npm run build
```

## Repository haritası

```text
apps/api/             FastAPI, domain, OKF ve workflow runtime
apps/web/             React + TypeScript web console
knowledge/            Raw vault ve OKF 0.1 company bundle
docs/                 Mimari, plan, rehber, ADR ve görsel spec
infra/qmd/            Opsiyonel local qmd sidecar
```

## Güvenlik varsayımları

- Tek kurulum = tek şirket; SaaS/multi-tenant değildir.
- Cloud model ve genel internet egress varsayılan kapalıdır.
- Connector sözleşmeleri MVP'de read-only'dir.
- LLM çıktısı tek başına kanıt sayılmaz; önemli iddia source locator ile çözülmelidir.
- Üretimde `.env` içindeki örnek secret'lar kullanılmamalı; Docker secret veya eşdeğeri verilmelidir.

## Tasarım kaynakları

- [Dashboard konsepti](./docs/design/dashboard-concept.png)
- [Workflow editörü konsepti](./docs/design/workflow-editor-concept.png)
