# Hotel Chain No-Show Prediction System

Bu repo, otel zinciri için geliştirilen iç kullanım odaklı **booking-time no-show prediction** sistemidir.

Mevcut kapsam:

- **V1**: no-show modelleme hattı + operasyon dashboardu
- **V2 başlangıcı**: no-show sistemine doğal olarak ait yönetim / iş raporları

Kapsam dışı:

- traffic / spend / ROAS / CPC / CTR dashboardları
- marketing attribution
- generic revenue BI ürünü

Bağlayıcı kapsam özeti için:

- `docs/v1-v2-gap-analysis.md`

## Current Product State

Şu anda repo aşağıdaki uçtan uca parçaları içerir:

- booking-time no-show eğitim hattı
- artifact üretimi
- prediction persistence için veri modeli
- operasyon dashboardu
- riskli rezervasyon listesi
- rezervasyon detay görünümü
- aksiyon oluşturma / güncelleme akışı
- benchmark rapor ekranı
- ilk yönetim raporları:
  - no-show trendi
  - cancellation vs no-show özeti
  - kanal bazlı kırılım
  - segment bazlı kırılım
  - aksiyon etkisi özeti

## Architecture

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
│   │   ├── services
│   │   └── training
│   └── tests
├── data
├── docs
├── frontend
│   ├── app
│   ├── components
│   └── lib
└── docker-compose.yml
```

Backend katmanları:

- `api/`: route tanımları
- `services/`: iş akışı orchestration
- `repositories/`: veri erişimi
- `models/`: ORM modelleri
- `schemas/`: request / response sözleşmeleri
- `training/`: eğitim, split, evaluation, persistence

## Database Schema

İlk migration şu ana tabloları kurar:

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
- clean katman hedefe yakın ama modelden dışlanacak alanları da saklayabilir
- feature katmanı booking-time-safe feature seti için ayrıdır
- predictions katmanı operasyon ekranlarını besler
- reservation actions katmanı manuel müdahaleyi kaydeder

## Scoring and Data Source Model

Uygulama operasyon ekranlarını iki moddan biriyle besler:

1. **DB prediction store**
   - `predictions` tablosunda persistence edilmiş skorlar varsa bu kaynak tercih edilir
   - aksiyon yazma akışı bu modda aktiftir

2. **Artifact fallback**
   - DB tarafında prediction store hazır değilse son training artifact okunur
   - bu mod read-only kabul edilir
   - dashboard ve reports yine çalışır ama action analytics sınırlıdır

Bu seçim özellikle `/dashboard`, `/reservations/[id]` ve `/reports` ekranlarında görünür hale getirilmiştir.

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

Backend varsayılan adresleri:

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`

### 3. Frontend kur ve çalıştır

```bash
cd frontend
npm install
npm run dev
```

Frontend varsayılan adresi:

- `http://localhost:3000`

## Main API Endpoints

Çekirdek endpointler:

- `GET /api/v1/health`
- `GET /api/v1/dashboard/summary`
- `GET /api/v1/reservations`
- `GET /api/v1/reservations/{reservation_id}`
- `GET /api/v1/reservations/{reservation_id}/actions`
- `POST /api/v1/reservations/{reservation_id}/actions`
- `PATCH /api/v1/actions/{action_id}`

Benchmark ve yönetim raporları:

- `GET /api/v1/reports/benchmark`
- `GET /api/v1/reports/operations-summary`
- `GET /api/v1/reports/no-show-trends`
- `GET /api/v1/reports/channel-breakdown`
- `GET /api/v1/reports/segment-breakdown`
- `GET /api/v1/reports/action-effectiveness`

## Frontend Routes

- `/dashboard`
  - operasyon özeti
  - riskli rezervasyon listesi
  - aksiyon sayacı
  - scoring source görünümü

- `/reservations`
  - filtrelenebilir rezervasyon kuyruğu

- `/reservations/[reservationId]`
  - rezervasyon detay görünümü
  - son skor
  - güvenli bağlamsal alanlar
  - aksiyon ekleme / güncelleme / geçmişi

- `/reports`
  - benchmark görünümü
  - no-show yönetim raporları

## Training Pipeline

Booking-time no-show eğitim hattı modüler olarak hazırdır:

- ingestion: `backend/app/training/ingestion.py`
- cleaning / mapping: `backend/app/training/features.py`
- temporal split: `backend/app/training/split.py`
- evaluation: `backend/app/training/evaluation.py`
- persistence: `backend/app/training/persistence.py`
- CLI entrypoint: `backend/app/jobs/train_booking_time_no_show.py`

### Booking-time modeli çalıştır

Yerelde `H1.csv` ve `H2.csv` yoksa script public kopyayı indirebilir.

```bash
cd backend
python3 -m pip install --user -r requirements.txt
python3 -m app.jobs.train_booking_time_no_show --model-stage booking_time --download-if-missing
```

### Prediction store'u DB'ye yaz

```bash
cd backend
python3 -m app.jobs.train_booking_time_no_show \
  --model-stage booking_time \
  --download-if-missing \
  --database-url "postgresql+psycopg://postgres:postgres@localhost:5432/hotel_no_show"
```

Bu akış:

- raw / clean / feature katmanını
- model prediction çıktılarını

DB tarafına persist eder. Uygulama daha sonra operasyon ekranlarında bunu **DB prediction store** olarak kullanır.

### Üretilen artifact yapısı

- `backend/artifacts/booking_time_no_show/<timestamp>/`
- `backend/artifacts/booking_time_no_show/latest/`

Başlıca çıktılar:

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

### Snapshot tabanlı post-booking stage eğitimi

`post_booking_day_1` ila `post_booking_day_4` stage'leri için `H1.csv` / `H2.csv` yeterli değildir; canonical snapshot CSV gerekir.

Örnek:

```bash
cd backend
python3 -m app.jobs.train_booking_time_no_show \
  --model-stage post_booking_day_1 \
  --snapshot-path /absolute/path/to/post_booking_day_1_snapshots.csv
```

Notlar:

- post-booking stage artifact’leri ayrı klasör altında yazılır
- bu stage'lerde DB persistence henüz açık değildir
- snapshot sözleşmesi `docs/modeling-plan.md` ile uyumlu olmalıdır

## Feature and Leakage Policy

Training code şu kuralları uygular:

- `ReservationStatus`, `ReservationStatusDate`, `IsCanceled` feature setine girmez
- `BookingChanges`, `DaysInWaitingList`, `AssignedRoomType` booking-time modelde kullanılmaz
- `Canceled` kayıtları ilk no-show eğitim setinden çıkarılır
- split kuralı zaman bazlıdır: train `2015-2016`, test `2017`

Detay için:

- `docs/feature-policy.md`
- `docs/modeling-plan.md`
- `docs/evaluation.md`

## Development Notes

- Aksiyon yazma akışı yalnızca DB-backed kullanım modunda anlamlıdır; artifact fallback read-only kabul edilir.
- Yönetim raporları intentionally no-show sistemine doğal kırılımlarla sınırlıdır.
- Revenue / traffic / marketing BI kapsamı bu repo için hedef değildir.
- Auth ve role-based access henüz tamamlanmış değildir.

## Validation

Backend doğrulama:

```bash
cd backend
pytest
python3 -m compileall app
```

Frontend doğrulama:

```bash
cd frontend
npm run typecheck
```

## Key Docs

- `AGENTS.md`
- `PLANS.md`
- `docs/v1-v2-gap-analysis.md`
- `docs/modeling-plan.md`
- `docs/feature-policy.md`
- `docs/data-mapping.md`
- `docs/evaluation.md`
- `docs/acceptance-criteria.md`

## Short Roadmap

Yakın vadede mantıklı sıradaki işler:

1. scoring akışını batch/live kullanım açısından daha net operationalize etmek
2. aksiyon analitiğini zenginleştirmek
3. yönetim raporlarında period comparison ve drill-down eklemek
4. auth / role-based access tarafını tamamlamak
