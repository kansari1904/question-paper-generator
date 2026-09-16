import {
  AlertTriangle,
  CheckCircle2,
  Info,
} from "lucide-react";

function ConstraintReport({ report }) {
  if (!report) {
    return null;
  }

  const deviations = Array.isArray(report.deviations)
    ? report.deviations
    : [];

  const warnings = Array.isArray(report.warnings)
    ? report.warnings
    : [];

  const isExact =
    deviations.length === 0 && warnings.length === 0;

  return (
    <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
      {/* Header */}
      <div className="flex items-start gap-3">
        <div
          className={`flex h - 9 w - 9 shrink - 0 items - center justify - center rounded - lg ${
    isExact
        ? "bg-emerald-50 text-emerald-600"
        : "bg-amber-50 text-amber-600"
} `}
        >
          {isExact ? (
            <CheckCircle2 className="h-5 w-5" />
          ) : (
            <AlertTriangle className="h-5 w-5" />
          )}
        </div>

        <div className="min-w-0">
          <h2 className="text-sm font-semibold text-slate-900">
            Constraint Report
          </h2>

          <p className="mt-1 text-xs leading-5 text-slate-500">
            {isExact
              ? "The generated paper matches the requested constraints."
              : "The paper was generated with some constraint deviations due to the available question bank."}
          </p>
        </div>
      </div>

      {/* Marks Summary */}
      <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-xs font-medium text-slate-500">
            Requested Marks
          </p>

          <p className="mt-1 text-lg font-bold text-slate-900">
            {report.requested_total_marks}
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-xs font-medium text-slate-500">
            Actual Marks
          </p>

          <p className="mt-1 text-lg font-bold text-slate-900">
            {report.actual_total_marks}
          </p>
        </div>
      </div>

      {/* Deviations */}
      {deviations.length > 0 && (
        <div className="mt-6">
          <div className="mb-3 flex items-center gap-2">
            <Info className="h-4 w-4 text-slate-500" />

            <h3 className="text-sm font-semibold text-slate-800">
              Deviations
            </h3>
          </div>

          <div className="space-y-3">
            {deviations.map((deviation, index) => {
              const difference =
                deviation.actual_pct -
                deviation.requested_pct;

              return (
                <div
                  key={`${ deviation.dimension } -${ index } `}
                  className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3"
                >
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    {/* Dimension + Reason */}
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-slate-800">
                        {deviation.dimension}
                      </p>

                      <p className="mt-1 text-xs leading-5 text-slate-500">
                        {deviation.reason}
                      </p>
                    </div>

                    {/* Percentages */}
                    <div className="flex shrink-0 flex-wrap gap-2">
                      <span className="rounded-md bg-white px-2.5 py-1.5 text-xs font-medium text-slate-600">
                        Requested: {deviation.requested_pct}%
                      </span>

                      <span className="rounded-md bg-white px-2.5 py-1.5 text-xs font-medium text-slate-600">
                        Actual: {deviation.actual_pct}%
                      </span>

                      <span
                        className={`rounded - md px - 2.5 py - 1.5 text - xs font - semibold ${
    difference === 0
        ? "bg-emerald-50 text-emerald-700"
        : "bg-amber-50 text-amber-700"
} `}
                      >
                        Difference:{" "}
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
        <div className="mt-6 rounded-xl border border-amber-200 bg-amber-50 p-4">
          <div className="flex items-start gap-2">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />

            <div>
              <h3 className="text-sm font-semibold text-amber-800">
                Notes
              </h3>

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
          </div>
        </div>
      )}

      {/* Exact Result */}
      {isExact && (
        <div className="mt-5 rounded-xl border border-emerald-200 bg-emerald-50 p-4">
          <div className="flex items-start gap-2">
            <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />

            <p className="text-xs leading-5 text-emerald-700">
              All requested constraints were satisfied successfully.
            </p>
          </div>
        </div>
      )}
    </section>
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

export default ConstraintReport;