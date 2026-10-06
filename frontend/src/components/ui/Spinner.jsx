import "./ui.css";

function Spinner({ size = 20, label }) {
  return (
    <span className="ui-spinner-wrap" role="status" aria-live="polite">
      <span
        className="ui-spinner"
        style={{ width: size, height: size }}
        aria-hidden="true"
      />
      {label && <span className="ui-spinner-label">{label}</span>}
    </span>
  );
}

export default Spinner;
