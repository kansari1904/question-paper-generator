import { useState } from "react";

import {
  BrainCircuit,
  FileText,
  Menu,
  X,
} from "lucide-react";

function Navbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const closeMenu = () => {
    setIsMenuOpen(false);
  };

  return (
    <nav className="fixed left-0 right-0 top-0 z-50 border-b border-slate-200/80 bg-white/90 backdrop-blur-xl">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">

          {/* Brand */}
          <a
            href="#"
            onClick={closeMenu}
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

          {/* Desktop Navigation */}
          <div className="hidden items-center gap-7 md:flex">
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
          </div>

          {/* Desktop Create Paper Button */}
          <a
            href="#generator"
            className="hidden items-center gap-2 rounded-xl bg-slate-900 px-4 py-2.5 text-xs font-semibold text-white transition-all hover:bg-slate-800 lg:flex"
          >
            <FileText className="h-4 w-4" />
            Create Paper
          </a>

          {/* Mobile / Tablet Menu Button */}
          <button
            type="button"
            onClick={() => setIsMenuOpen((prev) => !prev)}
            aria-label={isMenuOpen ? "Close menu" : "Open menu"}
            aria-expanded={isMenuOpen}
            className="flex h-10 w-10 items-center justify-center rounded-lg border border-slate-200 text-slate-700 transition hover:bg-slate-100 md:hidden"
          >
            {isMenuOpen ? (
              <X className="h-5 w-5" />
            ) : (
              <Menu className="h-5 w-5" />
            )}
          </button>
        </div>

        {/* Mobile / Tablet Navigation */}
        {isMenuOpen && (
          <div className="border-t border-slate-200 py-4 md:hidden">
            <div className="flex flex-col gap-1">

              <a
                href="#generator"
                onClick={closeMenu}
                className="rounded-lg px-3 py-3 text-sm font-medium text-slate-700 transition hover:bg-emerald-50 hover:text-emerald-600"
              >
                Generator
              </a>

              <a
                href="#features"
                onClick={closeMenu}
                className="rounded-lg px-3 py-3 text-sm font-medium text-slate-700 transition hover:bg-emerald-50 hover:text-emerald-600"
              >
                Features
              </a>

              <a
                href="#how-it-works"
                onClick={closeMenu}
                className="rounded-lg px-3 py-3 text-sm font-medium text-slate-700 transition hover:bg-emerald-50 hover:text-emerald-600"
              >
                How It Works
              </a>

              <a
                href="#about"
                onClick={closeMenu}
                className="rounded-lg px-3 py-3 text-sm font-medium text-slate-700 transition hover:bg-emerald-50 hover:text-emerald-600"
              >
                About
              </a>

              {/* Mobile / Tablet Create Paper */}
              <a
                href="#generator"
                onClick={closeMenu}
                className="mt-2 flex items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
              >
                <FileText className="h-4 w-4" />
                Create Paper
              </a>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}

export default Navbar;