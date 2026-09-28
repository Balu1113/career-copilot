import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  ArrowLeft,
  ArrowRight,
  Briefcase,
  Brain,
  CheckCircle2,
  MessageSquare,
  Palette,
  Rocket,
  Sparkles,
  Upload,
  X,
} from "lucide-react";

import "./OnboardingTour.css";


export const ONBOARDING_OPEN_EVENT = "onboarding:open";
export const ONBOARDING_COMPLETED_KEY = "onboarding_completed";


const markCompleted = () => {
  localStorage.setItem(ONBOARDING_COMPLETED_KEY, "1");
};


const steps = [
  {
    id: "welcome",
    icon: Rocket,
    title: "How to use this app",
    subtitle: "Your 60-second tour",
    description:
      "Seven short screens, each with the exact clicks to make. You will upload a resume, tailor one to a job, analyse yourself, prep for interviews and track applications.",
    howto: [
      "Press Next to move forward and Back to re-read any screen.",
      "Most screens have an action box that jumps straight to that feature.",
      "Close the guide whenever you like and reopen it from Getting Started in the sidebar.",
    ],
  },
  {
    id: "resume",
    icon: Upload,
    title: "Upload your resume",
    subtitle: "Step 1 · Your foundation",
    description:
      "Everything starts from your resume. Upload it once and the AI extracts your skills, projects, experience and education into structured data.",
    howto: [
      "Open My Resumes in the sidebar.",
      "Choose a PDF or DOCX file and press Upload.",
      "Wait for the status badge to turn Ready — this takes a few seconds.",
      "Set it as your active resume so other features can read it.",
    ],
    action: { label: "Go to My Resumes", path: "/resumes" },
  },
  {
    id: "builder",
    icon: Palette,
    title: "Build a resume with a template",
    subtitle: "Step 2 · Resume Builder",
    description:
      "Pick an ATS-friendly template, preview it full screen, then generate a tailored resume from your existing content.",
    howto: [
      "Open Resume Builder and choose a source: existing resume or new.",
      "Click any template card to open its preview.",
      "Press Use this template to select it — or upload your own sample.",
      "Paste a job description and press Generate Resume, then Download.",
    ],
    action: { label: "Open Resume Builder", path: "/resume-builder" },
  },
  {
    id: "analysis",
    icon: Sparkles,
    title: "Analyse yourself against a job",
    subtitle: "Step 3 · Career analysis",
    description:
      "Paste any job description and get a full match report: required skills, your matching skills, skill gaps and a tailored roadmap.",
    howto: [
      "Copy the complete job description, not just the title.",
      "Press Analyse to get your match score and skill gaps.",
      "Read the roadmap that turns each gap into a study plan.",
      "Re-open past reports any time from Career History.",
    ],
    action: { label: "Open Career Analysis", path: "/career-analysis" },
  },
  {
    id: "intelligence",
    icon: Brain,
    title: "Ask anything about your resume",
    subtitle: "Step 4 · Resume AI Chat",
    description:
      "Your resume becomes a knowledge base. Ask in plain language and get answers grounded only in what your resume actually says.",
    howto: [
      "Type a question such as “What are my strongest technical skills?”.",
      "Read the answer — it never invents experience you do not have.",
      "Open Resume Intelligence to see the full extracted profile.",
    ],
    action: { label: "Open Resume AI Chat", path: "/resume-chat" },
  },
  {
    id: "interview",
    icon: MessageSquare,
    title: "Prepare for interviews",
    subtitle: "Step 5 · Interview prep",
    description:
      "Generate questions for your target role, rehearse spoken answers in the simulator, and watch your scores improve.",
    howto: [
      "Open Interview Prep and generate questions for your target role.",
      "Answer them in writing, or rehearse aloud in the Interview Simulator.",
      "Check Interview Performance after each session for feedback.",
    ],
    action: { label: "Open Interview Prep", path: "/interview-prep" },
  },
  {
    id: "applications",
    icon: Briefcase,
    title: "Track jobs and applications",
    subtitle: "Step 6 · Job search",
    description:
      "Browse jobs, review the roles recommended for your profile, and track every application from applied to offer in one place.",
    howto: [
      "Open Jobs to browse, or Recommended Jobs for profile matches.",
      "Add an application and move it through applied, interview and offer.",
      "Watch your totals update on the Dashboard.",
    ],
    action: { label: "Open Applications", path: "/applications" },
  },
  {
    id: "finish",
    icon: CheckCircle2,
    title: "You are all set",
    subtitle: "Ready to start",
    description:
      "That is the whole workflow: upload, tailor, analyse, practise, apply. Work through it in that order for the best results.",
    howto: [
      "Start with your resume — the other features read from it.",
      "Your data is private to your account and never shared.",
      "Update your profile and password any time in My Profile.",
      "Reopen this guide from Getting Started in the sidebar.",
    ],
  },
];


function OnboardingTour() {
  const navigate = useNavigate();

  const [open, setOpen] = useState(
    () =>
      localStorage.getItem(ONBOARDING_COMPLETED_KEY) !== "1" &&
      localStorage.getItem("access_token") !== null
  );
  const [stepIndex, setStepIndex] = useState(0);

  const step = steps[stepIndex];
  const isFirst = stepIndex === 0;
  const isLast = stepIndex === steps.length - 1;


  useEffect(() => {
    const handleOpen = () => {
      setStepIndex(0);
      setOpen(true);
    };

    window.addEventListener(ONBOARDING_OPEN_EVENT, handleOpen);

    return () =>
      window.removeEventListener(ONBOARDING_OPEN_EVENT, handleOpen);
  }, []);


  useEffect(() => {
    if (!open) return undefined;

    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        markCompleted();
        setOpen(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);

    return () =>
      window.removeEventListener("keydown", handleKeyDown);
  }, [open]);


  if (!open) {
    return null;
  }


  const goTo = (index) => {
    setStepIndex(index);
  };

  const goNext = () => {
    if (isLast) {
      markCompleted();
      setOpen(false);
      return;
    }

    goTo(stepIndex + 1);
  };

  const goBack = () => {
    if (isFirst) return;

    goTo(stepIndex - 1);
  };

  const skip = () => {
    markCompleted();
    setOpen(false);
  };

  const runAction = () => {
    setOpen(false);

    if (step.action) {
      navigate(step.action.path);
    }
  };


  const StepIcon = step.icon;

  return (
    <div
      className="onboarding-overlay"
      role="dialog"
      aria-modal="true"
      aria-label="Getting started guide"
    >
      <div className="onboarding-modal">

        <div className="onboarding-topbar">
          <span className="onboarding-step-badge">
            Step {stepIndex + 1} of {steps.length}
          </span>

          <button
            type="button"
            className="onboarding-close"
            onClick={skip}
            aria-label="Close guide"
          >
            <X size={18} />
          </button>
        </div>


        <div className="onboarding-progress">
          {steps.map((item, index) => (
            <button
              key={item.id}
              type="button"
              className={`onboarding-dot ${
                index === stepIndex ? "active" : ""
              } ${index < stepIndex ? "done" : ""}`}
              onClick={() => goTo(index)}
              aria-label={`Go to step ${index + 1}: ${item.title}`}
            />
          ))}
        </div>


        <div className="onboarding-body">

          <div className="onboarding-icon">
            <StepIcon size={26} />
          </div>

          <p className="onboarding-subtitle">{step.subtitle}</p>

          <h2 className="onboarding-title">{step.title}</h2>

          <p className="onboarding-description">
            {step.description}
          </p>


          <ol className="onboarding-steps">
            {step.howto.map((instruction, index) => (
              <li key={instruction}>
                <span className="onboarding-step-num">
                  {index + 1}
                </span>

                <span>{instruction}</span>
              </li>
            ))}
          </ol>


          {step.action && (
            <div className="onboarding-action-box">
              <div className="onboarding-action-text">
                <h3>Try it now</h3>

                <p>
                  {`Jump straight to ${step.action.label.replace(
                    /^Go to |^Open /,
                    ""
                  )} and come back to the guide whenever you like.`}
                </p>
              </div>

              <button
                type="button"
                className="onboarding-action-button"
                onClick={runAction}
              >
                {step.action.label}
                <ArrowRight size={16} />
              </button>
            </div>
          )}

        </div>


        <div className="onboarding-footer">

          <button
            type="button"
            className="onboarding-skip"
            onClick={skip}
          >
            Skip guide
          </button>

          <div className="onboarding-footer-right">

            <button
              type="button"
              className="onboarding-back"
              onClick={goBack}
              disabled={isFirst}
            >
              <ArrowLeft size={16} />
              Back
            </button>

            <button
              type="button"
              className="onboarding-next"
              onClick={goNext}
            >
              {isLast ? "Get Started" : "Next"}
              {!isLast && <ArrowRight size={16} />}
            </button>

          </div>

        </div>

      </div>
    </div>
  );
}


export default OnboardingTour;
