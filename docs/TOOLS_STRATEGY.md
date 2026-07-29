# Tool Stratejisi

Paydaş sorusu: *tool'lar nasıl bağlanır, hangileri kullanılmalı, telegram botu / internet araştırması / sosyal medya taraması mümkün mü?*

Bu doküman bugünkü gerçek durumu, bir tool eklemenin gerçek maliyetini ve önerilen sırayı anlatır. 28 Temmuz 2026 itibarıyla kod okunarak hazırlandı; her iddia `dosya:satır` ile bağlıdır.

---

## Bugün ne var

Bu kod tabanında "tool" = **capability**. Üç katman var ve üçü de kod-tanımlı (`AGENTS.md:26` — "Agent tools and workflow nodes come from code-defined allowlists. Do not execute user code or arbitrary plugins"):

1. **Katalog** — `agents/capabilities.py` içindeki `BUILTIN_CAPABILITIES`
2. **Handler** — `ScopedCapabilityTools` üzerinde bir Python metodu (`agents/runtime.py`)
3. **Bağlama** — `for_spec()` içindeki elle yazılmış `if` zinciri (`agents/runtime.py:199-206`)

Kayıtlı 11 capability'nin gerçek durumu:

| Durum | Adet | Hangileri |
|---|---|---|
| **Çalışıyor** | 4 | `knowledge.search`, `knowledge.read_source` / `context.query`, `metrics.calculate` |
| Tasarım gereği öneri-only | 1 | `wiki.propose_update` |
| `planned` stub | 4 | `web.scrape`, `crm.read`, `erp.read`, `battlecard.generate` |
| Ölü (yanlış handler, hiç bağlanmıyor) | 2 | `mcp.query`, `mcp.read_resource` |

**Çalışan dört tool'un tamamı iç dünyaya bakıyor.** Dışarı açılan hiçbir tool, hiçbir MCP bağlantısı, hiçbir mesaj gönderme yolu yok.

> `planned` capability'ler modele hiç sunulmuyor — `for_spec` onları `status == "available"` filtresiyle eliyor (`runtime.py:194`). Yani stub'lar modele sızmıyor; bu doğru davranış.

---

## Bir tool eklemenin maliyeti: üç kademe

### Kademe 1 — İç tool (veri okuma, hesaplama) · **saatler**

Dokunulacak üç dosya:

1. `agents/capabilities.py` → `BUILTIN_CAPABILITIES`'e `CapabilitySpec` ekle
2. `agents/runtime.py` → `ScopedCapabilityTools`'a `handler_name` ile birebir eşleşen metod ekle. **Docstring zorunlu** — Pydantic AI onu tool açıklaması olarak modele gönderir.
3. `agents/runtime.py:199-206` → binding dalı ekle

**Üçüncü adım atlanırsa tool sessizce ölür.** `mcp.query` ve `mcp.read_resource`'un başına gelen tam olarak bu: katalogda `available` görünüyorlar, `/api/capabilities` onları döndürüyor, editörde seçilebiliyorlar ve hiçbir şey yapmıyorlar.

Ayrıca agent spec'ine eklemek gerekir (`agents/specs/*.yaml`) ve **spec'in `version` alanı artırılmalıdır** — `ensure_platform_registry` `(id, version)` ile seed eder, versiyon artmazsa DB'deki eski tanım kalır.

Mimari engel yok. Migration gerekmez.

### Kademe 2 — Web arama / scraping · **kod kolay, ağ modeli sorunlu**

`AGENTS.md:21` web scraping'i **açıkça istisna tutuyor**, `web.scrape` stub'ı zaten duruyor, `beautifulsoup4` ve `httpx` kurulu.

Gerçek darboğaz `infra/egress/squid.conf`: allowlist `dstdomain` bazlı ve şu an yalnız dört model sağlayıcısını içeriyor, sonu `http_access deny all`. **Açık web araması sabit domain listesine sığmaz.**

İki çıkış:

- **Sabit domainli arama API'si** (Tavily, Brave, Exa) — tek host, allowlist'e uyar, ADR-0005'in güvenlik sınırını bozmaz. **Önerilen.**
- Allowlist modelini terk etmek — ADR-0005'i deler, önerilmez.

Pydantic AI'da hazır tool'lar var (`common_tools/tavily.py`, `exa.py`, `duckduckgo.py`) ama paketleri kurulu değil; opsiyonel bağımlılık grubunda.

Dönen içerik **untrusted data** olarak işaretlenmeli — mevcut desen `runtime.py:108` docstring'inde ve `model_gateway.py` control-plane policy'sinde zaten var.

### Kademe 3 — Telegram / herhangi bir dış yazma · **kod problemi değil, yönetişim problemi**

Bu kademede zorluk teknik değil.

- `AGENTS.md:21` "messaging" kelimesini açıkça yasaklıyor
- ADR-0004: "CRM/ERP update, email/call/send/delete capability'si derlenmiş üründe bulunmaz" — ve gizli feature flag'i güvenli sınır saymıyor (`0004:20`)

**Egress allowlist'e `api.telegram.org` eklemek yeterli değil, hatta ilgili adım bile değil.** Gerekenler:

1. ADR-0004'ü supersede eden yeni ADR
2. `AGENTS.md:21` ürün sınırı metninin değişmesi
3. ADR-0004:16'nın saydığı ön koşullar: consent/privacy incelemesi, idempotency, kill switch, ayrıntılı audit
4. Threat model güncellemesi (`docs/THREAT_MODEL.md`)
5. Approval Center entegrasyonu — **aşağıdaki nedenle en pahalı madde**
6. Egress + secret yönetimi (bot token için `config.py`'deki `SecretStr` + `*_file` deseni var)

**Neden 5. madde pahalı:** approval bugün yalnız **node seviyesinde** çalışıyor, tek bir `kind` üretiliyor (`okf-candidate-merge`), ve `approval_risk` alanı runtime'da **hiç okunmuyor** — saf metadata. Tool seviyesinde onay mekanizması yok. "Göndermeden önce onay" akışı sıfırdan inşa edilmeli.

**Önerilen desen:** tool doğrudan göndermez, bir *outbox* satırı yazar; graf sonraki `APPROVAL` node'unda yeni bir `kind` ile durur; onaydan sonra deterministik bir node gönderir. Bu, ADR-0004'ün "OKF merge'i bile insan onayı ister" mantığıyla tutarlı ve mevcut mimariye oturur.

**Gelen yön (inbound) zaten hazır:** `POST /api/webhooks/{source_id}` → `EventInbox` → trigger kuralları. Telegram webhook'u yeni bir `event_type` + `TriggerRule` ile bağlanabilir. Tek engel: `DEFAULT_TRIGGER_RULES` hardcoded ve in-memory, runtime'da kural eklenemiyor.

---

## MCP: ne zaman, ne için

MCP'nin doğal cevabı "tool'lar nasıl bağlanır" sorusuna gibi görünür, ama **sizin ihtiyacınız için değil.**

Bugünkü durum (ADR-0030): politika katmanı gerçek ve testli (onay, read-only, sınıflandırma, tool allowlist), **taşıma katmanı stub** — `invoke_tool` sabit sözlük döndürüyor (`mcp.py:76-80`), `transport_type` hiç okunmuyor, üretimde `MCPGateway` hiç kurulmuyor, `MCPProfile` tablosu daima boş.

MCP'nin değeri **müşterinin kendi tool'unu getirmesi**. Telegram ve web arama için native capability çok daha ucuz: 3 dosya, saatler. MCP ise transport, handshake, session, profil CRUD, timeout ve yeni bir dış-yürütme yüzeyi demek.

**Öneri:** MCP'yi şimdilik "target specification" olarak sınıflandırın, ölü `mcp.*` capability'lerini registry'den kaldırın, ve ilk müşteri entegrasyonu gerçekten gerektirdiğinde ele alın. Ele alınırsa: Pydantic AI'ın `MCPToolset`'i (`pydantic_ai/mcp.py`) hazır ve `process_tool_call` hook'u mevcut `MCPGateway.invoke_tool` politika kontrollerini takmak için birebir uygun. Ayrıca `toolsets` API'sinde `filtered()` ve `approval_required()` kombinatörleri var — projenin mevcut politika modeline neredeyse birebir oturuyor.

Tek engel: `build_pydantic_ai_agent` (`model_gateway.py`) `Agent(...)`'a yalnız `tools=` geçiriyor; `toolsets=` için imza genişletilmeli.

---

## Önerilen sıra

1. **Ölü `mcp.*` capability'lerini kaldır.** Bugün editörde seçilebiliyorlar ve hiçbir şey yapmıyorlar. *(Bu turda yapıldı: editör artık yalnız registry'nin bildirdiğini gösteriyor ve `planned` olanları seçilemez işaretliyor.)*
2. **`web.scrape`'i gerçek yap** — sabit domainli bir arama API'si seçerek. En düşük maliyetli görünür kazanım, ve `AGENTS.md` zaten izin veriyor.
3. **Tool çağrısı gözlemlenebilirliği ekle.** Şu an yalnız `tool_calls` sayacı tutuluyor (`WorkflowStepRun.token_usage`); hangi tool'un hangi argümanla çağrıldığı **hiç kaydedilmiyor**. Telegram'dan önce bu şart — onay verecek insanın neyi onayladığını görmesi gerekiyor.
4. **Tool seviyesinde approval mekanizması** (outbox + APPROVAL node deseni).
5. **Ancak bundan sonra telegram** — ve yeni ADR ile.

Kademe 3'e 1-4 tamamlanmadan girmeyin: onaysız ve izlenemez bir dış-yazma yolu, PRD §17'nin "kontrolsüz outbound automation aracı olmamalı" sınırını fiilen deler.

---

## İlgili kararlar

- ADR-0004 — MVP'de dış yazma yok (Kademe 3'ün önündeki asıl kapı)
- ADR-0005 — ingress/egress sınırları (Kademe 2'nin darboğazı)
- ADR-0030 — MCP statüsü, karar bekliyor
- ADR-0032 — tenancy; MCP transport'u bundan önce başlamamalı
- `docs/design/POLICY_ENGINE.md`, `docs/design/CONSENT_LEDGER.md` — Kademe 3'ün ön koşulları
