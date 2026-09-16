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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 px-4 py-6 backdrop-blur-sm">
      <div
        className="w-full max-w-lg overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl"
        role="dialog"
        aria-modal="true"
        aria-labelledby="constraint-modal-title"
      >
        {/* Header */}
        <div className="flex items-start justify-between border-b border-slate-200 px-5 py-5 sm:px-6">
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-amber-50 text-amber-600">
              <AlertTriangle className="h-5 w-5" />
            </div>

            <div>
              <h2
                id="constraint-modal-title"
                className="text-base font-semibold text-slate-900"
              >
                Constraint Notice
              </h2>

              <p className="mt-1 text-xs leading-5 text-slate-500">
                The paper was generated, but some requested
                percentages could not be matched exactly.
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Content */}
        <div className="max-h-[65vh] overflow-y-auto px-5 py-5 sm:px-6">
          {/* Marks */}
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
              <p className="text-[11px] font-medium text-slate-500">
                Requested Marks
              </p>

              <p className="mt-1 text-lg font-bold text-slate-900">
                {report.requested_total_marks}
              </p>
            </div>

            <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
              <p className="text-[11px] font-medium text-slate-500">
                Actual Marks
              </p>

              <p className="mt-1 text-lg font-bold text-slate-900">
                {report.actual_total_marks}
              </p>
            </div>
          </div>

          {/* Deviations */}
          {deviations.length > 0 && (
            <div className="mt-5">
              <h3 className="text-sm font-semibold text-slate-800">
                Constraint deviations
              </h3>

              <div className="mt-3 space-y-2">
                {deviations.map((deviation, index) => {
                  const difference =
                    deviation.actual_pct -
                    deviation.requested_pct;

                  return (
                    <div
                      key={`${ deviation.dimension } -${ index } `}
                      className="rounded-xl border border-slate-200 bg-slate-50 p-3"
                    >
                      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                        <div>
                          <p className="text-xs font-semibold text-slate-800">
                            {deviation.dimension}
                          </p>

                          <p className="mt-1 text-[11px] leading-5 text-slate-500">
                            {deviation.reason}
                          </p>
                        </div>

                        <div className="flex shrink-0 gap-2">
                          <span className="rounded-md bg-white px-2 py-1 text-[11px] font-medium text-slate-600">
                            {deviation.requested_pct}%
                            {" → "}
                            {deviation.actual_pct}%
                          </span>

                          <span className="rounded-md bg-amber-100 px-2 py-1 text-[11px] font-semibold text-amber-700">
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
            <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-4">
              <p className="text-xs font-semibold text-amber-800">
                Why this happened
              </p>

              <ul className="mt-2 space-y-2">
                {warnings.map((warning, index) => (
                  <li
                    key={index}
                    className="text-xs leading-5 text-amber-700"
                  >
                    • {formatWarning(warning)}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <p className="mt-5 text-xs leading-5 text-slate-500">
            The generated paper still satisfies the total marks
            requirement. The differences above result from the
            discrete marks assigned to each question type.
          </p>
        </div>

        {/* Footer */}
        <div className="flex flex-col-reverse gap-2 border-t border-slate-200 bg-slate-50 px-5 py-4 sm:flex-row sm:justify-end sm:px-6">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-100"
          >
            Close
          </button>

          <button
            type="button"
            onClick={onContinue}
            className="rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800"
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