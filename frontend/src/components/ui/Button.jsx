import "./ui.css";

const VARIANTS = {
  primary: "ui-btn-primary",
  secondary: "ui-btn-secondary",
  ghost: "ui-btn-ghost",
  danger: "ui-btn-danger",
  accentSoft: "ui-btn-accent-soft",
};

const SIZES = {
  sm: "ui-btn-sm",
  md: "ui-btn-md",
  lg: "ui-btn-lg",
};

function Button({
  variant = "primary",
  size = "md",
  loading = false,
  disabled = false,
  className = "",
  children,
  type = "button",
  ...rest
}) {
  return (
    <button
      type={type}
      className={`ui-btn ${VARIANTS[variant]} ${SIZES[size]} ${className}`.trim()}
      disabled={disabled || loading}
      {...rest}
    >
      {loading && <span className="ui-btn-spinner" aria-hidden="true" />}
      {children}
    </button>
  );
}

export default Button;
