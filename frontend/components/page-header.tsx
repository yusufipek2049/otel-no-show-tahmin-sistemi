type PageHeaderProps = {
  title: string;
  description: string;
  badges?: string[];
};

export function PageHeader({ title, description, badges = [] }: PageHeaderProps) {
  return (
    <section className="page-header">
      <div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>

      {badges.length > 0 ? (
        <div className="badge-row">
          {badges.map((badge) => (
            <span key={badge} className="pill">
              {badge}
            </span>
          ))}
        </div>
      ) : null}
    </section>
  );
}
