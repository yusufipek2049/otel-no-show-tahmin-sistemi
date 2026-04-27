# V1 / V2 Gap Analysis

## Amaç

Bu doküman, mevcut uygulamanın no-show tahmin sistemi olarak hangi seviyede olduğunu ve bir sonraki genişleme için hangi boşlukların kaldığını netleştirir.

Buradaki çerçeve:

- **V1**: booking-time no-show prediction + operasyon dashboardu
- **V2**: yönetim / iş dashboardu

---

## V1 Tanımı

V1 kapsamında sistemin aşağıdakileri sağlaması beklenir:

- rezervasyon verisini ingest edip temizleyebilmesi
- booking-time-safe feature seti üretebilmesi
- en az bir baseline ve bir güçlü aday model eğitebilmesi
- prediction çıktısı üretebilmesi
- operasyon ekibine riskli rezervasyon listesini gösterebilmesi
- rezervasyon detay ekranı sunabilmesi
- temel raporlama ve değerlendirme çıktıları gösterebilmesi

---

## V1 Mevcut Durum

### Var olanlar

- Eğitim hattı mevcut:
  - ingestion
  - feature build
  - temporal split
  - evaluation
  - artifact üretimi
- Temel veri modeli mevcut:
  - `reservations_raw`
  - `reservations_clean`
  - `reservation_features`
  - `predictions`
  - `reservation_actions`
- Backend API omurgası mevcut:
  - `GET /api/v1/dashboard/summary`
  - `GET /api/v1/reservations`
  - `GET /api/v1/reservations/{reservation_id}`
  - `GET /api/v1/reports/benchmark`
- Frontend operasyon ekranları mevcut:
  - `/dashboard`
  - `/reservations`
  - `/reservations/[reservationId]`
  - `/reports`
- Dashboard ekranı aşağıdaki çekirdek sinyalleri gösteriyor:
  - toplam rezervasyon
  - high risk rezervasyon sayısı
  - medium risk rezervasyon sayısı
  - son skorlama durumu
  - son riskli rezervasyon listesi
- Rezervasyon listesi filtrelenebilir:
  - otel
  - kanal
  - risk sınıfı
  - tarih aralığı
- Rezervasyon detay ekranı mevcut:
  - son skor
  - risk etiketi
  - giriş tarihi
  - rezervasyon bağlamı
  - bazı güvenli operasyon alanları
- Rapor ekranı model değerlendirme çıktıları gösterebiliyor:
  - PR-AUC
  - ROC-AUC
  - precision / recall / F1
  - threshold tablosu
  - top-k yakalama
  - Brier score

### Eksik olanlar

- Ayrı ve açık bir **live scoring / inference job** görünmüyor.
- Sistem daha çok eğitim artifact’lerinden veya persistence edilmiş prediction kayıtlarından besleniyor.
- `reservation_actions` tablosu var ama aksiyon oluşturma / güncelleme API’si görünmüyor.
- Frontend tarafında aksiyon formu, aksiyon geçmişi ve operasyon kapanış akışı yok.
- Dashboard’ta “aksiyon bekleyen”, “işlenen”, “tekrar kontrol edilecek” gibi operasyon durum alanları yok.
- Auth ve role-based access henüz scaffold seviyesinde veya eksik.

### V1 Kararı

Mevcut repo, V1’in önemli kısmını karşılıyor; ancak V1 tam bitmiş sayılmaz.

Pratik değerlendirme:

- **Modelleme ve değerlendirme tarafı:** büyük ölçüde mevcut
- **Operasyon görünürlüğü:** mevcut
- **Operasyon aksiyon akışı:** eksik
- **Canlı kullanım akışı:** eksik / belirsiz

---

## V1 İçin Kalan İşler

V1’i tamamlanmış saymak için öncelikli işler:

1. Prediction üretimini yalnızca training artifact akışından ayırıp net bir scoring akışı tanımla.
2. `reservation_actions` için write endpoint’leri ekle.
3. Rezervasyon detay ekranına aksiyon ekleme ve aksiyon geçmişi alanı koy.
4. Dashboard’a aksiyon durumu özetleri ekle.
5. Operasyonel kullanım için temel audit görünürlüğünü artır.

Önerilen minimum API genişlemeleri:

- `POST /api/v1/reservations/{reservation_id}/actions`
- `GET /api/v1/reservations/{reservation_id}/actions`
- gerekirse `PATCH /api/v1/actions/{action_id}`

---

## V2 Tanımı

V2 kapsamında sistem artık sadece riskli rezervasyon listesi veren operasyon aracı olmaktan çıkar ve yönetim / iş görünürlüğü de sunar.

Bu seviyede beklenen örnek çıktılar:

- no-show rate trendi
- cancellation vs no-show karşılaştırması
- kanal bazlı no-show görünümü
- segment bazlı risk / kayıp görünümü
- otel bazlı performans farkları
- tahmini gelir kaybı veya proxy loss metrikleri
- aksiyonların etkisi

---

## V2 Mevcut Durum

### Var olanlar

- `/reports` ekranı mevcut.
- Backend benchmark endpoint’i mevcut.
- Evaluation artifact’lerinden gelen karşılaştırma, threshold ve top-k tabloları gösterilebiliyor.

### Var olmayanlar

- Yönetim odaklı aggregate dashboard yok.
- No-show trend analizi yok.
- Cancellation vs no-show kıyası yok.
- Kanal bazlı aggregate no-show dashboard’u yok.
- Segment bazlı yönetim ekranı yok.
- Tahmini gelir kaybı metriği yok.
- Aksiyon etkisi raporu yok.
- Drift / dönemsel kalite takibi ekranı yok.

### V2 Kararı

Mevcut `/reports` ekranı bir **yönetim dashboard’u değil**, bir **model benchmark ekranı**dır.

Bu yüzden V2 henüz başlamış sayılmaz.

---

## V2 İçin Gerekli İşler

Önerilen ilk genişleme başlıkları:

1. Yönetim dashboard’u için ayrı aggregate endpoint’ler tasarla.
2. No-show ve cancellation kırılımlarını hesaplayan repository sorguları ekle.
3. `/reports` sayfasını ikiye ayır:
   - model benchmark görünümü
   - yönetim / iş görünümü
4. Gelir kaybı metriği için veri sözleşmesini netleştir.
5. Aksiyon etkisi takibi için `reservation_actions` verisini raporlama tarafına bağla.

Önerilen endpoint örnekleri:

- `GET /api/v1/reports/operations-summary`
- `GET /api/v1/reports/no-show-trends`
- `GET /api/v1/reports/channel-breakdown`
- `GET /api/v1/reports/segment-breakdown`
- `GET /api/v1/reports/action-effectiveness`

---

## Scope Notu

Burada önemli ayrım şudur:

- **No-show sistemine doğal olarak ait dashboardlar**:
  - risk kuyruğu
  - no-show trendi
  - kanal / segment bazlı risk
  - tahmini kayıp
  - aksiyon etkisi
- **Ayrı veri ekosistemi gerektiren dashboardlar**:
  - sessions
  - users
  - spend
  - CPC
  - CTR
  - ROAS
  - traffic funnel
  - campaign attribution

İkinci grup mevcut rezervasyon veri modeliyle doğal olarak gelmez; ek veri kaynakları gerekir.

---

## Sonuç

Mevcut repo için özet karar:

- **V1:** kısmen hazır, ama operasyon aksiyon katmanı ve net scoring akışı eksik
- **V2:** henüz mevcut değil; şu an yalnızca benchmark rapor ekranı var

En doğru ilerleme sırası:

1. V1 operasyon akışını tamamla
2. Yönetim dashboard’unu V2 olarak ekle
3. Marketing / traffic / spend tarzı dashboardları ancak veri sözleşmesi genişlediğinde değerlendir
