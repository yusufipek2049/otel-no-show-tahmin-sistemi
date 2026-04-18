# Hotel Chain No-Show Prediction System

Bu repo, otel zinciri için geliştirilen iç kullanım odaklı **booking-time no-show prediction** projesinin çalışma alanıdır.

İlk sürümün hedefi:
- rezervasyon verisini PostgreSQL üzerinde izlenebilir katmanlara ayırmak,
- backend ve frontend omurgasını kurmak,
- ileride eklenecek ingestion / feature / training işlerini aynı yapı üzerinde yürütmek.

## Current Bootstrap Scope

Bu commit ile eklenen çalışan temel omurga:
- PostgreSQL local development setup
- `docker-compose.yml` ile Postgres servisi
- FastAPI backend scaffold
- SQLAlchemy + Alembic setup
- ilk migration ile temel tablo yapısı
- Next.js frontend scaffold
- `/dashboard`, `/reservations`, `/reports` route iskeleti
- backend API client hazırlığı

Henüz tamamlanmayan kısımlar:
- benchmark çıktılarının frontend rapor ekranında daha zengin gösterimi

## Architecture

Repo yapısı:

```text
.
├── backend
│   ├── alembic
│   ├── app
│   │   ├── api
│   │   ├── core
│   │   ├── db
│   │   ├── jobs
│   │   ├── models
│   │   ├── repositories
│   │   ├── schemas
│   │   └── services
│   └── tests
├── docs
├── frontend
│   ├── app
│   ├── components
│   └── lib
└── docker-compose.yml
```

Backend modüler katmanlar kullanır:
- `api/`: route tanımları
- `services/`: iş akışı orchestration
- `repositories/`: SQLAlchemy sorguları
- `models/`: ORM modelleri
- `schemas/`: request / response sözleşmeleri
- `db/`: config ve session yönetimi

## Database Schema

İlk migration şu tabloları kurar:
- `reservation_import_batches`
- `reservation_import_errors`
- `reservations_raw`
- `reservations_clean`
- `reservation_features`
- `predictions`
- `reservation_actions`
- `audit_logs`

Tasarım mantığı:
- ham veri korunur
- clean katman leakage-adjacent kolonları saklayabilir
- feature katmanı booking-time-safe türetilmiş alanlar için ayrılır
- prediction ve action katmanları operasyon ekranı için temel oluşturur

## Environment

Örnek environment dosyası:

```bash
cp .env.example .env
```

Önemli değişkenler:
- `DATABASE_URL`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_PORT`
- `NEXT_PUBLIC_API_BASE_URL`

## How To Run

### 1. PostgreSQL başlat

Bu repo local geliştirme için Docker Compose üstünden Postgres bekler.

```bash
docker compose up -d postgres
```

### 2. Backend kur ve migrate et

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Backend varsayılan adresi:
- `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`

İlk endpointler:
- `GET /api/v1/health`
- `GET /api/v1/dashboard/summary`
- `GET /api/v1/reservations`
- `GET /api/v1/reservations/{reservation_id}`
- `GET /api/v1/reports/benchmark`

### 3. Frontend kur ve çalıştır

```bash
cd frontend
npm install
npm run dev
```

Frontend varsayılan adresi:
- `http://localhost:3000`

Hazır route’lar:
- `/dashboard`
- `/reservations`
- `/reports`

Frontend, `NEXT_PUBLIC_API_BASE_URL` üzerinden backend’e bağlanır. Backend kapalıysa boş durum fallback’leriyle yine açılır.
Gerçek dashboard / reservations / reports verisi görmek için önce training artifact üretmek gerekir:

```bash
cd backend
python3 -m app.jobs.train_booking_time_no_show --model-stage booking_time --download-if-missing
```

## Training Pipeline

Booking-time no-show eğitim hattı artık backend içinde modüler olarak hazır:
- ingestion: `backend/app/training/ingestion.py`
- cleaning / mapping: `backend/app/training/features.py`
- temporal split: `backend/app/training/split.py`
- evaluation: `backend/app/training/evaluation.py`
- persistence: `backend/app/training/persistence.py`
- CLI entrypoint: `backend/app/jobs/train_booking_time_no_show.py`

### Booking-time eğitim verisini indir ve modeli çalıştır

Yerelde `H1.csv` ve `H2.csv` yoksa script public kopyayı indirebilir.

```bash
cd backend
python3 -m pip install --user -r requirements.txt
python3 -m app.jobs.train_booking_time_no_show --model-stage booking_time --download-if-missing
```

İsteğe bağlı olarak raw / clean / features / predictions katmanlarını veritabanına da yazabilirsin:

```bash
cd backend
python3 -m app.jobs.train_booking_time_no_show \
  --model-stage booking_time \
  --download-if-missing \
  --database-url "postgresql+psycopg://postgres:postgres@localhost:5432/hotel_no_show"
```

Üretilen artifact klasörü:
- `backend/artifacts/booking_time_no_show/<timestamp>/`
- son çalışma için alias: `backend/artifacts/booking_time_no_show/latest/`

Temel çıktılar:
- `datasets/reservations_clean.csv`
- `datasets/reservation_features.csv`
- `reports/import_summary.json`
- `reports/split_summary.json`
- `reports/model_comparison.csv`
- `reports/evaluation_summary.json`
- `reports/*_threshold_metrics.csv`
- `reports/*_top_k_metrics.csv`
- `reports/*_calibration.csv`
- `predictions/logistic_regression_predictions.csv`
- `predictions/catboost_predictions.csv`
- `models/logistic_regression.joblib`
- `models/catboost_model.cbm`

### Snapshot tabanlı post-booking stage eğitimi

CLI artık stage-aware çalışır. `post_booking_day_1` ila `post_booking_day_4` stage'leri için `H1.csv` / `H2.csv` yeterli değildir; canonical snapshot CSV gerekir.

Örnek:

```bash
cd backend
python3 -m app.jobs.train_booking_time_no_show \
  --model-stage post_booking_day_1 \
  --snapshot-path /absolute/path/to/post_booking_day_1_snapshots.csv
```

Notlar:
- post-booking stage'ler `backend/artifacts/booking_time_no_show/<stage>/` altında ayrı artifact üretir
- bu stage'lerde DB persistence henüz açık değildir; önce artifact tabanlı benchmark amaçlanır
- snapshot CSV, `docs/modeling-plan.md` içindeki stage-aware sözleşmeye uymalıdır

### Feature ve leakage politikası

Training code şu kuralları kod içinde bloklar:
- `ReservationStatus`, `ReservationStatusDate`, `IsCanceled` feature setine girmez
- `BookingChanges`, `DaysInWaitingList`, `AssignedRoomType` booking-time modelde kullanılmaz
- `Canceled` kayıtları eğitim setinden çıkarılır
- split kuralı zaman bazlıdır: train `2015-2016`, test `2017`

## Development Notes

Bootstrap aşamasında bazı bilinçli sınırlar var:
- `ReservationStatus`, `ReservationStatusDate` ve `IsCanceled` feature setine dahil edilmedi; sadece raw / clean katmanda tutulmak üzere modellendi.
- `BookingChanges`, `DaysInWaitingList` ve `AssignedRoomType` clean katmanda saklanır ama v1 booking-time feature seti için dışarıda bırakılmalıdır.
- `IsHighSeason` için bootstrap varsayımı olarak `July` ve `August` ayları kullanıldı; bu kural ileride domain verisiyle tekrar ayarlanabilir.
- reports endpoint’i artifact varsa son training özetini okur; yoksa placeholder sözleşmeye geri düşer.

## Validation

Minimum doğrulama komutları:

```bash
cd backend
pytest
python3 -m compileall app
```

Node, npm veya Docker olmayan ortamlarda frontend ve compose komutları çalıştırılamaz; bu durumda dosya yapısı ve config seviyesinde doğrulama yapılır.

## Key Docs

- `AGENTS.md`
- `PLANS.md`
- `docs/modeling-plan.md`
- `docs/feature-policy.md`
- `docs/data-mapping.md`
- `docs/acceptance-criteria.md`
- `docs/codex-task-01-bootstrap.md`
