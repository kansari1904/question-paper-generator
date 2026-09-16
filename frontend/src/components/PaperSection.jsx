import QuestionCard from "./QuestionCard";

function PaperSection({
    section,
    questions,
    questionStartNumber,
    onSwap,
    swappingQuestionId,
    sectionLetter,
}) {
    const sectionTitle =
        {
            MCQ: "MCQ",
            SHORT: "SHORT ANSWER",
            LONG: "LONG ANSWER",
        }[section.qtype] || section.qtype;

    return (
        <section className="mt-8">
            {/* Section heading */}
            <div className="border-y-2 border-slate-900 py-3">
                <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                    <h2 className="text-sm font-bold uppercase tracking-wide text-slate-950 sm:text-base">
                        SECTION {sectionLetter} — {sectionTitle}
                    </h2>

                    <span className="text-sm font-bold text-slate-950">
                        {section.marks_subtotal} Marks
                    </span>
                </div>

                <p className="mt-2 text-xs leading-5 text-slate-600 sm:text-sm">
                    {section.instructions}
                </p>
            </div>

            {/* Questions */}
            <div>
                {section.question_ids.map((questionId, index) => {
                    const question = questions.find(
                        (item) => item.id === questionId
                    );

                    if (!question) {
                        return null;
                    }

                    return (
                        <QuestionCard
                            key={question.id}
                            question={question}
                            questionNumber={questionStartNumber + index}
                            onSwap={onSwap}
                            swapping={swappingQuestionId === question.id}
                        />
                    );
                })}
            </div>
        </section>
    );
}

export default PaperSection;