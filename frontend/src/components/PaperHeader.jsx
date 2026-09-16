import { useMemo } from "react";

function PaperHeader({ paper }) {
  const totalQuestions = useMemo(
    () => paper.questions?.length || 0,
    [paper.questions]
  );

  return (
    <header className="border-b-2 border-slate-900 pb-6">

      {/* Title */}
      <div className="text-center">
        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">
          SmartPaper
        </p>

        <h1 className="mt-2 text-2xl font-bold uppercase tracking-wide text-slate-950 sm:text-3xl">
          Question Paper
        </h1>
      </div>

      {/* Subject + Marks */}
      <div className="mt-7 flex flex-col gap-2 border-y border-slate-300 py-3 text-sm font-semibold sm:flex-row sm:items-center sm:justify-between">
        <div>
          Subject:{" "}
          <span className="font-normal text-slate-700">
            General Science
          </span>
        </div>

        <div className="flex gap-5">
          <span>
            Total Marks:{" "}
            <span className="font-bold">
              {paper.total_marks}
            </span>
          </span>

          <span className="hidden text-slate-300 sm:inline">
            |
          </span>

          <span>
            Questions:{" "}
            <span className="font-bold">
              {totalQuestions}
            </span>
          </span>
        </div>
      </div>

      {/* Student Details */}
      <div className="mt-6 grid grid-cols-1 gap-5 text-sm sm:grid-cols-2">
        <div>
          <span className="font-semibold">Name:</span>
          <span className="ml-2 inline-block w-[70%] border-b border-slate-400 sm:w-[75%]" />
        </div>

        <div>
          <span className="font-semibold">Roll No:</span>
          <span className="ml-2 inline-block w-[65%] border-b border-slate-400 sm:w-[70%]" />
        </div>

        <div>
          <span className="font-semibold">Date:</span>
          <span className="ml-2 inline-block w-[65%] border-b border-slate-400 sm:w-[70%]" />
        </div>

        <div>
          <span className="font-semibold">Class:</span>
          <span className="ml-2 inline-block w-[65%] border-b border-slate-400 sm:w-[70%]" />
        </div>
      </div>

      {/* General Instructions */}
      <div className="mt-7 border-t border-slate-300 pt-5">
        <h2 className="text-sm font-bold uppercase tracking-wide text-slate-900">
          General Instructions
        </h2>

        <ol className="mt-3 list-decimal space-y-1.5 pl-5 text-xs leading-5 text-slate-700 sm:text-sm">
          <li>
            Read all questions carefully before answering.
          </li>

          <li>
            Answer all questions as per the instructions given in each section.
          </li>

          <li>
            Marks allotted to each question are indicated against the question.
          </li>
        </ol>
      </div>

    </header>
  );
}

export default PaperHeader;