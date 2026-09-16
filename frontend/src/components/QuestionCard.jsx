import { RefreshCw } from "lucide-react";

function QuestionCard({
    question,
    questionNumber,
    onSwap,
    swapping,
}) {
    const isMCQ = question.qtype.toLowerCase() === "mcq";

    return (
        <div className="question-card border-b border-slate-200 py-5 last:border-b-0">
            {/* Question */}
            <div className="flex items-start gap-2">
                <span className="shrink-0 text-sm font-bold text-slate-900">
                    {questionNumber}.
                </span>

                <div className="min-w-0 flex-1">
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                        <p className="text-sm leading-7 text-slate-800 sm:text-[15px]">
                            {question.text}
                        </p>

                        <span className="shrink-0 self-start whitespace-nowrap text-xs font-semibold text-slate-600">
                            [{question.marks}{" "}
                            {question.marks === 1 ? "Mark" : "Marks"}]
                        </span>
                    </div>

                    {/* MCQ options */}
                    {isMCQ && question.options?.length > 0 && (
                        <div className="mt-3 grid grid-cols-1 gap-x-8 gap-y-2 pl-1 sm:grid-cols-2">
                            {question.options.map((option, index) => (
                                <div
                                    key={index}
                                    className="text-sm leading-6 text-slate-700"
                                >
                                    <span className="mr-2 font-medium text-slate-500">
                                        {String.fromCharCode(65 + index)}.
                                    </span>

                                    {option}
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Metadata + Swap */}
                    <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                        <div className="text-[11px] text-slate-400">
                            {question.topic}
                            {question.subtopic && ` • ${question.subtopic}`}
                            {" • "}
                            {question.difficulty}
                        </div>

                        <button
                            type="button"
                            onClick={() => onSwap(question.id)}
                            disabled={swapping}
                            className="inline-flex w-fit items-center gap-1.5 rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-[11px] font-semibold text-slate-500 transition hover:border-emerald-300 hover:bg-emerald-50 hover:text-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                            <RefreshCw
                                className={`h-3 w-3 ${swapping ? "animate-spin" : ""
                                    }`}
                            />

                            {swapping ? "Swapping..." : "Swap"}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default QuestionCard;