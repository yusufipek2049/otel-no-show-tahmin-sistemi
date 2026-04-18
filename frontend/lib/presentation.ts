const propertyNameMap: Record<string, string> = {
  CITY_H1: "Şehir Oteli 1",
  CITY_H2: "Şehir Oteli 2",
  RESORT_H1: "Tatil Oteli 1",
  RESORT_H2: "Tatil Oteli 2",
  Unavailable: "Hazır değil",
};

const riskLabelMap: Record<string, string> = {
  high: "Yüksek",
  medium: "Orta",
  low: "Düşük",
};

const metricLabelMap: Record<string, string> = {
  pr_auc: "PR-AUC",
  roc_auc: "ROC-AUC",
  precision: "Kesinlik",
  recall: "Duyarlılık",
  f1: "F1",
  calibration: "Kalibrasyon",
  brier_score: "Brier skoru",
};

const statusLabelMap: Record<string, string> = {
  planned: "Planlandı",
  pending: "Bekliyor",
  ready: "Hazır",
  complete: "Tamamlandı",
};

export function formatPropertyLabel(propertyId?: string | null): string {
  if (!propertyId) {
    return "-";
  }

  const normalized = propertyId.trim();
  if (propertyNameMap[normalized]) {
    return propertyNameMap[normalized];
  }

  const match = normalized.toUpperCase().match(/^(CITY|RESORT)_H(\d+)$/);
  if (match) {
    const hotelType = match[1] === "CITY" ? "Şehir Oteli" : "Tatil Oteli";
    return `${hotelType} ${match[2]}`;
  }

  return normalized.replaceAll("_", " ");
}

export function formatRiskLabel(riskClass?: string | null): string {
  if (!riskClass) {
    return "Bekleniyor";
  }

  return riskLabelMap[riskClass] ?? riskClass;
}

export function formatMetricLabel(metricName: string): string {
  return metricLabelMap[metricName] ?? metricName;
}

export function formatTopKSegmentLabel(segment: string): string {
  const topCountMatch = segment.match(/^top_(\d+)$/);
  if (topCountMatch) {
    return `İlk ${topCountMatch[1]} kayıt`;
  }

  const topPercentMatch = segment.match(/^top_(\d+)_percent$/);
  if (topPercentMatch) {
    return `İlk %${topPercentMatch[1]}`;
  }

  return segment.replaceAll("_", " ");
}

export function formatCandidateLabel(index: number): string {
  return `Aday ${index + 1}`;
}

export function formatStatusLabel(status: string): string {
  return statusLabelMap[status] ?? status;
}
