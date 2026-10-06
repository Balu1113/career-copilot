import { Inbox } from "lucide-react";

import "./ui.css";

function EmptyState({ icon: Icon = Inbox, title, description, action }) {
  return (
    <div className="ui-empty-state">
      <span className="ui-empty-icon" aria-hidden="true">
        <Icon size={22} />
      </span>
      <h3>{title}</h3>
      {description && <p>{description}</p>}
      {action}
    </div>
  );
}

export default EmptyState;
