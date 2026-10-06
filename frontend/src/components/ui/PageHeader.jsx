import "./ui.css";

function PageHeader({ title, description, actions, children }) {
  return (
    <header className="ui-page-header">
      <div className="ui-page-header-text">
        <h1>{title}</h1>
        {description && <p>{description}</p>}
        {children}
      </div>
      {actions && <div className="ui-page-header-actions">{actions}</div>}
    </header>
  );
}

export default PageHeader;
