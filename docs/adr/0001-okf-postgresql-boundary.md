# ADR-0001: OKF ile PostgreSQL'in sorumluluk sınırı

- Durum: Accepted
- Tarih: 2026-07-13

## Bağlam

Şirket bilgisinin veritabanından bağımsız, Git ile diff edilebilir ve başka sisteme taşınabilir olması isteniyor. Kullanıcı, workflow ve durable state ise transaction, index ve erişim kontrolü gerektiriyor.

## Karar

Bilgi içeriği OKF 0.1 Markdown/YAML bundle'ında; kullanıcı, rol, evidence locator, workflow run, approval, audit ve idempotency PostgreSQL'de tutulur. qmd yalnız bundle'dan yeniden üretilebilir arama indeksidir. OKF adapter sürüm sınırını izole eder.

## Sonuçlar

Bundle insan tarafından okunur ve taşınır; operational state güvenli transaction alır. İki katman arasındaki `source_id/resource/entity_id` bütünlüğü test edilmelidir. OKF tek transaction database olarak kullanılamaz.

## Alternatifler

Her şeyi PostgreSQL JSONB'de tutmak taşınabilirliği; her şeyi Markdown'da tutmak concurrency, auth ve durable workflow güvenilirliğini zayıflatır.

