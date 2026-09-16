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
    <div className="rounded-2xl border border-slate-200 bg-white p-5 sm:p-6">
      <div className="mb-5">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h3 className="text-base font-semibold text-slate-900">
              {title}
            </h3>

            <p className="mt-1 text-xs leading-5 text-slate-500">
              {description}
            </p>
          </div>

          <div
            className={`rounded-lg px-3 py-1.5 text-xs font-semibold ${
              isValid
                ? "bg-emerald-50 text-emerald-700"
                : "bg-amber-50 text-amber-700"
            }`}
          >
            Total: {total}%
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((item) => (
          <PercentageInput
            key={item.key}
            label={item.label}
            value={values[item.key]}
            onChange={(value) => onChange(item.key, value)}
          />
        ))}
      </div>

      {!isValid && (
        <p className="mt-4 text-xs font-medium text-amber-600">
          Percentages must add up to exactly 100%.
        </p>
      )}
    </div>
  );
}

export default ConstraintSection;