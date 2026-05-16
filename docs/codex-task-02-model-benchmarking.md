> Historical task spec. This file is kept as implementation history and is superseded by
> `docs/model-training-decision-record.md`, `docs/modeling-plan.md`, and `docs/model-tierlist.md`.
> Do not use it as the current modeling policy.

Önce şu dosyaları tekrar oku:

- AGENTS.md
- README.md
- docs/modeling-plan.md
- docs/model-tierlist.md
- docs/evaluation.md
- docs/acceptance-criteria.md
- docs/codex-task-02-model-benchmarking.md

Görev:
docs/codex-task-02-model-benchmarking.md içindeki işi uygula.

Amaç:
İlk benchmark hattını Tier-list mantığına göre genişlet ve web arayüzünü backend ile daha görünür biçimde bağla.

Model tier sırası:
Tier 1:
- CatBoost
- LightGBM
- XGBoost

Tier 2:
- Logistic Regression

Tier 3:
- Random Forest

Tier 4 ve Tier 5:
- şimdilik implement etmek zorunda değilsin
- future work veya not olarak ekleyebilirsin

Kurallar:
- Mevcut leakage-safe feature policy’ye uy
- Aynı hedef tanımını koru
- Aynı zaman bazlı split mantığını koru
- Tüm modelleri adil kıyas için aynı veri hazırlama akışıyla değerlendir
- Feature setini modelin doğasına göre dikkatli işle ama hedef bilgisi sızdırma
- Eğer bazı modeller ek bağımlılık gerektiriyorsa bunu açıkça dokümante et

Zorunlu değerlendirme:
Her model için ayrı ayrı hesapla:
- ROC-AUC
- PR-AUC
- Precision at action threshold
- Recall at action threshold
- F1 at threshold
- Recall at top-k
- calibration değerlendirmesi
- Brier score mümkünse ekle

Operasyonel bakış:
- Yalnızca genel skor değil, aksiyon alınabilirlik de raporlansın
- Top 25, Top 50, Top 100 veya uygun yüzde dilimleri için recall göster
- Threshold tablosu üret
- Model comparison tablosu üret

Web arayüzü geliştirme zorunluluğu:
Bu görevde frontend sadece scaffold halinde kalmamalı.
Çalışan ilk operasyon paneli kurulmalı.

Frontend gereksinimleri:
- dashboard sayfasında riskli rezervasyon listesi göster
- filters ekle:
  - property / hotel
  - date range
  - booking channel
  - risk class
- reservation detail page veya drawer ekle
- reports sayfasında temel model kıyas sonuçlarını göster
- action threshold ve top-k özetlerini kullanıcıya göster
- sade, hızlı ve iç kullanıcı odaklı tasarım kullan

Backend API gereksinimleri:
- latest predictions list endpoint
- reservation detail endpoint
- benchmark / report endpoint
- threshold ve top-k sonuçlarını dönen rapor endpointleri
- frontend bu endpointlere bağlansın

Beklenen çıktı:
- benchmark pipeline
- model karşılaştırma tablosu
- evaluation report
- mümkünse csv/json özetleri
- çalışan dashboard listesi
- çalışan detail görünümü
- çalışan reports görünümü
- hangi modelin neden önde olduğuna dair kısa yorum
- hangi modelin prod adayı olduğuna dair öneri

Karar mantığı:
- Tek başına ROC-AUC ile karar verme
- Öncelik PR-AUC, recall at top-k, precision at threshold ve calibration’da olsun
- Logistic Regression güçlü baseline olarak kalsın
- CatBoost, LightGBM ve XGBoost ana yarışmacılar olarak kıyaslansın
- Random Forest referans benchmark olarak raporlansın

İş bitmeden önce:
- backend ve frontend için çalıştırdığın komutları yaz
- üretilen dosyaları listele
- changed files, assumptions, out-of-scope, validation result ve recommended next step başlıklarıyla özet ver
