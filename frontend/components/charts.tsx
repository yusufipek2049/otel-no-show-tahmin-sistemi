import { formatTopKSegmentLabel } from "@/lib/presentation";
import type { DimensionBreakdownRow, TrendPoint, BenchmarkReport } from "@/lib/types";

type ChartPoint = {
  label: string;
  value: number;
};

type TrendChartProps = {
  points: TrendPoint[];
};

type ChannelRiskChartProps = {
  rows: DimensionBreakdownRow[];
};

type CaptureChartProps = {
  rows: BenchmarkReport["top_k_tables"][string];
};

function clampPercent(value: number): number {
  return Math.max(0, Math.min(100, value * 100));
}

function buildPolyline(points: ChartPoint[], width: number, height: number, maxValue: number): string {
  if (points.length === 1) {
    const y = height - (points[0].value / maxValue) * height;
    return `0,${y.toFixed(2)} ${width},${y.toFixed(2)}`;
  }

  return points
    .map((point, index) => {
      const x = (index / Math.max(points.length - 1, 1)) * width;
      const y = height - (point.value / maxValue) * height;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(" ");
}

export function TrendLineChart({ points }: TrendChartProps) {
  if (points.length === 0) {
    return <div className="empty-state">Grafik için henüz trend verisi yok.</div>;
  }

  const chartWidth = 640;
  const chartHeight = 180;
  const noShowPoints = points.map((point) => ({
    label: point.period,
    value: clampPercent(point.no_show_rate),
  }));
  const cancelPoints = points.map((point) => ({
    label: point.period,
    value: clampPercent(point.cancellation_rate),
  }));
  const maxValue = Math.max(1, ...noShowPoints.map((point) => point.value), ...cancelPoints.map((point) => point.value));

  return (
    <div className="chart-card" aria-label="Gerçekleşmeme ve iptal trend grafiği">
      <svg className="line-chart" viewBox={`0 0 ${chartWidth} ${chartHeight}`} role="img">
        <title>Gerçekleşmeme ve iptal trendi</title>
        {[0.25, 0.5, 0.75].map((ratio) => (
          <line
            key={ratio}
            x1="0"
            x2={chartWidth}
            y1={chartHeight * ratio}
            y2={chartHeight * ratio}
            className="chart-grid-line"
          />
        ))}
        <polyline
          points={buildPolyline(cancelPoints, chartWidth, chartHeight, maxValue)}
          className="chart-line chart-line-secondary"
        />
        <polyline
          points={buildPolyline(noShowPoints, chartWidth, chartHeight, maxValue)}
          className="chart-line chart-line-primary"
        />
      </svg>
      <div className="chart-footer">
        <span>{points[0]?.period}</span>
        <span>{points.at(-1)?.period}</span>
      </div>
      <div className="chart-legend">
        <span><i className="legend-dot legend-primary" />Gerçekleşmeme</span>
        <span><i className="legend-dot legend-secondary" />İptal</span>
      </div>
    </div>
  );
}

export function ChannelRiskChart({ rows }: ChannelRiskChartProps) {
  const visibleRows = rows.slice(0, 6);

  if (visibleRows.length === 0) {
    return <div className="empty-state">Grafik için henüz kanal verisi yok.</div>;
  }

  const maxTotal = Math.max(1, ...visibleRows.map((row) => row.total_reservations));

  return (
    <div className="bar-chart" aria-label="Kanal bazlı risk dağılımı">
      {visibleRows.map((row) => {
        const highRiskWidth = (row.high_risk_reservations / maxTotal) * 100;
        const totalWidth = (row.total_reservations / maxTotal) * 100;

        return (
          <div className="bar-row" key={row.dimension_value}>
            <div className="bar-label">
              <strong>{row.dimension_value}</strong>
              <span>{row.high_risk_reservations} yüksek risk</span>
            </div>
            <div className="bar-track" title={`${row.total_reservations} rezervasyon`}>
              <span className="bar-total" style={{ width: `${totalWidth}%` }} />
              <span className="bar-risk" style={{ width: `${highRiskWidth}%` }} />
            </div>
            <div className="bar-value">{(row.no_show_rate * 100).toFixed(1)}%</div>
          </div>
        );
      })}
      <div className="chart-legend">
        <span><i className="legend-dot legend-primary" />Yüksek risk</span>
        <span><i className="legend-dot legend-muted" />Toplam rezervasyon</span>
      </div>
    </div>
  );
}

export function CaptureBarChart({ rows }: CaptureChartProps) {
  if (rows.length === 0) {
    return <div className="empty-state">Grafik için henüz yakalama verisi yok.</div>;
  }

  return (
    <div className="capture-chart" aria-label="Liste boyutuna göre yakalama grafiği">
      {rows.map((row) => {
        const recallPercent = clampPercent(row.recall);

        return (
          <div className="capture-column" key={row.segment}>
            <div className="capture-bar-wrap">
              <span className="capture-bar" style={{ height: `${Math.max(3, recallPercent)}%` }} />
            </div>
            <strong>{recallPercent.toFixed(1)}%</strong>
            <span>{formatTopKSegmentLabel(row.segment)}</span>
          </div>
        );
      })}
    </div>
  );
}
