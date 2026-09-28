import { useEffect } from "react";

import {
  CheckCircle2,
  ShieldCheck,
  X,
} from "lucide-react";

import api from "../services/api";

import "./TemplatePreview.css";


const SAMPLE = {
  name: "Jordan Avery",
  role: "Product Engineer",
  contact:
    "jordan.avery@email.com  ·  +1 555 010 2233  ·  github.com/javery",

  summary:
    "Product engineer with 6+ years shipping web platforms used by " +
    "millions. Strong on frontend architecture, design systems and " +
    "performance work, comfortable across the stack from React to " +
    "PostgreSQL.",

  skills: [
    "JavaScript",
    "TypeScript",
    "React",
    "Node.js",
    "PostgreSQL",
    "AWS",
    "Docker",
    "CI/CD",
    "GraphQL",
    "Testing",
  ],

  experience: [
    {
      title: "Senior Product Engineer",
      company: "Northwind Labs",
      dates: "2021 – Present",
      bullets: [
        "Led the rebuild of the checkout flow, lifting conversion by 18%.",
        "Cut first-contentful-paint from 3.4s to 1.1s across 40 routes.",
        "Mentored 4 engineers and owned the design system.",
      ],
    },
    {
      title: "Software Engineer",
      company: "Bluepeak Systems",
      dates: "2018 – 2021",
      bullets: [
        "Built internal tooling that saved ~30 support hours a week.",
        "Migrated a legacy PHP app to a React + Node codebase.",
      ],
    },
  ],

  projects: [
    {
      title: "Open Source Form Kit",
      company: "github.com/javery/form-kit",
      dates: "2022",
      bullets: [
        "Accessible form primitives, 4.2k stars, used in 600+ repos.",
      ],
    },
  ],

  education: [
    {
      title: "B.Tech, Computer Science",
      company: "State University",
      dates: "2014 – 2018",
      bullets: [],
    },
  ],

  certifications: [
    {
      title: "AWS Certified Developer – Associate",
      company: "Amazon Web Services",
      dates: "2023",
      bullets: [],
    },
  ],

  publications: [
    {
      title: "Practical Design Systems for Small Teams",
      company: "Frontend Weekly",
      dates: "2023",
      bullets: [],
    },
  ],
};


const SECTION_TITLES = {
  summary: "Profile",
  skills: "Skills",
  experience: "Experience",
  projects: "Projects",
  education: "Education",
  certifications: "Certifications",
  publications: "Publications",
};

const DENSITY_LABELS = {
  compact: "Compact",
  comfortable: "Comfortable",
  airy: "Airy",
};

const HEADING_LABELS = {
  rule: "Rule under heading",
  bar: "Accent bar",
  caps: "Uppercase tracked",
  underline: "Bold underline",
};

const HEADER_LABELS = {
  centered: "Centred, twin rules",
  accent: "Accent bar beside name",
  minimal: "Tracked capitals",
  band: "Full-width banner",
  split: "Split header",
  boxed: "Name plate",
};

const SKILL_LABELS = {
  pipes: "Dot separated",
  chips: "Pill tags",
  grid: "Grid boxes",
};


function getSpec(template = {}) {
  const data = template.template_data || {};
  const preview = data.preview || {};

  return {
    accent: preview.accent || "#4f46e5",
    accentSoft: preview.accent_soft || "#eef2ff",
    headerStyle: preview.header_style || "centered",
    headingStyle: preview.heading_style || "bar",
    skillStyle: preview.skill_style || "chips",
    fontCss:
      preview.font_css ||
      (data.typography && data.typography.font) ||
      "Arial, Helvetica, sans-serif",
    fontLabel:
      preview.font_label ||
      (data.typography && data.typography.font) ||
      "Default",
    headerAlign:
      preview.header_align ||
      (data.header && data.header.alignment) ||
      "left",
    density: preview.density || "comfortable",
    columns:
      (data.layout && Number(data.layout.columns)) || 1,
  };
}


function mediaUrl(path) {
  if (!path) {
    return null;
  }

  if (/^https?:\/\//i.test(path)) {
    return path;
  }

  const base =
    api.defaults.baseURL || "http://127.0.0.1:8000/api";

  const origin = base.replace(/\/api\/?$/, "");

  return `${origin}${path.startsWith("/") ? "" : "/"}${path}`;
}


function ExperienceBlock({ sectionKey }) {
  const entries = SAMPLE[sectionKey] || [];

  return (
    <div className="tm-section">
      <h4 className="tm-h">
        {SECTION_TITLES[sectionKey]}
      </h4>

      {entries.map((entry) => (
        <div className="tm-entry" key={entry.title}>
          <div className="tm-entry-row">
            <strong>{entry.title}</strong>
            <span>{entry.dates}</span>
          </div>

          <div className="tm-entry-row tm-entry-sub">
            <em>{entry.company}</em>
          </div>

          {entry.bullets.map((bullet) => (
            <div className="tm-bullet" key={bullet}>
              {bullet}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}


function TemplateSection({ sectionKey, spec }) {
  if (sectionKey === "summary") {
    return (
      <div className="tm-section">
        <h4 className="tm-h">
          {SECTION_TITLES.summary}
        </h4>

        <p className="tm-paragraph">{SAMPLE.summary}</p>
      </div>
    );
  }

  if (sectionKey === "skills") {
    return (
      <div className="tm-section">
        <h4 className="tm-h">
          {SECTION_TITLES.skills}
        </h4>

        <SkillsList spec={spec} />
      </div>
    );
  }

  if (sectionKey === "education") {
    return (
      <div className="tm-section">
        <h4 className="tm-h">
          {SECTION_TITLES.education}
        </h4>

        <div className="tm-entry">
          <div className="tm-entry-row">
            <strong>{SAMPLE.education[0].title}</strong>
            <span>{SAMPLE.education[0].dates}</span>
          </div>

          <div className="tm-entry-row tm-entry-sub">
            <em>{SAMPLE.education[0].company}</em>
          </div>
        </div>
      </div>
    );
  }

  if (
    sectionKey === "certifications" ||
    sectionKey === "publications"
  ) {
    const entries = SAMPLE[sectionKey];

    return (
      <div className="tm-section">
        <h4 className="tm-h">
          {SECTION_TITLES[sectionKey]}
        </h4>

        <div className="tm-entry">
          <div className="tm-entry-row">
            <strong>{entries[0].title}</strong>
            <span>{entries[0].dates}</span>
          </div>

          <div className="tm-entry-row tm-entry-sub">
            <em>{entries[0].company}</em>
          </div>
        </div>
      </div>
    );
  }

  return (
    <ExperienceBlock
      sectionKey={
        sectionKey === "projects" ? "projects" : "experience"
      }
      spec={spec}
    />
  );
}


/**
 * The name block. Each template ships its own header treatment so
 * the six designs never look interchangeable.
 */
function TemplateHeader({ spec }) {
  const name = <div className="tm-name">{SAMPLE.name}</div>;
  const role = <div className="tm-role">{SAMPLE.role}</div>;
  const contact = (
    <div className="tm-contact">{SAMPLE.contact}</div>
  );

  switch (spec.headerStyle) {
    case "band":
      return (
        <header className="tm-header tm-header-band">
          <div className="tm-band">
            {name}
            {role}
          </div>

          <div className="tm-band-meta">{contact}</div>
        </header>
      );

    case "accent":
      return (
        <header className="tm-header tm-header-accent">
          <div className="tm-accent-block">
            {name}
            {role}
          </div>

          {contact}

          <div className="tm-accent-rule" />
        </header>
      );

    case "minimal":
      return (
        <header className="tm-header tm-header-minimal">
          {name}
          {role}
          {contact}

          <div className="tm-hairline" />
        </header>
      );

    case "split":
      return (
        <header className="tm-header tm-header-split">
          <div className="tm-split-name">
            {name}
            {role}
          </div>

          <div className="tm-split-contact">{contact}</div>

          <div className="tm-accent-rule" />
        </header>
      );

    case "boxed":
      return (
        <header className="tm-header tm-header-boxed">
          <div className="tm-plate">
            {name}
            {role}
          </div>

          {contact}
        </header>
      );

    case "centered":
    default:
      return (
        <header className="tm-header tm-header-centered">
          {name}
          {role}
          {contact}

          <div className="tm-double-rule" />
        </header>
      );
  }
}


/**
 * Skill list styles: pills, dot separated text or a boxed grid.
 */
function SkillsList({ spec }) {
  if (spec.skillStyle === "pipes") {
    return (
      <div className="tm-pipes">
        {SAMPLE.skills.map((skill, index) => (
          <span className="tm-pipe" key={skill}>
            {skill}
            {index < SAMPLE.skills.length - 1 && (
              <span className="tm-pipe-sep">·</span>
            )}
          </span>
        ))}
      </div>
    );
  }

  if (spec.skillStyle === "grid") {
    return (
      <div className="tm-skill-grid">
        {SAMPLE.skills.map((skill) => (
          <span key={skill}>{skill}</span>
        ))}
      </div>
    );
  }

  return (
    <div className="tm-chips">
      {SAMPLE.skills.map((skill) => (
        <span className="tm-chip" key={skill}>
          {skill}
        </span>
      ))}
    </div>
  );
}


/**
 * A design mock of a template rendered as an A4 page.
 *
 * Everything inside is sized in container units so the same markup
 * works as a small card thumbnail and as a large modal preview.
 */
export function TemplateMock({ template, className = "" }) {
  const spec = getSpec(template);

  const data = template.template_data || {};
  const sections =
    Array.isArray(data.sections) && data.sections.length > 0
      ? data.sections
      : [
          "summary",
          "skills",
          "experience",
          "education",
        ];

  return (
    <div
      className={`tm-frame ${className}`}
      style={{
        "--tm-accent": spec.accent,
        "--tm-accent-soft": spec.accentSoft,
        "--tm-font": spec.fontCss,
      }}
    >
      <div className="tm-page">
        <TemplateHeader spec={spec} />

        <div
          className={`tm-body tm-density-${spec.density}`}
        >
          {sections.map((sectionKey) => (
            <TemplateSection
              key={sectionKey}
              sectionKey={sectionKey}
              spec={spec}
            />
          ))}
        </div>
      </div>
    </div>
  );
}


function TemplatePreviewModal({
  template,
  isSelected,
  onSelect,
  onClose,
}) {
  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    window.addEventListener("keydown", handleKeyDown);

    return () =>
      window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  if (!template) {
    return null;
  }

  const spec = getSpec(template);
  const data = template.template_data || {};

  const fileUrl = mediaUrl(template.sample_file);
  const canShowFile =
    Boolean(fileUrl) && template.file_type === "pdf";

  const columns =
    (data.layout && Number(data.layout.columns)) || 1;

  return (
    <div
      className="tpm-overlay"
      role="dialog"
      aria-modal="true"
      aria-label={`${template.name} preview`}
      onClick={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
    >
      <div className="tpm-modal">
        <div className="tpm-header">
          <div className="tpm-title">
            <h2>{template.name}</h2>

            <div className="tpm-badges">
              <span
                className={`tpm-badge ${
                  template.is_builtin
                    ? "tpm-badge-accent"
                    : ""
                }`}
              >
                {template.is_builtin
                  ? "ATS template"
                  : "Your upload"}
              </span>

              {template.ats_score ? (
                <span className="tpm-badge tpm-badge-score">
                  <ShieldCheck size={13} />
                  ATS {template.ats_score}
                </span>
              ) : null}
            </div>
          </div>

          <button
            type="button"
            className="tpm-close"
            onClick={onClose}
            aria-label="Close preview"
          >
            <X size={20} />
          </button>
        </div>

        <div className="tpm-body">
          <div className="tpm-preview">
            <div className="tpm-preview-label">
              {canShowFile
                ? "Uploaded sample resume"
                : "Design preview with sample content"}
            </div>

            {canShowFile ? (
              <iframe
                className="tpm-frame"
                title={`${template.name} sample`}
                src={`${fileUrl}#toolbar=0&view=FitH`}
              />
            ) : (
              <TemplateMock
                template={template}
                className="tm-large"
              />
            )}

            <p className="tpm-preview-note">
              {template.file_type === "docx"
                ? "DOCX samples cannot be rendered in the browser, so this is a design preview built from the analysed layout."
                : "Your resume content replaces this sample text when the resume is generated."}
            </p>
          </div>

          <div className="tpm-info">
            <p className="tpm-description">
              {template.description ||
                "A sample resume you uploaded. Its font, spacing and section styles are analysed and reused for every resume you generate."}
            </p>

            <dl className="tpm-specs">
              <div>
                <dt>Font</dt>
                <dd>{spec.fontLabel}</dd>
              </div>

              <div>
                <dt>Layout</dt>
                <dd>
                  {columns > 1
                    ? `${columns} columns`
                    : "Single column"}
                </dd>
              </div>

              <div>
                <dt>Name block</dt>
                <dd>
                  {HEADER_LABELS[spec.headerStyle] || "Standard"}
                </dd>
              </div>

              <div>
                <dt>Skill list</dt>
                <dd>
                  {SKILL_LABELS[spec.skillStyle] || "Standard"}
                </dd>
              </div>

              <div>
                <dt>Section headings</dt>
                <dd>
                  {HEADING_LABELS[spec.headingStyle] ||
                    "Standard"}
                </dd>
              </div>

              <div>
                <dt>Spacing</dt>
                <dd>
                  {DENSITY_LABELS[spec.density] ||
                    "Comfortable"}
                </dd>
              </div>

              <div>
                <dt>Body size</dt>
                <dd>
                  {(data.typography &&
                    data.typography.body_size) ||
                    "11"}
                  pt
                </dd>
              </div>
            </dl>

            <div className="tpm-ats">
              <h3>
                <ShieldCheck size={15} />
                Why it passes ATS
              </h3>

              <ul>
                <li>
                  Single-column flow, so parsers read it top to
                  bottom.
                </li>
                <li>
                  Standard section names — no tables, text boxes
                  or graphics.
                </li>
                <li>
                  Real selectable text with a widely installed
                  font.
                </li>
                <li>
                  Contact details and headings are machine
                  readable.
                </li>
              </ul>
            </div>
          </div>
        </div>

        <div className="tpm-footer">
          <button
            type="button"
            className="tpm-button tpm-button-ghost"
            onClick={onClose}
          >
            Close
          </button>

          <button
            type="button"
            className={`tpm-button tpm-button-primary ${
              isSelected ? "tpm-button-done" : ""
            }`}
            onClick={() => onSelect(template)}
            disabled={isSelected}
          >
            {isSelected ? (
              <>
                <CheckCircle2 size={16} />
                Selected
              </>
            ) : (
              <>Use this template</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export default TemplatePreviewModal;
