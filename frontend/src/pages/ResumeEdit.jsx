import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  AlertCircle,
  ArrowLeft,
  Award,
  Bot,
  Briefcase,
  CheckCircle2,
  Code2,
  Download,
  FolderKanban,
  GraduationCap,
  Loader2,
  Plus,
  Save,
  Sparkles,
  Trash2,
  User,
} from "lucide-react";

import api from "../services/api";

import "./ResumeEdit.css";

const emptyResumeContent = {
  personal: {
    name: "",
    email: "",
    phone: "",
    location: "",
    linkedin: "",
    github: "",
    website: "",
  },
  summary: "",
  skills: {},
  experience: [],
  projects: [],
  education: [],
  certifications: [],
  publications: [],
};

const emptyExperience = {
  company: "",
  role: "",
  location: "",
  start_date: "",
  end_date: "",
  current: false,
  bullets: [""],
};

const emptyProject = {
  name: "",
  description: "",
  technologies: [],
  url: "",
  bullets: [""],
};

const emptyEducation = {
  degree: "",
  institution: "",
  location: "",
  start_date: "",
  end_date: "",
  grade: "",
};

const emptyCertification = {
  name: "",
  issuer: "",
  date: "",
  url: "",
};

const emptyPublication = {
  title: "",
  authors: "",
  venue: "",
  date: "",
  url: "",
};

const personalFields = [
  { key: "name", label: "Full Name" },
  { key: "email", label: "Email" },
  { key: "phone", label: "Phone" },
  { key: "location", label: "Location" },
  { key: "linkedin", label: "LinkedIn" },
  { key: "github", label: "GitHub" },
  { key: "website", label: "Website" },
];

const requiredSummarySections = [
  { key: "personal", label: "Personal Information" },
  { key: "experience", label: "Experience" },
  { key: "education", label: "Education" },
  { key: "skills", label: "Skills" },
  { key: "certifications", label: "Certifications" },
  { key: "projects", label: "Projects" },
];

const isFilled = (value) => {
  if (value === null || value === undefined) return false;

  if (Array.isArray(value)) {
    return value.some((item) => isFilled(item));
  }

  if (typeof value === "object") {
    return Object.values(value).some((item) => isFilled(item));
  }

  return String(value).trim().length > 0;
};

const missingSummarySections = (content) => {
  if (!content) return requiredSummarySections;

  return requiredSummarySections.filter(
    ({ key }) => !isFilled(content[key])
  );
};

function Field({
  label,
  value,
  onChange,
  placeholder = "",
  type = "text",
}) {
  return (
    <div className="ed-field">
      <label>{label}</label>

      <input
        type={type}
        value={value || ""}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}

function TextAreaField({
  label,
  value,
  onChange,
  placeholder = "",
  rows = 5,
}) {
  return (
    <div className="ed-field">
      {label && <label>{label}</label>}

      <textarea
        rows={rows}
        value={value || ""}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}

function Section({ icon: Icon, title, action, children }) {
  return (
    <div className="ed-section">
      <div className="ed-section-title">
        <h3>
          <Icon size={16} />
          {title}
        </h3>

        {action}
      </div>

      {children}
    </div>
  );
}

function ResumeEdit() {
  const { type, id } = useParams();
  const navigate = useNavigate();

  const [resumeId, setResumeId] = useState(null);
  const [title, setTitle] = useState("");

  const [content, setContent] = useState(emptyResumeContent);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [downloading, setDownloading] = useState(false);

  const [aiWorking, setAiWorking] = useState(false);
  const [summaryWorking, setSummaryWorking] = useState(false);

  const [instruction, setInstruction] = useState("");
  const [jobDescription, setJobDescription] = useState("");

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const loadResume = async () => {
    setLoading(true);
    setError("");

    try {
      if (type === "generated") {
        const response = await api.get(
          "/resume-builder/resumes/"
        );

        const list = Array.isArray(response.data)
          ? response.data
          : [];

        const found = list.find(
          (resume) =>
            String(resume.id) === String(id)
        );

        if (!found) {
          throw {
            response: {
              data: { detail: "Resume not found." },
            },
          };
        }

        setResumeId(found.id);
        setTitle(found.title);
        setContent({
          ...emptyResumeContent,
          ...(found.content || {}),
        });

        if (found.job_description) {
          setJobDescription(found.job_description);
        }
      } else if (type === "uploaded") {
        const response = await api.post(
          `/resume-builder/resumes/edit-from-upload/${id}/`
        );

        const data = response.data;

        setResumeId(data.id);
        setTitle(data.title);
        setContent({
          ...emptyResumeContent,
          ...(data.content || {}),
        });
      } else {
        throw {
          response: {
            data: { detail: "Unknown resume type." },
          },
        };
      }
    } catch (err) {
      console.error(err);

      setError(
        err?.response?.data?.detail ||
          "Unable to load this resume for editing."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadResume();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [type, id]);

  const handleSave = async () => {
    if (!resumeId) return;

    setSaving(true);
    setError("");
    setSuccess("");

    try {
      await api.patch(
        `/resume-builder/resumes/${resumeId}/`,
        { content }
      );

       setSuccess(
         "Resume saved successfully."
       );
    } catch (err) {
      console.error(err);

      setError(
        err?.response?.data?.detail ||
          "Failed to save resume."
      );
    } finally {
      setSaving(false);
    }
  };

  const handleDownload = async () => {
    if (!resumeId) return;

    setDownloading(true);
    setError("");

    try {
      const response = await api.get(
        `/resume-builder/resumes/${resumeId}/download/`,
        { responseType: "blob" }
      );

      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");

      link.href = url;
      link.download = `${title || "resume"}.docx`;

      document.body.appendChild(link);
      link.click();
      link.remove();

      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);

      setError("Failed to download the resume.");
    } finally {
      setDownloading(false);
    }
  };

  const handleApplyAIEdit = async () => {
    if (!resumeId) return;

    if (!instruction.trim()) {
      setError(
        "Please describe the change you want the AI agent to make."
      );
      return;
    }

    setAiWorking(true);
    setError("");
    setSuccess("");

    try {
      const response = await api.post(
        `/resume-builder/resumes/${resumeId}/ai-edit/`,
        {
          instruction: instruction.trim(),
          job_description: jobDescription,
        }
      );

      setContent({
        ...emptyResumeContent,
        ...(response.data.content || {}),
      });

      setInstruction("");

      setSuccess(
        "AI agent updated the resume. Review the changes and save."
      );
    } catch (err) {
      console.error(err);

      setError(
        err?.response?.data?.detail ||
          "AI agent failed to update the resume."
      );
    } finally {
      setAiWorking(false);
    }
  };

  const handleGenerateSummary = async () => {
    const missing = missingSummarySections(content);

    if (missing.length) {
      setError(
        `Complete these sections first: ${missing
          .map((section) => section.label)
          .join(", ")}. (Publications is optional.)`
      );
      return;
    }

    setSummaryWorking(true);
    setError("");
    setSuccess("");

    try {
      const response = await api.post(
        "/resume-builder/summary/generate/",
        {
          content,
          job_description: jobDescription,
        }
      );

      setContent((prev) => ({
        ...prev,
        summary: response.data.summary || "",
      }));

      setSuccess(
        "Professional summary generated successfully."
      );
    } catch (err) {
      console.error(err);

      setError(
        err?.response?.data?.detail ||
          "Failed to generate professional summary."
      );
    } finally {
      setSummaryWorking(false);
    }
  };

  const updatePersonal = (field, value) => {
    setContent((prev) => ({
      ...prev,
      personal: { ...prev.personal, [field]: value },
    }));
  };

  const addExperience = () => {
    setContent((prev) => ({
      ...prev,
      experience: [
        ...prev.experience,
        { ...emptyExperience, bullets: [""] },
      ],
    }));
  };

  const removeExperience = (index) => {
    setContent((prev) => ({
      ...prev,
      experience: prev.experience.filter(
        (_, i) => i !== index
      ),
    }));
  };

  const updateExperience = (index, field, value) => {
    setContent((prev) => {
      const experience = [...prev.experience];

      experience[index] = {
        ...experience[index],
        [field]: value,
      };

      return { ...prev, experience };
    });
  };

  const updateExperienceBullet = (
    expIndex,
    bulletIndex,
    value
  ) => {
    setContent((prev) => {
      const experience = [...prev.experience];
      const bullets = [
        ...(experience[expIndex].bullets || []),
      ];

      bullets[bulletIndex] = value;

      experience[expIndex] = {
        ...experience[expIndex],
        bullets,
      };

      return { ...prev, experience };
    });
  };

  const addExperienceBullet = (index) => {
    setContent((prev) => {
      const experience = [...prev.experience];

      experience[index] = {
        ...experience[index],
        bullets: [
          ...(experience[index].bullets || []),
          "",
        ],
      };

      return { ...prev, experience };
    });
  };

  const removeExperienceBullet = (
    expIndex,
    bulletIndex
  ) => {
    setContent((prev) => {
      const experience = [...prev.experience];
      const bullets = [
        ...(experience[expIndex].bullets || []),
      ];

      bullets.splice(bulletIndex, 1);

      experience[expIndex] = {
        ...experience[expIndex],
        bullets,
      };

      return { ...prev, experience };
    });
  };

  const addProject = () => {
    setContent((prev) => ({
      ...prev,
      projects: [
        ...prev.projects,
        { ...emptyProject, bullets: [""] },
      ],
    }));
  };

  const removeProject = (index) => {
    setContent((prev) => ({
      ...prev,
      projects: prev.projects.filter(
        (_, i) => i !== index
      ),
    }));
  };

  const updateProject = (index, field, value) => {
    setContent((prev) => {
      const projects = [...prev.projects];

      projects[index] = {
        ...projects[index],
        [field]: value,
      };

      return { ...prev, projects };
    });
  };

  const updateProjectBullet = (
    projIndex,
    bulletIndex,
    value
  ) => {
    setContent((prev) => {
      const projects = [...prev.projects];
      const bullets = [
        ...(projects[projIndex].bullets || []),
      ];

      bullets[bulletIndex] = value;

      projects[projIndex] = {
        ...projects[projIndex],
        bullets,
      };

      return { ...prev, projects };
    });
  };

  const addProjectBullet = (index) => {
    setContent((prev) => {
      const projects = [...prev.projects];

      projects[index] = {
        ...projects[index],
        bullets: [
          ...(projects[index].bullets || []),
          "",
        ],
      };

      return { ...prev, projects };
    });
  };

  const removeProjectBullet = (
    projIndex,
    bulletIndex
  ) => {
    setContent((prev) => {
      const projects = [...prev.projects];
      const bullets = [
        ...(projects[projIndex].bullets || []),
      ];

      bullets.splice(bulletIndex, 1);

      projects[projIndex] = {
        ...projects[projIndex],
        bullets,
      };

      return { ...prev, projects };
    });
  };

  const addEducation = () => {
    setContent((prev) => ({
      ...prev,
      education: [...prev.education, { ...emptyEducation }],
    }));
  };

  const removeEducation = (index) => {
    setContent((prev) => ({
      ...prev,
      education: prev.education.filter(
        (_, i) => i !== index
      ),
    }));
  };

  const updateEducation = (index, field, value) => {
    setContent((prev) => {
      const education = [...prev.education];

      education[index] = {
        ...education[index],
        [field]: value,
      };

      return { ...prev, education };
    });
  };

  const addCertification = () => {
    setContent((prev) => ({
      ...prev,
      certifications: [
        ...prev.certifications,
        { ...emptyCertification },
      ],
    }));
  };

  const removeCertification = (index) => {
    setContent((prev) => ({
      ...prev,
      certifications: prev.certifications.filter(
        (_, i) => i !== index
      ),
    }));
  };

  const updateCertification = (index, field, value) => {
    setContent((prev) => {
      const certifications = [...prev.certifications];

      certifications[index] = {
        ...certifications[index],
        [field]: value,
      };

      return { ...prev, certifications };
    });
  };

  const addPublication = () => {
    setContent((prev) => ({
      ...prev,
      publications: [
        ...prev.publications,
        { ...emptyPublication },
      ],
    }));
  };

  const removePublication = (index) => {
    setContent((prev) => ({
      ...prev,
      publications: prev.publications.filter(
        (_, i) => i !== index
      ),
    }));
  };

  const updatePublication = (index, field, value) => {
    setContent((prev) => {
      const publications = [...prev.publications];

      publications[index] = {
        ...publications[index],
        [field]: value,
      };

      return { ...prev, publications };
    });
  };

  const updateSkillCategory = (category, value) => {
    setContent((prev) => ({
      ...prev,
      skills: {
        ...prev.skills,
        [category]: value
          .split(",")
          .map((skill) => skill.trim())
          .filter(Boolean),
      },
    }));
  };

  const addSkillCategory = () => {
    const category = window.prompt("Enter skill category");

    if (!category?.trim()) return;

    setContent((prev) => ({
      ...prev,
      skills: {
        ...prev.skills,
        [category.trim()]: [],
      },
    }));
  };

  const removeSkillCategory = (category) => {
    setContent((prev) => {
      const skills = { ...prev.skills };

      delete skills[category];

      return { ...prev, skills };
    });
  };

  const renderResumePreview = () => {
    const personal = content.personal || {};
    const skills = Object.values(content.skills || {}).flat();

    return (
      <aside className="ed-preview-panel">
        <div className="ed-preview-card">
          <div className="ed-preview-header">
            <h2>{personal.name || "Your Name"}</h2>
            <div className="ed-preview-meta">
              {[personal.email, personal.phone, personal.location, personal.linkedin, personal.github, personal.website]
                .filter(Boolean)
                .map((item, index) => (
                  <span key={`${item}-${index}`}>{item}</span>
                ))}
            </div>
          </div>

          {content.summary && (
            <div className="ed-preview-section">
              <h3>Professional Summary</h3>
              <p>{content.summary}</p>
            </div>
          )}

          {skills.length > 0 && (
            <div className="ed-preview-section">
              <h3>Skills</h3>
              <div className="ed-preview-tags">
                {skills.map((skill, index) => (
                  <span key={`${skill}-${index}`}>{skill}</span>
                ))}
              </div>
            </div>
          )}

          {(content.experience || []).length > 0 && (
            <div className="ed-preview-section">
              <h3>Experience</h3>
              {content.experience.map((item, index) => (
                <div className="ed-preview-item" key={index}>
                  <div className="ed-preview-item-heading">
                    <strong>{item.role || "Role"}</strong>
                    <span>
                      {item.start_date || ""}
                      {item.start_date && item.end_date ? " - " : ""}
                      {item.end_date || ""}
                    </span>
                  </div>
                  <div className="ed-preview-muted">
                    {item.company || "Company"}
                    {item.location ? ` | ${item.location}` : ""}
                  </div>
                  {(item.bullets || []).filter(Boolean).length > 0 && (
                    <ul>
                      {(item.bullets || []).filter(Boolean).map((bullet, bulletIndex) => (
                        <li key={bulletIndex}>{bullet}</li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          )}

          {(content.projects || []).length > 0 && (
            <div className="ed-preview-section">
              <h3>Projects</h3>
              {content.projects.map((item, index) => (
                <div className="ed-preview-item" key={index}>
                  <strong>{item.name || "Project"}</strong>
                  {item.description && <p>{item.description}</p>}
                  {(item.technologies || []).length > 0 && (
                    <div className="ed-preview-tags">
                      {item.technologies.map((tech, techIndex) => (
                        <span key={`${tech}-${techIndex}`}>{tech}</span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {(content.education || []).length > 0 && (
            <div className="ed-preview-section">
              <h3>Education</h3>
              {content.education.map((item, index) => (
                <div className="ed-preview-item" key={index}>
                  <strong>{item.degree || "Degree"}</strong>
                  <div className="ed-preview-muted">
                    {item.institution || "Institution"}
                    {item.location ? ` | ${item.location}` : ""}
                  </div>
                </div>
              ))}
            </div>
          )}

          {(content.certifications || []).length > 0 && (
            <div className="ed-preview-section">
              <h3>Certifications</h3>
              {content.certifications.map((item, index) => (
                <div className="ed-preview-item" key={index}>
                  <strong>{item.name || "Certification"}</strong>
                  <div className="ed-preview-muted">{item.issuer || "Issuer"}</div>
                </div>
              ))}
            </div>
          )}

          {!content.summary && !skills.length &&
            !(content.experience || []).length &&
            !(content.projects || []).length &&
            !(content.education || []).length &&
            !(content.certifications || []).length && (
              <p className="ed-preview-empty">
                Start editing to see your resume preview here.
              </p>
            )}
        </div>
      </aside>
    );
  };

  if (loading) {
    return (
      <div className="page-loading">
        Loading resume...
      </div>
    );
  }

  const summaryMissing = missingSummarySections(content);

  return (
    <div className="resume-edit-page">
      <div className="ed-topbar">
        <div className="ed-topbar-info">
          <h1>{title || "Edit Resume"}</h1>

          <p>
            {type === "uploaded"
              ? "Editing an uploaded resume. Changes are saved to the generated resume below."
              : "Editing a generated resume."}
          </p>
        </div>

        <div className="ed-topbar-actions">
          <button
            type="button"
            className="ed-btn ed-btn-secondary"
            onClick={() => navigate("/resumes")}
          >
            <ArrowLeft size={15} />
            Back
          </button>

          <button
            type="button"
            className="ed-btn ed-btn-outline"
            onClick={handleSave}
            disabled={saving || !resumeId}
          >
            {saving ? (
              <>
                <Loader2 size={15} />
                Saving...
              </>
            ) : (
              <>
                <Save size={15} />
                Save
              </>
            )}
          </button>

          <button
            type="button"
            className="ed-btn ed-btn-primary"
            onClick={handleDownload}
            disabled={downloading || !resumeId}
          >
            {downloading ? (
              <>
                <Loader2 size={15} />
                Downloading...
              </>
            ) : (
              <>
                <Download size={15} />
                Download
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="ed-alert ed-alert-error">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="ed-alert ed-alert-success">
          <CheckCircle2 size={16} />
          <span>{success}</span>
        </div>
      )}

      {/* AI AGENT */}
      <div className="ed-ai-panel">
        <div className="ed-ai-header">
          <div className="ed-ai-icon">
            <Bot size={18} />
          </div>

          <div>
            <h2>AI Agent</h2>

            <p>
              Tell the AI agent how to modify this resume and it will
              apply the change for you to review.
            </p>
          </div>
        </div>

        <TextAreaField
          label="Instruction for the AI agent"
          value={instruction}
          onChange={setInstruction}
          placeholder='e.g. "Rewrite my experience bullets to sound more achievement-focused" or "Add a Tools category to my skills"'
          rows={4}
        />

        <TextAreaField
          label="Target job description (optional)"
          value={jobDescription}
          onChange={setJobDescription}
          placeholder="Paste a job description to help the AI agent tailor the resume..."
          rows={4}
        />

        <button
          type="button"
          className="ed-btn ed-btn-primary"
          onClick={handleApplyAIEdit}
          disabled={aiWorking || !resumeId}
        >
          {aiWorking ? (
            <>
              <Loader2 size={15} />
              AI agent working...
            </>
          ) : (
            <>
              <Sparkles size={15} />
              Apply AI Edit
            </>
          )}
        </button>
      </div>

      <div className="ed-editor-layout">
        <div className="ed-editor-form">
      {/* PERSONAL */}
      <Section icon={User} title="Personal Information">
        <div className="ed-grid-2">
          {personalFields.map((field) => (
            <Field
              key={field.key}
              label={field.label}
              value={content.personal?.[field.key]}
              onChange={(value) =>
                updatePersonal(field.key, value)
              }
            />
          ))}
        </div>
      </Section>

      {/* SUMMARY */}
      <Section
        icon={Sparkles}
        title="Professional Summary"
        action={
          <button
            type="button"
            className="ed-btn ed-btn-outline"
            onClick={handleGenerateSummary}
            disabled={summaryWorking}
            title={
              summaryMissing.length
                ? `Complete first: ${summaryMissing
                    .map((s) => s.label)
                    .join(", ")}. (Publications optional.)`
                : "Generate professional summary with AI"
            }
          >
            {summaryWorking ? (
              <>
                <Loader2 size={14} />
                Generating...
              </>
            ) : (
              <>
                <Sparkles size={14} />
                AI Generate Summary
              </>
            )}
          </button>
        }
      >
        <TextAreaField
          value={content.summary}
          onChange={(value) =>
            setContent((prev) => ({
              ...prev,
              summary: value,
            }))
          }
          rows={5}
          placeholder="Write a short professional summary or generate one with AI..."
        />
      </Section>

      {/* SKILLS */}
      <Section
        icon={Code2}
        title="Skills"
        action={
          <button
            type="button"
            className="ed-btn ed-btn-outline"
            onClick={addSkillCategory}
          >
            <Plus size={14} />
            Add Category
          </button>
        }
      >
        {Object.keys(content.skills || {}).length ===
        0 ? (
          <p className="ed-empty">
            No skills added yet.
          </p>
        ) : (
          Object.entries(content.skills || {}).map(
            ([category, skills]) => (
              <div className="ed-item" key={category}>
                <div className="ed-item-top">
                  <strong>{category}</strong>

                  <button
                    type="button"
                    className="ed-small-button"
                    onClick={() =>
                      removeSkillCategory(category)
                    }
                  >
                    <Trash2 size={14} />
                  </button>
                </div>

                <Field
                  label="Skills (comma separated)"
                  value={(skills || []).join(", ")}
                  onChange={(value) =>
                    updateSkillCategory(category, value)
                  }
                  placeholder="Python, Django, React"
                />
              </div>
            )
          )
        )}
      </Section>

      {/* EXPERIENCE */}
      <Section
        icon={Briefcase}
        title="Experience"
        action={
          <button
            type="button"
            className="ed-btn ed-btn-outline"
            onClick={addExperience}
          >
            <Plus size={14} />
            Add
          </button>
        }
      >
        {(content.experience || []).length === 0 && (
          <p className="ed-empty">
            No experience added yet.
          </p>
        )}

        {(content.experience || []).map(
          (experience, index) => (
            <div className="ed-item" key={index}>
              <div className="ed-item-top">
                <span className="ed-item-number">
                  Experience {index + 1}
                </span>

                <button
                  type="button"
                  className="ed-small-button"
                  onClick={() => removeExperience(index)}
                >
                  <Trash2 size={14} />
                </button>
              </div>

              <div className="ed-grid-2">
                <Field
                  label="Company"
                  value={experience.company}
                  onChange={(value) =>
                    updateExperience(
                      index,
                      "company",
                      value
                    )
                  }
                />

                <Field
                  label="Role"
                  value={experience.role}
                  onChange={(value) =>
                    updateExperience(index, "role", value)
                  }
                />

                <Field
                  label="Location"
                  value={experience.location}
                  onChange={(value) =>
                    updateExperience(
                      index,
                      "location",
                      value
                    )
                  }
                />

                <Field
                  label="Start Date"
                  value={experience.start_date}
                  onChange={(value) =>
                    updateExperience(
                      index,
                      "start_date",
                      value
                    )
                  }
                />

                <Field
                  label="End Date"
                  value={experience.end_date}
                  onChange={(value) =>
                    updateExperience(
                      index,
                      "end_date",
                      value
                    )
                  }
                />
              </div>

              <div className="ed-bullets">
                <label>Bullet Points</label>

                {(experience.bullets || []).map(
                  (bullet, bulletIndex) => (
                    <div
                      className="ed-bullet-row"
                      key={bulletIndex}
                    >
                      <input
                        value={bullet || ""}
                        placeholder="Describe an achievement..."
                        onChange={(e) =>
                          updateExperienceBullet(
                            index,
                            bulletIndex,
                            e.target.value
                          )
                        }
                      />

                      <button
                        type="button"
                        className="ed-small-button"
                        onClick={() =>
                          removeExperienceBullet(
                            index,
                            bulletIndex
                          )
                        }
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  )
                )}

                <button
                  type="button"
                  className="ed-btn ed-btn-outline"
                  onClick={() =>
                    addExperienceBullet(index)
                  }
                >
                  <Plus size={14} />
                  Add Bullet
                </button>
              </div>
            </div>
          )
        )}
      </Section>

      {/* PROJECTS */}
      <Section
        icon={FolderKanban}
        title="Projects"
        action={
          <button
            type="button"
            className="ed-btn ed-btn-outline"
            onClick={addProject}
          >
            <Plus size={14} />
            Add
          </button>
        }
      >
        {(content.projects || []).length === 0 && (
          <p className="ed-empty">
            No projects added yet.
          </p>
        )}

        {(content.projects || []).map(
          (project, index) => (
            <div className="ed-item" key={index}>
              <div className="ed-item-top">
                <span className="ed-item-number">
                  Project {index + 1}
                </span>

                <button
                  type="button"
                  className="ed-small-button"
                  onClick={() => removeProject(index)}
                >
                  <Trash2 size={14} />
                </button>
              </div>

              <div className="ed-grid-2">
                <Field
                  label="Name"
                  value={project.name}
                  onChange={(value) =>
                    updateProject(index, "name", value)
                  }
                />

                <Field
                  label="URL"
                  value={project.url}
                  onChange={(value) =>
                    updateProject(index, "url", value)
                  }
                />
              </div>

              <TextAreaField
                label="Description"
                value={project.description}
                onChange={(value) =>
                  updateProject(
                    index,
                    "description",
                    value
                  )
                }
                rows={3}
              />

              <Field
                label="Technologies (comma separated)"
                value={(project.technologies || []).join(
                  ", "
                )}
                onChange={(value) =>
                  updateProject(
                    index,
                    "technologies",
                    value
                      .split(",")
                      .map((tech) => tech.trim())
                      .filter(Boolean)
                  )
                }
                placeholder="React, Node.js"
              />

              <div className="ed-bullets">
                <label>Bullet Points</label>

                {(project.bullets || []).map(
                  (bullet, bulletIndex) => (
                    <div
                      className="ed-bullet-row"
                      key={bulletIndex}
                    >
                      <input
                        value={bullet || ""}
                        placeholder="Describe a feature or result..."
                        onChange={(e) =>
                          updateProjectBullet(
                            index,
                            bulletIndex,
                            e.target.value
                          )
                        }
                      />

                      <button
                        type="button"
                        className="ed-small-button"
                        onClick={() =>
                          removeProjectBullet(
                            index,
                            bulletIndex
                          )
                        }
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  )
                )}

                <button
                  type="button"
                  className="ed-btn ed-btn-outline"
                  onClick={() =>
                    addProjectBullet(index)
                  }
                >
                  <Plus size={14} />
                  Add Bullet
                </button>
              </div>
            </div>
          )
        )}
      </Section>

      {/* EDUCATION */}
      <Section
        icon={GraduationCap}
        title="Education"
        action={
          <button
            type="button"
            className="ed-btn ed-btn-outline"
            onClick={addEducation}
          >
            <Plus size={14} />
            Add
          </button>
        }
      >
        {(content.education || []).length === 0 && (
          <p className="ed-empty">
            No education added yet.
          </p>
        )}

        {(content.education || []).map(
          (education, index) => (
            <div className="ed-item" key={index}>
              <div className="ed-item-top">
                <span className="ed-item-number">
                  Education {index + 1}
                </span>

                <button
                  type="button"
                  className="ed-small-button"
                  onClick={() => removeEducation(index)}
                >
                  <Trash2 size={14} />
                </button>
              </div>

              <div className="ed-grid-2">
                <Field
                  label="Degree"
                  value={education.degree}
                  onChange={(value) =>
                    updateEducation(
                      index,
                      "degree",
                      value
                    )
                  }
                />

                <Field
                  label="Institution"
                  value={education.institution}
                  onChange={(value) =>
                    updateEducation(
                      index,
                      "institution",
                      value
                    )
                  }
                />

                <Field
                  label="Location"
                  value={education.location}
                  onChange={(value) =>
                    updateEducation(
                      index,
                      "location",
                      value
                    )
                  }
                />

                <Field
                  label="Start Date"
                  value={education.start_date}
                  onChange={(value) =>
                    updateEducation(
                      index,
                      "start_date",
                      value
                    )
                  }
                />

                <Field
                  label="End Date"
                  value={education.end_date}
                  onChange={(value) =>
                    updateEducation(
                      index,
                      "end_date",
                      value
                    )
                  }
                />

                <Field
                  label="Grade"
                  value={education.grade}
                  onChange={(value) =>
                    updateEducation(index, "grade", value)
                  }
                />
              </div>
            </div>
          )
        )}
      </Section>

      {/* CERTIFICATIONS */}
      <Section
        icon={Award}
        title="Certifications"
        action={
          <button
            type="button"
            className="ed-btn ed-btn-outline"
            onClick={addCertification}
          >
            <Plus size={14} />
            Add
          </button>
        }
      >
        {(content.certifications || []).length ===
          0 && (
          <p className="ed-empty">
            No certifications added yet.
          </p>
        )}

        {(content.certifications || []).map(
          (certification, index) => (
            <div className="ed-item" key={index}>
              <div className="ed-item-top">
                <span className="ed-item-number">
                  Certification {index + 1}
                </span>

                <button
                  type="button"
                  className="ed-small-button"
                  onClick={() =>
                    removeCertification(index)
                  }
                >
                  <Trash2 size={14} />
                </button>
              </div>

              <div className="ed-grid-2">
                <Field
                  label="Name"
                  value={certification.name}
                  onChange={(value) =>
                    updateCertification(
                      index,
                      "name",
                      value
                    )
                  }
                />

                <Field
                  label="Issuer"
                  value={certification.issuer}
                  onChange={(value) =>
                    updateCertification(
                      index,
                      "issuer",
                      value
                    )
                  }
                />

                <Field
                  label="Date"
                  value={certification.date}
                  onChange={(value) =>
                    updateCertification(
                      index,
                      "date",
                      value
                    )
                  }
                />

                <Field
                  label="URL"
                  value={certification.url}
                  onChange={(value) =>
                    updateCertification(
                      index,
                      "url",
                      value
                    )
                  }
                />
              </div>
            </div>
          )
        )}
      </Section>

      {/* PUBLICATIONS */}
      <Section
        icon={Award}
        title="Publications"
        action={
          <button
            type="button"
            className="ed-btn ed-btn-outline"
            onClick={addPublication}
          >
            <Plus size={14} />
            Add
          </button>
        }
      >
        <p className="ed-hint">Optional section.</p>

        {(content.publications || []).length === 0 && (
          <p className="ed-empty">
            No publications added yet.
          </p>
        )}

        {(content.publications || []).map(
          (publication, index) => (
            <div className="ed-item" key={index}>
              <div className="ed-item-top">
                <span className="ed-item-number">
                  Publication {index + 1}
                </span>

                <button
                  type="button"
                  className="ed-small-button"
                  onClick={() =>
                    removePublication(index)
                  }
                >
                  <Trash2 size={14} />
                </button>
              </div>

              <div className="ed-grid-2">
                <Field
                  label="Title"
                  value={publication.title}
                  onChange={(value) =>
                    updatePublication(
                      index,
                      "title",
                      value
                    )
                  }
                />

                <Field
                  label="Authors"
                  value={publication.authors}
                  onChange={(value) =>
                    updatePublication(
                      index,
                      "authors",
                      value
                    )
                  }
                />

                <Field
                  label="Venue"
                  value={publication.venue}
                  onChange={(value) =>
                    updatePublication(
                      index,
                      "venue",
                      value
                    )
                  }
                />

                <Field
                  label="Date"
                  value={publication.date}
                  onChange={(value) =>
                    updatePublication(
                      index,
                      "date",
                      value
                    )
                  }
                />

                <Field
                  label="URL"
                  value={publication.url}
                  onChange={(value) =>
                    updatePublication(
                      index,
                      "url",
                      value
                    )
                  }
                />
              </div>
            </div>
          )
        )}
      </Section>

      <div className="ed-footer-actions">
        <button
          type="button"
          className="ed-btn ed-btn-outline"
          onClick={handleSave}
          disabled={saving || !resumeId}
        >
          {saving ? (
            <>
              <Loader2 size={15} />
              Saving...
            </>
          ) : (
            <>
              <Save size={15} />
              Save Changes
            </>
          )}
        </button>

        <button
          type="button"
          className="ed-btn ed-btn-primary"
          onClick={handleDownload}
          disabled={downloading || !resumeId}
        >
          <Download size={15} />
          Download Resume
        </button>
      </div>
        </div>

        {renderResumePreview()}
      </div>
    </div>
  );
}

export default ResumeEdit;
