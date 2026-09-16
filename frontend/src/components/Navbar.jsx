import {
    BrainCircuit,
    FileText,
    Code2,
} from "lucide-react";

function Navbar() {
    return (
        <nav className="fixed left-0 right-0 top-0 z-50 border-b border-slate-200/80 bg-white/90 backdrop-blur-xl">
            <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">

                {/* Brand */}

                <a
                    href="#"
                    className="flex items-center gap-3"
                >
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-400 to-teal-500 shadow-lg shadow-emerald-500/20">
                        <BrainCircuit
                            className="h-5 w-5 text-white"
                            strokeWidth={2}
                        />
                    </div>

                    <div>
                        <h1 className="text-sm font-semibold tracking-tight text-slate-900 sm:text-base">
                            SmartPaper
                        </h1>

                        <p className="hidden text-[11px] text-slate-500 sm:block">
                            Smart Question Generator
                        </p>
                    </div>
                </a>

                {/* Navigation */}

                <div className="hidden items-center gap-6 md:flex">
                    <a
                        href="#generator"
                        className="text-sm font-medium text-slate-600 transition-colors hover:text-emerald-600"
                    >
                        Generator
                    </a>

                    <a
                        href="#features"
                        className="text-sm font-medium text-slate-600 transition-colors hover:text-emerald-600"
                    >
                        Features
                    </a>

                    <a
                        href="#how-it-works"
                        className="text-sm font-medium text-slate-600 transition-colors hover:text-emerald-600"
                    >
                        How It Works
                    </a>

                    <a
                        href="#about"
                        className="text-sm font-medium text-slate-600 transition-colors hover:text-emerald-600"
                    >
                        About
                    </a>

                    {/* GitHub */}

                    <a
                        href="#"
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-2 text-sm font-medium text-slate-600 transition-colors hover:text-emerald-600"
                    >
                        <Code2 className="h-4 w-4" />

                        GitHub
                    </a>
                </div>

                {/* Action */}

                <a
                    href="#generator"
                    className="hidden items-center gap-2 rounded-xl bg-slate-900 px-4 py-2.5 text-xs font-semibold text-white transition-all hover:bg-slate-800 sm:flex"
                >
                    <FileText className="h-4 w-4" />

                    Create Paper
                </a>
            </div>
        </nav>
    );
}

export default Navbar;