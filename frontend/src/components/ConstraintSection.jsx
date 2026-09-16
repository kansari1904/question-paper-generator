
import PercentageInput from "./PercentageInput";

function ConstraintSection({
  title,
  description,
  items,
  values,
  onChange,
}) {
  const total = Object.values(values).reduce(
    (sum, value) => sum + value,
    0
  );

  const isValid = total === 100;

  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50/60 p-4">
      {/* Header */}
      <div className="mb-4 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="text-sm font-semibold text-slate-900">
            {title}
          </h3>

          <p className="mt-0.5 text-[11px] leading-4 text-slate-500">
            {description}
          </p>
        </div>

        {/* Total */}
        <div
          className={`shrink - 0 rounded - md px - 2 py - 1 text - [10px] font - bold ${
    isValid
        ? "bg-emerald-50 text-emerald-700"
        : "bg-amber-50 text-amber-700"
} `}
        >
          {total}%
        </div>
      </div>

      {/* Inputs */}
      <div className="grid grid-cols-3 gap-2">
        {items.map((item) => (
          <PercentageInput
            key={item.key}
            label={item.label}
            value={values[item.key]}
            onChange={(value) => onChange(item.key, value)}
          />
        ))}
      </div>

      {/* Validation */}
      {!isValid && (
        <p className="mt-3 text-[10px] font-medium text-amber-600">
          Must total 100%.
        </p>
      )}
    </div>
  );
}

export default ConstraintSection;
