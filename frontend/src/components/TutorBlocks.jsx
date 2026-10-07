import { Terminal } from "lucide-react";
import "./TutorBlocks.css";

function Block({ block }) {
  if (!block || typeof block !== "object") {
    return null;
  }

  if (block.type === "heading") {
    return <h4 className="tutor-heading">{block.text}</h4>;
  }

  if (block.type === "paragraph") {
    return <p className="tutor-paragraph">{block.text}</p>;
  }

  if (block.type === "code") {
    return (
      <div className="tutor-code">
        <div className="tutor-code-header">
          <Terminal size={13} />
          <span>{block.language || "code"}</span>
        </div>

        <pre>
          <code>{block.code}</code>
        </pre>
      </div>
    );
  }

  if (block.type === "numbered_list") {
    const items = Array.isArray(block.items)
      ? block.items
      : [];

    if (items.length === 0) return null;

    return (
      <ol className="tutor-list">
        {items.map((item, index) => (
          <li key={index}>{item}</li>
        ))}
      </ol>
    );
  }

  if (block.type === "bullet_list") {
    const items = Array.isArray(block.items)
      ? block.items
      : [];

    if (items.length === 0) return null;

    return (
      <ul className="tutor-list">
        {items.map((item, index) => (
          <li key={index}>{item}</li>
        ))}
      </ul>
    );
  }

  return null;
}

function TutorBlocks({ content }) {
  if (!content || typeof content !== "object") {
    return null;
  }

  const blocks = Array.isArray(content.blocks)
    ? content.blocks
    : [];

  return (
    <div className="tutor-blocks">
      {blocks.map((block, index) => (
        <Block block={block} key={index} />
      ))}

      {content.practice_question ? (
        <div className="tutor-practice">
          <strong>Practice:</strong>{" "}
          {content.practice_question}
        </div>
      ) : null}
    </div>
  );
}

export function TutorSuggestions({
  suggestions,
  onPick,
}) {
  if (!suggestions || suggestions.length === 0) {
    return null;
  }

  return (
    <div className="tutor-suggestions">
      {suggestions.map((suggestion, index) => (
        <button
          type="button"
          key={index}
          onClick={() => onPick(suggestion)}
        >
          {suggestion}
        </button>
      ))}
    </div>
  );
}

export default TutorBlocks;
