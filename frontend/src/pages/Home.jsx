import { useMemo, useState } from "react";

import {
    CheckCircle2,
    FileCheck2,
    FileText,
    RefreshCw,
    ShieldCheck,
    Sparkles,
    Target,
    WandSparkles,
} from "lucide-react";

import toast from "react-hot-toast";
import { useNavigate } from "react-router-dom";

import Navbar from "../components/Navbar";
import ConstraintSection from "../components/ConstraintSection";
import ConstraintModal from "../components/ConstraintModal";
import { generatePaper } from "../services/api";

function Home() {
    const [totalMarks, setTotalMarks] = useState(40);

    const navigate = useNavigate();

    const [isGenerating, setIsGenerating] = useState(false);

    const [showConstraintModal, setShowConstraintModal] =
        useState(false);

    const [generatedPaper, setGeneratedPaper] = useState(null);

    const [difficulty, setDifficulty] = useState({
        easy: 30,
        medium: 50,
        hard: 20,
    });

    const [topics, setTopics] = useState({
        physics: 40,
        chemistry: 30,
        biology: 30,
    });

    const [questionTypes, setQuestionTypes] = useState({
        mcq: 40,
        short: 40,
        long: 20,
    });

    const updateValues = (setter) => (key, value) => {
        setter((previous) => ({
            ...previous,
            [key]: value,
        }));
    };

    const difficultyValid = useMemo(
        () =>
            Object.values(difficulty).reduce(
                (a, b) => a + b,
                0
            ) === 100,
        [difficulty]
    );

    const topicsValid = useMemo(
        () =>
            Object.values(topics).reduce(
                (a, b) => a + b,
                0
            ) === 100,
        [topics]
    );

    const questionTypesValid = useMemo(
        () =>
            Object.values(questionTypes).reduce(
                (a, b) => a + b,
                0
            ) === 100,
        [questionTypes]
    );

    const formValid =
        totalMarks > 0 &&
        difficultyValid &&
        topicsValid &&
        questionTypesValid;

    const handleGenerate = async (e) => {
        e.preventDefault();

        if (!formValid) {
            toast.error(
                "Please fix the percentage distributions."
            );
            return;
        }

        const payload = {
            total_marks: totalMarks,

            difficulty_mix: {
                easy: difficulty.easy,
                medium: difficulty.medium,
                hard: difficulty.hard,
            },

            topic_weightage: {
                physics: topics.physics,
                chemistry: topics.chemistry,
                biology: topics.biology,
            },

            qtype_mix: {
                mcq: questionTypes.mcq,
                short: questionTypes.short,
                long: questionTypes.long,
            },
        };

        try {
            setIsGenerating(true);

            console.log("Sending payload:", payload);

            const result = await generatePaper(payload);

            console.log("Generated paper:", result);

            setGeneratedPaper(result);

            const hasDeviations =
                result.constraint_report?.deviations?.length > 0;

            const hasWarnings =
                result.constraint_report?.warnings?.length > 0;

            if (hasDeviations || hasWarnings) {
                setShowConstraintModal(true);

                toast.success(
                    "Paper generated with constraint notes."
                );

                return;
            }

            toast.success(
                "Question paper generated successfully!"
            );

            navigate("/paper", {
                state: {
                    paper: result,
                },
            });
        } catch (error) {
            console.error(
                "Generate paper error:",
                error
            );

            toast.error(
                error.message ||
                    "Failed to generate question paper."
            );
        } finally {
            setIsGenerating(false);
        }
    };

    const handleCloseConstraintModal = () => {
        setShowConstraintModal(false);
    };

    const handleContinueToPaper = () => {
        setShowConstraintModal(false);

        if (!generatedPaper) {
            return;
        }

        navigate("/paper", {
            state: {
                paper: generatedPaper,
            },
        });
    };

    return (
        <div className="relative min-h-screen overflow-hidden bg-gradient-to-br from-slate-50 via-white to-slate-50">
            {/* Background Grid */}
            <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(#e5e7eb_1px,transparent_1px)] [background-size:16px_16px]" />

            <Navbar />

            <main className="relative pt-16">
                {/* ==================================================
                    HERO
                ================================================== */}

                <section className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-7xl items-center px-4 py-20 sm:px-6 lg:px-8">
                    <div className="mx-auto max-w-3xl text-center">
                        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-4 py-2 text-xs font-semibold text-emerald-700">
                            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />

                            Constraint-aware question generation
                        </div>

                        <h1 className="text-4xl font-semibold tracking-tight text-slate-900 sm:text-5xl lg:text-6xl">
                            Build a balanced

                            <span className="block bg-gradient-to-r from-emerald-500 to-teal-500 bg-clip-text text-transparent">
                                question paper
                            </span>
                        </h1>

                        <p className="mx-auto mt-6 max-w-2xl text-sm leading-7 text-slate-500 sm:text-base">
                            Define your marks, difficulty, topics,
                            and question types. SmartPaper generates
                            a structured paper while respecting your
                            constraints as closely as mathematically
                            possible.
                        </p>

                        <div className="mt-9 flex flex-col justify-center gap-3 sm:flex-row">
                            <a
                                href="#generator"
                                className="inline-flex h-12 items-center justify-center rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 px-6 text-sm font-semibold text-white shadow-lg shadow-emerald-500/20 transition-all hover:from-emerald-600 hover:to-teal-600 active:scale-[0.98]"
                            >
                                Create Question Paper
                            </a>

                            <a
                                href="#how-it-works"
                                className="inline-flex h-12 items-center justify-center rounded-xl border border-slate-200 bg-white px-6 text-sm font-semibold text-slate-700 shadow-sm transition-all hover:border-slate-300 hover:bg-slate-50"
                            >
                                How it works
                            </a>
                        </div>
                    </div>
                </section>

                {/* ==================================================
                    GENERATOR
                ================================================== */}

                <section
                    id="generator"
                    className="mx-auto max-w-7xl px-4 py-16 sm:px-6 sm:py-24 lg:px-8"
                >
                    <div className="mb-8 text-center">
                        <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1.5 text-xs font-semibold text-slate-600">
                            <Sparkles className="h-3.5 w-3.5" />

                            Paper Configuration
                        </div>

                        <h2 className="text-2xl font-semibold text-slate-900 sm:text-3xl">
                            Configure your question paper
                        </h2>

                        <p className="mx-auto mt-3 max-w-2xl text-sm leading-6 text-slate-500">
                            Set the marks distribution and
                            constraints before generating your
                            paper.
                        </p>
                    </div>

                    <form onSubmit={handleGenerate}>
                        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-xl shadow-slate-200/40 sm:p-8">
                            {/* Total Marks */}

                            <div className="mb-8 rounded-2xl border border-slate-200 bg-slate-50 p-5 sm:p-6">
                                <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
                                    <div>
                                        <h3 className="text-base font-semibold text-slate-900">
                                            Total Marks
                                        </h3>

                                        <p className="mt-1 text-xs leading-5 text-slate-500">
                                            Define the total marks
                                            for the question paper.
                                        </p>
                                    </div>

                                    <div className="w-full sm:w-40">
                                        <div className="relative">
                                            <input
                                                type="number"
                                                min="1"
                                                value={totalMarks}
                                                onChange={(e) =>
                                                    setTotalMarks(
                                                        Number(
                                                            e.target
                                                                .value
                                                        )
                                                    )
                                                }
                                                className="h-12 w-full rounded-xl border border-slate-200 bg-white px-4 pr-16 text-lg font-semibold text-slate-900 outline-none transition-all focus:border-emerald-400 focus:ring-4 focus:ring-emerald-500/10"
                                            />

                                            <span className="absolute right-4 top-1/2 -translate-y-1/2 text-sm font-medium text-slate-400">
                                                marks
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Constraint Sections */}

                            <div className="space-y-5">
                                <ConstraintSection
                                    title="Difficulty Mix"
                                    description="Choose how the total marks should be distributed across difficulty levels."
                                    items={[
                                        {
                                            key: "easy",
                                            label: "Easy",
                                        },
                                        {
                                            key: "medium",
                                            label: "Medium",
                                        },
                                        {
                                            key: "hard",
                                            label: "Hard",
                                        },
                                    ]}
                                    values={difficulty}
                                    onChange={updateValues(
                                        setDifficulty
                                    )}
                                />

                                <ConstraintSection
                                    title="Topic Weightage"
                                    description="Define the percentage of marks allocated to each topic."
                                    items={[
                                        {
                                            key: "physics",
                                            label: "Physics",
                                        },
                                        {
                                            key: "chemistry",
                                            label: "Chemistry",
                                        },
                                        {
                                            key: "biology",
                                            label: "Biology",
                                        },
                                    ]}
                                    values={topics}
                                    onChange={updateValues(
                                        setTopics
                                    )}
                                />

                                <ConstraintSection
                                    title="Question Type Mix"
                                    description="Choose the distribution of MCQ, short-answer, and long-answer questions."
                                    items={[
                                        {
                                            key: "mcq",
                                            label: "MCQ — 1 mark",
                                        },
                                        {
                                            key: "short",
                                            label: "Short Answer — 3 marks",
                                        },
                                        {
                                            key: "long",
                                            label: "Long Answer — 5 marks",
                                        },
                                    ]}
                                    values={questionTypes}
                                    onChange={updateValues(
                                        setQuestionTypes
                                    )}
                                />
                            </div>

                            {/* Generate */}

                            <div className="mt-8 flex flex-col gap-4 border-t border-slate-200 pt-6 sm:flex-row sm:items-center sm:justify-between">
                                <div>
                                    <p className="text-sm font-medium text-slate-700">
                                        Ready to generate?
                                    </p>

                                    <p className="mt-1 text-xs text-slate-500">
                                        All percentage distributions
                                        must equal 100%.
                                    </p>
                                </div>

                                <button
                                    type="submit"
                                    disabled={
                                        !formValid ||
                                        isGenerating
                                    }
                                    className="inline-flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 px-6 text-sm font-semibold text-white shadow-lg shadow-emerald-500/20 transition-all hover:from-emerald-600 hover:to-teal-600 disabled:cursor-not-allowed disabled:opacity-50 disabled:shadow-none sm:w-auto"
                                >
                                    {isGenerating ? (
                                        <>
                                            <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />

                                            Generating...
                                        </>
                                    ) : (
                                        <>
                                            <FileText className="h-4 w-4" />

                                            Generate Paper
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                    </form>
                </section>

                {/* ==================================================
                    HOW IT WORKS
                ================================================== */}

                <section
                    id="how-it-works"
                    className="border-y border-slate-200 bg-white"
                >
                    <div className="mx-auto max-w-7xl px-4 py-20 sm:px-6 sm:py-24 lg:px-8">
                        <div className="mx-auto max-w-2xl text-center">
                            <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700">
                                <WandSparkles className="h-3.5 w-3.5" />

                                Simple workflow
                            </div>

                            <h2 className="text-2xl font-semibold text-slate-900 sm:text-3xl">
                                How SmartPaper works
                            </h2>

                            <p className="mt-3 text-sm leading-6 text-slate-500">
                                From constraints to a classroom-ready
                                question paper in a few simple steps.
                            </p>
                        </div>

                        <div className="mt-12 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
                            {[
                                {
                                    number: "01",
                                    icon: Target,
                                    title: "Define constraints",
                                    description:
                                        "Set total marks, difficulty mix, topic weightage, and question-type distribution.",
                                },
                                {
                                    number: "02",
                                    icon: ShieldCheck,
                                    title: "Validate",
                                    description:
                                        "The system checks whether your requested distributions can be satisfied by the available question bank.",
                                },
                                {
                                    number: "03",
                                    icon: Sparkles,
                                    title: "Optimize",
                                    description:
                                        "A constraint-aware solver selects questions while minimizing unavoidable deviations.",
                                },
                                {
                                    number: "04",
                                    icon: FileCheck2,
                                    title: "Review & export",
                                    description:
                                        "Review the generated paper, swap individual questions, inspect constraint notes, and export to PDF.",
                                },
                            ].map((step) => {
                                const Icon = step.icon;

                                return (
                                    <div
                                        key={step.number}
                                        className="group rounded-2xl border border-slate-200 bg-slate-50 p-6 transition-all hover:-translate-y-1 hover:border-emerald-200 hover:bg-white hover:shadow-lg hover:shadow-slate-200/50"
                                    >
                                        <div className="flex items-center justify-between">
                                            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-white text-emerald-600 shadow-sm ring-1 ring-slate-200 transition-colors group-hover:bg-emerald-50 group-hover:ring-emerald-200">
                                                <Icon className="h-5 w-5" />
                                            </div>

                                            <span className="text-xs font-bold tracking-widest text-slate-300">
                                                {step.number}
                                            </span>
                                        </div>

                                        <h3 className="mt-6 text-base font-semibold text-slate-900">
                                            {step.title}
                                        </h3>

                                        <p className="mt-2 text-sm leading-6 text-slate-500">
                                            {step.description}
                                        </p>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </section>

                {/* ==================================================
                    FEATURES
                ================================================== */}

                <section
                    id="features"
                    className="mx-auto max-w-7xl px-4 py-20 sm:px-6 sm:py-24 lg:px-8"
                >
                    <div className="grid gap-12 lg:grid-cols-[0.9fr_1.1fr] lg:items-center">
                        <div>
                            <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1.5 text-xs font-semibold text-slate-600">
                                <CheckCircle2 className="h-3.5 w-3.5" />

                                Built for teachers
                            </div>

                            <h2 className="text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
                                More than just random question selection
                            </h2>

                            <p className="mt-4 text-sm leading-7 text-slate-500">
                                SmartPaper treats question-paper
                                generation as a constraint problem.
                                The goal is not simply to pick
                                questions, but to create a balanced
                                and usable paper.
                            </p>

                            <a
                                href="#generator"
                                className="mt-7 inline-flex items-center gap-2 rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
                            >
                                Start generating

                                <FileText className="h-4 w-4" />
                            </a>
                        </div>

                        <div className="grid gap-4 sm:grid-cols-2">
                            {[
                                {
                                    icon: Target,
                                    title: "Constraint-aware",
                                    text: "Handles marks, difficulty, topic, and question-type requirements together.",
                                },
                                {
                                    icon: ShieldCheck,
                                    title: "Infeasibility handling",
                                    text: "Clearly reports when exact constraints cannot be satisfied.",
                                },
                                {
                                    icon: RefreshCw,
                                    title: "Question swapping",
                                    text: "Replace an individual question without rebuilding the entire paper.",
                                },
                                {
                                    icon: FileText,
                                    title: "Real paper structure",
                                    text: "Organizes questions into sections with instructions and marks subtotals.",
                                },
                            ].map((feature) => {
                                const Icon = feature.icon;

                                return (
                                    <div
                                        key={feature.title}
                                        className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-emerald-200 hover:shadow-md"
                                    >
                                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600">
                                            <Icon className="h-5 w-5" />
                                        </div>

                                        <h3 className="mt-4 text-sm font-semibold text-slate-900">
                                            {feature.title}
                                        </h3>

                                        <p className="mt-2 text-xs leading-5 text-slate-500">
                                            {feature.text}
                                        </p>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </section>

                {/* ==================================================
                    ABOUT
                ================================================== */}

                <section
                    id="about"
                    className="border-t border-slate-200 bg-slate-950"
                >
                    <div className="mx-auto max-w-7xl px-4 py-20 sm:px-6 sm:py-24 lg:px-8">
                        <div className="mx-auto max-w-3xl text-center">
                            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs font-semibold text-slate-300">
                                <Sparkles className="h-3.5 w-3.5 text-emerald-400" />

                                About SmartPaper
                            </div>

                            <h2 className="text-2xl font-semibold text-white sm:text-3xl">
                                Structured question-paper generation
                            </h2>

                            <p className="mt-5 text-sm leading-7 text-slate-400 sm:text-base">
                                SmartPaper is a constraint-aware
                                question-paper generator designed
                                to help teachers create balanced
                                papers from an available question
                                bank.
                            </p>

                            <p className="mt-4 text-sm leading-7 text-slate-400 sm:text-base">
                                Instead of treating every requirement
                                independently, the system considers
                                total marks, difficulty, topics, and
                                question types together and selects
                                a feasible combination.
                            </p>

                            <div className="mt-9 flex flex-col justify-center gap-3 sm:flex-row">
                                <a
                                    href="#generator"
                                    className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-emerald-500/10 transition hover:from-emerald-600 hover:to-teal-600"
                                >
                                    Create a paper

                                    <FileText className="h-4 w-4" />
                                </a>

                                <a
                                    href="#how-it-works"
                                    className="inline-flex items-center justify-center rounded-xl border border-slate-700 px-6 py-3 text-sm font-semibold text-slate-300 transition hover:bg-slate-900"
                                >
                                    See how it works
                                </a>
                            </div>
                        </div>
                    </div>
                </section>

                {/* ==================================================
                    FOOTER
                ================================================== */}

                <footer className="border-t border-slate-800 bg-slate-950">
                    <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-6 text-center sm:flex-row sm:items-center sm:justify-between sm:px-6 sm:text-left lg:px-8">
                        <div>
                            <p className="text-sm font-semibold text-white">
                                SmartPaper
                            </p>

                            <p className="mt-1 text-xs text-slate-500">
                                Constraint-aware question paper
                                generation.
                            </p>
                        </div>

                        <div className="text-xs text-slate-500">
                            Built for the Evalvia Intern Assignment
                        </div>
                    </div>
                </footer>
            </main>

            {/* Constraint Warning Modal */}

            <ConstraintModal
                isOpen={showConstraintModal}
                report={generatedPaper?.constraint_report}
                onClose={handleCloseConstraintModal}
                onContinue={handleContinueToPaper}
            />
        </div>
    );
}

export default Home;