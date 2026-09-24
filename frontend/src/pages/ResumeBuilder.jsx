import React, { useEffect, useState } from "react";
import {
  FileText,
  Sparkles,
  Upload,
  Briefcase,
  Palette,
  ChevronRight,
  Download,
  Save,
  Plus,
  Trash2,
  User,
  GraduationCap,
  Award,
  FolderKanban,
  Code2,
  FileCheck2,
  Loader2,
  CheckCircle2,
  AlertCircle,
  WandSparkles,
} from "lucide-react";

import api from "../services/api";

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

const steps = [
  { id: 1, title: "Resume Source", icon: FileText },
  { id: 2, title: "Template", icon: Palette },
  { id: 3, title: "Job Description", icon: Briefcase },
  { id: 4, title: "Generate", icon: Sparkles },
];

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

function SectionHeader({ icon: Icon, title, description }) {
  return (
    <div className="rb-section-header">
      <div className="rb-section-icon">
        <Icon size={19} />
      </div>

      <div>
        <h3>{title}</h3>

        {description && <p>{description}</p>}
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  placeholder = "",
  type = "text",
}) {
  return (
    <div className="rb-field">
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
    <div className="rb-field">
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

function ResumeBuilder() {
  const [sourceType, setSourceType] =
    useState("existing_resume");

  const [resumes, setResumes] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [profile, setProfile] = useState(null);

  const [selectedResumeId, setSelectedResumeId] =
    useState("");

  const [selectedTemplateId, setSelectedTemplateId] =
    useState("");

  const [templateFile, setTemplateFile] =
    useState(null);

  const [templateName, setTemplateName] =
    useState("");

  const [jobDescription, setJobDescription] =
    useState("");

  const [resumeContent, setResumeContent] =
    useState(emptyResumeContent);

  const [generatedResumeId, setGeneratedResumeId] =
    useState(null);

  const [loading, setLoading] = useState(false);
  const [uploadingTemplate, setUploadingTemplate] =
    useState(false);
  const [saving, setSaving] = useState(false);
  const [generatingSummary, setGeneratingSummary] =
    useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [showEditor, setShowEditor] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [resumeResponse, templateResponse, profileResponse] =
        await Promise.all([
          api.get("/resumes/"),
          api.get("/resume-builder/templates/"),
          api.get("/resume-builder/profile/"),
        ]);

      const resumeData =
        resumeResponse.data.results ||
        resumeResponse.data ||
        [];

      const templateData =
        templateResponse.data.results ||
        templateResponse.data ||
        [];

      setResumes(resumeData);
      setTemplates(templateData);
      setProfile(profileResponse.data);
    } catch (err) {
      console.error(err);

      setError(
        "Unable to load resumes and templates."
      );
    }
  };

  const handleSourceChange = (type) => {
    setSourceType(type);

    setError("");
    setSuccess("");

    if (type === "new_resume") {
      setSelectedResumeId("");

      // Prefill from profile if available
      if (profile) {
        setResumeContent((prev) => ({
          ...prev,
          personal: profile.personal || prev.personal,
          experience: profile.experience || prev.experience,
          education: profile.education || prev.education,
          certifications: profile.certifications || prev.certifications,
          publications: profile.publications || prev.publications,
        }));
      }
    }
  };

  const handleTemplateUpload = async () => {
    if (!templateFile) {
      setError(
        "Please select a PDF or DOCX template."
      );
      return;
    }

    try {
      setUploadingTemplate(true);
      setError("");
      setSuccess("");

      const formData = new FormData();

      formData.append(
        "name",
        templateName.trim() ||
        templateFile.name
      );

      formData.append(
        "sample_file",
        templateFile
      );

      const response = await api.post(
        "/resume-builder/templates/",
        formData,
        {
          headers: {
            "Content-Type":
              "multipart/form-data",
          },
        }
      );

      const newTemplate = response.data;

      setTemplates((prev) => [
        newTemplate,
        ...prev,
      ]);

      setSelectedTemplateId(
        String(newTemplate.id)
      );

      setTemplateFile(null);
      setTemplateName("");

      setSuccess(
        "Template uploaded successfully."
      );
    } catch (err) {
      console.error(err);

      setError(
        err?.response?.data?.detail ||
        "Failed to upload the template."
      );
    } finally {
      setUploadingTemplate(false);
    }
  };

  const handleDeleteTemplate = async (
    templateId
  ) => {
    const template = templates.find(
      (item) =>
        String(item.id) === String(templateId)
    );

    const confirmed = window.confirm(
      `Delete "${template?.name || "this template"
      }"?`
    );

    if (!confirmed) {
      return;
    }

    try {
      setError("");
      setSuccess("");

      await api.delete(
        `/resume-builder/templates/${templateId}/`
      );

      setTemplates((prev) =>
        prev.filter(
          (item) =>
            String(item.id) !==
            String(templateId)
        )
      );

      if (
        String(selectedTemplateId) ===
        String(templateId)
      ) {
        setSelectedTemplateId("");
      }

      setSuccess(
        "Template deleted successfully."
      );
    } catch (err) {
      console.error(err);

      setError(
        err?.response?.data?.detail ||
        "Failed to delete the template."
      );
    }
  };

  const handleGenerate = async () => {
    setError("");
    setSuccess("");

    if (!selectedTemplateId) {
      setError(
        "Please select or upload a resume template."
      );
      return;
    }

    if (!jobDescription.trim()) {
      setError(
        "Please enter the job description."
      );
      return;
    }

    if (
      sourceType === "existing_resume" &&
      !selectedResumeId
    ) {
      setError(
        "Please select an existing resume."
      );
      return;
    }

    try {
      setLoading(true);

      const payload = {
        source_type: sourceType,
        template_id: Number(
          selectedTemplateId
        ),
        job_description: jobDescription,
      };

      if (sourceType === "existing_resume") {
        payload.resume_id =
          Number(selectedResumeId);
      }

      const response = await api.post(
        "/resume-builder/generate/",
        payload
      );

      setGeneratedResumeId(response.data.id);

      setResumeContent(
        response.data.content ||
        emptyResumeContent
      );

      setShowEditor(true);

      setSuccess(
        "Resume generated successfully."
      );
    } catch (err) {
      console.error(err);

      setError(
        err?.response?.data?.detail ||
        "Failed to generate the resume."
      );
    } finally {
      setLoading(false);
    }
  };

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

  const requiredSummarySections = [
    { key: "personal", label: "Personal Information" },
    { key: "experience", label: "Experience" },
    { key: "education", label: "Education" },
    { key: "skills", label: "Skills" },
    { key: "certifications", label: "Certifications" },
    { key: "projects", label: "Projects" },
  ];

  const missingSummarySections = (content) => {
    if (!content) return requiredSummarySections;

    return requiredSummarySections.filter(
      ({ key }) => !isFilled(content[key])
    );
  };

  const hasContentForSummary = (content) =>
    missingSummarySections(content).length === 0;

  const handleGenerateSummary = async () => {
    const missing = missingSummarySections(resumeContent);

    if (missing.length) {
      setError(
        `Please complete the following sections before generating a professional summary: ${missing
          .map((section) => section.label)
          .join(", ")}. (Publications is optional.)`
      );
      return;
    }

    try {
      setGeneratingSummary(true);
      setError("");
      setSuccess("");

      const response = await api.post(
        "/resume-builder/summary/generate/",
        {
          content: resumeContent,
          job_description: jobDescription,
        }
      );

      setResumeContent((prev) => ({
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
      setGeneratingSummary(false);
    }
  };

  const handleSave = async () => {
    if (!generatedResumeId) {
      return;
    }

    try {
      setSaving(true);
      setError("");
      setSuccess("");

      const response = await api.patch(
        `/resume-builder/resumes/${generatedResumeId}/`,
        {
          content: resumeContent,
        }
      );

      // Update profile data from response (backend saves profile)
      if (response.data && response.data.content) {
        setProfile((prev) => ({
          ...prev,
          personal: response.data.content.personal || prev?.personal || {},
          experience: response.data.content.experience || prev?.experience || [],
          education: response.data.content.education || prev?.education || [],
          certifications: response.data.content.certifications || prev?.certifications || [],
          publications: response.data.content.publications || prev?.publications || [],
        }));
      }

      // Reload resumes to show the new entry in "My Resumes"
      try {
        const resumeResponse = await api.get("/resumes/");
        const resumeData = resumeResponse.data.results || resumeResponse.data || [];
        setResumes(resumeData);
      } catch (err) {
        console.warn("Failed to reload resumes:", err);
      }

      setSuccess(
        "Resume changes saved successfully and added to My Resumes."
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
    if (!generatedResumeId) {
      return;
    }

    try {
      const response = await api.get(
        `/resume-builder/resumes/${generatedResumeId}/download/`,
        {
          responseType: "blob",
        }
      );

      const blob = new Blob([
        response.data,
      ]);

      const url =
        window.URL.createObjectURL(blob);

      const link =
        document.createElement("a");

      link.href = url;
      link.download =
        "optimized_resume.docx";

      document.body.appendChild(link);

      link.click();

      link.remove();

      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);

      setError(
        "Failed to download the resume."
      );
    }
  };

  const updatePersonal = (
    field,
    value
  ) => {
    setResumeContent((prev) => ({
      ...prev,

      personal: {
        ...prev.personal,
        [field]: value,
      },
    }));
  };

  const addExperience = () => {
    setResumeContent((prev) => ({
      ...prev,

      experience: [
        ...prev.experience,
        {
          ...emptyExperience,
          bullets: [""],
        },
      ],
    }));
  };

  const removeExperience = (index) => {
    setResumeContent((prev) => ({
      ...prev,

      experience:
        prev.experience.filter(
          (_, i) => i !== index
        ),
    }));
  };

  const updateExperience = (
    index,
    field,
    value
  ) => {
    setResumeContent((prev) => {
      const experience = [
        ...prev.experience,
      ];

      experience[index] = {
        ...experience[index],
        [field]: value,
      };

      return {
        ...prev,
        experience,
      };
    });
  };

  const updateExperienceBullet = (
    experienceIndex,
    bulletIndex,
    value
  ) => {
    setResumeContent((prev) => {
      const experience = [
        ...prev.experience,
      ];

      const bullets = [
        ...(experience[
          experienceIndex
        ].bullets || []),
      ];

      bullets[bulletIndex] = value;

      experience[experienceIndex] = {
        ...experience[experienceIndex],
        bullets,
      };

      return {
        ...prev,
        experience,
      };
    });
  };

  const addExperienceBullet = (
    index
  ) => {
    setResumeContent((prev) => {
      const experience = [
        ...prev.experience,
      ];

      experience[index] = {
        ...experience[index],

        bullets: [
          ...(experience[index]
            .bullets || []),
          "",
        ],
      };

      return {
        ...prev,
        experience,
      };
    });
  };

  const removeExperienceBullet = (
    experienceIndex,
    bulletIndex
  ) => {
    setResumeContent((prev) => {
      const experience = [
        ...prev.experience,
      ];

      const bullets = [
        ...(experience[
          experienceIndex
        ].bullets || []),
      ];

      bullets.splice(bulletIndex, 1);

      experience[experienceIndex] = {
        ...experience[experienceIndex],
        bullets,
      };

      return {
        ...prev,
        experience,
      };
    });
  };

  const addProject = () => {
    setResumeContent((prev) => ({
      ...prev,

      projects: [
        ...prev.projects,
        {
          ...emptyProject,
          technologies: [],
          bullets: [""],
        },
      ],
    }));
  };

  const removeProject = (index) => {
    setResumeContent((prev) => ({
      ...prev,

      projects: prev.projects.filter(
        (_, i) => i !== index
      ),
    }));
  };

  const updateProject = (
    index,
    field,
    value
  ) => {
    setResumeContent((prev) => {
      const projects = [
        ...prev.projects,
      ];

      projects[index] = {
        ...projects[index],
        [field]: value,
      };

      return {
        ...prev,
        projects,
      };
    });
  };

  const updateProjectBullet = (
    projectIndex,
    bulletIndex,
    value
  ) => {
    setResumeContent((prev) => {
      const projects = [
        ...prev.projects,
      ];

      const bullets = [
        ...(projects[projectIndex]
          .bullets || []),
      ];

      bullets[bulletIndex] = value;

      projects[projectIndex] = {
        ...projects[projectIndex],
        bullets,
      };

      return {
        ...prev,
        projects,
      };
    });
  };

  const addProjectBullet = (index) => {
    setResumeContent((prev) => {
      const projects = [
        ...prev.projects,
      ];

      projects[index] = {
        ...projects[index],

        bullets: [
          ...(projects[index].bullets ||
            []),
          "",
        ],
      };

      return {
        ...prev,
        projects,
      };
    });
  };

  const removeProjectBullet = (
    projectIndex,
    bulletIndex
  ) => {
    setResumeContent((prev) => {
      const projects = [
        ...prev.projects,
      ];

      const bullets = [
        ...(projects[projectIndex]
          .bullets || []),
      ];

      bullets.splice(bulletIndex, 1);

      projects[projectIndex] = {
        ...projects[projectIndex],
        bullets,
      };

      return {
        ...prev,
        projects,
      };
    });
  };

  const addEducation = () => {
    setResumeContent((prev) => ({
      ...prev,

      education: [
        ...prev.education,
        {
          ...emptyEducation,
        },
      ],
    }));
  };

  const removeEducation = (index) => {
    setResumeContent((prev) => ({
      ...prev,

      education:
        prev.education.filter(
          (_, i) => i !== index
        ),
    }));
  };

  const updateEducation = (
    index,
    field,
    value
  ) => {
    setResumeContent((prev) => {
      const education = [
        ...prev.education,
      ];

      education[index] = {
        ...education[index],
        [field]: value,
      };

      return {
        ...prev,
        education,
      };
    });
  };

  const addCertification = () => {
    setResumeContent((prev) => ({
      ...prev,

      certifications: [
        ...prev.certifications,
        {
          ...emptyCertification,
        },
      ],
    }));
  };

  const removeCertification = (
    index
  ) => {
    setResumeContent((prev) => ({
      ...prev,

      certifications:
        prev.certifications.filter(
          (_, i) => i !== index
        ),
    }));
  };

  const updateCertification = (
    index,
    field,
    value
  ) => {
    setResumeContent((prev) => {
      const certifications = [
        ...prev.certifications,
      ];

      certifications[index] = {
        ...certifications[index],
        [field]: value,
      };

      return {
        ...prev,
        certifications,
      };
    });
  };

  const addPublication = () => {
    setResumeContent((prev) => ({
      ...prev,

      publications: [
        ...prev.publications,
        {
          ...emptyPublication,
        },
      ],
    }));
  };

  const removePublication = (
    index
  ) => {
    setResumeContent((prev) => ({
      ...prev,

      publications:
        prev.publications.filter(
          (_, i) => i !== index
        ),
    }));
  };

  const updatePublication = (
    index,
    field,
    value
  ) => {
    setResumeContent((prev) => {
      const publications = [
        ...prev.publications,
      ];

      publications[index] = {
        ...publications[index],
        [field]: value,
      };

      return {
        ...prev,
        publications,
      };
    });
  };

  const updateSkillCategory = (
    category,
    value
  ) => {
    setResumeContent((prev) => ({
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
    const category = window.prompt(
      "Enter skill category"
    );

    if (!category?.trim()) {
      return;
    }

    setResumeContent((prev) => ({
      ...prev,

      skills: {
        ...prev.skills,
        [category.trim()]: [],
      },
    }));
  };

  const removeSkillCategory = (
    category
  ) => {
    setResumeContent((prev) => {
      const skills = {
        ...prev.skills,
      };

      delete skills[category];

      return {
        ...prev,
        skills,
      };
    });
  };

  const renderResumePreview = () => {
    const personal = resumeContent.personal || {};
    const skillEntries = Object.entries(
      resumeContent.skills || {}
    );
    const experienceList = resumeContent.experience || [];
    const projectList = resumeContent.projects || [];
    const educationList = resumeContent.education || [];
    const certificationList = resumeContent.certifications || [];

    return (
      <aside className="rb-preview-panel">
        <div className="rb-preview-card">
          <div className="rb-preview-header">
            <h3>{personal.name || "Your Name"}</h3>

            <div className="rb-preview-meta">
              {personal.email && <span>{personal.email}</span>}
              {personal.phone && <span>{personal.phone}</span>}
              {personal.location && <span>{personal.location}</span>}
              {personal.linkedin && <span>{personal.linkedin}</span>}
              {personal.github && <span>{personal.github}</span>}
              {personal.website && <span>{personal.website}</span>}
            </div>
          </div>

          {resumeContent.summary && (
            <div className="rb-preview-section">
              <h4>Professional Summary</h4>

              <p className="rb-preview-summary">
                {resumeContent.summary}
              </p>
            </div>
          )}

          {skillEntries.length > 0 && (
            <div className="rb-preview-section">
              <h4>Skills</h4>

              <div className="rb-preview-skill-grid">
                {skillEntries.flatMap(([category, skills]) =>
                  (skills || []).map((skill) => (
                    <span
                      key={`${category}-${skill}`}
                      className="rb-preview-skill"
                    >
                      {skill}
                    </span>
                  ))
                )}
              </div>
            </div>
          )}

          {experienceList.length > 0 && (
            <div className="rb-preview-section">
              <h4>Experience</h4>

              <div className="rb-preview-list">
                {experienceList.map((item, index) => (
                  <div key={index} className="rb-preview-item">
                    <div className="rb-preview-role">
                      <strong>{item.role || "Role"}</strong>

                      <span>
                        {item.start_date || ""}
                        {item.start_date && item.end_date ? " - " : ""}
                        {item.end_date || ""}
                      </span>
                    </div>

                    <div className="rb-preview-role">
                      <span>{item.company || "Company"}</span>
                      <span>{item.location || "Location"}</span>
                    </div>

                    {item.bullets?.length > 0 && (
                      <ul className="rb-preview-bullets">
                        {item.bullets
                          .filter(Boolean)
                          .map((bullet, bulletIndex) => (
                            <li key={bulletIndex}>{bullet}</li>
                          ))}
                      </ul>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {projectList.length > 0 && (
            <div className="rb-preview-section">
              <h4>Projects</h4>

              <div className="rb-preview-list">
                {projectList.map((project, index) => (
                  <div key={index} className="rb-preview-item">
                    <div className="rb-preview-role">
                      <strong>{project.name || "Project"}</strong>
                    </div>

                    {project.description && (
                      <p className="rb-preview-summary">
                        {project.description}
                      </p>
                    )}

                    {project.technologies?.length > 0 && (
                      <div className="rb-preview-skill-grid" style={{ marginTop: 8 }}>
                        {project.technologies.map((tech) => (
                          <span key={tech} className="rb-preview-skill">
                            {tech}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {educationList.length > 0 && (
            <div className="rb-preview-section">
              <h4>Education</h4>

              <div className="rb-preview-list">
                {educationList.map((item, index) => (
                  <div key={index} className="rb-preview-list-card">
                    <strong>{item.degree || "Degree"}</strong>
                    {item.institution || "Institution"}
                    {item.start_date || item.end_date ? (
                      <div>
                        {item.start_date || ""}
                        {item.start_date && item.end_date ? " - " : ""}
                        {item.end_date || ""}
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            </div>
          )}

          {certificationList.length > 0 && (
            <div className="rb-preview-section">
              <h4>Certifications</h4>

              <div className="rb-preview-list">
                {certificationList.map((item, index) => (
                  <div key={index} className="rb-preview-list-card">
                    <strong>{item.name || "Certification"}</strong>
                    {item.issuer || "Issuer"}
                  </div>
                ))}
              </div>
            </div>
          )}

          {!resumeContent.summary &&
            skillEntries.length === 0 &&
            experienceList.length === 0 &&
            projectList.length === 0 &&
            educationList.length === 0 &&
            certificationList.length === 0 && (
              <div className="rb-preview-empty">
                Start editing to see a live preview here.
              </div>
            )}
        </div>
      </aside>
    );
  };

  return (
    <div className="resume-builder-page">
      <style>{`
        * {
          box-sizing: border-box;
        }

        .resume-builder-page {
          min-height: 100vh;
          background: #f6f7fb;
          color: #172033;
          font-family:
            Inter,
            -apple-system,
            BlinkMacSystemFont,
            "Segoe UI",
            sans-serif;
        }

        .rb-container {
          width: 100%;
          max-width: 1450px;
          margin: 0 auto;
          padding: 30px 38px 60px;
        }

        .rb-topbar {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 28px;
        }

        .rb-brand {
          display: flex;
          align-items: center;
          gap: 13px;
        }

        .rb-brand-icon {
          width: 43px;
          height: 43px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          background: linear-gradient(
            135deg,
            #5b5ce2,
            #7c3aed
          );
          box-shadow:
            0 8px 24px
            rgba(91, 92, 226, 0.22);
        }

        .rb-brand h1 {
          margin: 0;
          font-size: 24px;
          font-weight: 750;
          letter-spacing: -0.5px;
        }

        .rb-brand p {
          margin: 3px 0 0;
          color: #6b7280;
          font-size: 13px;
        }

        .rb-ai-badge {
          display: flex;
          align-items: center;
          gap: 7px;
          padding: 8px 13px;
          border-radius: 999px;
          color: #4f46e5;
          background: #eef2ff;
          border: 1px solid #dfe3ff;
          font-size: 12px;
          font-weight: 700;
        }

        .rb-layout {
          display: grid;
          grid-template-columns: 235px minmax(0, 1fr);
          gap: 25px;
          align-items: start;
        }

        .rb-sidebar {
          position: sticky;
          top: 25px;
          padding: 17px;
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 17px;
          box-shadow:
            0 8px 30px
            rgba(15, 23, 42, 0.05);
        }

        .rb-sidebar-title {
          margin-bottom: 16px;
          color: #9ca3af;
          font-size: 11px;
          font-weight: 750;
          letter-spacing: 0.08em;
          text-transform: uppercase;
        }

        .rb-step {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 10px;
          margin-bottom: 5px;
          border-radius: 10px;
          color: #7b8495;
        }

        .rb-step.active {
          color: #4f46e5;
          background: #f1f2ff;
        }

        .rb-step-number {
          width: 30px;
          height: 30px;
          flex: 0 0 30px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 9px;
          color: #6b7280;
          background: #f3f4f6;
        }

        .rb-step.active
          .rb-step-number {
          color: white;
          background: #5b5ce2;
        }

        .rb-step-text {
          font-size: 12px;
          font-weight: 650;
        }

        .rb-main {
          min-width: 0;
        }

        .rb-card {
          padding: 24px;
          margin-bottom: 19px;
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 17px;
          box-shadow:
            0 8px 30px
            rgba(15, 23, 42, 0.045);
        }

        .rb-section-header {
          display: flex;
          align-items: flex-start;
          gap: 12px;
          margin-bottom: 21px;
        }

        .rb-section-icon {
          width: 37px;
          height: 37px;
          flex: 0 0 37px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 10px;
          color: #5557d8;
          background: #f1f2ff;
        }

        .rb-section-header h3 {
          margin: 0;
          font-size: 16px;
          font-weight: 750;
        }

        .rb-section-header p {
          margin: 4px 0 0;
          color: #7b8495;
          font-size: 12px;
          line-height: 1.5;
        }

        .rb-source-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 14px;
        }

        .rb-source-card {
          padding: 18px;
          border: 1.5px solid #e5e7eb;
          border-radius: 13px;
          cursor: pointer;
          background: white;
          transition: 0.18s ease;
        }

        .rb-source-card:hover {
          border-color: #a5a7f4;
          transform: translateY(-1px);
        }

        .rb-source-card.selected {
          border-color: #5b5ce2;
          background: #f8f8ff;
          box-shadow:
            0 0 0 3px
            rgba(91, 92, 226, 0.08);
        }

        .rb-source-card-icon {
          width: 40px;
          height: 40px;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-bottom: 12px;
          border-radius: 10px;
          color: #4f46e5;
          background: #f1f2ff;
        }

        .rb-source-card h4 {
          margin: 0 0 5px;
          font-size: 14px;
        }

        .rb-source-card p {
          margin: 0;
          color: #7b8495;
          font-size: 12px;
          line-height: 1.5;
        }

        .rb-field {
          margin-bottom: 16px;
        }

        .rb-field label {
          display: block;
          margin-bottom: 7px;
          color: #374151;
          font-size: 12px;
          font-weight: 700;
        }

        .rb-field input,
        .rb-field textarea,
        .rb-select {
          width: 100%;
          padding: 11px 12px;
          border: 1px solid #dfe3ea;
          border-radius: 9px;
          outline: none;
          color: #172033;
          background: white;
          font-family: inherit;
          font-size: 13px;
          transition: 0.18s ease;
        }

        .rb-field textarea {
          min-height: 110px;
          resize: vertical;
          line-height: 1.55;
        }

        .rb-field input:focus,
        .rb-field textarea:focus,
        .rb-select:focus {
          border-color: #696be6;
          box-shadow:
            0 0 0 3px
            rgba(91, 92, 226, 0.09);
        }

        .rb-grid-2 {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 15px;
        }

        .rb-upload {
          padding: 21px;
          border: 1.5px dashed #cfd4df;
          border-radius: 13px;
          text-align: center;
          background: #fafbfc;
        }

        .rb-upload-icon {
          width: 43px;
          height: 43px;
          display: flex;
          align-items: center;
          justify-content: center;
          margin: 0 auto 10px;
          border-radius: 11px;
          color: #5557d8;
          background: #eef2ff;
        }

        .rb-upload h4 {
          margin: 0 0 5px;
          font-size: 14px;
        }

        .rb-upload p {
          margin: 0 0 14px;
          color: #7b8495;
          font-size: 11px;
        }

        .rb-file-row {
          display: flex;
          align-items: center;
          gap: 10px;
          text-align: left;
        }

        .rb-file-row input[type="file"] {
          flex: 1;
          min-width: 0;
          font-size: 11px;
        }

        .rb-button {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 7px;
          padding: 10px 14px;
          border: none;
          border-radius: 9px;
          cursor: pointer;
          font-family: inherit;
          font-size: 12px;
          font-weight: 700;
          transition: 0.18s ease;
        }

        .rb-button:hover {
          transform: translateY(-1px);
        }

        .rb-button:disabled {
          opacity: 0.55;
          cursor: not-allowed;
          transform: none;
        }

        .rb-button-primary {
          color: white;
          background: linear-gradient(
            135deg,
            #5b5ce2,
            #7048d9
          );
          box-shadow:
            0 8px 20px
            rgba(91, 92, 226, 0.2);
        }

        .rb-button-secondary {
          color: #374151;
          background: #f3f4f6;
        }

        .rb-button-outline {
          color: #4f46e5;
          background: white;
          border: 1px solid #dfe2ff;
        }

        .rb-button-danger {
          color: #dc2626;
          background: #fff1f2;
        }

        .rb-generate-box {
          padding: 21px;
          border: 1px solid #e3e4ff;
          border-radius: 14px;
          background:
            linear-gradient(
              135deg,
              #f4f4ff,
              #faf7ff
            );
        }

        .rb-generate-content {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 18px;
        }

        .rb-generate-content h3 {
          margin: 0 0 5px;
          font-size: 15px;
        }

        .rb-generate-content p {
          margin: 0;
          color: #6b7280;
          font-size: 12px;
        }

        .rb-alert {
          display: flex;
          align-items: flex-start;
          gap: 9px;
          padding: 12px 14px;
          margin-bottom: 17px;
          border-radius: 10px;
          font-size: 12px;
        }

        .rb-alert-error {
          color: #be123c;
          background: #fff1f2;
          border: 1px solid #fecdd3;
        }

        .rb-alert-success {
          color: #047857;
          background: #ecfdf5;
          border: 1px solid #bbf7d0;
        }

        .rb-template-list {
          display: flex;
          flex-direction: column;
          gap: 9px;
          margin-bottom: 18px;
        }

        .rb-template-item {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 5px;
          border: 1px solid #e5e7eb;
          border-radius: 11px;
          background: white;
          transition: 0.18s ease;
        }

        .rb-template-item:hover {
          border-color: #c7c9f7;
        }

        .rb-template-item.selected {
          border-color: #6869e6;
          background: #f8f8ff;
          box-shadow:
            0 0 0 2px
            rgba(91, 92, 226, 0.05);
        }

        .rb-template-select {
          display: flex;
          align-items: center;
          flex: 1;
          min-width: 0;
          gap: 11px;
          padding: 7px;
          border: none;
          text-align: left;
          cursor: pointer;
          background: transparent;
        }

        .rb-template-icon {
          width: 35px;
          height: 35px;
          flex: 0 0 35px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 9px;
          color: #5557d8;
          background: #f1f2ff;
        }

        .rb-template-info {
          display: flex;
          flex-direction: column;
          gap: 3px;
          min-width: 0;
        }

        .rb-template-info strong {
          overflow: hidden;
          color: #273044;
          font-size: 13px;
          font-weight: 700;
          white-space: nowrap;
          text-overflow: ellipsis;
        }

        .rb-template-info span {
          color: #8a91a1;
          font-size: 10px;
        }

        .rb-template-check {
          margin-left: auto;
          color: #5b5ce2;
        }

        .rb-template-delete {
          width: 34px;
          height: 34px;
          display: flex;
          align-items: center;
          justify-content: center;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          color: #9ca3af;
          background: transparent;
        }

        .rb-template-delete:hover {
          color: #dc2626;
          background: #fff1f2;
        }

        .rb-empty-template {
          display: flex;
          align-items: center;
          gap: 11px;
          padding: 14px;
          border: 1px dashed #d9dce5;
          border-radius: 11px;
          color: #8a91a1;
          background: #fafbfc;
        }

        .rb-empty-template > svg {
          flex: 0 0 auto;
          color: #6869e6;
        }

        .rb-empty-template strong {
          display: block;
          color: #4b5563;
          font-size: 12px;
        }

        .rb-empty-template p {
          margin: 3px 0 0;
          font-size: 11px;
        }

        .rb-editor-shell {
          overflow: visible;
        }

        .rb-editor-title {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 15px;
          margin-bottom: 20px;
        }

        .rb-editor-title h2 {
          margin: 0;
          font-size: 21px;
        }

        .rb-editor-subtitle {
          margin: 5px 0 0;
          color: #7b8495;
          font-size: 12px;
        }

        .rb-editor-actions {
          display: flex;
          gap: 8px;
        }

        .rb-editor-layout {
          display: grid;
          grid-template-columns: minmax(0, 1.5fr) minmax(320px, 0.9fr);
          gap: 20px;
          align-items: start;
        }

        .rb-editor-form {
          min-width: 0;
        }

        .rb-preview-panel {
          position: sticky;
          top: 20px;
        }

        .rb-preview-card {
          background: linear-gradient(180deg, #ffffff 0%, #f8f9ff 100%);
          border: 1px solid #e5e7eb;
          border-radius: 16px;
          box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
          padding: 22px 20px;
          min-height: 760px;
          color: #1f2937;
        }

        .rb-preview-header {
          border-bottom: 1px solid #e5e7eb;
          padding-bottom: 12px;
          margin-bottom: 16px;
        }

        .rb-preview-header h3 {
          margin: 0;
          font-size: 24px;
          line-height: 1.2;
          word-break: break-word;
        }

        .rb-preview-meta {
          display: flex;
          flex-wrap: wrap;
          gap: 8px 12px;
          margin-top: 8px;
          color: #475569;
          font-size: 11px;
        }

        .rb-preview-meta span {
          display: inline-flex;
          align-items: center;
          gap: 4px;
        }

        .rb-preview-section {
          margin-bottom: 18px;
        }

        .rb-preview-section h4 {
          margin: 0 0 6px;
          font-size: 12px;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          color: #4f46e5;
        }

        .rb-preview-summary {
          margin: 0;
          font-size: 12px;
          line-height: 1.6;
          color: #374151;
        }

        .rb-preview-skill-grid {
          display: flex;
          flex-wrap: wrap;
          gap: 7px;
        }

        .rb-preview-skill {
          padding: 5px 8px;
          border-radius: 999px;
          background: #eef2ff;
          color: #3730a3;
          font-size: 11px;
          font-weight: 600;
        }

        .rb-preview-item {
          margin-bottom: 14px;
          padding-bottom: 12px;
          border-bottom: 1px solid #eef2f7;
        }

        .rb-preview-item:last-child {
          border-bottom: none;
          margin-bottom: 0;
          padding-bottom: 0;
        }

        .rb-preview-role {
          display: flex;
          justify-content: space-between;
          gap: 12px;
          margin-bottom: 4px;
          font-size: 12px;
          color: #374151;
        }

        .rb-preview-role strong {
          font-size: 13px;
          color: #111827;
        }

        .rb-preview-role span {
          color: #64748b;
        }

        .rb-preview-bullets {
          margin: 7px 0 0;
          padding-left: 18px;
          color: #374151;
          font-size: 11px;
          line-height: 1.5;
        }

        .rb-preview-bullets li {
          margin-bottom: 4px;
        }

        .rb-preview-list {
          display: grid;
          gap: 10px;
        }

        .rb-preview-list-card {
          font-size: 11px;
          color: #374151;
          line-height: 1.5;
        }

        .rb-preview-list-card strong {
          display: block;
          margin-bottom: 2px;
          color: #111827;
        }

        .rb-preview-empty {
          color: #64748b;
          font-size: 11px;
          font-style: italic;
        }

        .rb-editor-section {
          padding: 19px;
          margin-bottom: 15px;
          border: 1px solid #e6e8ee;
          border-radius: 13px;
          background: white;
        }

        .rb-editor-section-title {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 10px;
          margin-bottom: 17px;
        }

        .rb-editor-section-title h3 {
          display: flex;
          align-items: center;
          gap: 8px;
          margin: 0;
          font-size: 14px;
        }

        .rb-item {
          padding: 16px;
          margin-bottom: 12px;
          border: 1px solid #e8eaf0;
          border-radius: 12px;
          background: #fafbfc;
        }

        .rb-item-top {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 13px;
        }

        .rb-item-number {
          color: #6b7280;
          font-size: 11px;
          font-weight: 750;
        }

        .rb-small-button {
          width: 31px;
          height: 31px;
          display: flex;
          align-items: center;
          justify-content: center;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          color: #6b7280;
          background: #f3f4f6;
        }

        .rb-small-button:hover {
          color: #dc2626;
          background: #fff1f2;
        }

        .rb-bullet-row {
          display: flex;
          gap: 8px;
          margin-bottom: 8px;
        }

        .rb-bullet-row input {
          flex: 1;
          min-width: 0;
          padding: 9px 10px;
          border: 1px solid #dfe3ea;
          border-radius: 8px;
          outline: none;
          font-size: 12px;
        }

        .rb-bullet-row input:focus {
          border-color: #696be6;
          box-shadow:
            0 0 0 3px
            rgba(91, 92, 226, 0.08);
        }

        .rb-skill-category {
          padding: 13px;
          margin-bottom: 10px;
          border: 1px solid #e8eaf0;
          border-radius: 11px;
          background: #fafbfc;
        }

        .rb-skill-category-top {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 8px;
        }

        .rb-skill-category-top strong {
          font-size: 12px;
        }

        .rb-skill-category input {
          width: 100%;
          padding: 9px 10px;
          border: 1px solid #dfe3ea;
          border-radius: 8px;
          outline: none;
          font-size: 12px;
        }

        .rb-footer-actions {
          position: sticky;
          bottom: 15px;
          display: flex;
          justify-content: flex-end;
          gap: 9px;
          padding-top: 14px;
        }

        @media (max-width: 1050px) {
          .rb-layout {
            grid-template-columns: 1fr;
          }

          .rb-sidebar {
            position: static;
            display: flex;
            align-items: center;
            gap: 5px;
            overflow-x: auto;
          }

          .rb-sidebar-title {
            display: none;
          }

          .rb-step {
            flex: 0 0 auto;
            margin-bottom: 0;
          }
        }

        @media (max-width: 700px) {
          .rb-container {
            padding: 20px 14px 40px;
          }

          .rb-ai-badge {
            display: none;
          }

          .rb-source-grid,
          .rb-grid-2 {
            grid-template-columns: 1fr;
          }

          .rb-generate-content,
          .rb-editor-title {
            align-items: stretch;
            flex-direction: column;
          }

          .rb-editor-actions {
            flex-wrap: wrap;
          }

          .rb-card {
            padding: 17px;
          }

          .rb-file-row {
            flex-direction: column;
            align-items: stretch;
          }
        }
      `}</style>

      <div className="rb-container">
        {/* HEADER */}
        <div className="rb-topbar">
          <div className="rb-brand">
            <div className="rb-brand-icon">
              <WandSparkles size={22} />
            </div>

            <div>
              <h1>Resume Builder</h1>

              <p>
                Build or tailor your resume with AI
              </p>
            </div>
          </div>

          <div className="rb-ai-badge">
            <Sparkles size={14} />
            AI Powered
          </div>
        </div>

        <div className="rb-layout">
          {/* BUILDER SIDEBAR */}
          <aside className="rb-sidebar">
            <div className="rb-sidebar-title">
              Build Resume
            </div>

            {steps.map((step) => {
              const Icon = step.icon;

              return (
                <div
                  key={step.id}
                  className={`rb-step ${(!showEditor &&
                      step.id <= 3) ||
                      (showEditor &&
                        step.id === 4)
                      ? "active"
                      : ""
                    }`}
                >
                  <div className="rb-step-number">
                    <Icon size={14} />
                  </div>

                  <span className="rb-step-text">
                    {step.title}
                  </span>
                </div>
              );
            })}
          </aside>

          <main className="rb-main">
            {/* ======================================================
                GENERATOR
            ====================================================== */}

            {!showEditor ? (
              <>
                {error && (
                  <div className="rb-alert rb-alert-error">
                    <AlertCircle size={16} />

                    <span>{error}</span>
                  </div>
                )}

                {success && (
                  <div className="rb-alert rb-alert-success">
                    <CheckCircle2 size={16} />

                    <span>{success}</span>
                  </div>
                )}

                {/* SOURCE */}
                <div className="rb-card">
                  <SectionHeader
                    icon={FileText}
                    title="Choose your resume source"
                    description="Start with an existing resume or build a new one from a template."
                  />

                  <div className="rb-source-grid">
                    <div
                      className={`rb-source-card ${sourceType ===
                          "existing_resume"
                          ? "selected"
                          : ""
                        }`}
                      onClick={() =>
                        handleSourceChange(
                          "existing_resume"
                        )
                      }
                    >
                      <div className="rb-source-card-icon">
                        <FileCheck2 size={19} />
                      </div>

                      <h4>
                        I have a resume
                      </h4>

                      <p>
                        Use your existing resume
                        and optimize its skills
                        and projects for the
                        target job.
                      </p>
                    </div>

                    <div
                      className={`rb-source-card ${sourceType ===
                          "new_resume"
                          ? "selected"
                          : ""
                        }`}
                      onClick={() =>
                        handleSourceChange(
                          "new_resume"
                        )
                      }
                    >
                      <div className="rb-source-card-icon">
                        <Sparkles size={19} />
                      </div>

                      <h4>
                        Create a new resume
                      </h4>

                      <p>
                        Start from a sample
                        design and manually fill
                        your personal information
                        and experience.
                      </p>
                    </div>
                  </div>
                </div>

                {/* EXISTING RESUME */}
                {sourceType ===
                  "existing_resume" && (
                    <div className="rb-card">
                      <SectionHeader
                        icon={FileText}
                        title="Select existing resume"
                        description="Choose the resume you want to tailor."
                      />

                      <select
                        className="rb-select"
                        value={selectedResumeId}
                        onChange={(e) =>
                          setSelectedResumeId(
                            e.target.value
                          )
                        }
                      >
                        <option value="">
                          Select a resume
                        </option>

                        {resumes.map(
                          (resume) => (
                            <option
                              key={resume.id}
                              value={resume.id}
                            >
                              {resume.title ||
                                `Resume #${resume.id}`}
                            </option>
                          )
                        )}
                      </select>
                    </div>
                  )}

                {/* TEMPLATE */}
                <div className="rb-card">
                  <SectionHeader
                    icon={Palette}
                    title="Choose resume template"
                    description="The sample resume is used as the visual design and layout reference."
                  />

                  <div className="rb-template-list">
                    {templates.length ===
                      0 ? (
                      <div className="rb-empty-template">
                        <Palette size={18} />

                        <div>
                          <strong>
                            No templates
                            uploaded
                          </strong>

                          <p>
                            Upload a sample
                            resume to use
                            it as a design
                            template.
                          </p>
                        </div>
                      </div>
                    ) : (
                      templates.map(
                        (template) => (
                          <div
                            key={template.id}
                            className={`rb-template-item ${String(
                              selectedTemplateId
                            ) ===
                                String(
                                  template.id
                                )
                                ? "selected"
                                : ""
                              }`}
                          >
                            <button
                              type="button"
                              className="rb-template-select"
                              onClick={() =>
                                setSelectedTemplateId(
                                  String(
                                    template.id
                                  )
                                )
                              }
                            >
                              <div className="rb-template-icon">
                                <FileText
                                  size={17}
                                />
                              </div>

                              <div className="rb-template-info">
                                <strong>
                                  {
                                    template.name
                                  }
                                </strong>

                                <span>
                                  {template.file_type
                                    ?.toUpperCase() ||
                                    "TEMPLATE"}
                                </span>
                              </div>

                              {String(
                                selectedTemplateId
                              ) ===
                                String(
                                  template.id
                                ) && (
                                  <CheckCircle2
                                    size={17}
                                    className="rb-template-check"
                                  />
                                )}
                            </button>

                            <button
                              type="button"
                              className="rb-template-delete"
                              title="Delete template"
                              onClick={() =>
                                handleDeleteTemplate(
                                  template.id
                                )
                              }
                            >
                              <Trash2
                                size={15}
                              />
                            </button>
                          </div>
                        )
                      )
                    )}
                  </div>

                  <div className="rb-upload">
                    <div className="rb-upload-icon">
                      <Upload size={20} />
                    </div>

                    <h4>
                      Upload a sample resume
                    </h4>

                    <p>
                      PDF or DOCX — used only
                      for visual template
                      analysis
                    </p>

                    <div className="rb-field">
                      <input
                        type="text"
                        placeholder="Template name (optional)"
                        value={templateName}
                        onChange={(e) =>
                          setTemplateName(
                            e.target.value
                          )
                        }
                      />
                    </div>

                    <div className="rb-file-row">
                      <input
                        type="file"
                        accept=".pdf,.docx"
                        onChange={(e) =>
                          setTemplateFile(
                            e.target.files?.[0] ||
                            null
                          )
                        }
                      />

                      <button
                        type="button"
                        className="rb-button rb-button-outline"
                        onClick={
                          handleTemplateUpload
                        }
                        disabled={
                          uploadingTemplate ||
                          !templateFile
                        }
                      >
                        {uploadingTemplate ? (
                          <>
                            <Loader2
                              size={14}
                            />
                            Uploading...
                          </>
                        ) : (
                          <>
                            <Upload
                              size={14}
                            />
                            Upload
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </div>

                {/* JOB DESCRIPTION */}
                <div className="rb-card">
                  <SectionHeader
                    icon={Briefcase}
                    title="Target job description"
                    description="Paste the complete job description you want to optimize the resume for."
                  />

                  <TextAreaField
                    value={jobDescription}
                    onChange={
                      setJobDescription
                    }
                    placeholder="Paste the complete job description here..."
                    rows={10}
                  />

                  <div className="rb-generate-box">
                    <div className="rb-generate-content">
                      <div>
                        <h3>
                          Ready to optimize?
                        </h3>

                        <p>
                          AI will tailor the
                          Skills and Projects
                          sections to match the
                          target job.
                        </p>
                      </div>

                      <button
                        type="button"
                        className="rb-button rb-button-primary"
                        onClick={
                          handleGenerate
                        }
                        disabled={loading}
                      >
                        {loading ? (
                          <>
                            <Loader2
                              size={16}
                            />
                            Generating...
                          </>
                        ) : (
                          <>
                            <Sparkles
                              size={16}
                            />
                            Generate Resume
                            <ChevronRight
                              size={15}
                            />
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              /* ======================================================
                 EDITOR
              ====================================================== */
              <div className="rb-card">
                <div className="rb-editor-title">
                  <div>
                    <h2>
                      Edit Your Generated Resume
                    </h2>

                    <p className="rb-editor-subtitle">
                      Review the generated content
                      and make manual changes before
                      downloading.
                    </p>
                  </div>

                  <div className="rb-editor-actions">
                    <button
                      type="button"
                      className="rb-button rb-button-secondary"
                      onClick={() =>
                        setShowEditor(false)
                      }
                    >
                      Back
                    </button>

                    <button
                      type="button"
                      className="rb-button rb-button-outline"
                      onClick={handleSave}
                      disabled={saving}
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
                      className="rb-button rb-button-primary"
                      onClick={
                        handleDownload
                      }
                    >
                      <Download size={15} />
                      Download
                    </button>
                  </div>
                </div>

                {error && (
                  <div className="rb-alert rb-alert-error">
                    <AlertCircle size={16} />
                    <span>{error}</span>
                  </div>
                )}

                {success && (
                  <div className="rb-alert rb-alert-success">
                    <CheckCircle2 size={16} />
                    <span>{success}</span>
                  </div>
                )}

                <div className="rb-editor-layout">
                  <div className="rb-editor-form">
                    {/* PERSONAL */}
                    <div className="rb-editor-section">
                      <div className="rb-editor-section-title">
                        <h3>
                          <User size={16} />
                          Personal Information
                        </h3>
                      </div>

                      <div className="rb-grid-2">
                        <Field
                          label="Full Name"
                          value={
                            resumeContent
                              .personal?.name
                          }
                          onChange={(value) =>
                            updatePersonal(
                              "name",
                              value
                            )
                          }
                        />

                        <Field
                          label="Email"
                          value={
                            resumeContent
                              .personal?.email
                          }
                          onChange={(value) =>
                            updatePersonal(
                              "email",
                              value
                            )
                          }
                        />

                        <Field
                          label="Phone"
                          value={
                            resumeContent
                              .personal?.phone
                          }
                          onChange={(value) =>
                            updatePersonal(
                              "phone",
                              value
                            )
                          }
                        />

                        <Field
                          label="Location"
                          value={
                            resumeContent
                              .personal?.location
                          }
                          onChange={(value) =>
                            updatePersonal(
                              "location",
                              value
                            )
                          }
                        />

                        <Field
                          label="LinkedIn"
                          value={
                            resumeContent
                              .personal?.linkedin
                          }
                          onChange={(value) =>
                            updatePersonal(
                              "linkedin",
                              value
                            )
                          }
                        />

                        <Field
                          label="GitHub"
                          value={
                            resumeContent
                              .personal?.github
                          }
                          onChange={(value) =>
                            updatePersonal(
                              "github",
                              value
                            )
                          }
                        />

                        <Field
                          label="Website"
                          value={
                            resumeContent
                              .personal?.website
                          }
                          onChange={(value) =>
                            updatePersonal(
                              "website",
                              value
                            )
                          }
                        />
                      </div>
                    </div>

                    {/* SUMMARY */}
                    <div className="rb-editor-section">
                      <div className="rb-editor-section-title">
                        <h3>
                          <FileText size={16} />
                          Professional Summary
                        </h3>

                        <button
                          type="button"
                          className="rb-button rb-button-outline"
                          onClick={handleGenerateSummary}
                          disabled={generatingSummary || !hasContentForSummary(resumeContent)}
                          title={
                            generatingSummary
                              ? "Generating summary..."
                              : missingSummarySections(resumeContent).length
                              ? "Complete the following sections to enable AI summary generation: " +
                                missingSummarySections(resumeContent)
                                  .map((section) => section.label)
                                  .join(", ") +
                                ". (Publications is optional.)"
                              : "Generate professional summary with AI"
                          }
                        >
                          {generatingSummary ? (
                            <>
                              <Loader2 size={14} className="spin" />
                              Generating...
                            </>
                          ) : (
                            <>
                              <Sparkles size={14} />
                              AI Generate
                            </>
                          )}
                        </button>
                      </div>

                      <TextAreaField
                        value={
                          resumeContent.summary
                        }
                        onChange={(value) =>
                          setResumeContent(
                            (prev) => ({
                              ...prev,
                              summary: value,
                            })
                          )
                        }
                        rows={5}
                      />
                    </div>

                    {/* SKILLS */}
                    <div className="rb-editor-section">
                      <div className="rb-editor-section-title">
                        <h3>
                          <Code2 size={16} />
                          Skills
                        </h3>

                        <button
                          type="button"
                          className="rb-button rb-button-outline"
                          onClick={
                            addSkillCategory
                          }
                        >
                          <Plus size={14} />
                          Add Category
                        </button>
                      </div>

                      {Object.entries(
                        resumeContent.skills || {}
                      ).map(
                        ([category, skills]) => (
                          <div
                            className="rb-skill-category"
                            key={category}
                          >
                            <div className="rb-skill-category-top">
                              <strong>
                                {category}
                              </strong>

                              <button
                                type="button"
                                className="rb-small-button"
                                onClick={() =>
                                  removeSkillCategory(
                                    category
                                  )
                                }
                              >
                                <Trash2
                                  size={13}
                                />
                              </button>
                            </div>

                            <input
                              value={skills.join(
                                ", "
                              )}
                              onChange={(e) =>
                                updateSkillCategory(
                                  category,
                                  e.target.value
                                )
                              }
                              placeholder="Python, Django, React..."
                            />
                          </div>
                        )
                      )}
                    </div>

                    {/* EXPERIENCE */}
                    <div className="rb-editor-section">
                      <div className="rb-editor-section-title">
                        <h3>
                          <Briefcase size={16} />
                          Work Experience
                        </h3>

                        <button
                          type="button"
                          className="rb-button rb-button-outline"
                          onClick={
                            addExperience
                          }
                        >
                          <Plus size={14} />
                          Add Experience
                        </button>
                      </div>

                      {resumeContent.experience.map(
                        (
                          experience,
                          index
                        ) => (
                          <div
                            className="rb-item"
                            key={index}
                          >
                            <div className="rb-item-top">
                              <span className="rb-item-number">
                                Experience{" "}
                                {index + 1}
                              </span>

                              <button
                                type="button"
                                className="rb-small-button"
                                onClick={() =>
                                  removeExperience(
                                    index
                                  )
                                }
                              >
                                <Trash2
                                  size={14}
                                />
                              </button>
                            </div>

                            <div className="rb-grid-2">
                              <Field
                                label="Company"
                                value={
                                  experience.company
                                }
                                onChange={(
                                  value
                                ) =>
                                  updateExperience(
                                    index,
                                    "company",
                                    value
                                  )
                                }
                              />

                              <Field
                                label="Role"
                                value={
                                  experience.role
                                }
                                onChange={(
                                  value
                                ) =>
                                  updateExperience(
                                    index,
                                    "role",
                                    value
                                  )
                                }
                              />

                              <Field
                                label="Location"
                                value={
                                  experience.location
                                }
                                onChange={(
                                  value
                                ) =>
                                  updateExperience(
                                    index,
                                    "location",
                                    value
                                  )
                                }
                              />

                              <Field
                                label="Start Date"
                                value={
                                  experience.start_date
                                }
                                onChange={(
                                  value
                                ) =>
                                  updateExperience(
                                    index,
                                    "start_date",
                                    value
                                  )
                                }
                              />

                              <Field
                                label="End Date"
                                value={
                                  experience.end_date
                                }
                                onChange={(
                                  value
                                ) =>
                                  updateExperience(
                                    index,
                                    "end_date",
                                    value
                                  )
                                }
                              />
                            </div>

                            <label
                              style={{
                                display:
                                  "flex",
                                alignItems:
                                  "center",
                                gap: "7px",
                                marginBottom:
                                  "13px",
                                fontSize:
                                  "12px",
                              }}
                            >
                              <input
                                type="checkbox"
                                checked={Boolean(
                                  experience.current
                                )}
                                onChange={(e) =>
                                  updateExperience(
                                    index,
                                    "current",
                                    e.target
                                      .checked
                                  )
                                }
                              />

                              Currently working
                              here
                            </label>

                            <label
                              style={{
                                display:
                                  "block",
                                marginBottom:
                                  "8px",
                                fontSize:
                                  "12px",
                                fontWeight:
                                  700,
                              }}
                            >
                              Responsibilities /
                              Achievements
                            </label>

                            {(
                              experience.bullets ||
                              []
                            ).map(
                              (
                                bullet,
                                bulletIndex
                              ) => (
                                <div
                                  className="rb-bullet-row"
                                  key={
                                    bulletIndex
                                  }
                                >
                                  <input
                                    value={
                                      bullet
                                    }
                                    onChange={(
                                      e
                                    ) =>
                                      updateExperienceBullet(
                                        index,
                                        bulletIndex,
                                        e
                                          .target
                                          .value
                                      )
                                    }
                                    placeholder="Describe your responsibility or achievement"
                                  />

                                  <button
                                    type="button"
                                    className="rb-small-button"
                                    onClick={() =>
                                      removeExperienceBullet(
                                        index,
                                        bulletIndex
                                      )
                                    }
                                  >
                                    <Trash2
                                      size={13}
                                    />
                                  </button>
                                </div>
                              )
                            )}

                            <button
                              type="button"
                              className="rb-button rb-button-secondary"
                              onClick={() =>
                                addExperienceBullet(
                                  index
                                )
                              }
                            >
                              <Plus size={13} />
                              Add Bullet
                            </button>
                          </div>
                        )
                      )}
                    </div>

                    {/* PROJECTS */}
                    <div className="rb-editor-section">
                      <div className="rb-editor-section-title">
                        <h3>
                          <FolderKanban
                            size={16}
                          />
                          Projects
                        </h3>

                        <button
                          type="button"
                          className="rb-button rb-button-outline"
                          onClick={addProject}
                        >
                          <Plus size={14} />
                          Add Project
                        </button>
                      </div>

                      {resumeContent.projects.map(
                        (
                          project,
                          index
                        ) => (
                          <div
                            className="rb-item"
                            key={index}
                          >
                            <div className="rb-item-top">
                              <span className="rb-item-number">
                                Project{" "}
                                {index + 1}
                              </span>

                              <button
                                type="button"
                                className="rb-small-button"
                                onClick={() =>
                                  removeProject(
                                    index
                                  )
                                }
                              >
                                <Trash2
                                  size={14}
                                />
                              </button>
                            </div>

                            <Field
                              label="Project Name"
                              value={
                                project.name
                              }
                              onChange={(value) =>
                                updateProject(
                                  index,
                                  "name",
                                  value
                                )
                              }
                            />

                            <TextAreaField
                              label="Description"
                              value={
                                project.description
                              }
                              onChange={(value) =>
                                updateProject(
                                  index,
                                  "description",
                                  value
                                )
                              }
                              rows={4}
                            />

                            <Field
                              label="Technologies"
                              value={(
                                project.technologies ||
                                []
                              ).join(", ")}
                              onChange={(value) =>
                                updateProject(
                                  index,
                                  "technologies",
                                  value
                                    .split(",")
                                    .map(
                                      (item) =>
                                        item.trim()
                                    )
                                    .filter(
                                      Boolean
                                    )
                                )
                              }
                              placeholder="Python, Django, React..."
                            />

                            <Field
                              label="Project URL"
                              value={
                                project.url
                              }
                              onChange={(value) =>
                                updateProject(
                                  index,
                                  "url",
                                  value
                                )
                              }
                            />

                            <label
                              style={{
                                display:
                                  "block",
                                marginBottom:
                                  "8px",
                                fontSize:
                                  "12px",
                                fontWeight:
                                  700,
                              }}
                            >
                              Project Bullets
                            </label>

                            {(
                              project.bullets ||
                              []
                            ).map(
                              (
                                bullet,
                                bulletIndex
                              ) => (
                                <div
                                  className="rb-bullet-row"
                                  key={
                                    bulletIndex
                                  }
                                >
                                  <input
                                    value={
                                      bullet
                                    }
                                    onChange={(
                                      e
                                    ) =>
                                      updateProjectBullet(
                                        index,
                                        bulletIndex,
                                        e
                                          .target
                                          .value
                                      )
                                    }
                                    placeholder="Describe project functionality or contribution"
                                  />

                                  <button
                                    type="button"
                                    className="rb-small-button"
                                    onClick={() =>
                                      removeProjectBullet(
                                        index,
                                        bulletIndex
                                      )
                                    }
                                  >
                                    <Trash2
                                      size={13}
                                    />
                                  </button>
                                </div>
                              )
                            )}

                            <button
                              type="button"
                              className="rb-button rb-button-secondary"
                              onClick={() =>
                                addProjectBullet(
                                  index
                                )
                              }
                            >
                              <Plus size={13} />
                              Add Bullet
                            </button>
                          </div>
                        )
                      )}
                    </div>

                    {/* EDUCATION */}
                    <div className="rb-editor-section">
                      <div className="rb-editor-section-title">
                        <h3>
                          <GraduationCap
                            size={17}
                          />
                          Education
                        </h3>

                        <button
                          type="button"
                          className="rb-button rb-button-outline"
                          onClick={
                            addEducation
                          }
                        >
                          <Plus size={14} />
                          Add Education
                        </button>
                      </div>

                      {resumeContent.education.map(
                        (
                          education,
                          index
                        ) => (
                          <div
                            className="rb-item"
                            key={index}
                          >
                            <div className="rb-item-top">
                              <span className="rb-item-number">
                                Education{" "}
                                {index + 1}
                              </span>

                              <button
                                type="button"
                                className="rb-small-button"
                                onClick={() =>
                                  removeEducation(
                                    index
                                  )
                                }
                              >
                                <Trash2
                                  size={14}
                                />
                              </button>
                            </div>

                            <div className="rb-grid-2">
                              <Field
                                label="Degree"
                                value={
                                  education.degree
                                }
                                onChange={(
                                  value
                                ) =>
                                  updateEducation(
                                    index,
                                    "degree",
                                    value
                                  )
                                }
                              />

                              <Field
                                label="Institution"
                                value={
                                  education.institution
                                }
                                onChange={(
                                  value
                                ) =>
                                  updateEducation(
                                    index,
                                    "institution",
                                    value
                                  )
                                }
                              />

                              <Field
                                label="Location"
                                value={
                                  education.location
                                }
                                onChange={(
                                  value
                                ) =>
                                  updateEducation(
                                    index,
                                    "location",
                                    value
                                  )
                                }
                              />

                              <Field
                                label="Grade"
                                value={
                                  education.grade
                                }
                                onChange={(
                                  value
                                ) =>
                                  updateEducation(
                                    index,
                                    "grade",
                                    value
                                  )
                                }
                              />

                              <Field
                                label="Start Date"
                                value={
                                  education.start_date
                                }
                                onChange={(
                                  value
                                ) =>
                                  updateEducation(
                                    index,
                                    "start_date",
                                    value
                                  )
                                }
                              />

                              <Field
                                label="End Date"
                                value={
                                  education.end_date
                                }
                                onChange={(
                                  value
                                ) =>
                                  updateEducation(
                                    index,
                                    "end_date",
                                    value
                                  )
                                }
                              />
                            </div>
                          </div>
                        )
                      )}
                    </div>

                    {/* CERTIFICATIONS */}
                    <div className="rb-editor-section">
                      <div className="rb-editor-section-title">
                        <h3>
                          <Award size={16} />
                          Certifications
                        </h3>

                        <button
                          type="button"
                          className="rb-button rb-button-outline"
                          onClick={
                            addCertification
                          }
                        >
                          <Plus size={14} />
                          Add Certification
                        </button>
                      </div>

                      {resumeContent.certifications.map(
                        (
                          certification,
                          index
                        ) => (
                          <div
                            className="rb-item"
                            key={index}
                          >
                            <div className="rb-item-top">
                              <span className="rb-item-number">
                                Certification{" "}
                                {index + 1}
                              </span>

                              <button
                                type="button"
                                className="rb-small-button"
                                onClick={() =>
                                  removeCertification(
                                    index
                                  )
                                }
                              >
                                <Trash2
                                  size={14}
                                />
                              </button>
                            </div>

                            <div className="rb-grid-2">
                              <Field
                                label="Certification"
                                value={
                                  certification.name
                                }
                                onChange={(
                                  value
                                ) =>
                                  updateCertification(
                                    index,
                                    "name",
                                    value
                                  )
                                }
                              />

                              <Field
                                label="Issuer"
                                value={
                                  certification.issuer
                                }
                                onChange={(
                                  value
                                ) =>
                                  updateCertification(
                                    index,
                                    "issuer",
                                    value
                                  )
                                }
                              />

                              <Field
                                label="Date"
                                value={
                                  certification.date
                                }
                                onChange={(
                                  value
                                ) =>
                                  updateCertification(
                                    index,
                                    "date",
                                    value
                                  )
                                }
                              />

                              <Field
                                label="URL"
                                value={
                                  certification.url
                                }
                                onChange={(
                                  value
                                ) =>
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
                    </div>

                    {/* PUBLICATIONS */}
                    <div className="rb-editor-section">
                      <div className="rb-editor-section-title">
                        <h3>
                          <FileText size={16} />
                          Publications
                        </h3>

                        <button
                          type="button"
                          className="rb-button rb-button-outline"
                          onClick={
                            addPublication
                          }
                        >
                          <Plus size={14} />
                          Add Publication
                        </button>
                      </div>

                      {resumeContent.publications.map(
                        (
                          publication,
                          index
                        ) => (
                          <div
                            className="rb-item"
                            key={index}
                          >
                            <div className="rb-item-top">
                              <span className="rb-item-number">
                                Publication{" "}
                                {index + 1}
                              </span>

                              <button
                                type="button"
                                className="rb-small-button"
                                onClick={() =>
                                  removePublication(
                                    index
                                  )
                                }
                              >
                                <Trash2
                                  size={14}
                                />
                              </button>
                            </div>

                            <div className="rb-grid-2">
                              <Field
                                label="Title"
                                value={
                                  publication.title
                                }
                                onChange={(
                                  value
                                ) =>
                                  updatePublication(
                                    index,
                                    "title",
                                    value
                                  )
                                }
                              />

                              <Field
                                label="Authors"
                                value={
                                  publication.authors
                                }
                                onChange={(
                                  value
                                ) =>
                                  updatePublication(
                                    index,
                                    "authors",
                                    value
                                  )
                                }
                              />

                              <Field
                                label="Venue"
                                value={
                                  publication.venue
                                }
                                onChange={(
                                  value
                                ) =>
                                  updatePublication(
                                    index,
                                    "venue",
                                    value
                                  )
                                }
                              />

                              <Field
                                label="Date"
                                value={
                                  publication.date
                                }
                                onChange={(
                                  value
                                ) =>
                                  updatePublication(
                                    index,
                                    "date",
                                    value
                                  )
                                }
                              />

                              <Field
                                label="URL"
                                value={
                                  publication.url
                                }
                                onChange={(
                                  value
                                ) =>
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
                    </div>

                    {/* FOOTER ACTIONS */}
                    <div className="rb-footer-actions">
                      <button
                        type="button"
                        className="rb-button rb-button-outline"
                        onClick={handleSave}
                        disabled={saving}
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
                        className="rb-button rb-button-primary"
                        onClick={
                          handleDownload
                        }
                      >
                        <Download size={15} />
                        Download Resume
                      </button>
                    </div>
                  </div>

                  {renderResumePreview()}
                </div>
              </div>
            )}
          </main>
        </div>
      </div>
    </div>
  );
}

export default ResumeBuilder;


