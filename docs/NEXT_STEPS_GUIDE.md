# Bundan Sonra Nasıl İlerlemeliyim?

Bu rehber günlük kararları basitleştirir. Önce [mimariyi](./PROJECT_ARCHITECTURE.md), sonra yalnız çalışacağınız fazın [teknik plan](./MVP_IMPLEMENTATION_PLAN.md) bölümünü okuyun. PRD'yi vizyon olarak kullanın; her maddesini ilk sürüme taşımayın.

## Altın sıra

1. **Veriyi görün.** Kaynak, alan, kalite ve hassasiyet bilinmeden prompt yazmayın.
2. **Kanıt zincirini kurun.** Her önemli iddia source ID + locator ile açılabilsin.
3. **Deterministik hesabı yazın.** Skor ve sayılar Python/SQL ile üretilecek.
4. **Agent'ı ekleyin.** Agent yalnız yorum, özet ve hipotez üretir.
5. **Eval çalıştırın.** “Güzel çıktı” yerine ölçütlere bakın.
6. **İnsan onayını ekleyin.** Bilgi tabanı merge veya harici aksiyon önce onaylanır.
7. **Sonra UI'ı tamamlayın.** Kullanıcı kanıtı ve belirsizliği görebilmeli.

## Her faz başında

- Önceki fazın çıkış kriterini gerçekten geçtim mi?
- Bu ticket MVP'nin Growth Diagnostic değerine hizmet ediyor mu?
- Yeni veri sınıfı, capability veya dış ağ erişimi ekliyor mu?
- Hangi hata kullanıcıya yanlış karar verdirebilir?
- Test fixture ve rollback yolu nedir?

Bir faz bitmeden yeni PRD modülü eklemeyin. “İleride lazım olur” gerekçesi, finans/call/lead/social modüllerini bugünkü koda sokmak için yeterli değildir.

## AI değişikliklerinde

- Agent, prompt, tool, model veya retrieval değiştiyse golden eval'ı tekrar çalıştırın.
- Önce eksik/yanlış veri, mapping ve evidence locator sorunlarını kontrol edin; hemen prompt tuning yapmayın.
- LLM'nin kendinden emin dili, kanıt değildir.
- `evidence_coverage`, claim'lerin ne kadarının çözülebilir kaynağa sahip olduğunu anlatır; model doğruluk olasılığı değildir.
- LLM'ye hesap yaptırmayın. Metrik sonucu tool input'u olarak verin.
- Prompt içindeki doküman metnini untrusted data olarak ayırın; dokümandaki komutları çalıştırmayın.

## OKF değişikliklerinde

- `okf_version: "0.1"` sabitini değiştirmeden önce yeni ADR açın.
- Standart `type`, `title`, `description`, `resource`, `tags`, `timestamp` alanlarını yeniden anlamlandırmayın.
- Ürüne özel metadata'yı `agi:` namespace'inde tutun.
- Bilinmeyen type/alanı okurken ve tekrar yazarken kaybetmeyin.
- Broken link importu durdurmasın; warning üretsin. Desteksiz claim ise publish'i durdursun.
- `index.md` ve `log.md` reserved dosyaları için ayrı validator kullanın.

## Connector değişikliklerinde

- Read ve write yetkisini aynı adapter içinde sessizce birleştirmeyin.
- MVP connector'ı yalnız test/discover/preview/sync/health içerir.
- Raw snapshot'ı değişmez olarak saklayın; canonical mapping'i yeniden çalıştırılabilir yapın.
- Cursor, rate limit, schema drift ve deletion semantics'i açıkça kaydedin.
- CSV/XLSX önizlemesinde formula, encoding, tarih/para formatı ve PII kontrolü yapın.

## Mimari karar verirken

Karar kalıcıysa kısa ADR yazın: bağlam, karar, sonuç, alternatif. Paket seçmek tek başına ADR değildir; ürün sınırını veya geri dönüş maliyetini değiştiren seçim ADR'dir.

## Gerçek şirket bulunduğunda

Bu sırayı izleyin:

- [ ] Veriyi `public / internal / confidential / restricted` olarak sınıflandırın.
- [ ] Sunucu CPU/RAM/GPU/disk ve model structured-output testini çalıştırın.
- [ ] Gerçek CRM, ERP, doküman deposu ve web kaynağını keşfedin; ilk connector'ı kullanım sıklığına göre seçin.
- [ ] Alan mapping workshop yapın; “account”, “customer”, “order”, “revenue” tanımlarını iş birimiyle doğrulayın.
- [ ] KVKK/privacy, retention, consent ve çalışan/müşteri verisi kullanımını hukuk ekibiyle doğrulayın.
- [ ] Threat model, egress allowlist, secret yönetimi ve backup/restore politikasını güncelleyin.
- [ ] Sentetik golden set'e anonimleştirilmiş gerçek edge-case'ler ekleyin.
- [ ] Önce read-only pilot çalıştırın; önerileri insanla karşılaştırın.
- [ ] Write aksiyonu istenirse ayrı capability, ADR, onay sınıfı, kill switch ve audit tasarlayın.

## Durmanız gereken işaretler

- Citation kaynağı açılmıyor ama rapor publish ediliyor.
- Aynı input ile sayısal sonuç değişiyor.
- Agent'a gereğinden fazla tool veriliyor.
- “Confidence” kanıt kapsamı yerine kullanılıyor.
- Cloud provider açıldığı halde veri sınıflandırması/redaksiyon/audit yok.
- Workflow loop/custom code talebi güvenli catalog'u deliyor.
- Backup var ama boş kurulum restore testi hiç yapılmadı.

Bu işaretlerden biri varsa yeni özellik eklemek yerine önce güvenilirlik açığını kapatın.

