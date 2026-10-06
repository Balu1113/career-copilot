import "./ui.css";

const TONES = {
  neutral: "ui-badge-neutral",
  accent: "ui-badge-accent",
  success: "ui-badge-success",
  danger: "ui-badge-danger",
  warning: "ui-badge-warning",
  info: "ui-badge-info",
};

function Badge({ tone = "neutral", className = "", children }) {
  return (
    <span className={`ui-badge ${TONES[tone]} ${className}`.trim()}>
      {children}
    </span>
  );
}

export default Badge;
