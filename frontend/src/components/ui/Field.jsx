import { useId } from "react";

import "./ui.css";

function Field({
  label,
  hint,
  error,
  as = "input",
  className = "",
  ...rest
}) {
  const id = useId();
  const Tag = as;

  return (
    <div className={`ui-field ${className}`.trim()}>
      {label && (
        <label className="ui-label" htmlFor={id}>
          {label}
        </label>
      )}

      <Tag
        id={id}
        className={`ui-control ${error ? "ui-control-error" : ""}`.trim()}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${id}-error` : undefined}
        {...rest}
      />

      {error && (
        <p className="ui-field-error" id={`${id}-error`} role="alert">
          {error}
        </p>
      )}
      {!error && hint && <p className="ui-field-hint">{hint}</p>}
    </div>
  );
}

export default Field;
