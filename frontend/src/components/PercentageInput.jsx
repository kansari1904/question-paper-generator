
function PercentageInput({
  label,
  value,
  onChange,
  disabled = false,
}) {
  return (
    <div className="min-w-0">
      <label className="mb-1.5 block truncate text-[11px] font-medium text-slate-600">
        {label}
      </label>

      <div className="relative">
        <input
          type="number"
          min="0"
          max="100"
          value={value}
          disabled={disabled}
          onChange={(e) => onChange(Number(e.target.value))}
          className="h-9 w-full rounded-lg border border-slate-200 bg-white px-2.5 pr-7 text-xs font-semibold text-slate-900 outline-none transition-all placeholder:text-slate-400 focus:border-emerald-400 focus:ring-2 focus:ring-emerald-500/10 disabled:cursor-not-allowed disabled:opacity-60"
        />

        <span className="absolute right-2 top-1/2 -translate-y-1/2 text-[11px] font-semibold text-slate-400">
          %
        </span>
      </div>
    </div>
  );
}

export default PercentageInput;
