import { useEffect, useState } from "react";
import {
  Brain,
  FileText,
  Loader2,
} from "lucide-react";

import api from "../services/api";
import Sidebar from "../components/Sidebar";

import "./ResumeIntelligence.css";


function ResumeIntelligence() {
  const [resumes, setResumes] = useState([]);
  const [resumeId, setResumeId] = useState("");
  const [intelligence, setIntelligence] = useState(null);

  const [loadingResumes, setLoadingResumes] = useState(true);
  const [loadingIntelligence, setLoadingIntelligence] =
    useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");


  useEffect(() => {
    const loadResumes = async () => {
      try {
        setLoadingResumes(true);
        setError("");

        const response = await api.get("/resumes/");

        setResumes(response.data);

        if (response.data.length > 0) {
          setResumeId(String(response.data[0].id));
        }
      } catch (err) {
        setError(
          err.response?.data?.error ||
          "Unable to load resumes."
        );
      } finally {
        setLoadingResumes(false);
      }
    };

    loadResumes();
  }, []);


  useEffect(() => {
    if (!resumeId) {
      setIntelligence(null);
      return;
    }

    const loadIntelligence = async () => {
      try {
        setLoadingIntelligence(true);
        setError("");

        const response = await api.get(
          `/resumes/${resumeId}/intelligence/`
        );

        setIntelligence(response.data);
      } catch (err) {
        setIntelligence(null);

        setError(
          err.response?.data?.error ||
          "Resume intelligence has not been generated yet."
        );
      } finally {
        setLoadingIntelligence(false);
      }
    };

    loadIntelligence();
  }, [resumeId]);

  const handleGenerate = async () => {
  if (!resumeId) return;

  try {
    setGenerating(true);
    setError("");

    const response = await api.post(
      `/resumes/${resumeId}/intelligence/generate/`
    );

    setIntelligence(response.data);
  } catch (err) {
    setError(
      err.response?.data?.error ||
        "Failed to generate resume intelligence."
    );
  } finally {
    setGenerating(false);
  }
};

  return (
    <div className="dashboard-layout">
      <Sidebar />

      <main className="dashboard-main resume-intelligence-page">

        <div className="resume-intelligence-header">
          <div className="resume-intelligence-title">
            <Brain size={27} />

            <div>
              <h1>Resume Intelligence</h1>

              <p>
                View the structured information extracted
                from your resume by the AI system.
              </p>
            </div>
          </div>
        </div>


        <section className="resume-intelligence-selector">
  <label>Resume</label>

  {loadingResumes ? (
    <div className="resume-intelligence-loading-inline">
      <Loader2
        size={17}
        className="spinning"
      />
      Loading resumes...
    </div>
  ) : (
    <select
      value={resumeId}
      onChange={(event) =>
        setResumeId(event.target.value)
      }
    >
      {resumes.length === 0 ? (
        <option value="">
          No resumes available
        </option>
      ) : (
        resumes.map((resume) => (
          <option
            key={resume.id}
            value={resume.id}
          >
            {resume.title}
          </option>
        ))
      )}
    </select>
  )}

  <button
    type="button"
    className="generate-intelligence-button"
    onClick={handleGenerate}
    disabled={!resumeId || generating}
  >
    {generating ? (
      <>
        <Loader2
          size={17}
          className="spinning"
        />
        Generating...
      </>
    ) : (
      <>
        <Brain size={17} />
        Generate Intelligence
      </>
    )}
  </button>
</section>


        {error && (
          <div className="resume-intelligence-error">
            {error}
          </div>
        )}


        {loadingIntelligence ? (
          <div className="resume-intelligence-loading">
            <Loader2
              size={25}
              className="spinning"
            />

            <p>
              Loading resume intelligence...
            </p>
          </div>
        ) : intelligence ? (
          <div className="resume-intelligence-results">

            {intelligence.professional_summary && (
              <section className="resume-intelligence-card">
                <h2>Professional Summary</h2>

                <p className="intelligence-summary">
                  {intelligence.professional_summary}
                </p>
              </section>
            )}


            <IntelligenceTags
              title="Skills"
              items={intelligence.skills}
            />

            <IntelligenceTags
              title="Programming Languages"
              items={
                intelligence.programming_languages
              }
            />

            <IntelligenceTags
              title="Frameworks"
              items={intelligence.frameworks}
            />

            <IntelligenceTags
              title="Tools & Technologies"
              items={
                intelligence.tools_and_technologies
              }
            />

            <IntelligenceTags
              title="AI / ML Technologies"
              items={
                intelligence.ai_ml_technologies
              }
            />

            <IntelligenceProjects
            projects={intelligence.projects}
            />

            <IntelligenceList
              title="Experience"
              items={intelligence.experience}
            />

            <IntelligenceList
              title="Education"
              items={intelligence.education}
            />

            <IntelligenceList
              title="Certifications"
              items={intelligence.certifications}
            />

          </div>
        ) : null}

      </main>
    </div>
  );
}


function IntelligenceTags({
  title,
  items = [],
}) {
  if (!items || items.length === 0) {
    return null;
  }

  return (
    <section className="resume-intelligence-card">
      <h2>{title}</h2>

      <div className="intelligence-tags">
        {items.map((item, index) => (
          <span
            className="intelligence-tag"
            key={index}
          >
            {item}
          </span>
        ))}
      </div>
    </section>
  );
}

function IntelligenceProjects({
  projects = [],
}) {
  if (!projects || projects.length === 0) {
    return null;
  }

  return (
    <section className="resume-intelligence-card">
      <h2>Projects</h2>

      <div className="intelligence-projects">
        {projects.map((project, index) => (
          <div
            className="intelligence-project"
            key={index}
          >
            <div className="intelligence-project-header">
              <div className="intelligence-number">
                {index + 1}
              </div>

              <h3>{project.name}</h3>
            </div>

            {project.description &&
              project.description.length > 0 && (
                <div className="intelligence-project-section">
                  <h4>Description</h4>

                  <ul>
                    {project.description.map(
                      (description, descriptionIndex) => (
                        <li key={descriptionIndex}>
                          {description}
                        </li>
                      )
                    )}
                  </ul>
                </div>
              )}

            {project.technologies &&
              project.technologies.length > 0 && (
                <div className="intelligence-project-section">
                  <h4>Technologies</h4>

                  <div className="intelligence-tags">
                    {project.technologies.map(
                      (technology, technologyIndex) => (
                        <span
                          className="intelligence-tag"
                          key={technologyIndex}
                        >
                          {technology}
                        </span>
                      )
                    )}
                  </div>
                </div>
              )}
          </div>
        ))}
      </div>
    </section>
  );
}

function IntelligenceList({
  title,
  items = [],
}) {
  if (!items || items.length === 0) {
    return null;
  }

  return (
    <section className="resume-intelligence-card">
      <h2>{title}</h2>

      <div className="intelligence-list">
        {items.map((item, index) => (
          <div
            className="intelligence-list-item"
            key={index}
          >
            <div className="intelligence-list-content">

              {title === "Experience" && (
                <>
                  <h3 className="intelligence-item-title">
                    {item.role}
                  </h3>

                  {item.company && (
                    <div className="intelligence-item-meta">
                      {item.company}
                    </div>
                  )}

                  {item.description?.length > 0 && (
                    <ul className="intelligence-item-description">
                      {item.description.map(
                        (description, descriptionIndex) => (
                          <li key={descriptionIndex}>
                            {description}
                          </li>
                        )
                      )}
                    </ul>
                  )}

                  {item.technologies?.length > 0 && (
                    <div className="intelligence-item-technologies">
                      <strong>Technologies:</strong>

                      <div className="intelligence-tags">
                        {item.technologies.map(
                          (technology, technologyIndex) => (
                            <span
                              className="intelligence-tag"
                              key={technologyIndex}
                            >
                              {technology}
                            </span>
                          )
                        )}
                      </div>
                    </div>
                  )}
                </>
              )}

              {title === "Education" && (
                <>
                  <h3 className="intelligence-item-title">
                    {item.degree}
                  </h3>

                  {item.institution && (
                    <div className="intelligence-item-meta">
                      {item.institution}
                    </div>
                  )}

                  {item.dates && (
                    <p className="intelligence-item-text">
                      {item.dates}
                    </p>
                  )}
                </>
              )}

              {title === "Certifications" && (
                <>
                  <h3 className="intelligence-item-title">
                    {item.name}
                  </h3>

                  {item.issuer && (
                    <div className="intelligence-item-meta">
                      Issued by: {item.issuer}
                    </div>
                  )}
                </>
              )}

            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

export default ResumeIntelligence;