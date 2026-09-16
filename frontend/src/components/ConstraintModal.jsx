import { AlertTriangle, X } from "lucide-react";

function ConstraintModal({
  isOpen,
  report,
  onClose,
  onContinue,
}) {
  if (!isOpen || !report) {
    return null;
  }

  const deviations = Array.isArray(report.deviations)
    ? report.deviations
    : [];

  const warnings = Array.isArray(report.warnings)
    ? report.warnings
    : [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 px-3 py-4 backdrop-blur-sm sm:px-4 sm:py-6">
      <div
        className="flex max-h-[92vh] w-full max-w-lg flex-col overflow-hidden rounded-xl border border-slate-200 bg-white shadow-2xl sm:max-h-[88vh] sm:rounded-2xl"
        role="dialog"
        aria-modal="true"
        aria-labelledby="constraint-modal-title"
      >
        {/* Header */}
        <div className="flex shrink-0 items-start justify-between gap-3 border-b border-slate-200 px-4 py-4 sm:px-6 sm:py-5">
          <div className="flex min-w-0 items-start gap-2.5 sm:gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-amber-50 text-amber-600 sm:h-10 sm:w-10 sm:rounded-xl">
              <AlertTriangle className="h-4 w-4 sm:h-5 sm:w-5" />
            </div>

            <div className="min-w-0">
              <h2
                id="constraint-modal-title"
                className="text-sm font-semibold text-slate-900 sm:text-base"
              >
                Constraint Notice
              </h2>

              <p className="mt-1 text-[11px] leading-4 text-slate-500 sm:text-xs sm:leading-5">
                The paper was generated, but some requested
                percentages could not be matched exactly.
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="shrink-0 rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700 sm:p-2"
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4 sm:px-6 sm:py-5">
          {/* Marks */}
          <div className="grid grid-cols-2 gap-2.5 sm:gap-3">
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-2.5 sm:rounded-xl sm:p-3">
              <p className="text-[10px] font-medium text-slate-500 sm:text-[11px]">
                Requested Marks
              </p>

              <p className="mt-1 text-base font-bold text-slate-900 sm:text-lg">
                {report.requested_total_marks}
              </p>
            </div>

            <div className="rounded-lg border border-slate-200 bg-slate-50 p-2.5 sm:rounded-xl sm:p-3">
              <p className="text-[10px] font-medium text-slate-500 sm:text-[11px]">
                Actual Marks
              </p>

              <p className="mt-1 text-base font-bold text-slate-900 sm:text-lg">
                {report.actual_total_marks}
              </p>
            </div>
          </div>

          {/* Deviations */}
          {deviations.length > 0 && (
            <div className="mt-4 sm:mt-5">
              <h3 className="text-xs font-semibold text-slate-800 sm:text-sm">
                Constraint deviations
              </h3>

              <div className="mt-2.5 space-y-2 sm:mt-3">
                {deviations.map((deviation, index) => {
                  const difference =
                    deviation.actual_pct -
                    deviation.requested_pct;

                  return (
                    <div
                      key={`${ deviation.dimension } -${ index } `}
                      className="rounded-lg border border-slate-200 bg-slate-50 p-3 sm:rounded-xl"
                    >
                      <div className="flex flex-col gap-2.5">
                        {/* Dimension + reason */}
                        <div className="min-w-0">
                          <p className="text-xs font-semibold text-slate-800">
                            {deviation.dimension}
                          </p>

                          <p className="mt-1 text-[10px] leading-4 text-slate-500 sm:text-[11px] sm:leading-5">
                            {deviation.reason}
                          </p>
                        </div>

                        {/* Percentage information */}
                        <div className="flex flex-wrap items-center gap-1.5">
                          <span className="rounded-md bg-white px-2 py-1 text-[10px] font-medium text-slate-600 sm:text-[11px]">
                            {deviation.requested_pct}%
                            {" → "}
                            {deviation.actual_pct}%
                          </span>

                          <span className="rounded-md bg-amber-100 px-2 py-1 text-[10px] font-semibold text-amber-700 sm:text-[11px]">
                            {difference > 0 ? "+" : ""}
                            {difference.toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Warnings */}
          {warnings.length > 0 && (
            <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-3 sm:mt-5 sm:rounded-xl sm:p-4">
              <p className="text-[11px] font-semibold text-amber-800 sm:text-xs">
                Why this happened
              </p>

              <ul className="mt-2 space-y-1.5 sm:space-y-2">
                {warnings.map((warning, index) => (
                  <li
                    key={index}
                    className="text-[10px] leading-4 text-amber-700 sm:text-xs sm:leading-5"
                  >
                    • {formatWarning(warning)}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <p className="mt-4 text-[10px] leading-4 text-slate-500 sm:mt-5 sm:text-xs sm:leading-5">
            The generated paper still satisfies the total marks
            requirement. The differences above result from the
            discrete marks assigned to each question type.
          </p>
        </div>

        {/* Footer */}
        <div className="flex shrink-0 flex-col gap-2 border-t border-slate-200 bg-slate-50 px-4 py-3 sm:flex-row sm:justify-end sm:px-6 sm:py-4">
          <button
            type="button"
            onClick={onClose}
            className="w-full rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 sm:w-auto"
          >
            Close
          </button>

          <button
            type="button"
            onClick={onContinue}
            className="w-full rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800 sm:w-auto"
          >
            View Paper
          </button>
        </div>
      </div>
    </div>
  );
}

function formatWarning(warning) {
  if (typeof warning !== "string") {
    return String(warning);
  }

  return warning
    .replace(/because(?=[A-Z])/g, "because ")
    .replace(/because(?=\d)/g, "because ")
    .replace(/\s+/g, " ")
    .trim();
}

export default ConstraintModal;
