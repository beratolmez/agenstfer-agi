# Agentic Growth Intelligence — MVP Uygulama Planı

Bu plan tek geliştirici, 14–18 hafta ve tek şirketlik self-hosted kurulum varsayar. Faz sırası bir bağımlılık sırasıdır; takvim tahmini kalite kapısını geçersiz kılmaz.

## Çalışma ilkeleri

- Her faz başında giriş koşulları, sonunda otomatik test + demo yapılır.
- Yeni modül yalnız mevcut fazın “done” tanımı karşılandıktan sonra eklenir.
- LLM hesap yapmaz; metrik ve skorlar deterministic koddan gelir.
- Önemli claim evidence olmadan kullanıcıya “doğrulanmış” gösterilmez.
- Agent/prompt/model değişikliği golden eval sonucuyla beraber review edilir.
- Harici sisteme write, MVP connector interface'inde bile yer almaz.

## Teknik backlog sözleşmeleri

### Canonical entity

MVP entity türleri: `Company`, `Account`, `Contact`, `Opportunity`, `Product`, `Campaign`, `Order`, `Invoice`. PostgreSQL tablosu generic entity/fact ilişkisini tutar; OKF concept, taşınabilir anlatısal görünümüdür. İlk sürümde graph database yoktur.

### EvidenceItem

Zorunlu alanlar: `source_id`, `snapshot_sha256`, `locator`, `excerpt_hash`, `collected_at`, `classification`. Locator opaque string değil typed JSON'dur. Claim, bir veya daha çok EvidenceItem ID'si taşır.

### Agent çıktıları

- `CompanyAnalysis`: summary, segments, strengths, weaknesses, data_gaps, claims.
- `OpportunityHypothesis[]`: en fazla 10, evidence IDs, impact inputs, risk.
- `EvidenceReview`: supported/rejected claims, contradiction, stale flag.
- `GrowthDiagnostic`: deterministic top five + plan + coverage.

### Ranking

```text
score = 0.30 * goal_alignment
      + 0.25 * estimated_impact
      + 0.20 * evidence_coverage
      + 0.15 * urgency
      + 0.10 * feasibility
      - risk_penalty
```

Tüm girdiler 0–100 normalize edilir; risk 0–20 puandır. UI bunun olasılık veya model confidence olmadığını açıklar.

## Faz 0 — Belgeler ve kararlar (Hafta 1)

**Giriş:** PRD, `ARCHITECTURE_CONTEXT.md` ve ürün sahibinin MVP kararları mevcut.

**Backlog**

- Yöneticiye sunulabilir mimari, mantıksal/sequence/deployment Mermaid diyagramları.
- MVP sınırı, teknoloji matrisi, risk ve kabul kriterleri.
- Teknik faz planı ve basit sonraki adımlar rehberi.
- OKF/PostgreSQL, Pydantic AI/DBOS, local-first ve no-write ADR'leri.
- Dashboard ve workflow editörü görsel tasarım spesifikasyonu.

**Done:** Yeni geliştirici teknoloji veya kapsam kararı vermeden Faz 1'e başlayabilir; açık sorular ayrı listelenmiştir.

## Faz 1 — Temel platform (Hafta 2–3)

**Giriş:** ADR'ler accepted/proposed olarak kaydedilmiş, referans Linux kapasitesi belli.

**Backlog**

- `uv` Python workspace, React/Vite app, ortak lint/test komutları.
- Compose: app, Postgres, Ollama; healthcheck ve persistent volumes.
- SQLAlchemy schema ve Alembic baseline: users, entities, evidence, workflow, approval, audit.
- Bootstrap token, Argon2id password, role matrix ve audit middleware.
- Model profile config ve Ollama health/structured-output probe.
- Seed generator: belirtilen sayılarda deterministic Anka dataset.

**Testler:** API health, migration up/down, duplicate bootstrap, role denial, seed determinism, model unavailable fallback.

**Done:** Temiz makinede sistem açılır; admin oluşturulur; demo veri sayıları doğrulanır; Ollama yoksa açık degraded status gösterilir.

## Faz 2 — OKF bilgi katmanı (Hafta 4–6)

**Giriş:** Persistent knowledge volume, source/evidence ID sözleşmesi ve classification enum hazır.

**Backlog**

- Immutable raw snapshot + SHA-256 manifest.
- `OKFBundlePort`: parser/writer, unknown metadata preservation, path safety.
- Root index/version, newest-first log, Reference concept ve citation resolver.
- Link/backlink index, orphan/broken-link/metadata quality lint.
- ZIP/tar export/import; archive traversal ve size limitleri.
- qmd CLI adapter: lexical default, hybrid optional, built-in lexical fallback.
- Knowledge Explorer: tree, search, concept, backlinks, source locator, Git diff.

**Testler**

- Parse edilebilir frontmatter ve non-empty `type`.
- Unknown type/nested metadata round-trip.
- Absolute/relative link; broken link warning.
- Reserved index/log biçimi ve ordering.
- Export/import concept/link/metadata equivalence.
- Citation → EvidenceItem → raw locator.
- Malicious ZIP path ve oversized file reddi.

**Done:** Demo source conformant OKF bundle'a dönüşür; archive başka boş bundle'a import edilir; semantik eşdeğerlik korunur.

## Faz 3 — Growth Diagnostic dikey dilimi (Hafta 7–9)

**Giriş:** OKF ve evidence resolver kalite kapısı yeşil; demo adapter özel bypass kullanmıyor.

**Backlog**

- Demo CRM/ERP connector'ları ve canonical mapping.
- Deterministic metric calculator ve altı planted insight oracle'ı.
- Wiki Curator, Company Analyst, Growth Opportunity Analyst, Evidence Reviewer.
- Managed agent spec, model profile, typed result ve capability filter.
- Candidate claims → evidence review → scoring → top five.
- Growth Diagnostic OKF concept, Markdown ve print-ready HTML renderer.
- Golden dataset ve tekrar-run stability ölçümü.

**Agent kalite kapısı**

- Planted insight recall ≥ 5/6.
- Material claim evidence resolution = %100.
- Unsupported numerical claim = 0.
- Structured output success ≥ %95.
- Top-five overlap across runs ≥ %70.
- 9B geçmezse 27B profile; model büyütmeden önce veri/evidence hatası ayıklanır.

**Done:** Tek API/workflow komutuyla kanıtlı rapor ve 30 günlük plan çıkar; her önemli claim source locator açar.

## Faz 4 — Workflow ve Approval (Hafta 10–13)

**Giriş:** Built-in diagnostic düz Python orchestration ile stabil ve idempotent.

**Backlog**

- Agent/Capability Registry ve immutable version.
- Node/edge Pydantic DSL, typed port catalog ve graph validator.
- Static DBOS workflow içinde generic deterministic DAG interpreter.
- Her node durable step; büyük çıktı artifact URI ile saklanır.
- Run idempotency key ve step history.
- Approval node: DBOS `send/recv`, RBAC decision, 7 gün timeout.
- Draft/publish/clone/dry-run REST API.
- React Flow editor: catalog, canvas, inspector, validator, history.

**Testler:** cycle/type mismatch reject; duplicate idempotency; process restart resume; approval restart; reject branch no-merge; qmd fallback.

**Done:** Kullanıcı built-in workflow'u klonlayıp izinli node'larla değiştirir; dry-run yapar; restart demonstrasyonunda son başarılı step'ten devam eder.

## Faz 5 — Ürünleştirme (Hafta 14–16)

**Giriş:** Diagnostic ve workflow kalite kapıları yeşil; UI bilgi mimarisi onaylı.

**Backlog**

- Dashboard, opportunity detail, evidence drawer, approval center.
- 10 adımlı setup wizard ve mapping preview.
- Score feedback/correction; override nedeni audit'e yazılır.
- Türkçe catalog + i18n key mimarisi.
- OTel trace/run correlation; prompt/source body redaction.
- PostgreSQL + knowledge volume backup ve boş kurulum restore script'i.
- Markdown/HTML/OKF archive export.

**Done:** Ürün yöneticisi terminale dönmeden onboarding → diagnostic → citation → approval → export akışını tamamlar; restore drill geçer.

## Faz 6 — Güvenlik ve release (Hafta 17–18)

**Giriş:** Feature freeze; release checklist ve hedef Linux sunucu hazır.

**Backlog**

- Prompt injection fixture ve tool escape denemeleri.
- Markdown HTML XSS, SSRF/private IP/redirect/DNS rebinding.
- CSV formula injection, path traversal, archive bomb ve file limit.
- Secret/prompt/source content log scan ve unexpected egress capture.
- Ollama/qmd/Postgres restart, disk-full ve corrupt snapshot senaryoları.
- Compose image pinning, non-root container, read-only FS uygulanabilirliği.
- Migration/backup/restore/release notes; mimari as-built güncellemesi.

**Done:** Temiz Linux sunucuda nihai demo kabulü eksiksiz; yüksek güvenlik bulgusu yok; rollback ve restore kanıtı mevcut.

## Nihai demo senaryosu

1. `docker compose up --build` sonrası wizard açılır.
2. Bootstrap token ile admin yaratılır ve sentetik şirket seçilir.
3. Adapter preview/mapping gösterilir; OKF bundle üretilir.
4. Growth Diagnostic çalışır; top five ve 30 günlük plan görünür.
5. Citation tıklaması raw snapshot locator'a gider.
6. Candidate wiki diff Approval Center'da onaylanır ve merge edilir.
7. Bundle ZIP olarak export ve boş ortama import edilir.
8. Workflow klonlanır, güvenli node değiştirilir, dry-run geçer.
9. Backup alınır; boş kurulumda restore edilir.

## Definition of Done — her ticket

- Kabul kriteri ve threat/evidence etkisi yazılmıştır.
- Unit/integration testi veya neden test gerekmediği kayıtlıdır.
- Log/trace içinde hassas veri yoktur.
- Migration geriye uyumlu veya release notunda açıkça kırıcıdır.
- Kullanıcı görünür metni Türkçe ve i18n key üzerinden gelir.
- Agent değişikliği varsa eval raporu PR artifact'idir.
- Mimari karar değiştiyse ADR ve diagram güncellenmiştir.

