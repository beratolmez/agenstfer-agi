# ADR-0002: Pydantic AI ve DBOS kullanımı

- Durum: Accepted
- Tarih: 2026-07-13

## Bağlam

Typed agent çıktıları, model bağımsızlığı ve restart sonrası süren insan onayı gerekir. Kullanıcı LangGraph yerine Pydantic AI tercih ediyor; tek geliştirici için ayrı queue/worker kümesi istenmiyor.

## Karar

Agent/model/tool sözleşmesi için Pydantic AI 2.x; Postgres-backed durable step, idempotency ve approval messaging için DBOS kullanılır. Kullanıcı tarafından çizilen DAG, tek bir versioned DBOS workflow içindeki generic interpreter tarafından çalıştırılır.

## Sonuçlar

Agent'lar typed ve capability-scoped olur; restart/resume daha az altyapıyla sağlanır. DBOS fonksiyon determinism ve payload sınırları gözetilir; büyük içerik artifact reference ile taşınır. Workflow DSL ürünün kendi güvenlik sınırıdır.

## Alternatifler

LangGraph ürün tercihiyle uyuşmaz. Celery/Redis durable approval için ek altyapı ve özel state machine gerektirir. Temporal ilk MVP için operasyonel olarak ağırdır.

