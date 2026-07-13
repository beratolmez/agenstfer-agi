# Product Requirements Document

## Agentic Growth Intelligence Server

> **Belge türü:** Ürün Gereksinimleri Dokümanı (PRD)

---

## 1. Ürün Tanımı

Agentic Growth Intelligence Server, B2B firmaların satış, pazarlama, müşteri ilişkileri, rekabet istihbaratı, pazar sinyalleri, inbound talepler, outbound iletişim, CRM, ERP ve dijital kanal verilerini tek bir yapay zeka destekli karar ve orkestrasyon katmanında birleştiren agentic growth operating system ürünüdür.

Ürün, klasik bir CRM, klasik bir pazarlama otomasyon aracı, klasik bir lead generation platformu veya basit bir chatbot değildir. Ürünün temel amacı, firmanın iç ve dış dünyasından gelen sinyalleri anlamlandırmak, bu sinyalleri firma bağlamına yerleştirmek, büyüme fırsatlarını ortaya çıkarmak, önerilen aksiyonları kanıt ve risk bilgisiyle birlikte sunmak ve insan onayıyla güvenli şekilde icraya dönüştürmektir.

Sistemin merkezinde bir Growth Context Graph bulunur. Bu yapı, firmanın müşterilerini, potansiyel müşterilerini, ürünlerini, hizmetlerini, rakiplerini, kampanyalarını, satış aktivitelerini, ERP verilerini, web sinyallerini, çağrı kayıtlarını, sosyal medya aktivitelerini, etkinlik fırsatlarını ve müşteri iletişim geçmişini ilişkisel bir bağlam içinde tutar.

Ürün, yapay zeka agentlarını serbest hareket eden otonom varlıklar gibi değil, sınırları, yetkileri, risk seviyeleri, veri erişimi ve onay gereksinimleri tanımlanmış dijital iş birimleri olarak çalıştırır.

## 2. Ürün Vizyonu

Ürün, firmaların dağınık büyüme operasyonlarını tek merkezden yönetebilecekleri güvenli, açıklanabilir ve bağlam farkındalığına sahip bir growth intelligence server haline gelmelidir.

Vizyon, firmanın şu sorulara sürekli ve veri destekli cevap alabilmesini sağlamaktır:

- Hangi müşteri segmentleri daha yüksek potansiyel taşıyor?
- Hangi potansiyel müşteriler şu anda satın almaya daha yakın?
- Hangi rakip hareketleri satış stratejimizi etkiliyor?
- Hangi kampanyalar gerçekten gelir oluşturuyor?
- Hangi sosyal medya, reklam, etkinlik veya outbound aktivitesi satışa katkı sağlıyor?
- Hangi inbound talepler öncelikli olarak ele alınmalı?
- Hangi müşteri, hangi mesajla, hangi kanaldan ve hangi zamanda hedeflenmeli?
- Hangi aksiyonlar otomatik yapılabilir, hangileri insan onayı gerektirir?
- CRM ve ERP verileri pazarlama ve satış kararlarını nasıl değiştirmeli?
- Firmanın büyüme stratejisi hangi kanıtlarla destekleniyor?

Bu vizyonun ana farkı, sistemi yalnızca veri toplayan veya mesaj gönderen bir araç olarak değil, firmanın büyüme kararlarını organize eden bir control plane olarak tasarlamasıdır.

## 3. Stratejik Konumlandırma

Piyasadaki benzer ürünler farklı alanlarda güçlüdür. Salesforce ve HubSpot CRM odaklı agent yaklaşımında güçlüdür. Clay veri zenginleştirme ve GTM workflow tarafında güçlüdür. Apollo, Amplemarket, ZoomInfo ve 6sense satış verisi, intent signal ve outbound automation tarafında güçlüdür. Twilio konuşma, mesajlaşma ve kanal altyapısında güçlüdür. Crayon rekabet istihbaratı ve battlecard tarafında güçlüdür. n8n ise self hosted workflow automation tarafında güçlüdür.

Bu ürünün rekabet stratejisi bu ürünlerin yaptığı işleri birebir kopyalamak olmamalıdır. Doğru strateji, bu parçalı yapıların üzerinde çalışan bağımsız, policy aware, approval centered ve context driven bir büyüme orkestrasyon katmanı oluşturmaktır.

Ürünün temel konumlandırması şudur:

> **Ürün konumlandırması:** KOBİ ve orta ölçekli B2B firmalar için güvenli, onay kontrollü, CRM ve ERP bağlantılı, açık model destekli Agentic Growth Operating System.

Bu konumlandırma üç ana fark yaratır.

Birincisi, ürün yalnızca lead bulmaz. Leadin firma bağlamındaki değerini, geçmiş müşteri verileriyle uyumunu, kampanya etkisini, rakip durumunu ve satış potansiyelini birlikte değerlendirir.

İkincisi, ürün yalnızca mesaj göndermez. Hangi mesajın neden gönderilmesi gerektiğini, hangi kanıtla üretildiğini, hangi risk seviyesine sahip olduğunu ve hangi onayın gerektiğini gösterir.

Üçüncüsü, ürün yalnızca rapor üretmez. Raporu workflow, CRM görevi, outbound draft, battlecard, kampanya önerisi veya yönetici kararı haline getirebilir.

## 4. Ana Ürün Prensipleri

### 4.1 Context First Yaklaşımı

Her agent, her workflow ve her öneri Growth Context Graph üzerine dayanmalıdır. Agentlar izole şekilde cevap üretmemeli, firma bağlamı, müşteri geçmişi, kampanya verileri, CRM kayıtları, ERP sonuçları ve rakip sinyalleri üzerinden değerlendirme yapmalıdır.

### 4.2 Approval First Yaklaşımı

Dış dünyaya etki eden tüm aksiyonlar risk seviyesine göre onay mekanizmasına bağlanmalıdır. E posta gönderimi, WhatsApp mesajı, telefon araması, CRM güncellemesi, teklif taslağı, ERP writeback, reklam audience güncellemesi ve sosyal medya mesajı gibi işlemler onay ve audit trail olmadan kontrolsüz çalışmamalıdır.

### 4.3 Compliance By Design Yaklaşımı

LinkedIn, WhatsApp, Google Maps, e posta, SMS, telefon ve kişisel veri işleme gibi alanlarda platform kuralları ve hukuki gereklilikler ürün davranışının parçası olmalıdır. Sistem yasaklı veya riskli otomasyonları doğal olarak engellemeli, alternatif olarak resmi API, onaylı sağlayıcı veya müşteri tarafından yetkilendirilmiş bağlantı yöntemlerini kullanmalıdır.

### 4.4 Human In The Loop Yaklaşımı

Ürün, insanları devreden çıkaran bir sistem değil, satış, pazarlama, yönetim ve müşteri hizmetleri ekiplerini daha doğru karar verebilir hale getiren bir sistemdir. İnsan onayı, insan düzeltmesi, insan geri bildirimi ve insan devri ürünün temel parçasıdır.

### 4.5 Evidence Based AI Yaklaşımı

Her öneri, kullanılan veri kaynakları ve kanıtlarla birlikte sunulmalıdır. Sistem yalnızca “bu müşteriye ulaşın” dememeli, neden bu müşterinin öncelikli olduğunu, hangi sinyallerin bunu desteklediğini, güven skorunu ve riskleri de göstermelidir.

### 4.6 Model Agnostic Yaklaşımı

Sistem tek bir LLM sağlayıcısına bağlı kalmamalıdır. Local modeller, açık kaynak modeller, cloud modeller, domain specific modeller ve farklı API sağlayıcıları merkezi bir Model Gateway üzerinden yönetilmelidir.

## 5. Hedef Kullanıcılar

### 5.1 Firma Sahibi ve Üst Yönetim

Firma sahibi ve üst yönetim, ürünü büyüme kararlarını daha doğru almak için kullanır. Sistem onlara müşteri segmentleri, satış fırsatları, rakip hareketleri, kampanya etkileri, kanal performansı ve stratejik öneriler sunar.

Yönetim için en önemli çıktı, haftalık ve aylık büyüme raporları, fırsat haritaları, riskler, önerilen aksiyonlar ve gelir etkisi analizleridir.

### 5.2 Satış Ekibi

Satış ekibi, ürünü doğru leadleri bulmak, önceliklendirmek, kişiselleştirilmiş iletişim taslakları üretmek, görüşme öncesi brief almak, rakip itirazlarına hazırlanmak ve CRM aktivitelerini düzenlemek için kullanır.

Satış ekibi için en önemli çıktı, sıcak lead listeleri, account priority score, buying signal, call script, e posta draftı, competitor battlecard ve takip görevleridir.

### 5.3 Pazarlama Ekibi

Pazarlama ekibi, ürünü segment analizi, kampanya planlama, sosyal medya stratejisi, reklam performansı, içerik briefleri, AI search visibility, event fırsatları ve revenue attribution için kullanır.

Pazarlama için en önemli çıktı, kanal bazlı strateji, kampanya önerileri, hedef kitle segmentleri, içerik briefleri, reklam bütçesi yönlendirmesi ve kampanya gelir etkisi analizidir.

### 5.4 Müşteri Hizmetleri ve Inbound Ekipleri

Müşteri hizmetleri ve inbound ekipleri, ürünü gelen talepleri sınıflandırmak, müşteri geçmişini görmek, AI destekli cevap taslağı almak, doğru kişiye yönlendirme yapmak ve çağrı sonrası özet oluşturmak için kullanır.

Bu ekip için en önemli çıktı, inbound intent classification, urgency score, customer context, suggested response, handoff summary ve CRM notudur.

### 5.5 Operasyon ve RevOps Ekibi

Operasyon ve RevOps ekibi, ürünü CRM sağlığı, veri kalitesi, workflow güvenilirliği, connector performansı, consent durumu, model kullanımı ve audit kayıtlarını yönetmek için kullanır.

Bu ekip için en önemli çıktı, veri kalite skorları, duplicate uyarıları, connector health, workflow run history, approval status ve compliance dashboard olur.

### 5.6 Teknik Ekip

Teknik ekip, sistemi kurar, model gateway ayarlarını yapar, connectorları yönetir, MCP bağlantılarını yapılandırır, erişim politikalarını tanımlar, güvenlik ve gözlemlenebilirlik katmanını yönetir.

## 6. Temel Ürün Bileşenleri

### 6.1 Growth Context Graph

Growth Context Graph ürünün ana beyni olarak çalışır. Bu yapı, firma ile ilgili tüm varlıkları ve ilişkileri tutar.

Graph içinde şu varlıklar bulunmalıdır:

Company

Account

Contact

Lead

Customer

Opportunity

Product

Service

Campaign

Channel

Competitor

Event

Conversation

Call

Email

Social Interaction

CRM Record

ERP Record

Invoice

Order

Proposal

Consent Record

Data Source

Evidence Item

Recommendation

Agent Action

Growth Context Graph yalnızca veri saklama katmanı değildir. Aynı zamanda agentların karar verirken referans aldığı bağlam katmanıdır. Örneğin bir lead analiz edilirken sistem yalnızca leadin web sitesine bakmaz. Aynı zamanda bu leadin sektörünü, lokasyonunu, firmanın geçmişte benzer müşterilerle başarı durumunu, rakiplerin bu segmentteki aktivitelerini, kampanya performansını ve satış ekibinin kapasitesini birlikte değerlendirir.

### 6.2 Evidence ve Provenance Katmanı

Sistem her veri parçasının nereden geldiğini, ne zaman alındığını, hangi güven skoruna sahip olduğunu ve hangi aksiyonda kullanıldığını saklamalıdır.

Her öneri için şu bilgiler gösterilmelidir:

- Kullanılan veri kaynakları
- Veri güncelliği
- Kaynak güven seviyesi
- Çıkarımın gerekçesi
- Alternatif yorumlar
- Eksik veri uyarıları
- İnsan onayı gereksinimi

Bu yapı, agent çıktılarının güvenilirliğini artırır ve yönetim ekibinin önerilere neden güvenmesi gerektiğini açık hale getirir.

### 6.3 Policy Engine

Policy Engine, sistemde hangi agentın hangi veriye erişebileceğini, hangi aksiyonu hangi koşulda yapabileceğini, hangi kanalın hangi kurallarla kullanılacağını ve hangi durumda insan onayı gerektiğini belirler.

Policy Engine şu alanları yönetmelidir:

- Kanal bazlı izin kuralları
- Kullanıcı rolü ve yetki seviyesi
- Agent yetki sınırları
- Consent durumu
- Opt out durumu
- Do not call durumu
- Veri hassasiyet seviyesi
- Platform kullanım kuralları
- Ülke ve bölge bazlı ticari iletişim kuralları
- Risk sınıflandırması
- Onay gereksinimi
- Aksiyon limiti

Policy Engine, ürünün en kritik savunma mekanizmalarından biridir. Bu katman olmadan ürün kontrolsüz bir outbound automation aracına dönüşür ve hukuki, etik ve platform riski doğurur.

### 6.4 Consent Ledger

Consent Ledger, kişi veya firma bazında iletişim izinlerini ve veri kullanım dayanaklarını tutar.

Her contact için şu bilgiler saklanmalıdır:

- E posta iletişim izni
- Telefon araması izni
- SMS izni
- WhatsApp izni
- Sosyal medya iletişim durumu
- Opt in kaynağı
- Opt in zamanı
- Opt out zamanı
- Do not call durumu
- Consent evidence
- Consent expiry
- Legal basis
- Kullanılabilir kanallar

Bu yapı sayesinde sistem hangi kişiye hangi kanaldan ulaşılabileceğini otomatik kontrol eder. Eğer iletişim izni yoksa agent gönderim önerisini aksiyona çeviremez, yalnızca iç görev veya manuel inceleme önerisi oluşturabilir.

### 6.5 Agent Registry

Agent Registry, sistemdeki tüm agentları merkezi olarak yönetir.

Her agent için şu alanlar tanımlanmalıdır:

- Agent adı
- Agent görevi
- Agent açıklaması
- Kullanabileceği veri kaynakları
- Kullanabileceği connectorlar
- Çalışabileceği workflowlar
- Üretebileceği çıktı türleri
- Alabileceği aksiyon türleri
- Risk seviyesi
- Onay gereksinimi
- Maksimum işlem limiti
- Model tercihi
- Prompt template versiyonu
- Audit seviyesi
- Başarı metrikleri
Örnek agentlar:

- Company Analyst Agent
- Market Research Agent
- Lead Discovery Agent
- Lead Enrichment Agent
- Lead Scoring Agent
- Buying Signal Agent
- Competitive Intelligence Agent
- Battlecard Agent
- Social Media Strategy Agent
- Campaign Attribution Agent
- Outbound Draft Agent
- Inbound Triage Agent
- Voice Call Agent
- CRM Hygiene Agent
- ERP Insight Agent
- Compliance Review Agent
- Executive Report Agent
- Knowledge Base Agent
- Event Intelligence Agent
- AEO Visibility Agent

### 6.6 Workflow Orchestrator

Workflow Orchestrator, sistemdeki tüm iş akışlarını çalıştırır. Bu yapı klasik otomasyon ile agentic decision flow arasında köprü kurar.

Workflowlar şu şekilde tetiklenebilir:

- Zaman bazlı
- CRM kaydı değiştiğinde
- ERP verisi güncellendiğinde
- Yeni inbound talep geldiğinde
- Yeni lead bulunduğunda
- Rakip değişikliği yakalandığında
- Kampanya performansı değiştiğinde
- Kullanıcı manuel başlattığında
- Agent önerisiyle
- Webhook ile
Workflow Orchestrator şu özelliklere sahip olmalıdır:

- Retry yönetimi
- Hata yönetimi
- İnsan görevi oluşturma
- Onay bekleme
- Geri alma mantığı
- Versiyonlama
- Audit log
- Workflow run history
- Connector health kontrolü
- Risk bazlı durdurma

Bu sistemin n8n gibi mevcut bir workflow motoruyla entegre edilmesi mümkündür, ancak ürünün asıl değerli katmanı n8n’in üstündeki context, policy, approval, agent governance ve business intelligence katmanı olmalıdır.

### 6.7 Model Gateway

Model Gateway, tüm LLM ve AI model çağrılarını tek merkezden yönetir.

Model Gateway şu işleri yapmalıdır:

- Göreve göre model seçimi
- Local model kullanımı
- Cloud model kullanımı
- Açık kaynak model desteği
- Prompt versiyonlama
- Token ve kullanım takibi
- Maliyet değil, kaynak tüketimi kontrolü
- Latency takibi
- Model fallback
- Output validation
- Prompt injection kontrolü
- Sensitive data masking
- Model response audit
- Cache kullanımı

Basit sınıflandırma, veri çıkarımı, skor hesaplama ve formatlama gibi görevlerde local modeller kullanılabilir. Daha karmaşık muhakeme, raporlama, strateji üretimi ve çok adımlı analizlerde daha güçlü modeller kullanılabilir.

### 6.8 Connector Layer

Connector Layer, dış sistemlerle bağlantı kurar. Sistem doğrudan platform kurallarını ihlal eden scraping ve otomasyondan kaçınmalı, resmi API, MCP, müşteri yetkilendirmesi, onaylı sağlayıcı veya güvenilir middleware kullanmalıdır.

Connector türleri:

- Read only connector
- Write enabled connector
- Action connector
- Intelligence connector
- Communication connector
- ERP connector
- CRM connector
- Ads connector
- Event connector
- MCP connector
Örnek bağlantılar:

- HubSpot
- Salesforce
- Zoho
- Pipedrive
- Frappe CRM
- ERPNext
- QuickBooks
- Paraşüt
- Mikro
- Logo
- Gmail
- Microsoft 365
- Google Ads
- Meta Ads
- LinkedIn Ads
- WhatsApp Business Provider
- Twilio
- Apify
- Firecrawl
- Clay
- Apollo
- ZoomInfo
- n8n
- Slack
- Teams

Connectorlar yalnızca teknik bağlantı olarak değil, risk ve yetki yönetimiyle birlikte düşünülmelidir. Örneğin bir CRM connector read only olabilir, fakat ERP connector yüksek riskli write action gerektirebilir.

## 7. Ana Fonksiyonel Modüller

### 7.1 Firma Analiz Modülü

Sistem firmayı detaylı şekilde analiz eder. Analiz şu kaynaklardan beslenir:

- Firma web sitesi
- Sosyal medya hesapları
- CRM verileri
- ERP verileri
- Ürün ve hizmet dokümanları
- Geçmiş müşteri listesi
- Satış fırsatları
- Kampanya geçmişi
- Reklam verileri
- Rakip listesi
- Müşteri yorumları
- Çağrı ve görüşme özetleri

Bu modül, firmanın dijital ve ticari profilini çıkarır. Firmanın güçlü yönleri, zayıf yönleri, hedef müşteri segmentleri, satış avantajları, pazar konumu ve büyüme fırsatları belirlenir.

### 7.2 Lead Discovery Modülü

Lead Discovery Modülü, potansiyel müşteri adaylarını belirler. Ancak sistem her kaynağı kontrolsüz şekilde taramamalıdır. Veri toplama yöntemi policy engine tarafından yönetilmelidir.

Kaynaklar şunlar olabilir:

- Resmi işletme dizinleri
- Müşteri tarafından sağlanan listeler
- CRM içindeki pasif kayıtlar
- ERP içindeki geçmiş müşteriler
- Web sitesi formları
- Etkinlik ve fuar katılımcı listeleri
- Reklam etkileşimleri
- Üçüncü parti veri sağlayıcıları
- Müşteri lisanslı enrichment servisleri
- Public web verileri
Her lead için şu alanlar çıkarılır:

- Firma adı
- Sektör
- Lokasyon
- Web sitesi
- İletişim kanalları
- Karar verici olabilecek kişiler
- Firma büyüklüğü
- Uygun ürün veya hizmet
- İhtiyaç sinyali
- Güven skoru
- Veri kaynağı
- İletişim izni durumu

### 7.3 Lead Enrichment Modülü

Lead Enrichment Modülü, bulunan leadlerin verisini tamamlar ve doğrular.

Zenginleştirme alanları:

- E posta
- Telefon
- Sosyal profil
- Web sitesi teknolojileri
- Şirket büyüklüğü
- Karar verici kişiler
- Şirket haberleri
- İş ilanları
- Büyüme sinyalleri
- Teknoloji kullanımı
- Reklam aktivitesi
- CRM geçmişi
- ERP geçmişi
- Consent durumu

Her veri alanı için confidence score tutulur. Eğer sistem bir veriden emin değilse bunu açıkça gösterir.

### 7.4 Signal Fusion Modülü

Signal Fusion Modülü, farklı kaynaklardan gelen sinyalleri birleştirir.

Sinyal türleri:

- Web site ziyareti
- Form doldurma
- Pricing page ziyareti
- Demo talebi
- E posta açma
- E posta tıklama
- Reklam etkileşimi
- Sosyal medya etkileşimi
- İş ilanı artışı
- Yeni lokasyon açılışı
- Yeni ürün duyurusu
- Rakip ile ilgili hareket
- Etkinlik katılımı
- Müşteri hizmetleri talebi
- CRM activity
- ERP satış verisi

Bu sinyaller tek tek değerlendirilmez. Sistem bunları account, contact ve segment seviyesinde birleştirerek öncelik skoru üretir.

### 7.5 Lead Scoring ve Account Priority Modülü

Sistem her lead ve account için skor üretir.

Skor kriterleri:

- ICP uyumu
- Satın alma ihtimali
- Bütçe potansiyeli
- Lokasyon uygunluğu
- Hizmet ihtiyacı
- Web sitesi olgunluğu
- Dijital eksiklik
- CRM geçmişi
- ERP geçmişi
- Intent sinyali
- Rakip etkisi
- İletişim izni
- Veri güven skoru
- Satış ekibinin erişim ihtimali
- Zamanlama uygunluğu

Skor sonucu yalnızca sayısal bir puan olmamalıdır. Sistem neden bu puanın verildiğini açıklamalıdır.

### 7.6 Buying Group Detection Modülü

B2B satışlarda karar çoğu zaman tek kişiyle alınmaz. Bu nedenle sistem account içinde satın alma grubunu tespit etmeye çalışmalıdır.

Roller:

- Decision maker
- Influencer
- Technical evaluator
- Finance approver
- Procurement contact
- End user representative
- Executive sponsor
- Gatekeeper

Sistem bu kişilerin ilişki haritasını çıkarır ve satış ekibine kime nasıl yaklaşması gerektiğini önerir.

### 7.7 Outbound Draft ve Sequence Modülü

Sistem outbound iletişimi doğrudan kontrolsüz başlatmak yerine onaya hazır taslaklar ve sequence önerileri üretmelidir.

Desteklenen kanallar:

- E posta
- Telefon araması
- WhatsApp Business
- SMS
- LinkedIn Ads audience
- CRM task
- Sosyal medya etkileşim önerisi
- Manuel takip görevi
- Her outbound önerisi şu bilgilerle sunulmalıdır:
- Hedef kişi
- Hedef firma
- Kullanılacak kanal
- Mesaj taslağı
- Kişiselleştirme gerekçesi
- Kullanılan kanıtlar
- Risk seviyesi
- Consent durumu
- Onay gereksinimi
- Beklenen sonraki adım

Sistem kullanıcı onayı olmadan yüksek riskli toplu gönderim yapmamalıdır.

### 7.8 Deliverability ve Identity Health Modülü

Outbound iletişimin sürdürülebilir olması için sistem gönderim sağlığını takip etmelidir.

Takip alanları:

- Domain reputation
- SPF
- DKIM
- DMARC
- Bounce oranı
- Spam complaint oranı
- Unsubscribe oranı
- Reply oranı
- Open ve click trendleri
- Mailbox limitleri
- Gönderim yoğunluğu
- Riskli kampanya uyarıları

Sistem, riskli kampanyaları otomatik durdurabilmeli veya Approval Center’a göndermelidir.

### 7.9 Inbound Intelligence Modülü

Inbound Intelligence Modülü, farklı kanallardan gelen talepleri tek merkezde toplar ve anlamlandırır.

Kaynaklar:

- Web formu
- E posta
- WhatsApp
- Telefon
- Sosyal medya mesajı
- Chatbot
- CRM ticket
- Landing page formu
Sistem gelen talebi sınıflandırır:

- Sales inquiry
- Pricing request
- Demo request
- Support request
- Complaint
- Partnership request
- Vendor message
- Job application
- Spam
- Urgent customer issue

Her talep için urgency score, customer value score, routing suggestion ve response draft oluşturulur.

### 7.10 Voice Agent ve Call Intelligence Modülü

Voice Agent Modülü, inbound ve outbound çağrı süreçlerini destekler. Sistem, tamamen kontrolsüz arama yapan bir bot olarak değil, bağlamı anlayan, görüşmeleri özetleyen, lead qualify eden ve gerektiğinde insana devreden bir yapı olarak tasarlanmalıdır.

Inbound çağrı özellikleri:

- Müşteriyi karşılama
- Kimlik veya firma tanıma
- CRM kaydı bulma
- Önceki konuşma bağlamını getirme
- İhtiyaç sınıflandırma
- Lead qualification
- Randevu talebi alma
- İlgili kişiye aktarma
- Çağrı özetini çıkarma
- CRM notu oluşturma
Outbound çağrı özellikleri:

- Onaylı lead listesi üzerinden arama önerisi
- Call script üretimi
- İtiraz sınıflandırma
- Satın alma ilgisi ölçümü
- Randevu önerisi
- İnsan temsilciye sıcak devir
- Çağrı sonucu oluşturma

Voice Agent fiyat, indirim, sözleşme, ödeme, hukuki taahhüt veya finansal işlem içeren durumlarda insan onayı olmadan bağlayıcı beyan vermemelidir.

### 7.11 Competitive Intelligence Modülü

Sistem rakipleri sürekli izler ve yalnızca rapor üretmez, satış ve pazarlama aksiyonlarına çevrilebilir rekabet zekası üretir.

Takip alanları:

- Web sitesi değişiklikleri
- Yeni ürün veya hizmet duyuruları
- Fiyat sinyalleri
- Blog içerikleri
- Sosyal medya paylaşımları
- Reklam sinyalleri
- Müşteri yorumları
- Review siteleri
- Hiring aktiviteleri
- Basın duyuruları
- Etkinlik katılımları
- SEO görünürlüğü

Sistem önemli değişiklikleri özetler ve Growth Context Graph içine işler.

### 7.12 Battlecard ve Sales Play Modülü

Rekabet istihbaratı satış ekibinin kullanabileceği hale getirilmelidir.

Üretilen çıktılar:

- Competitor battlecard
- Rakip karşılaştırma özeti
- Objection handling guide
- Sales talk track
- Win loss insight
- Rakibe karşı güçlü argümanlar
- Zayıf kalınan noktalar
- Fiyat itirazlarına cevap taslağı
- Ürün karşılaştırma notları
- CRM opportunity bazlı öneriler

Battlecardlar statik doküman olmamalıdır. Rakipte önemli bir değişiklik olduğunda güncellenebilir olmalıdır.

### 7.13 Campaign Attribution Modülü

Sistem pazarlama ve satış aktivitelerinin gerçek gelir etkisini analiz eder.

Veri kaynakları:

- Google Ads
- Meta Ads
- LinkedIn Ads
- CRM opportunities
- ERP satışları
- Faturalar
- Siparişler
- Form submissions
- Call logs
- Email engagement
- Event participation
Sistem şu sorulara cevap vermelidir:

- Hangi kampanya lead getirdi?
- Hangi kampanya gerçek satışa dönüştü?
- Hangi kanal daha kaliteli müşteri üretti?
- Hangi müşteri segmenti daha iyi dönüştü?
- Hangi reklam harcaması satış etkisi oluşturdu?
- Hangi kampanya yalnızca etkileşim getirdi ama gelir oluşturmadı?
- Hangi ürün veya hizmet kampanyadan etkilendi?

Bu modül ürünün en önemli farklılaşma alanlarından biridir, çünkü birçok rakip CRM veya reklam performansında kalırken bu ürün CRM ve ERP geri beslemesini birlikte kullanır.

### 7.14 Social Media Strategy Modülü

Sistem sosyal medya içerik üretiminden önce strateji üretmelidir.

Analiz alanları:

- Platform bazlı performans
- Hedef kitle
- Rakip içerikleri
- Paylaşım zamanları
- Etkileşim oranı
- İçerik türleri
- Kampanya temaları
- Reklam bütçesi yönlendirmesi
- Segment bazlı mesajlaşma
- Satış etkisi
Çıktılar:

- Aylık sosyal medya stratejisi
- Kanal bazlı paylaşım önerisi
- İçerik briefi
- Kampanya teması
- Hedef kitle önerisi
- Reklam audience önerisi
- Rakip içerik fark analizi

### 7.15 AEO ve AI Search Visibility Modülü

Yeni arama davranışları yalnızca Google SEO ile sınırlı değildir. AI answer engine ve yapay zeka destekli arama sonuçlarında markanın görünürlüğü takip edilmelidir.

Sistem şu alanları analiz eder:

- Firma adı AI cevaplarında geçiyor mu?
- Ürün veya hizmet kategorilerinde firma öneriliyor mu?
- Rakipler AI cevaplarında nasıl konumlanıyor?
- Web sitesi yapısı AI sistemleri için anlaşılır mı?
- FAQ ve knowledge base eksikleri neler?
- Hangi içerikler answer engine visibility artırabilir?

Bu modül inbound büyüme için stratejik fark yaratır.

### 7.16 Knowledge Base Agent Modülü

Knowledge Base Agent, firmanın dokümanlarını, FAQ sayfalarını, ürün açıklamalarını, hizmet metinlerini, teklif şablonlarını ve geçmiş müşteri cevaplarını kullanarak müşteri sorularına destek olur.

Bu agent şu işleri yapmalıdır:

- Müşteri sorusuna bilgi tabanından cevap üretme
- Eksik bilgi alanlarını tespit etme
- Sık sorulan soruları raporlama
- Satış ekibine ürün açıklaması hazırlama
- Inbound taleplerde cevap taslağı üretme
- Bilgi tabanı güncelleme önerisi oluşturma

### 7.17 CRM Hygiene Modülü

Sistem CRM verilerinin kalitesini sürekli izler.

Kontroller:

- Duplicate kayıt
- Eksik e posta
- Eksik telefon
- Eksik firma bilgisi
- Sahipsiz opportunity
- Uzun süredir temas edilmeyen lead
- Yanlış segment
- Eksik consent bilgisi
- Güncel olmayan contact
- Kapanmamış görevler

Sistem düzeltme önerileri üretir ve gerekli durumlarda kullanıcı onayına sunar.

### 7.18 ERP Insight Modülü

ERP verileri yalnızca muhasebe veya operasyon verisi olarak kalmamalıdır. Sistem ERP verisini büyüme kararlarında kullanmalıdır.

Analiz alanları:

- Ürün bazlı satış
- Müşteri bazlı gelir
- Segment bazlı gelir
- Lokasyon bazlı satış
- Fatura durumu
- Tahsilat durumu
- Tekrar satın alma
- Kampanya sonrası satış değişimi
- Sezonsal dalgalanma
- Pasif müşteri fırsatları

Bu modül, pazarlama ve satış kararlarının gerçek iş sonuçlarıyla bağlantısını kurar.

### 7.19 Event Intelligence Modülü

Sistem gerçek dünyadaki etkinlikleri ve organizasyonları büyüme fırsatı olarak takip eder.

Takip alanları:

- Fuarlar
- Konferanslar
- Yerel etkinlikler
- Ticaret odası etkinlikleri
- Sektörel toplantılar
- Networking organizasyonları
- Sponsorluk fırsatları
- Okul ve toplum etkinlikleri
- Belediye etkinlikleri
- Pazar buluşmaları
Sistem firmaya şu önerileri sunar:

- Bu etkinliğe katılmalı
- Bu etkinlikte stand açmalı
- Bu etkinliğe sponsor olmalı
- Bu etkinlik için özel kampanya hazırlanmalı
- Bu etkinlikte hedeflenecek müşteri listesi çıkarılmalı
- Etkinlik sonrası takip workflowu başlatılmalı

## 8. Approval Center

Approval Center ürünün güven ve kontrol merkezidir.

Onay ekranında şu bilgiler gösterilmelidir:

- Önerilen aksiyon
- Hedef kişi veya firma
- Kullanılacak kanal
- Agent gerekçesi
- Kullanılan kanıtlar
- Risk seviyesi
- Consent durumu
- Platform policy durumu
- Tahmini etki
- Alternatif aksiyonlar
- Onaylayan kişi
- Onay zamanı
- Aksiyon sonrası sonuç
Risk seviyeleri:

#### Düşük risk

İç rapor, meeting brief, rakip özeti, CRM okuma, segment analizi gibi dış dünyaya doğrudan etki etmeyen işlemler.

#### Orta risk

E posta draftı, CRM alan güncellemesi, kampanya önerisi, sales play oluşturma gibi insan onayıyla ilerlemesi gereken işlemler.

#### Yüksek risk

E posta gönderimi, WhatsApp mesajı, outbound arama, sosyal medya mesajı, toplu CRM güncellemesi gibi dış dünyaya etki eden işlemler.

#### Kritik risk

ERP writeback, fiyat teklifi, indirim, sözleşme, finansal kayıt, fatura veya hukuki ifade içeren işlemler.

## 9. Güvenlik Gereksinimleri

Sistem güvenlik açısından enterprise standardına uygun tasarlanmalıdır.

Gereksinimler:

- Multi tenant isolation
- Role based access control
- Attribute based action control
- Tenant level data boundary
- API key encryption
- OAuth token güvenliği
- Secrets manager kullanımı
- Audit log zorunluluğu
- Data masking
- Sensitive data detection
- Prompt injection koruması
- Tool abuse koruması
- Connector permission boundary
- Session logging
- Human approval trail
- Kill switch
- Channel pause
- Model allowlist
- Data retention policy
- User activity tracking

## 10. Compliance Gereksinimleri

Compliance ürünün çekirdeğinde olmalıdır.

Sistem şu alanları desteklemelidir:

- Ticari e posta izni
- SMS izni
- Telefon araması kuralları
- WhatsApp opt in
- Opt out yönetimi
- Do not call list kontrolü
- Consent evidence saklama
- Veri kaynağı takibi
- Veri kullanım amacı
- Kişisel veri silme talebi
- Veri erişim talebi
- Platform policy enforcement
- Bölgesel privacy kuralları
- Auditlenebilir aksiyon geçmişi

Sistem özellikle LinkedIn, WhatsApp, Google Maps ve benzeri platformlarda kontrolsüz scraping veya otomatik mesajlaşma yaklaşımını desteklememelidir. Bunun yerine resmi API, onaylı sağlayıcı, reklam entegrasyonu veya müşteri tarafından yetkilendirilmiş kanal bağlantısı kullanılmalıdır.

## 11. Dashboard ve Kullanıcı Deneyimi

Ana dashboard, kullanıcının tüm büyüme operasyonunu tek bakışta görebileceği şekilde tasarlanmalıdır.

Dashboard alanları:

- Firma büyüme skoru
- Yeni fırsatlar
- Hot account listesi
- Buying signal uyarıları
- Rakip hareketleri
- Bekleyen onaylar
- Kampanya performansı
- Inbound talep dağılımı
- Outbound önerileri
- Voice call özetleri
- CRM sağlık skoru
- ERP bazlı satış etkisi
- Event fırsatları
- AEO visibility durumu
- Haftalık yönetici özeti

## 12. Raporlama Gereksinimleri

Sistem farklı kullanıcı grupları için farklı raporlar üretmelidir.

Rapor türleri:

- Executive Growth Report
- Weekly Growth Brief
- Competitor Intelligence Report
- Battlecard Update Report
- Lead Quality Report
- Account Priority Report
- Campaign Attribution Report
- CRM Health Report
- ERP Sales Insight Report
- Social Media Strategy Report
- AEO Visibility Report
- Event Opportunity Report
- Inbound Summary Report
- Voice Call Summary Report
- Compliance and Consent Report

Raporlar yalnızca metin olarak değil, aksiyon önerileriyle birlikte sunulmalıdır. Her raporda “önerilen sonraki adım” bulunmalıdır.

## 13. Observability ve Trust Layer

Sistem tüm agent ve workflow davranışlarını izlemelidir.

İzlenecek alanlar:

- Workflow run history
- Agent decision trace
- Model response trace
- Connector success rate
- Connector error rate
- Approval waiting time
- Aksiyon sonuçları
- Lead enrichment başarı oranı
- Veri güven skoru
- Policy violation attempt
- Model fallback oranı
- Human correction oranı
- Kullanıcı onay oranı
- Generated action outcome

Bu katman yöneticilere ve teknik ekibe sistemin neden böyle davrandığını görme imkanı verir.

## 14. Başarı Metrikleri

Ürünün başarısı yalnızca kaç lead bulunduğuyla ölçülmemelidir. Asıl başarı, bulunan leadlerin kalitesi, önerilerin doğruluğu, compliance güvenliği ve gerçek gelir etkisiyle ölçülmelidir.

Temel metrikler:

- Sales accepted lead oranı
- Lead to meeting dönüşüm oranı
- Meeting to opportunity dönüşüm oranı
- Opportunity to revenue dönüşüm oranı
- Lead enrichment confidence score
- Canonical entity match accuracy
- Outbound reply rate
- Bounce rate
- Unsubscribe oranı
- Policy violation sayısı
- Approval acceptance rate
- Human correction rate
- Campaign to revenue attribution accuracy
- CRM data completeness
- Inbound response time
- AI to human handoff completeness
- Battlecard update usefulness
- Executive report usage rate
- Workflow success rate
- Connector reliability

## 15. Rakiplere Göre Farklılaşma

### 15.1 Salesforce ve HubSpot’a Göre Fark

Salesforce ve HubSpot CRM ekosistemi içinde güçlüdür. Bu ürün ise CRM bağımsız ve connector based çalışmalıdır. Bir firma HubSpot, Salesforce, Zoho, Frappe veya yerel CRM kullanıyor olsa bile aynı context graph ve approval center üzerinden büyüme operasyonunu yönetebilmelidir.

### 15.2 Clay’e Göre Fark

Clay veri zenginleştirme ve GTM workflow tarafında güçlüdür. Bu ürün ise yalnızca enrichment değil, consent, policy, approval, CRM ve ERP geri beslemesi, voice, competitive intelligence ve campaign attribution katmanlarını da bağlar.

### 15.3 Apollo, Amplemarket, ZoomInfo ve 6sense’e Göre Fark

Bu araçlar lead, intent, outbound ve sales intelligence tarafında güçlüdür. Bu ürün ise satış zekasını firmanın tüm iş bağlamıyla birleştirir. Özellikle ERP verisi, campaign attribution, approval center ve compliance enforcement farklılaştırıcı alanlardır.

### 15.4 Twilio’ya Göre Fark

Twilio iletişim altyapısı sağlar. Bu ürün Twilio gibi sağlayıcıları connector olarak kullanabilir, fakat ürünün değeri arama yapmak değil, hangi aramanın neden yapılacağını, hangi bağlamla yapılacağını ve sonucunun CRM ile ERP kararlarına nasıl yansıyacağını yönetmektir.

### 15.5 Crayon’a Göre Fark

Crayon competitive intelligence tarafında güçlüdür. Bu ürün rakip bilgisini yalnızca izlemekle kalmaz, bunu lead scoring, sales play, campaign strategy ve executive decision support içine bağlar.

### 15.6 n8n’e Göre Fark

n8n workflow motoru olarak kullanılabilir. Ancak bu ürünün farkı, domain specific growth intelligence, policy engine, agent registry, context graph, consent ledger ve approval center katmanlarını ürünleştirmesidir.

## 16. Ürün Kapsamı

Sistem şu ana yetenekleri kapsamalıdır:

- Firma analizi
- Growth Context Graph
- Agent Registry
- Workflow Orchestration
- Policy Engine
- Consent Ledger
- Approval Center
- Lead Discovery
- Lead Enrichment
- Signal Fusion
- Lead Scoring
- Buying Group Detection
- Outbound Drafts
- Deliverability Health
- Inbound Intelligence
- Voice Call Intelligence
- Competitive Intelligence
- Battlecard Generation
- Campaign Attribution
- Social Media Strategy
- AEO Visibility
- Knowledge Base Agent
- CRM Hygiene
- ERP Insight
- Event Intelligence
- Model Gateway
- Connector Layer
- Observability
- Compliance Dashboard
- Executive Reporting

## 17. Ürün Dışı Kapsam

Sistem şu şekilde konumlandırılmamalıdır:

- Kontrolsüz scraping aracı
- Spam outbound platformu
- İnsan onayı olmadan çalışan tam otonom satış botu
- Sosyal medya hesaplarını kuralsız yöneten otomasyon aracı
- CRM’in tamamen yerine geçen sistem
- ERP’nin tamamen yerine geçen sistem
- Tek başına call center yazılımı
- Yalnızca içerik üretim aracı
- Yalnızca lead database
- Yalnızca chatbot

Bu sınırların açık olması ürünün hem güvenli hem de pazarda daha net konumlandırılmasını sağlar.

## 18. Sistem Davranış Kuralları

Agentlar şu kurallara göre çalışmalıdır:

- Kendi yetki alanı dışına çıkmamalıdır.
- Veri kaynağı belirsiz öneri üretmemelidir.
- Eksik veri varsa bunu açıkça belirtmelidir.
- Riskli aksiyonlarda insan onayı istemelidir.
- Dış iletişimde consent kontrolü yapmalıdır.
- Platform policy ihlali doğuracak aksiyonları önermemelidir.
- Her öneri için gerekçe sunmalıdır.
- Her aksiyon audit log üretmelidir.
- Hassas veriyi gereksiz yere modele göndermemelidir.
- Yanlış veya düşük güvenli veriyle otomatik aksiyon almamalıdır.

## 19. Genel Sonuç

Agentic Growth Intelligence Server fikri, pazardaki mevcut ürünlerin parçalı kaldığı bir alana konumlanabilir. En önemli fırsat, lead generation veya outbound automation gibi tekil bir alanı daha iyi yapmak değil, firmanın büyüme operasyonlarını tek bir güvenli, bağlam farkındalığına sahip ve onay kontrollü karar katmanında birleştirmektir.

Ürünün en güçlü çekirdeği şu dört bileşen olmalıdır:

- Growth Context Graph
- Policy Engine
- Approval Center
- CRM ve ERP geri beslemeli Action Orchestrator

Bu çekirdek doğru kurulursa sistem yalnızca satış ve pazarlama ekiplerine değil, firma yönetimine de stratejik karar desteği sağlayan güçlü bir büyüme altyapısına dönüşebilir.
