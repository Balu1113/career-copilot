import { useEffect, useState } from "react";
import {
  CheckCircle2,
  FileText,
  Trash2,
} from "lucide-react";

import api from "../services/api";

import "./Resumes.css";


function Resumes() {

  const [resumes, setResumes] =
    useState([]);

  const [activeResumeId, setActiveResumeId] =
    useState(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");


  const fetchResumes = async () => {

    try {

      setLoading(true);

      const response =
        await api.get(
          "/resumes/"
        );

      setResumes(
        response.data
      );

    } catch (error) {

      setError(
        "Unable to load resumes."
      );

    } finally {

      setLoading(false);
    }
  };


  useEffect(() => {

    fetchResumes();

  }, []);


  const activateResume = async (
    resumeId
  ) => {

    try {

      await api.post(
        `/resumes/${resumeId}/activate/`
      );

      setActiveResumeId(
        resumeId
      );

    } catch (error) {

      setError(
        "Unable to activate resume."
      );
    }
  };


  const deleteResume = async (
    resumeId
  ) => {

    const confirmed =
      window.confirm(
        "Delete this resume?"
      );

    if (!confirmed) {
      return;
    }


    try {

      await api.delete(
        `/resumes/${resumeId}/`
      );

      setResumes(
        (current) =>
          current.filter(
            (resume) =>
              resume.id !== resumeId
          )
      );


      if (
        activeResumeId === resumeId
      ) {

        setActiveResumeId(null);

      }

    } catch (error) {

      setError(
        "Unable to delete resume."
      );
    }
  };


  if (loading) {

    return (
      <div className="page-loading">
        Loading resumes...
      </div>
    );
  }


  return (
    <div className="resumes-page">

      <div className="page-header">

        <div>

          <h1>
            My Resumes
          </h1>

          <p>
            Manage your resume versions.
          </p>

        </div>

      </div>


      {error && (
        <p className="error-message">
          {error}
        </p>
      )}


      {resumes.length === 0 ? (

        <div className="empty-state">

          <FileText size={42} />

          <h2>
            No resumes yet
          </h2>

          <p>
            Upload your first resume from
            the dashboard.
          </p>

        </div>

      ) : (

        <div className="resume-grid">

          {resumes.map(
            (resume) => {

              const isActive =
                activeResumeId ===
                resume.id;

              return (

                <div
                  className={
                    `resume-card ${
                      isActive
                        ? "active"
                        : ""
                    }`
                  }
                  key={resume.id}
                >

                  <div className="resume-icon">

                    <FileText size={26} />

                  </div>


                  <div className="resume-info">

                    <h3>
                      {resume.title}
                    </h3>

                    <p>
                      Uploaded{" "}
                      {new Date(
                        resume.uploaded_at
                      ).toLocaleDateString()}
                    </p>

                  </div>


                  {isActive && (

                    <div className="active-badge">

                      <CheckCircle2
                        size={15}
                      />

                      Active

                    </div>

                  )}


                  <div className="resume-actions">

                    {!isActive && (

                      <button
                        onClick={() =>
                          activateResume(
                            resume.id
                          )
                        }
                      >
                        Use this resume
                      </button>

                    )}


                    <button
                      className="delete-button"
                      onClick={() =>
                        deleteResume(
                          resume.id
                        )
                      }
                    >

                      <Trash2
                        size={16}
                      />

                      Delete

                    </button>

                  </div>

                </div>

              );
            }
          )}

        </div>

      )}

    </div>
  );
}


export default Resumes;