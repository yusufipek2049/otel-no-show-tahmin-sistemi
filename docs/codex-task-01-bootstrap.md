> Historical task spec. This file is kept as implementation history and is superseded by
> `docs/model-training-decision-record.md`, `docs/modeling-plan.md`, and `docs/model-card.md`.
> Do not use it as the current modeling policy.

Önce şu dosyaları oku ve talimat zinciri olarak kullan:

- AGENTS.md
- README.md
- docs/feature-policy.md
- docs/data-mapping.md
- docs/modeling-plan.md
- docs/model-tierlist.md
- docs/evaluation.md
- docs/acceptance-criteria.md
- docs/codex-task-01-bootstrap.md

Görev:
docs/codex-task-01-bootstrap.md içindeki işi uygula.

Bağlam:
Bu proje otel zinciri için booking-time no-show tahmin sistemi kuruyor.
Veri kaynağı H1.csv ve H2.csv.
İlk model saf no-show modeli olacak.

Hedef tanımı:
- no_show_flag = 1 if ReservationStatus == "No-Show"
- no_show_flag = 0 if ReservationStatus == "Check-Out"
- Canceled kayıtlarını ilk eğitim setinden çıkar

Zorunlu mimari:
Bu görev yalnızca notebook veya tek script üretmek için değildir.
PostgreSQL tabanlı çalışan bir uygulama omurgası kurulmalıdır.

Veritabanı zorunlulukları:
- PostgreSQL connection config ekle
- .env ile DATABASE_URL kullan
- SQLAlchemy setup kur
- Alembic migration yapısını kur
- docker-compose içinde postgres servisi tanımla
- En az şu tabloları oluştur:
  - reservations_raw
  - reservations_clean
  - reservation_features
  - predictions
  - reservation_import_batches
  - reservation_import_errors
  - reservation_actions
  - audit_logs

Frontend / web arayüzü zorunluluğu:
Bu projede internal web arayüzü zorunludur.
İlk görevde tam tasarım bitmek zorunda değil ama çalışan bir frontend iskeleti mutlaka kurulmalıdır.

Frontend gereksinimleri:
- Next.js tabanlı frontend scaffold kur
- basit bir operations dashboard route yapısı oluştur
- en az şu sayfalar veya route iskeletleri olsun:
  - /dashboard
  - /reservations
  - /reports
- backend API’ye bağlanacak client yapısını hazırla
- sade, iç kullanıcı odaklı bir arayüz yaklaşımı kullan
- marketing sitesi yapma

Kritik kurallar:
- ReservationStatus, ReservationStatusDate ve IsCanceled kolonlarını feature setine alma
- Booking-time modelde BookingChanges, DaysInWaitingList ve AssignedRoomType kullanma
- Leakage-safe feature policy’ye sadık kal
- Önce kısa bir plan yaz, sonra implementasyona geç
- Kod modüler olsun
- Varsayımları dokümante et
- H1.csv ve H2.csv birleşiminden çalışan bir veri hazırlama hattı kur

Model kuralları:
- Önce çok hafif bir heuristic olabilir ama zorunlu olarak Logistic Regression baseline kur
- Ana güçlü model olarak CatBoost kur
- İki modeli aynı veri split mantığında karşılaştır
- Zaman bazlı split kullan; random split kullanma
- Accuracy ana metrik olmasın

Zorunlu değerlendirme metrikleri:
- ROC-AUC
- PR-AUC
- Precision
- Recall
- F1
- calibration çıktıları için hazırlık
- mümkünse top-k analizi için altyapı

Beklenen çıktı:
- veri ingestion kodu
- veri temizleme ve mapping kodu
- leakage-safe feature engineering
- train/validation/test veya train/test zaman bazlı ayrım
- Logistic Regression training pipeline
- CatBoost training pipeline
- evaluation çıktıları
- kaydedilebilir prediction output yapısı
- PostgreSQL migration ve tablo yapısı
- docker-compose ile çalışan local database
- Next.js frontend scaffold
- dashboard / reservations / reports route iskeleti

İş bitmeden önce:
- mümkün olan testleri çalıştır
- en azından backend ve frontend’in ayağa kalkabildiğini doğrula
- changed files, assumptions, out-of-scope, run steps ve validation result başlıklarıyla özet ver
