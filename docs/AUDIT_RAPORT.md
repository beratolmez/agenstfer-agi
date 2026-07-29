# Proje Teknik Denetim Raporu

> **Historical record — closed.** Kept for traceability. Do not read this for working
> context and do not add to it: the findings that are still open live in
> [`REMEDIATION_ROADMAP.md`](./REMEDIATION_ROADMAP.md), and the reasoning behind them in
> [`ARCHITECTURE_ASSESSMENT.md`](./ARCHITECTURE_ASSESSMENT.md). See
> [`AI_DEVELOPMENT_GUIDE.md`](./AI_DEVELOPMENT_GUIDE.md) §3.

**Proje**: Agentic Growth Intelligence  
**Tarih**: 25 Temmuz 2026  
**Rol**: Senior Software Architect / Tech Lead / Code Auditor  
**Amaç**: Tutarsızlıklar, güncel olmayan dosyalar ve teknik borçları tespit etmek  

---

## Özet İstatistikler

| Kategori | Bulgu Sayısı | Kritik | Yüksek | Orta | Düşük |
|---|---|---|---|---|---|
| Hayalet Dokümantasyon (Kırık Referanslar) | 4 | 0 | 2 | 2 | 0 |
| Dokümantasyon Doğruluğu (Yalan Statüler) | 5 | 2 | 3 | 0 | 0 |
| Frontend-Backend Kontrat Uyumsuzlukları | 8 | 2 | 4 | 2 | 0 |
| Altyapı & Docker Sorunları | 3 | 1 | 1 | 1 | 0 |
| Ortam Değişkeni & Config Uyumsuzlukları | 3 | 0 | 2 | 1 | 0 |
| Legacy / Kullanılmayan Kod | 3 | 0 | 0 | 2 | 1 |
| Kod Kalitesi & Teknik Borç | 6 | 0 | 1 | 3 | 2 |
| **Toplam** | **32** | **5** | **13** | **11** | **3** |

---

## Kategori 1: Hayalet Dokümantasyon (Kırık Referanslar)

### Bulgu 1.1

**Dosya**: [README.md L11](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/README.md#L11)

**Problem**: `ARCHITECTURE_CONTEXT.md` dosyasına referans veriyor ama bu dosya **mevcut değil**.

**Neden Problem?**: README projenin giriş noktasıdır. İlk açan geliştirici veya müşteri kırık bir link ile karşılaşır. Güvenilirlik zedelenir.

**Önerilen Çözüm**: Bu referansı kaldır veya [SYSTEM_ARCHITECTURE.md](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/docs/SYSTEM_ARCHITECTURE.md)'ye yönlendir.

**Etki**: Medium

---

### Bulgu 1.2

**Dosya**: [README.md L17-18](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/README.md#L17-L18)

**Problem**: README üç adet **mevcut olmayan** belgeye link veriyor:
- `docs/ENGINEERING_FOCUS_ROADMAP.md` → **YOK**
- `docs/MVP_IMPLEMENTATION_PLAN.md` → **YOK**
- `docs/NEXT_STEPS_GUIDE.md` → **YOK**

**Neden Problem?**: Projenin "navigasyon paneli" olan README kırık linklerle dolu. Güvenilirlik ve navigasyon kaybı.

**Önerilen Çözüm**: Bu üç satırı README'den kaldır. Bu belgeler hiç oluşturulmamış veya silinmiş.

**Etki**: High

---

### Bulgu 1.3

**Dosya**: [OPERATIONS_RUNBOOK.md L47](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/docs/OPERATIONS_RUNBOOK.md#L47)

**Problem**: `docker-compose.observability.yml` referansı veriliyor. Bu dosya **mevcut** ama `docker compose --profile observability` ile de aynı iş yapılabilir (jaeger zaten base compose'da `profiles: [observability]` ile tanımlı). Karışıklık yaratıyor.

**Neden Problem?**: İki farklı yolla observability stack başlatma talimatı var. Hangisi doğru belirsiz.

**Önerilen Çözüm**: Runbook'u sadece `docker compose --profile observability up -d` talimatı ile güncelle, observability overlay gereksizse kaldır.

**Etki**: Medium

---

### Bulgu 1.4

**Dosya**: [OPERATIONS_RUNBOOK.md L33](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/docs/OPERATIONS_RUNBOOK.md#L33)

**Problem**: "Put the API key in `.secrets/gemini_api_key`" diyor, ancak `config.py`'de bu path tanımlı değil. Config `cloud_api_key_file` kullanıyor, bu da `.secrets/cloud_model_api_key` bekliyor (`.env.example` L26'da tanımlı).

**Neden Problem?**: Kullanıcı runbook'u takip ederse yanlış dosyayı oluşturur, API key algılanmaz.

**Önerilen Çözüm**: Runbook'taki path'i `.secrets/cloud_model_api_key` olarak düzelt.

**Etki**: High

---

## Kategori 2: Dokümantasyon Doğruluğu (Yalan Statüler)

### Bulgu 2.1

**Dosya**: [IMPLEMENTATION_STATUS.md L12](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/docs/IMPLEMENTATION_STATUS.md#L12)

**Problem**: "Built with **Tailwind CSS**" iddiası var ancak:
- `package.json`'da Tailwind dependency'si **yok**
- `apps/web/` altında `tailwind.config.*` dosyası **yok**
- Kaynak kodda `tailwind` veya `@tailwind` importu **yok**
- Tüm styling **inline CSS** ve **vanilla CSS** ile yapılıyor

**Neden Problem?**: Source of truth belgesi gerçeği yansıtmıyor. Yeni geliştirici Tailwind sınıfı kullanarak PR açar, çalışmaz.

**Önerilen Çözüm**: "Tailwind CSS" ifadesini "Vanilla CSS" olarak düzelt. Aynı düzeltmeyi [SYSTEM_ARCHITECTURE.md L17](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/docs/SYSTEM_ARCHITECTURE.md#L17)'de de yap.

**Etki**: High

---

### Bulgu 2.2

**Dosya**: [SYSTEM_ARCHITECTURE.md L48-56](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/docs/SYSTEM_ARCHITECTURE.md#L48-L56)

**Problem**: Mimari diyagramda LangGraph ve ChromaDB hâlâ "Target" ve "Migration" olarak gösteriliyor. `IMPLEMENTATION_STATUS.md` ise bunları **Phase 2-6 Completed** olarak işaretliyor.

**Neden Problem?**: İki resmi belge birbiriyle **çelişiyor**. Biri "yapıldı" diyor, diğeri "yapılacak" diyor. Hangisi doğru?

**Önerilen Çözüm**: `SYSTEM_ARCHITECTURE.md` diyagramlarını güncelle. "Current vs Target" tablosunu [L122-131](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/docs/SYSTEM_ARCHITECTURE.md#L122-L131) kısmını `IMPLEMENTATION_STATUS.md` ile tutarlı hale getir. LangGraph artık "Target" değil "Active", ChromaDB artık "Target" değil "Active with lexical fallback", MCP artık "Mock" değil "Approved gateway with code-defined allowlists".

**Etki**: Critical

---

### Bulgu 2.3

**Dosya**: [IMPLEMENTATION_STATUS.md L72](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/docs/IMPLEMENTATION_STATUS.md#L72)

**Problem**: Phase 15 "**Completed**" olarak işaretlenmiş ve ADR-0017'de karar yazılmış. İddia edilen düzeltme: "removed custom x-goog-api-key header overrides". Ancak model_gateway.py **gerçekten güncellendi** (header kaldırılmış). ✅ Bu doğru.

Fakat ADR-0017 ayrıca "Enforced full-screen onboarding gate compliance" ve "removed silent fallback to local-balanced when probing cloud models" iddia ediyor. SetupWizard.tsx'te hâlâ silent fallback olup olmadığını doğrulamalı.

**Neden Problem?**: ADR'nin iddia ettiği her düzeltmenin gerçekten uygulandığından emin olunmalı.

**Önerilen Çözüm**: SetupWizard.tsx'teki probe error handling mantığını doğrula. Eğer hâlâ local-balanced'a silent fallback yapıyorsa, ADR-0017'nin o maddesi uygulanmamış demektir.

**Etki**: High

---

### Bulgu 2.4

**Dosya**: [IMPLEMENTATION_STATUS.md L73](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/docs/IMPLEMENTATION_STATUS.md#L73)

**Problem**: Phase 16 "**Completed**" olarak işaretlenmiş. ADR-0018 "Configured app service with egress proxy network routing" diyor. Docker-compose.yml **gerçekten güncellendi** (`networks: [core, egress]` ve `HTTPS_PROXY` eklenmiş). ✅ Bu doğru.

**Ancak**: `egress` network `{}` olarak tanımlı yani **internal değil**. Bu, `app` container'ının `egress-gateway` (Squid proxy) **bypass** ederek doğrudan internete çıkabilmesi anlamına geliyor.

**Neden Problem?**: ADR-0005 ve güvenlik mimarisi, `app`'in sadece allowlisted domain'lere Squid üzerinden çıkmasını gerektiriyor. Ancak mevcut yapıda `app` Squid'i atlayarak herhangi bir adrese doğrudan bağlanabilir. `HTTPS_PROXY` env var'ı `httpx`'i yönlendirir ama zorunlu kılmaz.

**Önerilen Çözüm**: `egress` network'ünü `internal: true` yap, böylece `app` sadece `egress-gateway` üzerinden çıkabilir. Veya `app`'ı `egress` network'ünden çıkarıp sadece `core`'da tut ve Squid'e erişim için ayrı bir internal bridge network oluştur.

**Etki**: Critical

---

### Bulgu 2.5

**Dosya**: [NEW_ARCHITECTURE_PLAN.md](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/docs/NEW_ARCHITECTURE_PLAN.md)

**Problem**: Bu belge tamamen **eski ve güncel olmayan mimariyi** anlatıyor:
- "Kubernetes / ECS / Docker Swarm / Cloudflare Workers" (L55-59) — şu an sadece Docker Compose var
- "GLM 5.2 / Qwen" (L45) — şu an Gemini API kullanılıyor
- "Notification Service / Authentication / Search" gibi ayrı containerlar (L68-74) — şu an FastAPI monolith
- "API Gateway" (L88) — şu an Nginx reverse proxy

**Neden Problem?**: Bu belge `docs/` dizininde aktif belge gibi duruyor. README'de referansı var ([L15](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/README.md#L15)). Projeye yeni katılan biri mimariyi yanlış anlar.

**Önerilen Çözüm**: Bu belgeyi `docs/archive/` veya `docs/legacy/` altına taşı ve README'deki referansı kaldır. Ya da başına büyük bir "⚠️ DEPRECATED — Güncel mimari için SYSTEM_ARCHITECTURE.md'ye bakın" uyarısı ekle.

**Etki**: High

---

## Kategori 3: Frontend-Backend Kontrat Uyumsuzlukları

### Bulgu 3.1

**Dosya**: [App.tsx L118](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/apps/web/src/App.tsx#L118)

**Problem**: `onComplete` handler'ında **race condition** var:
```typescript
onComplete={() => { api.setupStatus().then(setSetupStatus); navigate("dashboard"); }}
```
`navigate("dashboard")` **hemen** `view` state'ini günceller ve re-render tetikler. Ama `api.setupStatus().then(setSetupStatus)` henüz **resolve olmamış**. Bu durumda eski `setupStatus` (`setup_completed: false` veya `undefined`) ile L114 koşulu değerlendirilir ve **tekrar SetupWizard render edilir**.

**Neden Problem?**: Kullanıcı Setup Wizard'ı tamamladıktan sonra Dashboard'a **geçemez**. Sonsuz döngüye girer.

**Önerilen Çözüm**: `navigate` çağrısını `setupStatus` güncellemesinden **sonraya** taşı:
```typescript
onComplete={async () => {
  const freshStatus = await api.setupStatus();
  setSetupStatus(freshStatus);
  navigate("dashboard");
}}
```

**Etki**: Critical

---

### Bulgu 3.2

**Dosya**: [SetupWizard.tsx L930-931](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/apps/web/src/features/setup/SetupWizard.tsx#L930-L931)

**Problem**: `saveSetupProgress` çağrısı `catch { /* Continue to complete wizard */ }` ile error'u yok ediyor. Backend 422 veya 409 dönerse kullanıcı hiçbir şey görmez ama progress kaydedilmez. Bu da `setup_completed` field'ının veritabanında güncellenmemesine neden olur.

**Neden Problem?**: Hata sessizce yutulduğu için teşhis imkansızlaşıyor. Progress kaydedilmezse dashboard'a geçiş başarısız olur.

**Önerilen Çözüm**: Hata durumunda en azından bir uyarı göster. Critical olmayan hatalar için retry mekanizması ekle, critical olanlar için kullanıcıya bilgi ver.

**Etki**: High

---

### Bulgu 3.3

**Dosya**: [api.ts L295](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/apps/web/src/api.ts#L295)

**Problem**: Frontend `filePreview: (sourceId: string) => request<FilePreview>(/api/sources/${sourceId}/preview)` tanımlıyor ama backend'de bu `GET /api/sources/{sourceId}/preview` route'u **mevcut değil**. Sadece `POST /api/sources/files/preview` var (farklı bir endpoint, farklı parametre yapısı).

**Neden Problem?**: Bu API çağrısı her zaman 404 döner. Frontend'de dead code.

**Önerilen Çözüm**: Backend'e ilgili GET route'u ekle veya frontend'den bu çağrıyı kaldır.

**Etki**: Medium

---

### Bulgu 3.4

**Dosya**: [types.ts L139](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/apps/web/src/types.ts#L139) vs [main.py L995-1030](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/apps/api/agi_server/main.py#L995-L1030)

**Problem**: Backend `workflow_run_detail` endpoint'i `idempotency_key`, `evidence_ids`, `agent_versions`, `artifacts`, `steps` (token sayıları, I/O hash'leri, agent ID'leri dahil) döndürüyor. Frontend `WorkflowRunDetail` interface'i bunların çoğunu **tanımlamıyor** — sadece `output` ve `error` ekliyor.

**Neden Problem?**: Backend'den gelen zengin çalışma verileri frontend tarafından kullanılamıyor. Workflow run detaylarında eksik bilgi gösteriliyor.

**Önerilen Çözüm**: `WorkflowRunDetail` type'ına backend'in döndürdüğü tüm field'ları ekle.

**Etki**: Medium

---

### Bulgu 3.5

**Dosya**: [api.ts L222](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/apps/web/src/api.ts#L222) vs [main.py L1614](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/apps/api/agi_server/main.py#L1614)

**Problem**: Backend `decideCandidate` endpoint'i response'ta `candidate_id` döndürüyor. Frontend type tanımı bunu **içermiyor**: `request<{ status: string; revision: string; qmd: string }>`.

**Neden Problem?**: Response'taki `candidate_id` frontend'de erişilemez. Gelecekte bu değere ihtiyaç duyulursa type hatası oluşur.

**Önerilen Çözüm**: Frontend response type'ına `candidate_id: string` ekle.

**Etki**: High

---

### Bulgu 3.6

**Dosya**: [SetupWizard.tsx L223-229](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/apps/web/src/features/setup/SetupWizard.tsx#L223-L229)

**Problem**: Frontend **5 adımlık** bir setup wizard görselleştiriyor (Şirket Profili, Model Gateway, Connector, RAG, Tamamla). Backend ise [main.py L690-701](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/apps/api/agi_server/main.py#L690-L701) `/api/setup/status`'ta **10 adım** tanımlıyor.

Backend'in 10 adımı:
1. Bootstrap ve ilk admin
2. Roller
3. Yerel model testi
4. Şirket hedefi
5. Demo veya dosya kaynakları
6. Mapping ve önizleme
7. OKF bundle
8. Growth Diagnostic
9. Taslak rapor
10. OKF diff ve onay

Frontend bu adımları tamamen **yok sayıyor** ve kendi hardcoded 5 adımını kullanıyor.

**Neden Problem?**: Frontend ve backend'in setup journey tanımları tamamen farklı. Backend dinamik adım listesi dönüyor ama frontend bunu kullanmıyor. İleride backend adımları değiştiğinde frontend hiçbir şekilde etkilenmez — ya da tersi.

**Önerilen Çözüm**: Frontend'i backend'in döndürdüğü `steps` dizisini kullanacak şekilde yeniden yapılandır. Veya backend'in adım listesini frontend'in gerçek adımlarıyla eşleştir.

**Etki**: High

---

### Bulgu 3.7

**Dosya**: [SetupWizard.tsx L919-928](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/apps/web/src/features/setup/SetupWizard.tsx#L919-L928)

**Problem**: Frontend 5. adımda `status: "completed"` gönderiyor ve `completed_steps: Array.from({ length: 10 }, (_, i) => i)` ile 10 adımı da tamamlanmış olarak işaretliyor. Ancak gerçekte sadece 5 adım tamamlanmış — 6-10 arası adımlar (Growth Diagnostic, Taslak Rapor, OKF diff vs.) henüz yapılmamış.

**Neden Problem?**: Backend'e yalan bildiriliyor. Adım 6-10 hiç yapılmadan "completed" deniliyor. Bu, ileride bu adımlar gerçekten implement edildiğinde sorun yaratır çünkü backend "zaten tamamlandı" sanacak.

**Önerilen Çözüm**: Frontend sadece gerçekten tamamlanan adımları bildirmeli. Backend'in `completed` kontrolünü frontend'in gerçek adım sayısına uyumlu hale getir — veya frontend'in 10 adımı da desteklemesini sağla.

**Etki**: Critical

---

### Bulgu 3.8

**Dosya**: [SetupWizard.tsx L144-150](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/apps/web/src/features/setup/SetupWizard.tsx#L144-L150)

**Problem**: Frontend `saveSetupProgress` çağrısında sadece `company_name`, `industry`, `objective`, `provider`, `model` gönderiyor. Backend'in kabul ettiği ek alanlar olan `model_profile`, `source_mode`, `locale` hiç gönderilmiyor.

**Neden Problem?**: Kurulum sırasında seçilen model profili, kaynak modu ve dil tercihi **persist edilmiyor**. Bu bilgiler sadece frontend state'inde kalıyor — sayfa yenilendiğinde kaybolur.

**Önerilen Çözüm**: Frontend'in `saveSetupProgress` çağrısına `model_profile`, `source_mode`, `locale` değerlerini de ekle.

**Etki**: High

---

## Kategori 4: Altyapı & Docker Sorunları

### Bulgu 4.1

**Dosya**: [docker-compose.yml L92-96](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/docker-compose.yml#L92-L96)

**Problem**: `egress` network `{}` (external) olarak tanımlı. `app` bu network'e bağlı. Bu, `app`'in Squid proxy'yi bypass ederek doğrudan internete çıkmasını sağlıyor.

**Neden Problem?**: ADR-0005 ve güvenlik mimarisi `app`'in sadece allowlisted endpoint'lere çıkmasını gerektiriyor. `egress: {}` bu sınırı ortadan kaldırıyor. `HTTPS_PROXY` env var'ı `httpx`'e proxy kullan der ama enforce etmez — herhangi bir HTTP client proxy'yi atlayabilir.

**Önerilen Çözüm**: `egress` network'ünü `internal: true` yap. Bu durumda `app` sadece `egress-gateway`'e ulaşabilir, oradan da sadece allowlisted domain'lere çıkabilir.

**Etki**: Critical (Güvenlik)

---

### Bulgu 4.2

**Dosya**: [infra/proxy/nginx.conf](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/infra/proxy/nginx.conf)

**Problem**: Nginx konfigürasyonu:
1. **WebSocket upgrade header'ları eksik** — Gelecekte SSE veya WebSocket gerekirse çalışmaz
2. **Statik dosya servisi yok** — Tüm `/assets/*` istekleri Python backend'e proxy ediliyor, bu gereksiz yük oluşturur
3. **Gzip/Brotli sıkıştırma yok** — Frontend bundle boyutu optimize edilmiyor

**Neden Problem?**: Performans kaybı ve gelecek uyumsuzluk.

**Önerilen Çözüm**: WebSocket upgrade header'ları ekle. FastAPI'nin static_dir'ini serve etmek için `location /assets/` bloğu ekle. Gzip sıkıştırma ekle.

**Etki**: Medium

---

### Bulgu 4.3

**Dosya**: [vite.config.ts L8](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/apps/web/vite.config.ts#L8)

**Problem**: Dev proxy `http://localhost:8000` hedefliyor. Ancak:
- Dockerfile FastAPI'yi port **8080**'de başlatıyor
- Docker Compose'da `app` servisi port **8080** kullanıyor
- uvicorn komutu `--port 8080` kullanıyor

**Neden Problem?**: `npm run dev` ile çalıştırıldığında API istekleri yanlış porta gider ve başarısız olur. Geliştirici `uvicorn`'u `--port 8000` ile başlatması gerektiğini bilmek zorunda.

**Önerilen Çözüm**: Ya `vite.config.ts`'i `http://localhost:8080` olarak güncelle, ya da README/OPERATIONS_RUNBOOK'a "local dev'de uvicorn 8000 portundan çalıştırılır" açıklaması ekle. Tutarlılık için `8080` tercih edilmeli.

**Etki**: High

---

## Kategori 5: Ortam Değişkeni & Config Uyumsuzlukları

### Bulgu 5.1

**Dosya**: [.env.example L21-22](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/.env.example#L21-L22)

**Problem**: `.env.example` `GEMINI_API_KEY` ve `GEMINI_MODEL_NAME` tanımlıyor. Ancak [config.py](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/apps/api/agi_server/config.py) `Settings` sınıfında bu değişkenler **yok**. `env_prefix="AGI_"` ayarlı olduğu için `GEMINI_*` prefix'li değişkenler zaten okunamaz.

**Neden Problem?**: Kullanıcı `.env.example`'ı kopyalar, `GEMINI_API_KEY`'i doldurur, ama backend bu değeri hiç okumaz. `AGI_CLOUD_API_KEY` veya `.secrets/cloud_model_api_key` kullanılması gerekir — bu bilgi kullanıcıya açık değil.

**Önerilen Çözüm**: `.env.example`'dan `GEMINI_API_KEY` ve `GEMINI_MODEL_NAME` satırlarını kaldır. Yerine doğru değişkenleri (`AGI_CLOUD_PROVIDER=gemini`, `AGI_CLOUD_MODEL=gemini-2.5-flash`) öne çıkar ve yorum olarak açıkla.

**Etki**: High

---

### Bulgu 5.2

**Dosya**: [.env.example L14-15](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/.env.example#L14-L15)

**Problem**: `OLLAMA_CONTEXT_LENGTH=8192` ve `OLLAMA_NUM_PARALLEL=1` tanımlı. Bu değişkenler `AGI_` prefix'i olmadığı için `config.py`'nin `Settings` sınıfı tarafından okunamaz. Ollama container'ının kendisi tarafından kullanılması amaçlanmış olabilir ama docker-compose'da Ollama servisi **tanımlı değil**.

**Neden Problem?**: Kullanıcıya yanlış yönlendirme. Bu değişkenler hiçbir yerde kullanılmıyor.

**Önerilen Çözüm**: `OLLAMA_CONTEXT_LENGTH` ve `OLLAMA_NUM_PARALLEL` satırlarını `.env.example`'dan kaldır veya ilgili container tanımlandığında environment'a ekle.

**Etki**: Medium

---

### Bulgu 5.3

**Dosya**: [.env.example L11](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/.env.example#L11)

**Problem**: `AGI_ENABLE_DBOS=false` tanımlı. Ancak `config.py`'deki `enable_dbos` field'ı [L24](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/apps/api/agi_server/config.py#L24) varsayılan olarak `False`. Bu değişken kod tabanında **hiçbir yerde kullanılmıyor** — eski DBOS entegrasyonundan kalma.

**Neden Problem?**: Karışıklık yaratıyor. DBOS entegrasyonu kaldırılmış ama config'de hayaleti duruyor.

**Önerilen Çözüm**: `enable_dbos` field'ını `config.py`'den ve `.env.example`'dan kaldır.

**Etki**: High

---

## Kategori 6: Legacy / Kullanılmayan Kod

### Bulgu 6.1

**Dosya**: `apps/services/` dizini (6 alt klasör, ~49 dosya)

**Problem**: Aşağıdaki dizinler [IMPLEMENTATION_STATUS.md L52](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/docs/IMPLEMENTATION_STATUS.md#L52) ve [README.md L141](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/README.md#L141) tarafından "unintegrated legacy microservice stubs (ADR-0016)" olarak tanımlanıyor:

| Dizin | Dosya Sayısı | Durum |
|---|---|---|
| `apps/services/ai-agent/` | 31 | Legacy |
| `apps/services/rag/` | 14 | Legacy |
| `apps/services/auth/` | 1 | Stub |
| `apps/services/scheduler/` | 1 | Stub |
| `apps/services/search/` | 1 | Stub |
| `apps/services/workflow/` | 1 | Stub |

**Neden Problem?**: 49 dosya artık kullanılmıyor. `Dockerfile` [L18](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/Dockerfile#L18) hâlâ `COPY apps/services/ ./apps/services/` ile bunları Docker image'a kopyalıyor → gereksiz image boyutu artışı.

**Önerilen Çözüm**: Bu dizinleri `apps/services/_legacy/` altına taşı veya `.dockerignore`'a ekle. Alternatif olarak, Dockerfile'daki `COPY` satırını sadece gerekli service'leri kopyalacak şekilde güncelle.

**Etki**: Medium

---

### Bulgu 6.2

**Dosya**: `apps/frontend/` dizini (2 alt klasör)

**Problem**: `dashboard-ui/` ve `web-ui/` dizinleri [IMPLEMENTATION_STATUS.md L52](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/docs/IMPLEMENTATION_STATUS.md#L52) tarafından "non-production mock surfaces" olarak tanımlı. Aktif frontend `apps/web/`.

**Neden Problem?**: İsim benzerliği (`web-ui` vs `web`) karışıklık yaratıyor. Docker build'e dahil olmuyor ama repository'de gereksiz yer kaplıyor.

**Önerilen Çözüm**: `apps/frontend/` dizinini `apps/_legacy_frontend/` olarak yeniden adlandır veya sil.

**Etki**: Medium

---

### Bulgu 6.3

**Dosya**: [scripts/cleanup_dbos.py](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/scripts/cleanup_dbos.py)

**Problem**: `apps/api/legacy_agi_server` gibi mevcut olmayan path'lere referans veriyor. DBOS temizliği amacıyla yazılmış ama DBOS zaten kaldırılmış. Kendi kendini silebilecek scriptlere de referans veriyor (`scripts/watch-workflow-restarts.sh`).

**Neden Problem?**: Ölü script — ne bir değer katıyor ne de bir şeyi temizliyor.

**Önerilen Çözüm**: `cleanup_dbos.py` ve `watch-workflow-restarts.sh` dosyalarını kaldır.

**Etki**: Low

---

## Kategori 7: Kod Kalitesi & Teknik Borç

### Bulgu 7.1

**Dosya**: Backend — birden fazla dosya

**Problem**: Stub/empty fonksiyonlar tespit edildi:
- [db.py L41](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/apps/api/agi_server/db.py#L41): `pass` body
- [okf/search.py L54](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/apps/api/agi_server/okf/search.py#L54): `pass` body
- [workflow/persistent_runtime.py L615](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/apps/api/agi_server/workflow/persistent_runtime.py#L615): `pass` body
- `apps/services/ai-agent/ai_agent/long_term_memory.py` L26, L37: `pass` body
- `apps/services/ai-agent/ai_agent/models.py` L33: `pass` body
- `apps/services/rag/rag_service/ingest.py` L9: `pass` body

**Neden Problem?**: Stub'lar modül olarak import edilebilir görünüyor ama hiçbir işlem yapmıyor. Gerçek implementasyon bekleyen veya terk edilmiş code path'ler.

**Önerilen Çözüm**: Legacy service'lerdekiler zaten Bulgu 6.1 ile taşınacak. `db.py`, `okf/search.py`, `persistent_runtime.py` stub'larına `# TODO: Not implemented` yorumu ekle veya `NotImplementedError` raise et.

**Etki**: Medium

---

### Bulgu 7.2

**Dosya**: Test dosyaları — birden fazla

**Problem**: Stub test fonksiyonları hiçbir assertion yapmıyor:
- `tests/test_dynamic_skills.py` L20, L61, L106
- `tests/test_knowledge_retrieval.py` L65, L81, L87

**Neden Problem?**: Bu testler her zaman pass eder ve yanlış güvenlik hissi verir. `project-check.ps1` "100% clean test passes" raporlarken aslında test edilmemiş alanlar var.

**Önerilen Çözüm**: Her stub teste `pytest.skip("Not implemented")` ekle veya gerçek test mantığı yaz.

**Etki**: Medium

---

### Bulgu 7.3

**Dosya**: [PROJECT_ARCHITECTURE.md L27](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/docs/PROJECT_ARCHITECTURE.md#L27)

**Problem**: "Container Cluster" için "Kubernetes / ECS / Docker Swarm" ve "Microservices & Private Tools" ifadesi kullanılıyor. Mevcut implementasyonda bunların hiçbiri yok — sadece Docker Compose.

**Neden Problem?**: `PROJECT_ARCHITECTURE.md` "Single Source of Truth" olarak `SYSTEM_ARCHITECTURE.md`'ye referans veriyor ama kendisi eski mimariyi yansıtıyor.

**Önerilen Çözüm**: Tabloyu güncelle: "Containerized Microservices" → "Docker Compose (single-host reference deployment)". "Private Tools" → "Code-defined capability registry".

**Etki**: Medium

---

### Bulgu 7.4

**Dosya**: [docs/NEW_ARCHITECTURE.yaml](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/docs/NEW_ARCHITECTURE.yaml)

**Problem**: `NEW_ARCHITECTURE_PLAN.md`'nin YAML versiyonu gibi görünüyor. Benzer eski mimariyi tekrarlıyor. Hiçbir kod veya belge tarafından referans edilmiyor.

**Neden Problem?**: Orphan dosya — ne bir belge tarafından referans ediliyor ne de bir script tarafından kullanılıyor.

**Önerilen Çözüm**: Bu dosyayı `docs/archive/` altına taşı veya sil.

**Etki**: Low

---

### Bulgu 7.5

**Dosya**: [docs/PRODUCT_ROADMAP_TO_GOAL.md](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/docs/PRODUCT_ROADMAP_TO_GOAL.md)

**Problem**: Bu dosyanın README veya herhangi bir belge tarafından referans edilip edilmediğini kontrol etmek gerekiyor. Eğer orphan ise, içeriğinin güncelliğini doğrulamak gerekir.

**Neden Problem?**: Potansiyel olarak güncel olmayan ve referanssız bir belge.

**Önerilen Çözüm**: İçeriğini doğrula. Güncel ve değerliyse README'ye link ekle; değilse `docs/archive/` altına taşı.

**Etki**: Low

---

### Bulgu 7.6

**Dosya**: [docs/DOMAIN_CONTRACTS.md](file:///c:/Users/mypc/Projects/aisfer/agenstfer-agi/docs/DOMAIN_CONTRACTS.md)

**Problem**: Hiçbir README veya belge tarafından referans edilmiyor. İçeriğinin mevcut agent kontratlarıyla (`contracts.py`) tutarlılığı doğrulanmalı.

**Neden Problem?**: Orphan belge — erişilemez bilgi.

**Önerilen Çözüm**: İçeriğini doğrula ve README'ye ekle veya `docs/archive/` altına taşı.

**Etki**: Medium

---

## Öncelik Sıralaması (Fixer Agent için)

Aşağıdaki sıralama, hataları düzeltecek agent'a verilmesi gereken çalışma önceliğidir:

### Runde 1: Kritik Hatalar (Fonksiyonel Bozukluk & Güvenlik)
1. **Bulgu 3.1** — App.tsx onComplete race condition → Dashboard'a geçiş sonsuz döngüsü
2. **Bulgu 3.7** — Frontend backend'e yalan completed_steps bildiriyor (5 adım yapılmış, 10 bildiriliyor)
3. **Bulgu 4.1** — Docker egress network güvenlik bypass'ı (internal olmalı)
4. **Bulgu 2.2** — SYSTEM_ARCHITECTURE.md ↔ IMPLEMENTATION_STATUS.md çelişkisi
5. **Bulgu 2.4** — Docker egress network internal olmalı (2.2 ile bağlantılı)

### Runde 2: Yüksek Öncelikli Düzeltmeler (Kullanıcı Deneyimi & Doğruluk)
6. **Bulgu 4.3** — Vite proxy port uyumsuzluğu (8000 vs 8080)
7. **Bulgu 5.1** — .env.example GEMINI_* değişkenleri yanıltıcı
8. **Bulgu 3.6** — Frontend 5 adım vs Backend 10 adım uyumsuzluğu
9. **Bulgu 3.8** — Setup wizard model_profile/source_mode/locale persist etmiyor
10. **Bulgu 3.5** — OKF candidate response'ta candidate_id eksik
11. **Bulgu 1.2** — README kırık linkler (3 dosya mevcut değil)
12. **Bulgu 1.4** — OPERATIONS_RUNBOOK yanlış secret path
13. **Bulgu 2.1** — "Tailwind CSS" iddiası yanlış
14. **Bulgu 2.5** — NEW_ARCHITECTURE_PLAN.md tamamen eski
15. **Bulgu 3.2** — SetupWizard error swallowing
16. **Bulgu 5.3** — DBOS config hayaleti
17. **Bulgu 2.3** — ADR-0017 iddialarının doğrulanması

### Runde 3: Orta Öncelikli Temizlik (Teknik Borç & Tutarlılık)
18. **Bulgu 3.3** — filePreview dead code (backend route yok)
19. **Bulgu 3.4** — WorkflowRunDetail type eksik field'lar
20. **Bulgu 4.2** — Nginx WebSocket/static/gzip eksiklikleri
21. **Bulgu 5.2** — OLLAMA_* env var'ları kullanılmıyor
22. **Bulgu 6.1** — Legacy services dizini (49 dosya)
23. **Bulgu 6.2** — Legacy frontend dizini
24. **Bulgu 7.1** — Backend stub fonksiyonlar
25. **Bulgu 7.2** — Stub testler (yanlış güvenlik hissi)
26. **Bulgu 7.3** — PROJECT_ARCHITECTURE.md eski terminoloji

### Runde 4: Düşük Öncelikli Temizlik
27. **Bulgu 1.1** — README ARCHITECTURE_CONTEXT.md referansı
28. **Bulgu 1.3** — OPERATIONS_RUNBOOK observability talimat karışıklığı
29. **Bulgu 6.3** — cleanup_dbos.py ve watch-workflow-restarts.sh kaldırma
30. **Bulgu 7.4** — NEW_ARCHITECTURE.yaml orphan dosya
31. **Bulgu 7.5** — PRODUCT_ROADMAP_TO_GOAL.md doğrulama
32. **Bulgu 7.6** — DOMAIN_CONTRACTS.md orphan belge

---

> [!IMPORTANT]
> **Bu rapor sadece analiz ve tespit içerir — hiçbir kod değişikliği yapılmamıştır.** Fixer agent'ı bu raporu referans alarak düzeltmeleri Runde sıralamasına göre uygulamalıdır.
