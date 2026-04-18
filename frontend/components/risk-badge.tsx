import { formatRiskLabel } from "@/lib/presentation";

type RiskBadgeProps = {
  riskClass?: string | null;
};

export function RiskBadge({ riskClass }: RiskBadgeProps) {
  if (!riskClass) {
    return <span className="pill">Bekleniyor</span>;
  }

  const className = `risk-badge ${
    riskClass === "high" ? "risk-high" : riskClass === "medium" ? "risk-medium" : "risk-low"
  }`;

  return <span className={className}>{formatRiskLabel(riskClass)}</span>;
}
