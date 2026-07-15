# ADR-0002: Pydantic AI ve DBOS kullanımı

- Durum: Accepted
- Tarih: 2026-07-13

## Bağlam

Typed agent çıktıları, model bağımsızlığı ve restart sonrası süren insan onayı gerekir. Kullanıcı
LangGraph yerine Pydantic AI tercih ediyor; tek geliştirici için ayrı queue/worker kümesi istenmiyor.

## Karar

Agent/model/tool sözleşmesi için Pydantic AI 2.x; PostgreSQL-backed durable step, idempotency ve
approval messaging için DBOS kullanılır. Kullanıcı tarafından çizilen DAG, tek bir versioned DBOS
workflow içindeki generic interpreter tarafından çalıştırılır.

## Sonuçlar

Agent'lar typed ve capability-scoped olur; restart/resume daha az altyapıyla sağlanır. DBOS function
determinism ve payload sınırları gözetilir; büyük içerik artifact reference ile taşınır. Workflow DSL
ürünün kendi güvenlik sınırıdır.

## Alternatifler

LangGraph ürün tercihiyle uyuşmaz. Celery/Redis durable approval için ek altyapı ve özel state machine
gerektirir. Temporal ilk MVP için operasyonel olarak ağırdır.

## Amendment — 15 July 2026

The built-in immutable Growth Diagnostic workflow advances to reserved ID
`builtin-growth-diagnostic`, version 2. User clones require a non-reserved target ID. Its durable path
executes Company Analyst, Growth Opportunity Analyst, Evidence Reviewer, and Wiki Curator before
candidate report creation and Approval. Dashboard compatibility consumes this persisted workflow
output, so the release browser path no longer validates a separate synchronous-only result.
