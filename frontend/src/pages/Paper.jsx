import { useState } from "react";
import { ArrowLeft} from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import toast from "react-hot-toast";

import Navbar from "../components/Navbar";
import PaperHeader from "../components/PaperHeader";
import PaperSection from "../components/PaperSection";
import ConstraintReport from "../components/ConstraintReport";
import { swapQuestion } from "../services/api";
import PdfButton from "../components/PdfButton";

function Paper() {
  const location = useLocation();

  const [paper, setPaper] = useState(
    location.state?.paper || null
  );

  const [swappingQuestionId, setSwappingQuestionId] =
    useState(null);

  const handleSwap = async (questionId) => {
    try {
      setSwappingQuestionId(questionId);

      const result = await swapQuestion(
        paper.paper_id,
        questionId
      );

      // No replacement available
      if (!result.success) {
        toast.error(
          result.message || "No valid replacement is available."
        );
        return;
      }

      // Successful replacement
      setPaper((currentPaper) => ({
        ...currentPaper,

        questions: currentPaper.questions.map((question) =>
          question.id === questionId
            ? result.new_question
            : question
        ),

        sections: currentPaper.sections.map((section) => ({
          ...section,

          question_ids: section.question_ids.map((id) =>
            id === questionId
              ? result.new_question.id
              : id
          ),
        })),
      }));

      toast.success("Question swapped successfully.");
    } catch (error) {
      console.error("Swap error:", error);

      toast.error(
        error.message || "Failed to swap question."
      );
    } finally {
      setSwappingQuestionId(null);
    }
  };

  // --------------------------------------------------
  // Paper not found
  // --------------------------------------------------

  if (!paper) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Navbar />

        <main className="flex min-h-screen items-center justify-center px-4 pt-16">
          <div className="text-center">
            <h1 className="text-xl font-semibold text-slate-900">
              Paper not found
            </h1>

            <p className="mt-2 text-sm text-slate-500">
              Please generate a paper first.
            </p>

            <Link
              to="/"
              className="mt-6 inline-flex items-center gap-2 rounded-lg bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Generator
            </Link>
          </div>
        </main>
      </div>
    );
  }

  let questionNumber = 1;

  return (
    <div className="min-h-screen bg-slate-100">
      <Navbar />

      <main className="px-2 pb-16 pt-24 sm:px-5 lg:px-8">
        <div className="mx-auto max-w-5xl">

          {/* Top Actions */}
          <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <Link
              to="/"
              className="inline-flex items-center gap-2 text-sm font-medium text-slate-600 transition hover:text-emerald-600"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Generator
            </Link>

                      <PdfButton />
          </div>

          {/* ------------------------------------------ */}
          {/* Actual Question Paper */}
          {/* ------------------------------------------ */}

          <div
            id="paper"
            className="bg-white px-5 py-7 shadow-xl shadow-slate-300/40 sm:px-10 sm:py-10 lg:px-14 lg:py-12"
          >
            <PaperHeader paper={paper} />

            {paper.sections.map((section, index) => {
              const startNumber = questionNumber;

              questionNumber += section.question_ids.length;

              return (
                <PaperSection
                  key={section.qtype}
                  section={section}
                  questions={paper.questions}
                  questionStartNumber={startNumber}
                  sectionLetter={String.fromCharCode(65 + index)}
                  onSwap={handleSwap}
                  swappingQuestionId={swappingQuestionId}
                />
              );
            })}

            {/* End of Paper */}
            <div className="mt-10 border-t-2 border-slate-900 pt-4 text-center">
              <p className="text-[10px] font-medium uppercase tracking-[0.2em] text-slate-400">
                End of Question Paper
              </p>
            </div>
          </div>

          {/* ------------------------------------------ */}
          {/* Constraint Report */}
          {/* ------------------------------------------ */}

          <ConstraintReport
            report={paper.constraint_report}
          />
        </div>
      </main>
    </div>
  );
}

export default Paper;