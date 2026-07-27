# Audit Findings

Bu dosya kümülatiftir. Yeni denetim turları **en alta eklenir**; önceki turlar silinmez.

---

# Tur 1 — İlk Tanı (First Diagnostic) Çalıştırılabilirlik Denetimi

**Tarih:** 27 Temmuz 2026
**Kapsam:** PRD (`Agentic_Growth_Intelligence_Server_PRD.md`), `docs/SYSTEM_ARCHITECTURE.md`, `docs/IMPLEMENTATION_STATUS.md` ve aktif baseline (`apps/api/agi_server`, `apps/web`)
**Yöntem:** Salt-okunur. Hiçbir proje dosyası değiştirilmedi. Bulgular iki sınıfa ayrıldı:

- **[RUNTIME]** — Bu denetim sırasında çalışan sistem üzerinde fiilen üretilip doğrulandı (Docker, canlı Gemini API, izole test konteyneri).
- **[STATİK]** — Kod okumasıyla tespit edildi, çalışma zamanında ayrıca tetiklenmedi.

**Denetim ortamı:**
- Docker Engine çalışır durumda; `agentic-growth-intelligence` stack'i ayağa kaldırıldı.
- Canlı Gemini API anahtarı ile gerçek çağrılar yapıldı (`gemini-3.6-flash`, `gemini-3.5-flash`, `gemini-3.1-flash-lite`, `gemini-2.0-flash`).
- Gerçek "sıfırdan ilk kurulum" senaryosu, mevcut veriye dokunmamak için **izole tek-kullanımlık konteynerde** (`agi-audit-fresh`, ayrı SQLite DB) çalıştırıldı.

---

## 0. Yönetici Özeti

**Soru: Proje bugün ilk tanıyı başarıyla çalıştırabiliyor mu? — Hayır.**

Temiz bir kurulumda ilk tanı, birbirinden bağımsız **beş ayrı bariyerin** her birinde durur. Her biri tek başına akışı bitirir:

| # | Bariyer | Sınıf |
|---|---|---|
| 1 | Belgelenen başlatma komutu (`docker compose up -d --build`) uygulamayı import-time'da çökertiyor | [RUNTIME] |
| 2 | Agent spec YAML'ları imaja girmiyor — düzeltme **commit edilmemiş** durumda | [RUNTIME] |
| 3 | Built-in diagnostic'in 4 agent node'u `local-balanced`'a çivili; Ollama servisi compose'da hiç yok | [RUNTIME] |
| 4 | Gemini 3.x düşünme (thinking) token'ları agent token bütçesini tüketiyor → boş/kesik çıktı | [RUNTIME] |
| 5 | Gemini 3.x paralel tool çağrılarında `thought_signature` gerektiriyor; Pydantic AI OpenAI katmanı bunu geri göndermiyor → HTTP 400 | [RUNTIME] |

**Kritik ikinci gözlem:** Bu hataların **hiçbiri loglanmıyor**. Kullanıcı yalnızca `409 "Diagnostic workflow başlatılamadı"` görüyor; konteyner loglarında tek satır bile yok; audit kaydında yalnızca `{"error_type": "ModelAPIError"}` var. Bu, sorunun teşhis edilebilirliğini sıfıra indiriyor ve muhtemelen `gemini-3.6-flash → gemini-2.0-flash` gibi **semptomu maskeleyen** commit edilmemiş değişikliklerin sebebidir.

**Olumlu bulgu:** Model çağrısı başarılı olduğunda agent hattı **gerçekten çalışıyor.** `gemini-3.1-flash-lite` ile `company-analyst` agent'ı geçerli, evidence ID'lerine bağlı, şemaya uygun bir `CompanyAnalysis` üretti (699 output token). Yani sorun agent mimarisinde değil, model gateway ayarları + deployment konfigürasyonunda.

---

## 1. BLOCKER Bulgular

### BLK-01 — Belgelenen başlatma komutu uygulamayı çökertiyor [RUNTIME]

**Kanıt:**
- `docker-compose.yml:17` — `AGI_CLOUD_MODELS_ENABLED: ${AGI_CLOUD_MODELS_ENABLED:-false}`
- `docker-compose.yml:6-20` — `environment:` bloğunda `AGI_CLOUD_PROVIDER`, `AGI_CLOUD_API_KEY`, `AGI_CLOUD_API_KEY_FILE`, `AGI_CLOUD_MODEL` **yok**
- `.env:18` — `AGI_CLOUD_MODELS_ENABLED=true`
- [apps/api/agi_server/config.py:60](apps/api/agi_server/config.py#L60) —
  ```python
  if self.cloud_models_enabled and (self.cloud_provider is None or self.cloud_api_key is None):
      raise ValueError("Cloud models require an explicit provider and API key")
  ```
- [apps/api/agi_server/db.py:372](apps/api/agi_server/db.py#L372) — `settings = get_settings()` **modül import seviyesinde**

**Sorun:** Docker Compose `${...}` yerine koyma işlemi host `.env`'i okur, dolayısıyla `AGI_CLOUD_MODELS_ENABLED=true` konteynere geçer. Ancak provider/key değişkenleri yalnızca `docker-compose.cloud.yml` overlay'inde tanımlıdır ve base compose bunları aktarmaz. Sonuç: fail-closed validator import anında patlar, uvicorn ölür, konteyner crash-loop'a girer. `web-proxy` de `depends_on: service_healthy` olduğu için hiç başlamaz — **UI tamamen erişilemez.**

Denetimde gözlenen çıktı:
```
dependency failed to start: container agentic-growth-intelligence-app-1 is unhealthy
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
  Value error, Cloud models require an explicit provider and API key
```

AGENTS.md "Mandatory Task Handoff Protocol" adım 2 tam olarak bu komutu zorunlu kılıyor — yani belgelenen prosedür bozuk durumda.

**Çözüm önerisi:** Base compose'da `AGI_CLOUD_MODELS_ENABLED` ya sabit `"false"` olmalı (cloud yalnız overlay ile açılır — ADR-0006'nın ruhu), ya da provider/model/key-file üçlüsü de aynı `environment` allowlist'ine eklenmelidir. Karışım kabul edilemez. Ayrıca `Settings` doğrulama hatası import-time yerine FastAPI `lifespan` içinde yakalanıp `/api/health` üzerinden "config invalid" olarak raporlanmalı; böylece yanlış konfigürasyon teşhis edilebilir bir duruma dönüşür.

**Doğrulama adımı:**
```bash
docker compose -f docker-compose.yml config | grep AGI_CLOUD
```
Beklenen (düzeltme sonrası): `AGI_CLOUD_MODELS_ENABLED` ile birlikte provider/key değişkenleri de görünmeli, veya bayrak `false` olmalı. Ardından `docker compose up -d --build` konteyneri `healthy` yapmalı.

---

### BLK-02 — Agent spec YAML'ları imaja girmiyor; düzeltme commit edilmemiş [RUNTIME]

**Kanıt:**
- `pyproject.toml:43-44` — **commit edilmemiş** çalışma kopyası eklemesi:
  ```toml
  [tool.setuptools.package-data]
  agi_server = ["agents/specs/*.yaml"]
  ```
  `git show HEAD:pyproject.toml | grep package-data` → **sonuç yok**
- `Dockerfile:19` — `uv pip install --no-deps .` (paket `site-packages`'a kurulur)
- [apps/api/agi_server/agents/registry.py:38-49](apps/api/agi_server/agents/registry.py#L38) — commit edilmemiş, CWD'ye bağımlı 3 adaylı fallback
- [apps/api/agi_server/workflow/registry_service.py:26](apps/api/agi_server/workflow/registry_service.py#L26) — `specs = AgentRegistry().list()`

**Sorun:** `Path.glob()` var olmayan dizinde hata atmaz, **boş liste** döner. HEAD'deki hâliyle imaj `agents/specs/*.yaml` dosyalarını içermez → `AgentRegistry().list()` sessizce `[]` döner → `ensure_platform_registry` hiçbir `AgentDefinitionRow` yazmaz, ama `registry_service.py:65-79`'da workflow satırını yine de `published` olarak yazar. Sonuç: `validate_workflow_bindings` "agent 'company-analyst' 3 has no published version" ile 422 verir. ADR-0023/ADR-0024'ün "daha çok yere `ensure_platform_registry` ekle" düzeltmeleri **semptomu** tedavi etmiş, kök nedeni değil.

Denetimde doğrulandı: çalışma kopyası düzeltmesiyle üretilen imajda spec'ler mevcut ve seeding çalışıyor —
```
agent_definitions: company-analyst v3 published, evidence-reviewer v3, growth-opportunity-analyst v3, wiki-curator v2
workflow_definitions: builtin-growth-diagnostic v3 published
```
Yani **repo'nun commit edilmiş hâli bozuk, yalnız yerel çalışma kopyası çalışıyor.**

**Çözüm önerisi:** `pyproject.toml` package-data değişikliği commit edilmeli. `AgentRegistry` dizin çözümlemesi CWD'ye bağımlı fallback yerine `importlib.resources.files("agi_server.agents") / "specs"` ile tek noktadan yapılmalı. En önemlisi `AgentRegistry.list()` **fail-closed** olmalı: sıfır spec bulunduğunda `RuntimeError` fırlatmalı, `ensure_platform_registry` boş registry ile workflow satırı yazmamalı. Sessiz boş liste bu sınıf hataların tekrarlamasının temel sebebidir.

**Doğrulama adımı:**
```bash
docker run --rm -w / agentic-growth-intelligence-app python -c "from agi_server.agents.registry import AgentRegistry; r=AgentRegistry(); print(r.directory, len(r.list()))"
```
CWD `/` iken bile spec sayısı 4 dönmelidir.

---

### BLK-03 — Built-in diagnostic `local-balanced`'a çivili; Ollama servisi compose'da yok [RUNTIME]

**Kanıt:**
- [apps/api/agi_server/workflow/default.py:36](apps/api/agi_server/workflow/default.py#L36), `:50`, `:73`, `:87` — dört AGENT_RUN node'unun tamamı `"model_profile": "local-balanced"`
- [apps/api/agi_server/workflow/registry_service.py:65](apps/api/agi_server/workflow/registry_service.py#L65) — `build_default_workflow()` **aynen** published olarak seed ediliyor
- [apps/api/agi_server/main.py:881](apps/api/agi_server/main.py#L881) — `/api/diagnostics/run` `ensure_platform_registry(db)` çağırıp bu workflow'u çalıştırıyor
- `docker-compose.yml:14-15` — `AGI_OLLAMA_BASE_URL: http://ollama:11434/v1`, `AGI_MODEL_PROFILE: ${AGI_MODEL_PROFILE:-local-balanced}`
- `docker compose config --services` → `postgres, app, egress-gateway, web-proxy` — **`ollama` yok.** `ollama` yalnızca `docker-compose.model-download.yml:2`'de tanımlı.
- Denetimde: `/api/health` → `"ollama":"unavailable"`

**Sorun:** Model gateway ne kadar doğru yapılandırılırsa yapılandırılsın (env, wizard, API key), `/api/diagnostics/run` üzerinden çalışan built-in tanı **her zaman** Ollama'ya gider. `settings.model_profile` bu yolda hiç okunmaz. `core` ağı `internal: true` olduğundan `ollama` adı DNS'te çözülmez. Kaçış yolu yalnızca Dashboard'ın `prepareDiagnosticWorkflow` klonlama akışıdır ([apps/web/src/api.ts:140-174](apps/web/src/api.ts#L140)) — yani belgelenen uyumluluk endpoint'i üretimde kullanılamaz durumda.

Ek olarak `scripts/pull-model.ps1:24` ve `scripts/pull-model.sh:17` base compose'da `ollama` servisini hedeflediği için **local modeli indirmenin desteklenen yolu da kırık** — bariyeri manuel aşmak da mümkün değil.

**Çözüm önerisi:** İki tutarlı seçenekten biri seçilmeli, ara durum bırakılmamalı: (a) `ollama` base compose'a bir profile ile geri konulup ADR-0003'ün "varsayılan gateway Ollama" kararı gerçekten uygulanmalı; veya (b) yeni bir ADR ile "varsayılan `cloud-balanced`, local opsiyonel overlay" kararı yazılmalı, `AGI_OLLAMA_BASE_URL` yalnız o overlay'de tanımlanmalı. Her iki durumda da node `model_profile` çözümlemesine deployment-seviyesi varsayılan eklenmeli: **node config > run-time override > `settings.model_profile` > spec**. Alternatif olarak `ensure_platform_registry` seed sırasında node profillerini `settings.model_profile` ile doldurmalı.

**Doğrulama adımı:**
```bash
docker exec agentic-growth-intelligence-app-1 python -c "import httpx;print(httpx.get('http://ollama:11434/api/tags',timeout=5).status_code)"
```
Düzeltme sonrası 200 dönmeli; veya built-in workflow node'ları `cloud-balanced` göstermeli.

---

### BLK-04 — Gemini 3.x thinking token'ları agent bütçesini tüketiyor; cloud profilinde reasoning kontrolü yok [RUNTIME]

**Kanıt:**
- [apps/api/agi_server/agents/model_gateway.py:122-136](apps/api/agi_server/agents/model_gateway.py#L122) — `model_settings_for_profile` `openai_reasoning_effort: "none"` ayarını **yalnızca `profile.local` için** uyguluyor; cloud profilinde sadece `max_tokens` gönderiliyor
- `apps/api/agi_server/agents/specs/company-analyst.yaml:12` — `max_output_tokens: 900` (diğerleri 900 / 1200 / 1800)
- Konteyner içinden doğrulandı:
  ```
  spec.max_output_tokens = 900
  model_settings sent = {'max_tokens': 900}
  ```

**Canlı reprodüksiyon** (gerçek `CompanyAnalysis` prompt'u, `max_tokens=900`, kodun gönderdiği ayarlarla birebir):
```
finish_reason = length
usage = {'completion_tokens': 31, 'prompt_tokens': 542, 'total_tokens': 1438}
→ gizli düşünme token'ı = 1438 - 542 - 31 = 865
content (85 karakter, kesik): ```json\n{\n  "summary": "Aisfer Endüstriyel Makina A.Ş., enerji verimli kompresör, yed
```
900 token'lık bütçenin **865'i görünmeyen reasoning'e** gitti, JSON yarıda kesildi → Pydantic AI şema doğrulaması başarısız → `retries=2` de aynı şekilde tükendi → adım düştü.

**Düzeltmenin doğrulaması:** Aynı istek `reasoning_effort: "minimal"` ile:
```
finish_reason = stop | completion_tokens = 677 | gizli düşünme token'ı = 0 | geçerli JSON: evet
```

**Önemli ayrıntı:** Gemini'nin OpenAI-uyumlu ucunda `reasoning_effort: "none"` **HTTP 400 INVALID_ARGUMENT** verir; geçerli değerler `"minimal"` ve `"low"`'dur. Yani Ollama için kullanılan `"none"` değeri cloud'a olduğu gibi taşınamaz.

**Yan bulgu — probe yanıltıyor:** [apps/api/agi_server/agents/probe.py:41](apps/api/agi_server/agents/probe.py#L41) `max_tokens=512` ile **iki alanlı** `StructuredOutputProbe`'u önemsiz bir prompt'la test ediyor. Denetimde probe `{"ready":true,"structured_output":true}` döndü, gerçek run ise aynı anda düşüyordu. AGENTS.md "A model integration is not complete until a real structured-output probe … pass" kuralı sağlanıyor görünüp aslında yanlış güven üretiyor.

**Çözüm önerisi:** `model_settings_for_profile` cloud profilleri için de reasoning bütçesini açıkça yönetmeli (Gemini'de `openai_reasoning_effort: "minimal"`), ve `max_output_tokens` **görünür çıktı** bütçesi olarak ele alınıp thinking payı ayrıca eklenmeli. Provider'a göre desteklenen değer kümesi kod tarafında ayrıştırılmalı (`none` yalnız Ollama, `minimal|low` Gemini). Probe, gerçek sözleşmelerden birini (`CompanyAnalysis`) gerçek spec bütçesiyle çalıştırmalı ki temsili olsun.

**Doğrulama adımı:**
```bash
curl -s "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions" -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" -d '{"model":"gemini-3.6-flash","messages":[{"role":"user","content":"Reply with JSON only: {\"ok\":true}"}],"max_tokens":50}'
```
`finish_reason: "length"` ve `completion_tokens` ≈ 0-2 gözlenir. `"reasoning_effort":"minimal"` eklendiğinde `finish_reason: "stop"` olmalıdır.

---

### BLK-05 — Gemini 3.x paralel tool çağrılarında `thought_signature` zorunlu; istemci geri göndermiyor → HTTP 400 [RUNTIME]

**Bu, tool kullanan tüm agent'lar için ilk tanının kesin durma noktasıdır.**

**Kanıt — üretim yolundan alınan gerçek hata:**
```
pydantic_ai.exceptions.ModelHTTPError: status_code: 400, model_name: gemini-3.1-flash-lite,
body: [{'error': {'code': 400, 'message': 'Function call is missing a thought_signature in
functionCall parts. This is required for tools to work correctly... Additional data, function
call `default_api:read_evidence` , position 2.', 'status': 'INVALID_ARGUMENT'}}]
During task with name 'company_agent'
```
Çağrı zinciri: `persistent_runtime.py:347` → `agents/runtime.py:234` → Pydantic AI → `OpenAIChatModel`.

**İzole reprodüksiyon** (ham HTTP, `gemini-3.1-flash-lite`, 3 paralel `read_evidence` çağrısı):

| Senaryo | Sonuç |
|---|---|
| Tur 1: 3 paralel tool çağrısı | `200` — yalnız **ilk** çağrı `extra_content.google.thought_signature` taşıyor |
| Tur 2: `thought_signature` **çıkarılmış** | **`400 INVALID_ARGUMENT`** |
| Tur 2: `thought_signature` **korunmuş** | `200` — model normal şekilde devam ediyor |

**Sorun:** Gemini 3.x ailesi çok turlu tool kullanımında `thought_signature` alanının geri gönderilmesini şart koşuyor. Alan OpenAI-uyumlu yanıtta `extra_content.google.thought_signature` içinde geliyor, ancak Pydantic AI'ın `OpenAIChatModel` sınıfı bu sağlayıcıya özgü alanı model mesajlarında taşımıyor. Sonuç: model **birden fazla** tool'u paralel çağırdığı anda bir sonraki istek 400 ile düşüyor.

Bu, built-in diagnostic'i doğrudan vuruyor: `company-analyst` spec'i `knowledge.search`, `knowledge.read_source`, `context.query`, `metrics.calculate` capability'lerine sahip ve [apps/api/agi_server/agents/runtime.py:183-198](apps/api/agi_server/agents/runtime.py#L183) bunları 3 ayrı tool olarak enjekte ediyor. Geniş bir analiz prompt'u model tarafından doğal olarak paralel tool çağrılarıyla karşılanıyor.

**Neden bugüne kadar fark edilmedi:** Tool **kullanılmayan** yollar sorunsuz çalışıyor — bu yüzden `/api/models/probe` (tool'suz) başarılı dönüyor ve tüm testler `model_override` ile `TestModel` kullandığından gerçek sağlayıcıya hiç çıkmıyor.

**Çözüm önerisi:** Üç seçenekten biri, tercih sırasıyla: (1) Pydantic AI'ın Gemini-native sağlayıcısına (`GoogleModel`/`GeminiModel`) geçilerek `thought_signature` round-trip'i kütüphaneye bırakılmalı — Model Gateway soyutlaması zaten bunu destekleyecek şekilde tasarlanmış; (2) `OpenAIChatModel` alt sınıflanıp `extra_content` alanı istek/yanıt arasında taşınmalı; (3) kısa vadeli azaltıcı olarak Gemini 3.x profillerinde paralel tool çağrısı kapatılmalı (`parallel_tool_calls=False`) — tek çağrı senaryosunda 400 üretilmiyor (denetimde doğrulandı). Seçilen yol bir ADR ile kayda geçmeli.

**Doğrulama adımı:** Tool'lu bir agent'ı gerçek Gemini 3.x modeliyle çalıştırın ve modeli birden fazla tool çağırmaya zorlayın:
```bash
docker exec <container> python -c "<company-analyst agent'ını 3 tool ile çalıştıran betik>"
```
Düzeltme öncesi `ModelHTTPError 400 ... thought_signature`; sonrası tamamlanmış `CompanyAnalysis` beklenir.

---

### BLK-06 — Hatalar tamamen yutuluyor; ilk tanı arızası teşhis edilemiyor [RUNTIME]

**Kanıt:**
- [apps/api/agi_server/main.py:917-927](apps/api/agi_server/main.py#L917) — `except Exception` → audit'e yalnız `{"error_type": ...}`, kullanıcıya `409 "Diagnostic workflow başlatılamadı"`
- [apps/api/agi_server/main.py:2145](apps/api/agi_server/main.py#L2145) — `except Exception` → `409 "Workflow run tamamlanamadı"`
- [apps/api/agi_server/workflow/persistent_runtime.py:525](apps/api/agi_server/workflow/persistent_runtime.py#L525) — `run.error_json = {"code": type(error).__name__, "message": "Workflow execution failed"}`

**Denetimde gözlenen:** İlk tanı başarısız oldu, konteyner loglarında **tek satır bile yok**. Audit tablosundaki tüm bilgi:
```
{'action': 'diagnostic.run_failed', 'metadata_json': '{"error_type": "ModelAPIError"}'}
```
Gerçek sebebe ulaşmak için uygulamanın iç fonksiyonlarını konteyner içinde elle çağırmak gerekti.

**Sorun:** İçerik-güvenliği gerekçesi (ADR-0010) meşrudur, ancak sır içermeyen alanların gizlenmesi için gerekçe yok: sağlayıcı, model adı, profil, HTTP durum kodu, node ID, `retry_after`. `/api/models/probe` bunu doğru yapıp gerçek mesajı iletiyor ([main.py:346-350](apps/api/agi_server/main.py#L346)) — sistem kendi içinde tutarsız. Bu bulgu, diğer beş blocker'ın neden bu kadar uzun süre çözülmeden kaldığının doğrudan açıklamasıdır.

**Çözüm önerisi:** İstisnalar en azından sunucu loguna tam traceback ile yazılmalı (prompt/evidence gövdesi hariç). `error_json` içerik-güvenli yapılandırılmış alanlarla zenginleştirilmeli: `provider`, `model`, `profile`, `http_status`, `node_id`, `retry_after_seconds`. UI bu alanları göstermeli.

**Doğrulama adımı:**
```bash
docker logs <app-container> 2>&1 | tail -50
```
Başarısız bir tanı sonrası logda gerçek istisnanın görünmesi beklenir.

---

## 2. HIGH Bulgular

### HI-01 — Commit edilmemiş model downgrade'i sorunu maskeliyor ve kullanılamaz model seçiyor [RUNTIME]

**Kanıt** (`git diff`, commit edilmemiş):
- [apps/api/agi_server/agents/model_gateway.py:23](apps/api/agi_server/agents/model_gateway.py#L23) — `gemini-3.6-flash` → `gemini-2.0-flash`
- [apps/api/agi_server/main.py:401-407](apps/api/agi_server/main.py#L401) — discover fallback listesi `gemini-3.6-flash, gemini-3.5-flash-lite, gemini-2.5-flash, gemini-2.0-flash` → `gemini-2.0-flash, gemini-1.5-flash, gemini-1.5-pro`

**Canlı doğrulama:**
- `gemini-3.6-flash` bu anahtarın model kataloğunda **mevcut** (57 model listelendi) → downgrade teknik zorunluluk değil.
- `gemini-2.0-flash` bu anahtarda **kota limiti 0**:
  ```
  429 ... Quota exceeded for metric: generate_content_free_tier_requests, limit: 0, model: gemini-2.0-flash
  ```
  Yani yeni varsayılan **hiç çalışmıyor.**
- `gemini-1.5-flash` / `gemini-1.5-pro` katalogda **yok** (emekliye ayrılmış) → seçilirse 404.
- `gemini-2.5-flash-lite`: `404 ... no longer available to new users`.

**Sorun:** Değişiklik BLK-04'ün (thinking token) semptomunu maskeleme girişimi gibi görünüyor ancak sonucu daha kötü: varsayılan model kullanılamaz hâle geliyor ve discover fallback'i var olmayan modeller öneriyor. Ayrıca `apps/api/tests/test_cloud_providers.py:16` (`assert gemini_model == "gemini-3.6-flash"`) **kesin olarak kırılıyor** → `scripts/project-check.ps1` temiz geçemez → AGENTS.md handoff protokolü adım 3 ihlali. ADR-004'ün "Default Gemini choices to `gemini-3.6-flash`" kararıyla da çelişiyor.

**Model adı tutarsızlığı** ayrıca 6 yerde farklı: `model_gateway.py:23` (`2.0-flash`), `SetupWizard.tsx:12` (`3.6-flash`), `SetupWizard.test.tsx:29` (`2.5-flash`), `.env.example:19` (`3.6-flash`), `.env:22-23` (`2.0-flash`), `ai_agent/models.py:21` (`2.5-flash`).

**Çözüm önerisi:** Downgrade geri alınmalı; asıl neden BLK-04/BLK-05 olarak düzeltilmeli. Varsayılan model tek kaynakta (`CLOUD_PROVIDERS`) tanımlanmalı; `.env`, `.env.example`, `SetupWizard.tsx` ve testler bu tek değere referans vermeli. Discover fallback listesi ya uzun ömürlü alias'larla (`gemini-flash-latest`) sınırlanmalı ya da tamamen kaldırılıp "API key girin" durumu gösterilmeli.

**Doğrulama adımı:**
```bash
uv run pytest apps/api/tests/test_cloud_providers.py -q
```
Şu anki çalışma kopyasında başarısız olmalı; düzeltme sonrası geçmeli.

---

### HI-02 — Onboarding'de girilen API key kalıcı değil [STATİK]

**Kanıt:**
- [apps/api/agi_server/main.py:465-476](apps/api/agi_server/main.py#L465) — `settings.cloud_api_key = SecretStr(payload.api_key)`, `settings.cloud_models_enabled = True`
- [apps/api/agi_server/config.py:104-106](apps/api/agi_server/config.py#L104) — `@lru_cache def get_settings()`
- Key'i DB'ye veya dosyaya yazan hiçbir kod yolu yok.

**Sorun:** `/api/models/configure` yalnızca `lru_cache`'lenmiş `Settings` singleton'ını mutasyona uğratıyor. Konteyner restart / `--force-recreate` sonrası key ve provider kaybolur, ancak `InstallationState.status = "completed"` DB'de kalıcıdır. Kullanıcı Dashboard'a düşer, tanı çalıştırır, `resolve_model_profile` `PermissionError` atar; wizard `setup_completed=true` olduğu için varsayılan olarak açılmaz — düzeltme yolu yok. AGENTS.md "state survives refresh when persistence is required" kuralının ihlali. `installation_state.configuration` içinde `provider`/`model` saklanıyor ama **hiçbir kod bunu okumuyor** — ölü konfigürasyon.

**Çözüm önerisi:** Provider/model seçimi kalıcı bir kayda (`installation_state` veya adanmış tablo) yazılmalı ve `Settings` talep başına bu kayıtla override edilmeli. API key için: geliştirmede `AGI_MASTER_KEY` ile şifrelenmiş DB alanı, üretimde mevcut mounted-secret yolu (üretimde payload ile key kabul etmeme davranışı `main.py:450-463`'te zaten doğru uygulanmış).

**Doğrulama adımı:**
```bash
docker compose restart app
docker exec <app> python -c "from agi_server.config import get_settings;s=get_settings();print(s.cloud_provider, s.cloud_model, s.cloud_api_key is not None)"
```
Configure sonrası restart'ta değerler korunmalı.

---

### HI-03 — Kurulum sihirbazı her koşulda `cloud-balanced` gönderiyor → 422 → sessiz yutma → onboarding döngüsü [STATİK]

**Kanıt:**
- [apps/web/src/features/setup/SetupWizard.tsx:54](apps/web/src/features/setup/SetupWizard.tsx#L54) — `useState("gemini")`
- `SetupWizard.tsx:150` ve `:932` — `model_profile: selectedProvider ? "cloud-balanced" : "local-balanced"`
- [apps/api/agi_server/main.py:747-754](apps/api/agi_server/main.py#L747) — profil çözümlenemezse `422`
- `SetupWizard.tsx:938-941` — `catch { console.error(...) }` ardından koşulsuz `onComplete()`
- [apps/web/src/App.tsx:114](apps/web/src/App.tsx#L114) — durum backend'den tazeleniyor, `setup_completed` hâlâ `false`

**Sorun:** `selectedProvider` başlangıçta `"gemini"` ve hiçbir yolda boşalmıyor; ternary daima `"cloud-balanced"` üretiyor. API key girmeyen kullanıcıda `cloud_models_enabled` `false` kalır, son PUT 422 döner, hata `console.error` ile yutulur, `onComplete()` yine de çağrılır ve kullanıcı wizard'a geri atılır. ADR-0018/ADR-0019'un "çözüldü" dediği sonsuz döngü farklı bir yoldan geri gelmiş.

**Çözüm önerisi:** `model_profile` gerçekten seçilen/probe edilen profilden türetilmeli; local seçeneği ayrı bir kart olmalı. `saveSetupProgress` hataları görünür kılınmalı ve `onComplete()` yalnız başarılı PUT sonrası çağrılmalı.

**Doğrulama adımı:** Temiz DB ile API key girmeden Adım 1→5 ilerleyip "Dashboard'a Geç"e basın; wizard'ın tekrar açıldığını gözleyin. DevTools'ta `PUT /api/setup/progress` → 422 görünür.

---

### HI-04 — Sahte bağlantı testleri: `/api/sources/test-db` ve `/api/sources/test-mcp` [STATİK + kod doğrulandı]

**Kanıt:** [apps/api/agi_server/main.py:1436-1447](apps/api/agi_server/main.py#L1436)
```python
return {
    "status": "connected",
    ...
    "tables_found": ["accounts", "contacts", "opportunities", "invoices", "products"],
    "connection_time_ms": 14,
```
ve `main.py:1465-1475` (sahte `protocol_version` + 3 uydurma MCP tool'u).

**Sorun:** Her iki endpoint de girdi parametrelerini hiç kullanmadan, hiçbir soket açmadan sabit başarı döndürüyor. UI bunu doğrulanmış bağlantı olarak gösteriyor (`SetupWizard.tsx:683-687`, `:775-784`). Müşteri var olmayan bir CRM veritabanına "bağlandığını" görüyor. Başarılı test hiçbir `DataSource` kaydı da yaratmıyor. AGENTS.md "Never label deterministic fixtures or placeholders as agent execution" ve ADR-0016'nın "Eliminates false claims regarding MCP" karar sürücüsünün doğrudan ihlali.

**Çözüm önerisi:** Endpoint'ler gerçek read-only denemesi yapmalı (DB: `SELECT 1` + `information_schema`; MCP: onaylı `MCPProfile` üzerinden `mcp.py` gateway'i) ve başarısızlıkta 4xx dönmeli; ya da UI'dan kaldırılıp "bu sürümde desteklenmiyor" olarak işaretlenmeli. Fixture yanıt hiçbir koşulda 200 dönmemeli.

**Doğrulama adımı:**
```bash
curl -X POST http://localhost:8080/api/sources/test-db -b cookies.txt -H "X-CSRF-Token: <t>" -H 'content-type: application/json' -d '{"db_type":"postgresql","host":"10.255.255.1","port":1,"database_name":"x","username":"y"}'
```
Erişilemeyen host için 4xx/5xx beklenir; bugün 200 + "connected" dönüyor.

---

### HI-05 — Capability tool'larının bir kısmı uydurma veri döndürüyor ve modele enjekte ediliyor [STATİK + kod doğrulandı]

**Kanıt:** [apps/api/agi_server/agents/runtime.py:151-172](apps/api/agi_server/agents/runtime.py#L151)
```python
def read_crm(self, account_id): return {"account_id": account_id, "status": "active", "lead_score": 85}
def read_erp(self, customer_id): return {"customer_id": customer_id, "status": "verified", "total_revenue": 150000.0}
```
`scrape_web` ve `generate_battlecard` de aynı şekilde sabit. Bunlar `capabilities.py:45-79`'da "Reads ERP sales, invoice history, and financial metrics" açıklamasıyla published capability olarak kataloglanıyor ve `for_spec` ile gerçek Pydantic AI tool'u olarak modele veriliyor.

**Sorun:** `lead_score: 85` ve `total_revenue: 150000.0` persisted evidence'a bağlı olmayan uydurma sayılardır. Bir admin `Settings.tsx` üzerinden `erp.read`'i bir agent'a eklerse bu sayılar model bağlamına girer ve `MaterialClaim` metnine sızabilir. AGENTS.md "Every material or numerical generated claim must resolve to persisted evidence" ve PRD 4.5 (Evidence Based AI) ihlali.

**Çözüm önerisi:** Bu handler'lar capability registry'sinden ve `for_spec` enjeksiyonundan çıkarılmalı; gerçek implementasyon gelene kadar capability katalogda "planned/unavailable" statüsüyle tutulup çağrıldığında `rejected` dönmeli (mevcut `calculate_metric` reddetme deseni gibi, `runtime.py:136-141`).

**Doğrulama adımı:**
```bash
rg "lead_score|total_revenue|Public web snapshot" apps/api/agi_server
```
Boş dönmeli.

---

### HI-06 — Workflow node capability allowlist'i çalışma zamanında hiç uygulanmıyor [STATİK + kod doğrulandı]

**Kanıt:**
- [apps/api/agi_server/workflow/persistent_runtime.py:361](apps/api/agi_server/workflow/persistent_runtime.py#L361) — `capability_allowlist=frozenset()`
- [apps/api/agi_server/agents/runtime.py:180-181](apps/api/agi_server/agents/runtime.py#L180) — `if capability_allowlist is not None and len(capability_allowlist) > 0:` → boş küme **daraltma yapmaz**
- `_execute_node` hiçbir yerde `node.config["capabilities"]` okumuyor
- UI ise bunu kullanıcıya seçtirip tanıma yazıyor: [apps/web/src/features/workflow/WorkflowEditor.tsx:230](apps/web/src/features/workflow/WorkflowEditor.tsx#L230)

**Sorun:** `IMPLEMENTATION_STATUS.md:33` ve ADR-0016 Faz 5 "workflow node scopes strictly narrowing (never expanding) published spec capabilities" diyor. Üretim yolunda daraltma **hiç uygulanmıyor**; agent her zaman spec'in tam capability setini alıyor. Daraltma yalnız `test_dynamic_skills.py:94-101` birim testinde var. UI kontrolü dekoratif.

**Çözüm önerisi:** `_execute_node` `frozenset(node.config.get("capabilities", []))` değerini geçirmeli; `for_spec`'in boş-liste semantiği "hiç tool verme" olarak netleştirilmeli (veya `None` ile ayrılmalı). `validate_workflow_bindings` publish sırasında node capability kümesinin spec kümesinin alt kümesi olduğunu doğrulamalı.

**Doğrulama adımı:** Bir agent_run node'unda yalnız `knowledge.search` seçip çalıştırın; step çıktısında `read_evidence` tool çağrısı olmamalı.

---

### HI-07 — `/api/diagnostics/run` 202 diyor ama senkron çalışıyor; nginx 60 sn'de kesiyor [STATİK]

**Kanıt:**
- [apps/api/agi_server/main.py:865](apps/api/agi_server/main.py#L865) — `status_code=202`
- `main.py:898` — `run = await start_persisted_workflow(...)` (tüm graph aynı istekte)
- `infra/proxy/nginx.conf:10-11` — `proxy_read_timeout` **tanımlı değil** (nginx varsayılanı 60 sn)
- Agent timeout bütçeleri: 300s / 360s / 420s / 300s

**Sorun:** Frontend `run_id`'yi alabilmek için POST'un dönmesini bekliyor; POST ise 4 LLM çağrısı bitene kadar açık kalıyor. `web-proxy` 60 saniyede 504 verir, kullanıcı hata görür — run arka planda devam etse bile UI hiçbir zaman `run_id`'ye ulaşamaz ve polling başlamaz. 202 kodu asenkron sözleşme ima ederken davranış senkron.

**Çözüm önerisi:** Run kaydı oluşturulup 202 + `run_id` ile hemen dönülmeli; yürütme arka plan görevine/worker'a devredilmeli (k8s manifestlerinde `agi-worker` topolojisi zaten var). Sadece nginx timeout'unu artırmak yeterli değildir; tarayıcı ve ara katman timeout'ları da devrededir.

**Doğrulama adımı:** Model hazırken `curl -i -X POST http://localhost:8080/api/diagnostics/run -H "Idempotency-Key: audit-$(date +%s)"` → 60 sn sonra 504; eş zamanlı `curl /api/runs` run'ın hâlâ `running` olduğunu gösterir.

---

### HI-08 — Kurulum verisi kullanılmıyor; tanı çıktısı sabit demo şirket [STATİK]

**Kanıt:**
- [apps/api/agi_server/domain/computed_diagnostic.py:81-85](apps/api/agi_server/domain/computed_diagnostic.py#L81) — `company=DEMO_COMPANY`, `objective="90 gün içinde..."`, `open_approvals=1`
- `persistent_runtime.py:385` — gerçek çalıştırma yolunda kullanılıyor
- `company_name` yalnız `main.py:732` (allowed_keys) ve `:762` (uzunluk doğrulaması) içinde geçiyor; başka tüketici yok

**Sorun:** Kullanıcı Adım 1'de şirket adı, sektör ve büyüme hedefini giriyor; ilk tanı çıktısı bunları tamamen yok sayıp sabit demo şirket adıyla ("Anka Endüstriyel Otomasyon") üretiliyor. Ayrıca `computed_diagnostic.py:88-120`'deki 30 günlük plan tamamen sabit metin ve Dashboard'da 1. haftanın ilk iki aksiyonu koşulsuz "tamamlandı" ✓ ile gösteriliyor ([Dashboard.tsx:80-81](apps/web/src/features/dashboard/Dashboard.tsx#L80)) — Faz 13'te kaldırıldığı iddia edilen sentetik ilerleme göstergesi.

**Çözüm önerisi:** `build_computed_diagnostic` çağrısına `InstallationState.configuration`'dan gelen `company_name`/`objective` geçirilmeli; `DEMO_COMPANY` yalnız demo dataset'i için kalmalı. Plan şablonu ya OKF bundle'dan okunmalı ya da UI'da açıkça "deterministik şablon" olarak etiketlenmeli. `is-done` sınıfı gerçek durumdan türetilmeli.

**Doğrulama adımı:** Wizard'da şirket adını "Test AŞ" yapıp tanı çalıştırın; `GET /api/runs/<id>` çıktısında `output.diagnostic.company` alanını okuyun.

---

### HI-09 — Ürün sözleşmesi tek bir sentetik demo şirkete kilitli [STATİK]

**Kanıt:**
- [apps/api/agi_server/agents/contracts.py:7-13](apps/api/agi_server/agents/contracts.py#L7) — `SignalId = Literal["energy-retrofit", "predictive-maintenance", "oem-export", "spare-parts-subscription", "digital-twin-commissioning"]`
- `contracts.py:41` — `hypotheses: list[...] = Field(min_length=5, max_length=5)`
- `domain/metrics.py:191-210` — ürün adlarına string eşleşmesi ("Enerji İzleme", "OEM Export Kit"...)
- `metrics.py:170-171` — hesap/işlem yoksa `ValueError`
- `persistent_runtime.py:263-267` — `if node.config.get("connector_id") != "demo-company": raise ValueError`

**Sorun:** Fırsat sözleşmesi tam olarak 5 sabit sinyal ID'si dayatıyor ve metrikler Türkçe ürün adlarına bağlı. Gerçek bir müşteri kurulumunda ilk tanı ya demo veri üretir ya da `ValueError` ile düşer. `ReadOnlyCRMConnector`/`ReadOnlyERPConnector` sınıfları hiçbir endpoint/UI/workflow tarafından çağrılmıyor (yalnız testlerde) — yani `IMPLEMENTATION_STATUS.md:17`'nin "ingesting Accounts, Leads, Opportunities..." iddiası aktif değil.

**Çözüm önerisi:** `SignalId` literal'i konfigürasyondan/OKF bundle'dan türeyen dinamik sinyal kataloğuna taşınmalı; `DATA_SOURCE_SYNC` allowlist'i DB'deki kayıtlı `DataSource` satırlarından üretilmeli; CRM/ERP sarmalayıcıları bu yola bağlanmalı veya kaldırılmalı.

**Doğrulama adımı:** DEMO dışı bir CSV seti yükleyip tanı çalıştırın; fırsat başlıklarının veriye göre değişmesi beklenir.

---

## 3. MEDIUM Bulgular

### ME-01 — SQLite modu shipped konteynerde çalışmıyor [RUNTIME]

**Kanıt:** [apps/api/agi_server/db.py:373-374](apps/api/agi_server/db.py#L373)
```python
if settings.database_url.startswith("sqlite"):
    Path("data").mkdir(exist_ok=True)
```
**Gözlenen:** `PermissionError: [Errno 13] Permission denied: 'data'` — konteyner CWD'si `/app` root'a ait, süreç `agi` (uid 10001) olarak çalışıyor.

**Sorun:** SQLite dosyası nerede olursa olsun CWD'de `data/` dizini yaratılmaya çalışılıyor. `.env.example:2` varsayılan olarak `sqlite:///./data/agi.db` gönderdiği için, belgelenen varsayılan DB konfigürasyonu resmi imajda **çalışmıyor**.

**Çözüm önerisi:** Dizin, DB URL'inden çözümlenen dosya yolunun **üst dizini** olmalı ve yalnız gerekliyse yaratılmalı; hata durumu anlamlı mesajla ele alınmalı.

**Doğrulama adımı:**
```bash
docker run --rm -e AGI_DATABASE_URL="sqlite:////tmp/x.db" <image> python -c "import agi_server.db"
```
Hatasız tamamlanmalı.

---

### ME-02 — `.secrets/cloud_model_api_key` bir dizin; `initialize-secrets` bu sırrı üretmiyor [RUNTIME]

**Kanıt:**
```
drwxr-xr-x .secrets/cloud_model_api_key/     <-- DİZİN
-rw-r--r-- .secrets/cloud_model_api_key.txt  <-- gerçek dosya
```
- `docker-compose.cloud.yml:18` — `file: ${AGI_CLOUD_API_KEY_HOST_FILE:-.secrets/cloud_model_api_key}`
- `.env.example:21` — `.secrets/cloud_model_api_key` (dizin adıyla aynı)
- `.env:24` — `.secrets/cloud_model_api_key.txt` (farklı!)
- `scripts/initialize-secrets.ps1:16` — yalnız `bootstrap_token`, `session_secret`, `master_key` üretiyor

**Sorun:** `.env.example` ile başlayan taze kurulumda dosya mevcut değildir; Docker Compose secret kaynağı yoksa onu **dizin olarak** yaratır (bu makinede tam olarak bu olmuş). Ardından `config.py:52-58` `IsADirectoryError` alır ve `Settings` doğrulaması patlar → app import-time çöker. Yani "cloud overlay ile ilk kurulum" reprodüklenebilir şekilde başarısız.

**Çözüm önerisi:** `initialize-secrets.{ps1,sh}`'a `cloud_model_api_key` adımı eklenmeli. `.env`, `.env.example` ve `docker-compose.cloud.yml` tek bir dosya adında birleşmeli. Kalıntı dizini temizleme adımı runbook'a yazılmalı.

**Doğrulama adımı:**
```bash
ls -la .secrets/ && ./scripts/initialize-secrets.sh && docker compose -f docker-compose.yml -f docker-compose.cloud.yml config | grep -A2 cloud_model_api_key
```

---

### ME-03 — Ücretsiz katman kotası + çarpan retry'lar tek tanıyı tüketebiliyor [RUNTIME]

**Kanıt (canlı):**
```
429 ... "quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier", "quotaValue": "20"
```
- `model_gateway.py:165` — Pydantic AI `retries=2`
- OpenAI SDK varsayılanı `max_retries: 2`

**Sorun:** Günlük limit model başına 20 istek. Diagnostic 4 agent node çalıştırıyor; en kötü durumda tek node 3 (SDK) × 3 (agent) = 9 istek üretebilir. Yani tek bir tam tanı günlük kotanın tamamını tüketebilir. Hiçbir yerde 429/`RetryInfo` işlenmiyor, kullanıcıya "kota doldu, X saniye sonra" mesajı gitmiyor.

**Çözüm önerisi:** 429 ayrı hata sınıfı olarak ele alınıp `retryDelay` kullanıcıya iletilmeli; SDK retry'ı 0'a çekilip retry tek katmanda tutulmalı; kapasite/faturalandırma gereksinimi deployment manifest'ine yazılmalı (ADR-0012 "capacity policy" maddesi doldurulmamış).

**Doğrulama adımı:** Tanı çalıştırıp `docker logs` üzerinden sağlayıcıya giden istek sayısını sayın; tek node için 1-2 olmalı.

---

### ME-04 — Onboarding gate yalnız `dashboard` görünümünde uygulanıyor [STATİK]

**Kanıt:** [apps/web/src/App.tsx:114](apps/web/src/App.tsx#L114)
```tsx
if (view === "setup" || (!setupStatus.setup_completed && view === "dashboard")) {
```

**Sorun:** `setup_completed === false` iken `#workflow`, `#sources`, `#settings` hash'leriyle uygulama kabuğu tamamen açılıyor. ADR-0017 Karar 3 "full-screen onboarding gate when `setup_completed` is `false`" ile çelişiyor. Kullanıcı yarım kurulumla Workflow Editor'a girip publish deneyebiliyor.

**Çözüm önerisi:** Koşul `view === "setup" || !setupStatus.setup_completed` hâline getirilmeli.

**Doğrulama adımı:** Temiz DB ile `http://localhost:8080/#workflow` adresine gidin; wizard'a yönlenmesi beklenir.

---

### ME-05 — Wizard ara adımları hiçbir şey persist etmiyor [STATİK]

**Kanıt:** `SetupWizard.tsx:388`, `:844`, `:899` — `onClick={() => setActiveStep(N)}`. `saveSetupProgress` yalnız `:141` (üst stepper) ve `:923` (final) çağrılıyor.

**Sorun:** Normal ileri akıştaki "Sonraki Adım" butonları hiçbir ara kaydetme yapmıyor. Adım 1'deki şirket bilgileri, Adım 2'deki model seçimi, Adım 3'teki sekme seçimi sayfa yenilendiğinde kayboluyor. Yalnız üstteki numaralı stepper'a tıklayan kullanıcı kaydetmiş oluyor — keşfedilemez davranış. `IMPLEMENTATION_STATUS.md:69`'un "ensured UI state survives refresh" iddiası doğrulanamıyor.

**Çözüm önerisi:** Her geçişte tek bir merkezî `persistProgress()` çağrılmalı; kaydetme hatası görünür olmalı ve geçişi bloklamalı.

**Doğrulama adımı:** Adım 1'de şirket adını değiştirip "Sonraki Adım"a basın → F5 → alanın sıfırlandığını gözleyin.

---

### ME-06 — `/api/models/discover` rol denetimsiz ve başarısız keşfi "dinamik" etiketliyor [STATİK]

**Kanıt:**
- [apps/api/agi_server/main.py:372-380](apps/api/agi_server/main.py#L372) — `require_role` **yok** (kardeş `probe`/`configure` endpoint'leri admin istiyor)
- `main.py:379-380` — key verilmezse sunucunun kendi key'ini kullanıyor
- `main.py:398-399` — `except Exception: pass`
- `main.py:423` — `"dynamic": len(discovered_models) > 0 and provider == "gemini" and bool(api_key)`

**Sorun:** Üç ayrı sorun: (1) `cloud_models_enabled=False` iken bile dışarı çıkıyor; (2) admin olmayan oturumlu kullanıcı tetikleyebiliyor; (3) HTTP çağrısı patlarsa statik fallback devreye girip `dynamic: true` dönüyor — UI'ya "senin key'inle dinamik keşfedildi" yalanı söyleniyor. Geçersiz key ile bile "keşif başarılı" görünüyor.

**Çözüm önerisi:** `require_role("admin")` eklenmeli; sunucu key'ine sessiz fallback kaldırılmalı; `dynamic` yalnız gerçek 200 yanıtından model çıkarıldığında `true` olmalı; yakalanan hata içerik-güvenli bir `discovery_error` alanında dönmeli.

**Doğrulama adımı:**
```bash
curl -X POST http://localhost:8080/api/models/discover -d '{"provider":"gemini","api_key":"INVALID"}' -H 'content-type: application/json'
```
`dynamic: false` ve bir hata sinyali beklenir.

---

### ME-07 — Model keşfi her tuş vuruşunda tetikleniyor; kısmi API key'ler dışarı gidiyor [STATİK]

**Kanıt:** [apps/web/src/features/setup/SetupWizard.tsx:160-176](apps/web/src/features/setup/SetupWizard.tsx#L160) — `useEffect(..., [selectedProvider, apiKey])`, debounce yok, `AbortController` yok, hatalar `.catch(() => {})` ile yutuluyor. Backend `main.py:385-387` anahtarı **URL query string'inde** gönderiyor.

**Sorun:** 40 karakterlik bir key elle yazıldığında ~40 ayrı outbound istek üretiliyor; her biri kısmi/geçersiz anahtarı query string içinde sağlayıcıya gönderiyor. Kota tüketimi (ME-03 ile birleşince ciddi), rate-limit riski ve yarış koşulu.

**Çözüm önerisi:** 500-800 ms debounce + minimum uzunluk eşiği + `AbortController`. Anahtar query string yerine `x-goog-api-key` header'ı ile gönderilmeli.

**Doğrulama adımı:** DevTools Network sekmesinde Adım 2'de key alanına 10 karakter yazıp istek sayısını sayın.

---

### ME-08 — `qmd` varsayılan compose'da yok ama URL her zaman set [STATİK + runtime gözlem]

**Kanıt:** `docker-compose.yml:16` — `AGI_QMD_URL: http://qmd:8181`; `docker-compose.yml:66-67` — `qmd: profiles: [search]`. Gözlenen: `/api/health` → `"qmd":"unavailable; lexical fallback active"`.

**Sorun:** Varsayılan `docker compose up` ile qmd hiç başlamaz, ama URL set olduğu için health kalıcı "unavailable" der ve her çağrıda boşa 1 sn timeout harcanır. `knowledge_search` sessizce lexical fallback'e düşer — tanı kalitesi düşer ve kullanıcıya bildirilmez. Ayrıca `IMPLEMENTATION_STATUS.md:20`'nin "ChromaDB / QMD vector retrieval **active**" iddiası varsayılan kurulumda geçerli değil.

**Çözüm önerisi:** `AGI_QMD_URL: ${AGI_QMD_URL:-}` yapılmalı veya `qmd` varsayılan servise alınmalı. Fallback durumu run çıktısında görünür uyarı olarak taşınmalı.

**Doğrulama adımı:** `curl -s localhost:8080/api/health` → `"disabled; lexical fallback active"` beklenir.

---

### ME-09 — LangGraph "StateGraph" gerçek koşullu kenar ve checkpointer kullanmıyor [STATİK]

**Kanıt:** [apps/api/agi_server/workflow/langgraph_runtime.py:76-82](apps/api/agi_server/workflow/langgraph_runtime.py#L76) — topolojik sıralamanın **doğrusal zinciri** kuruluyor; `add_conditional_edges` yok, `interrupt_before/after` yok, `compile()` **checkpointer'sız**. Koşullu dallanma `state_data["_active_edges"]` + `status="skipped"` ile emüle ediliyor.

**Sorun:** `SYSTEM_ARCHITECTURE.md:112` bu satırı "Phase 2-3 Completed" olarak işaretlerken hedef sütununda "Native LangGraph engine with PostgreSQL checkpointer" yazıyor; `IMPLEMENTATION_STATUS.md:48` ise dürüstçe "native Postgres checkpointers will be enabled in subsequent phases" diyor. İki doküman çelişiyor.

**Çözüm önerisi:** Ya `AsyncPostgresSaver` + `add_conditional_edges` + `interrupt_before` ile gerçek LangGraph semantiğine geçilmeli, ya da `SYSTEM_ARCHITECTURE.md` tablosu "checkpointer hariç" olarak düzeltilip ADR eklenmeli.

**Doğrulama adımı:**
```bash
uv run python -c "from agi_server.workflow.langgraph_runtime import build_langgraph_workflow; g=build_langgraph_workflow(); print(g.checkpointer)"
```
Bugün `None` döner.

---

### ME-10 — LangGraph motorunda kapsam dışı hatalar run'ı "running" bırakıyor [STATİK]

**Kanıt:** `langgraph_runtime.py:129-131` (approval dalı) ve `:56-58` (constructor) — failure handling yalnız `:155-181` arasındaki `_execute_node` çağrısını sarıyor.

**Sorun:** Approval dalında veya constructor'da oluşan exception'lar `run.status = "failed"` yazmadan yukarı fırlar; `start_persisted_workflow` run satırını zaten commit ettiği için DB'de **zombi "running" run** kalır. `workflow_run_retry` yalnız terminal durumları kabul ettiğinden retry edilemez ve frontend saatlerce poll eder. Fallback custom runtime'da tüm gövde `try/except` içinde — iki motor tutarsız.

**Çözüm önerisi:** `execute_workflow` baştan sona tek `try/except` ile sarılmalı; exception'da run `failed` + içerik-güvenli `error_json` ile kapatılmalı.

**Doğrulama adımı:** Approval dalında hata üreten bir workflow publish/run edin; `GET /api/runs/{id}` kalıcı `running` gösterir.

---

### ME-11 — `validate_workflow_bindings` pinlenmiş agent versiyonunu sessizce değiştiriyor [STATİK]

**Kanıt:** [apps/api/agi_server/workflow/registry_service.py:203-213](apps/api/agi_server/workflow/registry_service.py#L203) — istenen versiyon yok/yayınlanmamışsa en son published'a düşüyor; `:228-230` definition'ı yeniden pinliyor.

**Sorun:** ADR-0008 "pins the exact four agent versions" diyor. Bu fallback operatöre uyarı vermeden versiyon düşürüyor; audit'te de fark görünmüyor. Bir agent v4'e klonlanıp v3 geri çekildiğinde workflow farkında olmadan v4 ile çalışır ve golden evaluation geçerliliği sessizce bozulur.

**Çözüm önerisi:** Fallback yalnız `agent_version` hiç verilmemişse veya açık bir bayrakla uygulanmalı; aksi hâlde 422. Devreye girdiğinde audit event + yanıt içinde uyarı dönmeli.

**Doğrulama adımı:** `company-analyst` v3'ü `archived` yapıp workflow publish edin; `agent_version`'ın uyarısız değiştiğini gözleyin.

---

### ME-12 — Publish sırasında model profili **kullanılabilirliği** doğrulanmıyor [STATİK]

**Kanıt:** `registry_service.py:225-227` — yalnız string allowlist kontrolü; `resolve_model_profile` çağrılmıyor.

**Sorun:** ADR-0008 "verifies … model-profile availability" diyor. `cloud-balanced` seçili bir workflow, cloud opt-in kapalıyken sorunsuz publish edilir; hata ancak run sırasında ortaya çıkar ve BLK-06 nedeniyle generic 409 olarak maskelenir.

**Çözüm önerisi:** `validate_workflow_bindings` içinde `resolve_model_profile(profile, settings)` çağrılıp `PermissionError`/`ValueError` issue olarak toplanmalı (422).

**Doğrulama adımı:** `AGI_CLOUD_MODELS_ENABLED=false` iken bir node'u `cloud-balanced` yapıp publish edin; bugün 200 döner.

---

### ME-13 — Trigger kuralları var olmayan workflow'lara işaret ediyor; event yanlış "triggered" işaretleniyor [STATİK + kod doğrulandı]

**Kanıt:**
- `apps/api/agi_server/workflow/triggers.py:23,33,40,50` — `builtin-crm-erp-hygiene`, `builtin-inbound-triage`, `builtin-competitive-battlecard`, `builtin-lead-discovery`
- `apps/api/agi_server/workflow/default.py:140` — seed edilen tek workflow: `builtin-growth-diagnostic`
- `apps/api/agi_server/workflow/events.py:52,57` — dispatch `skipped` olsa bile inbox `triggered` yazılıyor
- UI bunu "⚡ Workflow Tetiklendi" gösteriyor (`EventPanel.tsx:178`)

**Sorun:** Dört kuralın dördü de var olmayan workflow ID'lerine bakıyor; kullanıcı hiç çalışmamış bir akış için başarı görüyor. `IMPLEMENTATION_STATUS.md:22`'nin "executing strictly published workflow versions" iddiası karşılanmıyor.

**Çözüm önerisi:** Inbox statüsü dispatch sonuçlarından türetilmeli (`triggered` yalnız en az bir `queued` varsa); kurallar var olan published workflow'lara bağlanmalı veya devre dışı seed edilmeli.

**Doğrulama adımı:** `POST /api/webhooks/src-crm-001` ile `crm.account_updated` gönderin; `EventInbox.status` `no_match` olmalı.

---

### ME-14 — Workflow şablonları `WorkflowDefinition` sözleşmesine uymuyor [STATİK]

**Kanıt:**
- `apps/api/agi_server/workflow/templates.py:17-32` — node şekli `{"id","type":"customNode","position","data":{...}}`
- `apps/web/src/api.ts:127` — `WorkflowDefinition[]` olarak tiplenmiş
- `WorkflowEditor.tsx:103-115` — üst seviye `node.kind`/`node.label`/`node.config` okuyor
- `validator.py:24-28`, `:150-162` — trigger + report_output + approval zorunlu; şablonlarda yok

**Sorun:** `executable: true` işaretli şablonların hiçbiri validator'dan geçemez ve editöre bozuk yükleniyor (`data.config === undefined` → Inspector'da TypeError riski, `"Taslak vundefined yüklendi"`). `IMPLEMENTATION_STATUS.md:39`'un "explicit executable vs catalog-only template metadata" iddiası karşılanmıyor.

**Çözüm önerisi:** Şablonlar gerçek `WorkflowDefinition` şemasına taşınmalı ve `/api/workflows/templates` yanıtı bu şemayla doğrulanmalı; geçmeyen şablon `executable: false` işaretlenmeli.

**Doğrulama adımı:**
```bash
uv run python -c "from agi_server.workflow.templates import get_executable_templates; from agi_server.workflow.models import WorkflowDefinition; [WorkflowDefinition.model_validate(t) for t in get_executable_templates()]"
```
Bugün `ValidationError` verir.

---

### ME-15 — İki capability registry'si birbirini doğrulamıyor [STATİK]

**Kanıt:**
- `agents/specs/growth-opportunity-analyst.yaml:9-10` — `demo_crm.read`, `erp_file.read`
- `agents/capabilities.py:16-94` — bu iki ID **yok** (orada `crm.read`, `erp.read` var)
- `registry_service.py:45-61` — YAML'daki **her** ID'yi DB'ye `{"implementation": "code-defined", "allowlisted": True}` etiketiyle yazıyor
- `capabilities.py:97-107` — `list_capabilities()` hiçbir yerde çağrılmıyor

**Sorun:** Kod karşılığı olmayan capability'ler "code-defined allowlisted" olarak API'den yayınlanıyor ve `for_spec`'te sessizce yok sayılıyor; buna karşılık gerçek kod-tanımlı `web.scrape`, `crm.read`, `erp.read` DB'ye hiç girmediği için `save_agent_draft` bunları reddediyor. ADR-0016 Faz 5 "tek code-defined allowlist registry" kararına aykırı.

**Çözüm önerisi:** Capability seeding **yalnızca** `BUILTIN_CAPABILITIES` üzerinden yapılmalı; `ManagedAgentSpec.capabilities` için `BUILTIN_CAPABILITIES` üyeliği Pydantic validator'ı eklenmeli (bozuk YAML startup'ta fail-fast olsun).

**Doğrulama adımı:**
```bash
uv run python -c "from agi_server.agents.registry import AgentRegistry; from agi_server.agents.capabilities import BUILTIN_CAPABILITIES; print(sorted({c for s in AgentRegistry().list() for c in s.capabilities} - set(BUILTIN_CAPABILITIES)))"
```
Bugün `['demo_crm.read', 'erp_file.read']` döner.

---

### ME-16 — `ensure_platform_registry` GET endpoint'lerinde yazma + commit yapıyor [STATİK]

**Kanıt:** `registry_service.py:28-42` (read-then-insert/update) + `:80` `db.commit()`; çağrıldığı GET'ler: `main.py:1743`, `:1879`, `:1901`, `:1910`.

**Sorun:** (a) İdempotent olmayan `SELECT`+`INSERT` deseni PostgreSQL'de eş zamanlı iki GET'te `IntegrityError` → 500 üretebilir; (b) her GET dört agent + workflow satırının `definition` JSON'unu yeniden yazıyor (gereksiz yazma, audit izlenebilirliğinin bozulması); (c) manuel arşivlenen bir built-in agent bir sonraki GET'te sessizce `published` yapılıyor.

**Çözüm önerisi:** Seeding yalnız `lifespan` ve migration'a taşınmalı, GET'lerden kaldırılmalı. Yazma gerekiyorsa `INSERT ... ON CONFLICT DO UPDATE` + advisory lock kullanılmalı.

**Doğrulama adımı:**
```bash
for i in $(seq 1 20); do curl -s -o /dev/null http://localhost:8080/api/agents & done; wait
```
Loglarda `IntegrityError`/500 arayın.

---

### ME-17 — Web Scraping paneli hiçbir API çağırmıyor [STATİK + kod doğrulandı]

**Kanıt:** `apps/web/src/features/scraping/WebScrapingPanel.tsx` — dosyada `api.` çağrısı sayısı **0**; `api` importu bile yok. Panel "Runtime Capability Status: Allowlisted Read-Only Web Scraping" diyor, Sidebar'da ana menü öğesi (`Sidebar.tsx:20`).

**Sorun:** Tamamen statik JSX bir yeteneği "aktif" gibi anlatıyor; `web.scrape` handler'ı zaten fixture (HI-05) ve hiçbir published agent spec'i bu capability'yi içermiyor. AGENTS.md "A UI control is not complete until it calls a real API" ihlali.

**Çözüm önerisi:** Panel `/api/capabilities` üzerinden `web.scrape` statüsünü okuyup gerçek durumu göstermeli, veya menüden kaldırılmalı.

**Doğrulama adımı:** `rg "api\." apps/web/src/features/scraping/WebScrapingPanel.tsx` en az bir çağrı göstermeli.

---

### ME-18 — Kurulum sihirbazında sentetik "42 kayıt" metni [STATİK + kod doğrulandı]

**Kanıt:** [apps/web/src/features/setup/SetupWizard.tsx:210](apps/web/src/features/setup/SetupWizard.tsx#L210)
```tsx
setSyncDetails(`${res.records_persisted || 42} kayıt OKF Wiki & RAG koleksiyonuna yüklendi.`);
```

**Sorun:** Backend 0 kayıt döndürürse UI "42 kayıt yüklendi" yazıyor — açık bir placeholder. Ayrıca `/api/setup/demo` aktif OKF bundle'ını değiştirmiyor; `status="pending"` bir candidate yaratıyor (ADR-0007 gereği **doğru** davranış) ama UI "RAG koleksiyonuna yüklendi" diyerek yanlış anlatıyor ve candidate onayı gerektiğini hiç söylemiyor. `IMPLEMENTATION_STATUS.md:69`'un "without synthetic success text" iddiasıyla çelişiyor.

**Çözüm önerisi:** `|| 42` kaldırılmalı; metin gerçeğe uydurulmalı ("N kayıt ingest edildi; OKF candidate `<id>` onay bekliyor") ve wizard'a candidate onayı için yönlendirme eklenmeli.

**Doğrulama adımı:** `POST /api/setup/demo` sonrası `GET /api/okf/candidates` → `status: "pending"`.

---

### ME-19 — `ExecutionContext` üretim yolunda ölü kod [STATİK]

**Kanıt:** `langgraph_runtime.py:219-227` context oluşturup state'e koyuyor, ancak `run_managed_agent(..., execution_context=...)` hiçbir üretim çağrısında geçirilmiyor. `context.py:29-53`'teki `validate_privacy_boundary` ve `sanitize_for_prompt` yalnız testlerde çalışıyor; `context_budget`, `retrieval_references` hiç doldurulmuyor.

**Sorun:** `IMPLEMENTATION_STATUS.md:32` bunu "enforcing … fail-closed privacy boundary validation across LangGraph short-term memory" diye tarif ediyor. Eşdeğer bir sınır `enforce_cloud_data_policy` ile ayrıca uygulandığı için güvenlik açığı değil, ancak **belge iddiası yanlış**.

**Çözüm önerisi:** Ya `execution_context` agent çağrı yoluna bağlanmalı ve context budget prompt boyutlandırmasında kullanılmalı, ya da status metni "prepared but not enforced" olarak düzeltilmeli.

**Doğrulama adımı:** `rg "execution_context=" apps/api/agi_server` en az bir üretim çağrısı göstermeli.

---

### ME-20 — `knowledge.search` capability'si vektör aramayı kullanmıyor [STATİK]

**Kanıt:** `capabilities.py:20` açıklaması "Searches active OKF wiki concepts **and vector embeddings**"; handler ise saf lexical `str.count` sayımı yapıyor ([runtime.py:104-122](apps/api/agi_server/agents/runtime.py#L104)). `KnowledgeSearch` (qmd/vector) yalnız `/api/knowledge` endpoint'inde kullanılıyor. Fallback locator'ları (`ev_concept_...`, `okf/search.py:74`) `evidence_items` tablosunda karşılığı olmayan sentetik ID'ler.

**Sorun:** Capability açıklaması yanlış; `IMPLEMENTATION_STATUS.md:20`'nin "`ev_...` locator provenance" ifadesi bu yüzden yanıltıcı — üretilen bazı locator'lar çözümlenemiyor.

**Çözüm önerisi:** Agent `search_knowledge` handler'ı `KnowledgeSearch` üzerinden geçirilmeli; gerçek `EvidenceItem` ID'sine çözülemeyen locator alanı `null` bırakılmalı, sahte `ev_` öneki üretilmemeli.

**Doğrulama adımı:** `/api/evidence/{locator}` ile arama sonucundaki her locator 200 dönmeli veya alan boş olmalı.

---

## 4. LOW Bulgular

| ID | Bulgu | Kanıt | Öneri |
|---|---|---|---|
| LO-01 | `.env`'de ADR-0020'nin kaldırılmasını kararlaştırdığı artıklar geri gelmiş (`AGI_ENABLE_DBOS`, `GEMINI_API_KEY`, `GEMINI_MODEL_NAME`) | `.env:11,21-22` vs `docs/adr/0020-*.md:21` | `.env`'i `.env.example` ile hizala; `Settings`'e `extra="forbid"` düşün |
| LO-02 | Canlı API key 4 ayrı konumda düz metin (`.env` ×2, `.secrets` ×2). Git geçmişine **sızmamış** (`git log -S` temiz) | `.env:20-21`, `.secrets/` | Tek kaynağa indir; anahtarı rotasyona sok |
| LO-03 | `/api/health` `mode` alanı sabit `"local-first"`, `postgres` bileşen adı SQLite'ta da "postgres" | [main.py:250](apps/api/agi_server/main.py#L250), `:222` | Gerçek profil ve DB türünden türet |
| LO-04 | İkinci, yönetişimsiz LLM yolu: `ai_agent/models.py` doğrudan `GEMINI_API_KEY` okuyor, yoksa sessizce `TestModel()` dönüyor | `apps/services/ai-agent/ai_agent/models.py:20-35` | Legacy paketi kaldır veya Model Gateway'e delege et |
| LO-05 | `apps/services/ai-agent/ai_agent/tools/web_scraper.py` gerçek dış HTTP GET yapıyor, egress/policy kontrolü yok (baseline'a bağlı değil ama repoda duruyor) | `web_scraper.py:1-33` | ADR-0016 Faz 5 "pruning" kararını uygula |
| LO-06 | `durable_*` DBOS kalıntıları ölü kod; `durable_persisted_workflow` beklemek yerine approval'ı **anında expire** ediyor | `persistent_runtime.py:609-620` | Kaldır; ADR-0022'yi güncelle |
| LO-07 | `policy_check` node'u koşulsuz `"passed"` yazıyor — sahte kapı | `persistent_runtime.py:280-283` | Gerçek değerlendirme bağla veya katalogdan kaldır |
| LO-08 | `NORMALIZE_CONTEXT` / `OKF_COMPILE` / `KNOWLEDGE_SEARCH` node'ları no-op; state'e sabit string yazıp `completed` işaretleniyor | `persistent_runtime.py:268-273` | Gerçek işe bağla veya katalogdan çıkar |
| LO-09 | `SetupProgressUpdate` sınırları hâlâ 10 adımlık eski şemayı yansıtıyor (`ge=0, le=9`, `max_length=10`) | `schemas.py:98-99` | `ge=1, le=5` / `max_length=5` yap |
| LO-10 | `completed_steps` mevcut (tamamlanmamış) adımı da içeriyor | `SetupWizard.tsx:142-143` | `[1..step-1]` olmalı |
| LO-11 | `source_mode` MCP ve canlı DB seçimlerini "file-upload" olarak kaydediyor | `SetupWizard.tsx:151`, `main.py:755-757` | Enum'u gerçek konektör tiplerini kapsayacak şekilde genişlet |
| LO-12 | Workflow Editor açılışı her seferinde yeni draft versiyon üretiyor (sınırsız versiyon büyümesi) | `WorkflowEditor.tsx:335` | Otomatik klonlamayı kaldır; mevcut draft varsa onu aç |
| LO-13 | `verify-no-egress` iddia ettiği şeyi doğrulamıyor (proxy 403'ünü "ağ izole" sanıyor) | `scripts/verify-no-egress.ps1` | Proxy'siz doğrudan bağlantı testi + allowlist testi ayrı yapılmalı |
| LO-14 | `egress-gateway` healthcheck'i ve `app` bağımlılığı yok | `docker-compose.yml:86-90` | `depends_on` + TCP healthcheck ekle |
| LO-15 | Yalnız `analyst` rolündeki kullanıcı ilk tanıyı çalıştıramıyor (publish `admin` istiyor) | `main.py:2103` vs `:868` | Onboarding sonunda otomatik publish veya akışı düzelt |
| LO-16 | Kullanılmayan agent sözleşmeleri mimari dokümanda aktif node gibi çiziliyor | `contracts.py:51-96` vs `SYSTEM_ARCHITECTURE.md:81-90` | "planned" olarak işaretle veya devreye al |
| LO-17 | Wizard'da "ilk tanıyı başlat" affordance'ı yok; tek giriş Dashboard boş-durum ekranı | `SetupWizard.tsx:955`, `Dashboard.tsx:178` | Adım 5'e birincil "İlk tanıyı çalıştır" butonu ekle |
| LO-18 | Dashboard yenilendiğinde devam eden run'ı fark etmiyor; kullanıcı ikinci run başlatabiliyor | `Dashboard.tsx:145`, `main.py:851-857` | Mount'ta `running` run'ı çekip poll'a devam et |

---

## 5. PRD ↔ Kod Uyum Tablosu

| PRD Bileşeni | Durum | Kanıt / Not |
|---|---|---|
| 6.1 Growth Context Graph | **KISMİ** | Jenerik graf altyapısı gerçek (`db.py:138-163`, subject/predicate/object + `evidence_ids`). Ancak yalnız 7 entity tipi ve tek sentetik konektörden (`connectors/demo.py:6-13`). PRD'nin 25 varlığından Lead, Customer, Campaign, Channel, Competitor, Event, Conversation, Call, Email, Social Interaction, Proposal, Consent Record, Recommendation, Agent Action **yok**. |
| 6.2 Evidence & Provenance | **KISMİ** | Immutable snapshot + content-addressed locator + excerpt-hash doğrulaması **güçlü ve gerçek** (`ingestion/service.py:171-197`, `:272-340`). Deterministik metrik makbuzu gerçek (`domain/metrics.py:85-125`). **Eksik:** kaynak güven skoru, alternatif yorumlar; ayrıca ME-20'deki çözümlenemeyen sentetik locator'lar. |
| 6.3 Policy Engine | **YOK** | Tek `policy_check` node'u koşulsuz `"passed"` (LO-07). PRD 6.3'ün 12 alanının hiçbiri değerlendirilmiyor. Komşu ilkeller var: RBAC (`security.py:169-177`), veri sınıflandırma sınırı (`runtime.py:78-85`). |
| 6.4 Consent Ledger | **YOK** | `rg -i "consent" apps/api/agi_server` → 0 sonuç. Tablo/model/endpoint/UI yok. |
| 6.5 Agent Registry | **KISMİ** | VAR: ad, versiyon, model tercihi, çıktı türü, risk seviyesi, capability'ler. **YOK:** açıklama, veri kaynakları, connectorlar, çalışabileceği workflowlar, işlem limiti, prompt template versiyonu, audit seviyesi, başarı metrikleri. PRD'de örnek 20 agent; kodda 4 spec. |
| 6.6 Workflow Orchestrator | **KISMİ** | Versiyonlama, audit, run history, approval, idempotency **gerçek ve sağlam**. Eksik: retry yönetimi, rollback, connector health, risk bazlı durdurma. ME-09/ME-10 ayrıca geçerli. |
| 6.7 Model Gateway | **KISMİ** | Provider seçimi, local/cloud opt-in, Pydantic output validation, sensitive-data masking gerçek. Eksik: prompt versiyonlama, model fallback, latency takibi, cache. BLK-04/BLK-05 aktif arızalar. |
| 6.8 Connector Layer | **KISMİ/YOK** | Çalışan tek yol CSV/XLSX yükleme (`main.py:1203-1403`). `ReadOnlyCRM/ERPConnector` hiçbir üretim yolundan çağrılmıyor. MCP gateway ürüne bağlı değil (`rg "MCPGateway"` → yalnız test + tanım); varsayılan transport fixture (`mcp.py:76-80`); MCP protokol bağımlılığı `pyproject.toml`'da yok. |
| 8 Approval Center | **KISMİ** | Gerçek onay akışı ve idempotent expire semantiği var. Ancak **tek onay türü** `okf-candidate-merge`. PRD 8'in hedef kişi/kanal/kanıt/risk/consent/etki/alternatif alanları modelde yok (`db.py:267-283`). |
| 12 Raporlama | **YOK/KISMİ** | 15 rapor türünden yalnız tek "Growth Diagnostic" artefaktı. |
| 13 Observability | **KISMİ** | İçerik-güvenli OTLP middleware gerçek ve doğru (`observability.py:41-86`) — yalnız HTTP metrikleri. Agent decision trace, model response trace, connector error rate, approval waiting time, policy violation ölçülmüyor. Langfuse entegrasyonu target spec. |
| 7.2–7.19 (Lead Discovery, Enrichment, Signal Fusion, Outbound, Inbound, Voice, Competitive Intel, Battlecard, Attribution, AEO, CRM Hygiene, ERP Insight, Event Intel) | **YOK** | Yalnız isim düzeyinde yer tutucular: şablon metinleri (`templates.py`), fixture handler'lar (`runtime.py:151-172`), kullanılmayan sözleşmeler (`contracts.py:51-96`). |

**Özet yargı:** Ürün bugünkü hâliyle bir "Agentic Growth Operating System" değil; **tek bir sentetik B2B veri seti üzerinde kanıta bağlı fırsat raporu üreten, onay kapılı bir OKF bilgi yönetim aracıdır.** Kendini tanımladığı dört çekirdekten ikisi (Policy Engine, Consent Ledger) hiç yok, üçüncüsü (Approval Center) yalnız tek tür bilgi-onayı olarak var, dördüncüsü (Growth Context Graph) tek demo şirkete kilitli.

---

## 6. `docs/IMPLEMENTATION_STATUS.md` — Doğrulanamayan İddialar

| Satır | İddia | Karşı-kanıt |
|---|---|---|
| `:13` | "…canonical entities, users, accounts, **leads**, evidence items…" | `leads` entity tipi hiç üretilmiyor (`connectors/demo.py:6-13`) |
| `:17` | "Read-Only CRM/ERP connector layer **ingesting** Accounts, Leads, Opportunities, Invoices, Products" | Sınıflar yalnız testlerde; hiçbir endpoint/UI/workflow çağırmıyor (`connectors/crm_erp.py:12,81`) |
| `:20` | "ChromaDB / QMD vector retrieval **integration** … `ev_...` locator provenance" | `qmd` varsayılan compose'da yok (ME-08); agent tool'u vektör aramayı hiç kullanmıyor (ME-20); fallback locator'lar çözümlenemiyor; `rag_service` aynı belgenin `:52` satırında "unintegrated legacy" ilan ediliyor |
| `:21` | "MCP Client Gateway … **operating** strictly on approved profiles" | Hiçbir üretim çağrısı yok; profil seed'i yok; transport fixture; MCP bağımlılığı yok |
| `:22` | "…matching approved trigger rules, and **executing** strictly published workflow versions" | 4 kuralın 4'ü de var olmayan workflow ID'lerine bakıyor (ME-13) |
| `:32` | "`ExecutionContext` … **enforcing** … across LangGraph short-term memory" | `execution_context` hiçbir agent çağrısına geçirilmiyor (ME-19) |
| `:33` | "…workflow node scopes strictly narrowing…" | Üretimde `capability_allowlist=frozenset()` — daraltma hiç uygulanmıyor (HI-06); iki registry uyuşmuyor (ME-15) |
| `:37` | "Onboarding Setup Wizard … CRM/ERP Connectors" | Connector adımı sahte "connected" gösteriyor (HI-04); girilen şirket profili kullanılmıyor (HI-08) |
| `:39` | "…explicit **executable** vs catalog-only template metadata" | `executable: true` şablonların hiçbiri validator'dan geçemez (ME-14) |
| `:69` (Faz 12) | "…**without synthetic success text or mock execution**" | `|| 42` fallback'i duruyor (ME-18); `test-db`/`test-mcp` mock yanıtları başarı olarak gösteriliyor (HI-04) |
| `:70` (Faz 13) | "Removed synthetic mock … **fake percentage bars**" | Dashboard'da veriye dayanmayan ✓ tamamlanma işaretleri kaldı (HI-08) |
| `:77` (Faz 20) | "finalized **100% resolution** of all 32 technical audit report findings" | Yukarıdaki tüm açık bulgular |
| `:78-79` (Faz 21/23) | Registry binding düzeltmeleri | Kök neden paketleme (BLK-02); düzeltmeler semptomu tedavi etmiş ve asıl paketleme düzeltmesi **commit edilmemiş** |

**Doğru bulunan iddialar** (karşı-kanıt yok): `:11`, `:12`, `:18`, `:19`, `:26`, `:27`, `:28`, `:29`, `:30`, `:31`, `:38`, `:40` ve `:48-52` "Current Architecture Gaps" bölümünün büyük kısmı.

---

## 7. Doğru Çalıştığı Doğrulanan Noktalar (regresyon riski — korunmalı)

- **Agent hattı model çağrısı başarılı olduğunda gerçekten çalışıyor.** `gemini-3.1-flash-lite` ile `company-analyst` geçerli, evidence ID'lerine bağlı, şemaya uygun `CompanyAnalysis` üretti (699 output token). [RUNTIME]
- **Gemini Bearer auth doğru.** `OpenAIProvider` → `Authorization: Bearer`. ADR-0017 kararı koda uymuş. [RUNTIME]
- **Egress zinciri çalışıyor ve güvenli.** `app` yalnız `core`'da (internal), `egress-gateway` çift ağlı köprü; squid allowlist'i `.generativelanguage.googleapis.com` içeriyor; `httpx` `trust_env` ile proxy'yi onurlandırıyor. **Not:** `docs/adr/0018-*.md:16` "app'i core VE egress'e bağladık" diyor — kod bunu yapmıyor; **ADR yanlış, kod daha güvenli.** Supersede eden ADR yazılmalı. [RUNTIME]
- **Alembic migration bütünlüğü tam.** 22 SQLAlchemy tablosunun 22'sinin de migration karşılığı var; temiz DB'de 9 migration sorunsuz uygulandı. [RUNTIME]
- **Evidence gate fail-closed.** Uydurma evidence ID'si, eksik karar veya `supported=False` run'ı düşürüyor (`diagnostics/service.py:385-400`); `report` node'u gate'ten önce artifact yazmıyor. [STATİK]
- **Approval pause/resume aynı run ID üzerinde gerçekten devam ediyor** (`persistent_runtime.py:754-763`; test: `test_langgraph_default_workflow.py:100-101`). [STATİK]
- **Idempotency çalışıyor** (`start_persisted_workflow:632-634` + `ux_step_run_sequence` unique index). [STATİK]
- **Cloud opt-in fail-closed kapısı ve veri sınıflandırma sınırı doğru** (`model_gateway.py:81-83`, `enforce_cloud_data_policy`). Üretimde payload ile key kabul etmeme davranışı doğru. [STATİK]
- **Observability içerik-güvenli** — yalnız method/route/status/request_id gönderiliyor (`observability.py:41-86`). [STATİK]
- **Untrusted-data politikası prompt'a doğru gömülü** (`model_gateway.py:29-33`). [STATİK]
- **Çoklu-tenant sızıntısı yok** (`rg -i "tenant"` → 0). **Not:** PRD 9 "Multi tenant isolation" isterken AGENTS.md tek-müşteri kurulumu dayatıyor; bu çatışma bir ADR ile kayda geçmeli — şu an kayıtlı değil.

---

## 8. Önerilen Düzeltme Sırası

**Aşama 1 — İlk tanıyı çalışır hâle getir (zorunlu sıra):**
1. **BLK-06** önce yapılmalı. Loglama olmadan diğerlerinin doğrulanması körlemesine ilerler.
2. **BLK-02** — `pyproject.toml` package-data commit + `importlib.resources` + boş registry'de fail-fast.
3. **BLK-01** — base compose cloud değişken tutarlılığı.
4. **BLK-03** — node `model_profile` çözümleme sırası + Ollama/compose kararı.
5. **BLK-05** — Gemini 3.x tool round-trip (`thought_signature`). Gemini-native model sınıfına geçiş en temiz yol.
6. **BLK-04** — cloud reasoning bütçesi + probe'un temsili hâle getirilmesi.
7. **HI-01** — model downgrade'ini geri al, testleri yeşile döndür.

**Aşama 2 — Yanlış güven üreten yüzeyler (ürün riski):**
8. **HI-04**, **HI-05**, **ME-17**, **ME-18**, **ME-13** — sahte başarı yanıtları ve fixture'ların temizlenmesi.

**Aşama 3 — Belgede "tamamlandı" denen güvenlik/allowlist iddiaları:**
9. **HI-06**, **ME-15**, **ME-12**, **ME-11**, **ME-19**.

**Aşama 4 — Ürünleşme:**
10. **HI-02**, **HI-03**, **HI-08**, **HI-09** — kalıcı konfigürasyon, onboarding tutarlılığı, demo-bağımlılığının kırılması.
11. **HI-07** — asenkron run mimarisi.

**Aşama 5 — PRD çekirdek boşlukları (yeni ADR gerektirir):**
12. Policy Engine ve Consent Ledger için tasarım + ADR. Bunlar PRD'nin ürün tanımının merkezinde; yokluklarının `IMPLEMENTATION_STATUS.md`'de açıkça kayıtlı olması gerekir.

**Her aşamada:** AGENTS.md handoff protokolü gereği `docs/IMPLEMENTATION_STATUS.md` güncellenmeli ve ilgili ADR eklenmeli/supersede edilmeli. Özellikle ADR-0018 (egress topolojisi), ADR-0022/0024 ("100% resolution") ve ADR-004 (6 adımlı onboarding) kod ile uyuşmadığı için düzeltilmeli.

---

## 9. Ek — Reprodüksiyon Referansı

**Belgelenen komutla çökme (BLK-01):**
```bash
docker compose up -d --build
docker compose logs app --tail 20
```

**İzole temiz kurulum testi (mevcut veriye dokunmadan):**
```bash
docker run -d --name agi-audit-fresh -p 8099:8080 -w /tmp \
  -e AGI_DATABASE_URL="sqlite:////tmp/audit.db" \
  -e AGI_BOOTSTRAP_TOKEN="audit-one-time-token-1234567890" \
  -e AGI_SESSION_SECRET="audit-session-secret-at-least-32-chars-long" \
  -e AGI_MASTER_KEY="audit-master-key-at-least-32-characters-long" \
  -e AGI_MODEL_PROFILE=cloud-balanced -e AGI_CLOUD_MODELS_ENABLED=true \
  -e AGI_CLOUD_PROVIDER=gemini -e AGI_CLOUD_MODEL=gemini-3.6-flash \
  -e AGI_CLOUD_API_KEY="<key>" agentic-growth-intelligence-app
```
`-w /tmp` olmadan ME-01 nedeniyle `PermissionError` alınır.

**Thinking token tüketimi (BLK-04):** `max_tokens=900` ile gerçek `CompanyAnalysis` prompt'u gönderin; `finish_reason: "length"`, `completion_tokens: 31`, `total_tokens: 1438` gözlenir.

**Tool round-trip 400'ü (BLK-05):** Modeli 3 paralel tool çağrısına zorlayın, ikinci turda `extra_content` alanını çıkarın → `400 INVALID_ARGUMENT ... thought_signature`. Alan korunduğunda `200`.

---

*Tur 1 sonu. Sonraki denetim turları bu satırın altına eklenmelidir.*
