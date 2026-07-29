# Demo Script

Arayüzden sıfırdan kurulum + ilk tanı + onay. Bu akış 29 Temmuz 2026'da tarayıcıda baştan
sona çalıştırılarak doğrulandı; aşağıdaki her adım gerçekten tıklandı.

**Süre:** ~8-10 dakika · **Model:** `gemini-3.1-flash-lite` · **Maliyet:** 4-7 sağlayıcı isteği

---

## Önce: demo öncesi kontrol listesi

- [ ] **Temiz bir örnek başlat.** Demo yarıda kalmış bir kurulumla başlamamalı.
  ```bash
  docker compose -f docker-compose.yml -f docker-compose.cloud.yml up -d --build
  ```
- [ ] **Kotayı doğrula.** Ücretsiz katmanda model başına dakikada 5, günde 20 istek var; bir
      tanı 4-7 istek harcıyor. Prova yaptıysan aynı dakika içinde tekrar deneme.
- [ ] **Provayı bir kez yap.** İlk tanı gerçek bir model çağrısıdır; sağlayıcı 503 dönebilir.
- [ ] Tarayıcıyı **hard refresh** ile aç (eski JS bundle'ı önbellekten gelirse eski davranışı
      görürsün).

---

## 1. İlk yönetici (30 sn)

Açılışta bootstrap ekranı gelir: token, ad soyad, e-posta, parola.

> **Anlat:** "Sistem tek kurulum, tek şirket. İlk yönetici hesabı yalnız bir kez, tek
> kullanımlık bir token'la oluşturulabiliyor — kurulum sonrası bu kapı kapanıyor."

---

## 2. Kurulum sihirbazı — 5 adım (3-4 dk)

### Adım 1: Şirket profili
Şirket adı, sektör, büyüme hedefi. **Şirket adını demo için değiştir** — bu isim tanı
çıktısında ve üst barda görünecek, canlı bir bağ olduğunu göstermek etkili.

> **Anlat:** "Burada girilen bağlam Growth Context Graph'ın kökü; tanı çıktısı buna bağlanıyor."

### Adım 2: Model Gateway
Dört sağlayıcı kartı (Gemini, Groq, Mistral, OpenRouter). API key alanı, model seçimi ve
**canlı test** butonu.

> **Anlat:** "Model sağlayıcısı ürüne gömülü değil. Aynı sistem bulut API'siyle de, kendi
> GPU sunucunuzdaki modelle de çalışıyor — veri sınırı politikası hangi içeriğin buluta
> çıkabileceğine karar veriyor."

⚠️ Kurulum env/secret ile önceden yapılandırılmışsa bu adım "önceden yapılandırılmış"
uyarısı gösterir. Canlı testi yine de çalıştır — izleyici bağlantının gerçek olduğunu görsün.

⚠️ **Varsayılan modeli değiştirme.** `gemini-3.1-flash-lite` seçili geliyor; daha ağır
modeller ücretsiz katmanda dakikalık limite takılıp tanıyı yarıda kesiyor.

### Adım 3: Veri bağlantıları
Üç sekme: MCP, canlı veritabanı, demo şirket + CSV. **"Demo Şirket & CSV Yükleme" sekmesi
varsayılan olarak açık gelir** — demo bu sekmede kalmalı.

> **Anlat:** "Bağlantılar read-only. MVP dış sistemlere yazmıyor; okuyor, kanıtlıyor, öneriyor."

⚠️ **MCP sekmesini açma.** Politika katmanı hazır ama taşıma katmanı henüz yok
(`docs/TOOLS_STRATEGY.md`). Soru gelirse: "MCP için onay ve allowlist katmanı hazır,
taşıma entegrasyonu yol haritasında."

### Adım 4: OKF & RAG indeksleme
Butona bas. Birkaç saniye sürer, sonra kaç kayıt ingest edildiğini ve **onay bekleyen bir OKF
candidate oluşturulduğunu** söyler.

> **Anlat:** "Dikkat edin — veri doğrudan bilgi tabanına yazılmadı. Bir *candidate* oluştu.
> Aktif bilgi tabanı ancak insan onayıyla değişiyor."

### Adım 5: Tamamla
Dashboard'a geç.

---

## 3. İlk tanı (2-3 dk)

Dashboard boş durumda "İlk tanıyı çalıştır" butonu var. Bas ve **bekle** — bu gerçek bir
model çalıştırması.

> **Anlat (beklerken):** "Şu an 12 düğümlü bir LangGraph iş akışı çalışıyor: veri senkronu,
> bilgi derlemesi, şirket analisti, fırsat analisti, deterministik skorlama, kanıt denetçisi,
> wiki küratörü. Her ajanın yazdığı her iddia, kalıcı bir kanıt kaydına bağlanmak zorunda."

Tamamlanınca dashboard dolar:
- Büyüme özeti, veri hazırlığı %, kanıt kapsamı %
- **5 öncelikli fırsat** — skor, hedef uyumu, kanıt yüzdesi
- 30 günlük plan
- Kanıt ve kaynaklar paneli ("Doğrulandı" rozetleriyle)
- Veri boşlukları

**En güçlü gösterim:** bir fırsatın kanıt yüzdesine tıkla, arkasındaki kaynağa in.

> **Anlat:** "Buradaki hiçbir sayı modelden gelmiyor. Sayısal iddialar deterministik olarak
> hesaplanıyor ve hash'i doğrulanmış bir kanıt makbuzuna bağlanıyor. Modelin doğrulanamayan
> bir gerekçesi varsa yayımlanmıyor — veri boşluğu olarak raporlanıyor."

Veri boşlukları listesinde "Doğrulanamayan iddia..." satırlarını göster. **Bu bir kusur
değil, ürünün çalıştığının kanıtı.**

---

## 4. Onay merkezi (1-2 dk)

Sol menüden **Onay Merkezi**. Bekleyen `okf-candidate-merge` onayı görünür.

1. **Diff**'e bas — bilgi tabanına önerilen değişikliği göster
2. **Karar gerekçesi** alanına en az 8 karakter yaz (zorunlu; yazılana kadar butonlar kapalı)
3. **Onayla**

> **Anlat:** "Gerekçe zorunlu ve audit kaydına işleniyor. Kim, ne zaman, neden onayladı —
> hepsi izlenebilir. Onay olmadan aktif bilgi tabanı değişmiyor."

Onaydan sonra run `completed` olur ve candidate aktif OKF paketine birleşir.

---

## 5. Kapanış

Göstermeye değer iki ekran daha:

- **İş Akışları** — görsel node grafiği. "İş akışları kod değil, konfigürasyon. Ajan, model
  profili ve yetkiler node bazında seçiliyor ve her sürüm değişmez olarak yayımlanıyor."
- **Ayarlar → Agent Registry** — dört yayımlanmış ajan, sürümleri ve yetkileri.

---

## Soru gelirse

| Soru | Cevap |
|---|---|
| "Telegram botu yapabilir mi?" | Gelen webhook altyapısı hazır. Giden mesaj bilinçli olarak kapalı: onay, consent ve audit katmanı tamamlanmadan dış dünyaya yazma açılmıyor. `docs/TOOLS_STRATEGY.md` |
| "İnternette arama yapabilir mi?" | Mimari izin veriyor, sabit domainli bir arama API'siyle kısa sürede eklenebilir. Açık web taraması egress allowlist modeliyle çelişiyor. |
| "Kendi modelimizi kullanabilir miyiz?" | Evet — Model Gateway sağlayıcıdan bağımsız; Ollama/vLLM/LM Studio destekleniyor. |
| "Veri buluta gidiyor mu?" | `confidential` ve `restricted` içerik bulut modeline **gönderilmiyor**, fail-closed. İletişim kimlikleri prompt'a girmeden maskeleniyor. |
| "Kaç müşteri barındırıyor?" | Tek kurulum, tek şirket. İzolasyon deployment seviyesinde (ADR-0032). |

---

## Bilinen sınırlar — sorulmadan söyleme, sorulursa dürüst ol

- Vektör arama varsayılan kurulumda kapalı; lexical fallback çalışıyor (ADR-0031)
- MCP taşıma katmanı yok, politika katmanı var (ADR-0030)
- Fırsat taksonomisi şu an demo veri setine bağlı; ikinci müşteri için soyutlanması gerekiyor
- Aynı anda tek tanı çalıştırılabilir
