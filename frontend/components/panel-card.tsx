type PanelCardProps = {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
};

export function PanelCard({ title, subtitle, children }: PanelCardProps) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <h2 className="panel-title">{title}</h2>
          {subtitle ? <div className="muted">{subtitle}</div> : null}
        </div>
      </div>
      {children}
    </section>
  );
}
