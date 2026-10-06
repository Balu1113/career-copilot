import "./ui.css";

function Card({ className = "", title, description, actions, children, ...rest }) {
  return (
    <section className={`ui-card ${className}`.trim()} {...rest}>
      {(title || actions) && (
        <header className="ui-card-header">
          <div>
            {title && <h2 className="ui-card-title">{title}</h2>}
            {description && <p className="ui-card-description">{description}</p>}
          </div>
          {actions && <div className="ui-card-actions">{actions}</div>}
        </header>
      )}
      {children}
    </section>
  );
}

export default Card;
