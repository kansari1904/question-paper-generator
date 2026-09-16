# SmartPaper — Smart Question Paper Generator

SmartPaper is a constraint-aware question paper generation system that creates structured Maths/Science-style question papers from teacher-defined requirements.

Instead of randomly selecting questions, SmartPaper treats paper generation as a **constraint optimization problem**.

A teacher can specify:

* Total marks
* Difficulty distribution
* Topic weightage
* Question-type distribution

The system then selects questions from an available question bank while trying to satisfy all requested constraints.

If the requested constraints cannot be satisfied exactly, SmartPaper does not silently ignore them or crash. Instead, it finds the closest feasible solution and reports the deviations to the teacher.

---

## Features

### 1. Constraint-aware paper generation

Teachers can configure:

* Total marks
* Easy / Medium / Hard distribution
* Topic weightage
* MCQ / Short Answer / Long Answer distribution

Example:

```text
Total Marks: 40

Difficulty:
Easy    → 30%
Medium  → 50%
Hard    → 20%

Topics:
Physics   → 40%
Chemistry → 30%
Biology   → 30%

Question Types:
MCQ          → 40%
Short Answer → 40%
Long Answer  → 20%
```

The system considers these constraints together instead of solving each one independently.

---

### 2. Constraint validation

Before generating a paper, the backend validates the request.

For example:

```text
Difficulty:
30 + 50 + 20 = 100%

Topics:
40 + 30 + 30 = 100%

Question Types:
40 + 40 + 20 = 100%
```

Invalid distributions are rejected at the frontend and backend levels.

The system also checks whether requested question types and marks can actually be produced from the available question bank.

---

### 3. Constraint optimization

The main generation engine uses **Mixed Integer Linear Programming (MILP)** through SciPy.

Each question is represented as a binary decision:

```text
xᵢ = 1 → question selected
xᵢ = 0 → question not selected
```

The solver then decides which combination of questions satisfies the paper requirements.

The optimization considers:

* Total marks
* Difficulty
* Topic
* Question type
* Available question pool

This allows the system to find a feasible combination instead of simply selecting random questions.

---

### 4. Graceful infeasibility handling

One of the most important parts of the assignment is handling impossible constraints.

For example, suppose the teacher requests:

```text
20% Hard questions
```

but the question bank does not contain enough suitable Hard questions.

A naive system might:

* crash
* return an invalid paper
* silently ignore the requirement

SmartPaper instead uses deviation variables in the optimization model.

Conceptually:

```text
Requested value
       │
       ▼
  Optimization
       │
       ├── Exact target possible
       │       ↓
       │   Meet target
       │
       └── Exact target impossible
               ↓
        Minimize deviation
               ↓
        Report deviation
```

The generated response contains a constraint report containing:

* Requested total marks
* Actual total marks
* Deviations
* Warnings

The frontend displays these constraint notes to the teacher before continuing to the generated paper.

This makes the behavior transparent instead of silently changing the teacher's requirements.

---

# Architecture

```text
┌───────────────────────────────┐
│           React UI            │
│                               │
│  Constraint Configuration      │
│  Paper Preview                 │
│  Question Swap                 │
│  PDF Export                    │
└───────────────┬───────────────┘
                │
                │ REST API
                ▼
┌───────────────────────────────┐
│          FastAPI              │
│                               │
│  Request Validation            │
│  Paper Generation API          │
│  Paper Retrieval               │
│  Question Swap API             │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│       Constraint Pipeline      │
│                               │
│  Validator                     │
│       ↓                        │
│  Exact Solver / MILP           │
│       ↓                        │
│  Selection Result              │
│       ↓                        │
│  Paper Composer                │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│        Question Bank           │
│                               │
│  Topic                         │
│  Difficulty                    │
│  Question Type                 │
│  Marks                         │
│  Options / Answer              │
└───────────────────────────────┘
```

---

# Project Structure

```text
smartpaper/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   │
│   │   ├── models/
│   │   │   └── ...
│   │   │
│   │   ├── engine/
│   │   │   ├── exact_solver.py
│   │   │   ├── validator.py
│   │   │   └── composer.py
│   │   │
│   │   └── ...
│   │
│   ├── tests/
│   │   └── ...
│   │
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.jsx
│   │   │   ├── ConstraintSection.jsx
│   │   │   ├── PercentageInput.jsx
│   │   │   ├── ConstraintModal.jsx
│   │   │   ├── ConstraintReport.jsx
│   │   │   ├── PaperHeader.jsx
│   │   │   ├── PaperSection.jsx
│   │   │   ├── QuestionCard.jsx
│   │   │   └── PdfButton.jsx
│   │   │
│   │   ├── pages/
│   │   │   ├── Home.jsx
│   │   │   └── Paper.jsx
│   │   │
│   │   ├── services/
│   │   │   └── api.js
│   │   │
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   │
│   └── package.json
│
└── README.md
```

---

# Core Generation Pipeline

The backend generation process is divided into several stages.

## Stage 1 — Validate Input

The teacher's configuration is received by FastAPI.

Example request:

```json
{
  "total_marks": 40,
  "difficulty_mix": {
    "easy": 30,
    "medium": 50,
    "hard": 20
  },
  "topic_weightage": {
    "physics": 40,
    "chemistry": 30,
    "biology": 30
  },
  "qtype_mix": {
    "mcq": 40,
    "short": 40,
    "long": 20
  }
}
```

Pydantic models validate the structure and allowed values.

---

# Stage 2 — Validate Question Bank Reachability

The system checks whether the requested question types and marks are compatible with the question bank.

For example:

```text
MCQ    → 1 mark
Short  → 3 marks
Long   → 5 marks
```

This prevents impossible configurations from being treated as normal generation requests.

---

# Stage 3 — Build the Optimization Model

Each available question becomes a binary decision variable.

For example:

```text
Question 1 → x₁
Question 2 → x₂
Question 3 → x₃
...
```

Each variable can only have:

```text
0 → Do not select
1 → Select
```

The solver then searches for the best combination.

---

# Stage 4 — Total Marks Constraint

The selected questions must satisfy the requested total marks.

Conceptually:

```text
Σ(question_marks × selection_variable)
= requested_total_marks
```

For a 40-mark paper:

```text
Selected marks = 40
```

This is one of the core hard constraints.

---

# Stage 5 — Difficulty Constraints

The solver calculates the requested target for each difficulty level.

For example:

```text
Total Marks = 40

Easy   = 30% → 12 marks
Medium = 50% → 20 marks
Hard   = 20% → 8 marks
```

The solver attempts to select questions whose marks distribution matches these targets.

---

# Stage 6 — Topic Constraints

The same process is applied to topics.

For example:

```text
Physics   = 40% → 16 marks
Chemistry = 30% → 12 marks
Biology   = 30% → 12 marks
```

The solver considers topic and difficulty simultaneously.

This is important because constraints can interact.

For example:

```text
Physics + Hard
```

may have fewer available questions than:

```text
Physics + Easy
```

The solver therefore needs to consider the complete combination instead of treating every distribution separately.

---

# Stage 7 — Question-Type Constraints

Question types also have fixed marks.

Current configuration:

```text
MCQ          → 1 mark
Short Answer → 3 marks
Long Answer  → 5 marks
```

The solver selects an appropriate combination while considering the requested question-type distribution.

For example:

```text
MCQ          → 40%
Short Answer → 40%
Long Answer  → 20%
```

The actual selected paper is determined by the available question bank and the mathematical constraints.

---

# Stage 8 — Objective Function

When exact constraints cannot all be satisfied, deviation variables are introduced.

Conceptually:

```text
deviation = |actual - requested|
```

The optimization objective is to minimize the total deviation.

Therefore:

```text
Minimize:

difficulty deviation
+ topic deviation
+ question-type deviation
```

A small random tie-breaker is also used so that equally good solutions can vary based on the generation seed.

This provides deterministic generation when a seed is supplied while still allowing different valid papers to be generated.

---

# Stage 9 — Paper Composition

The solver produces a selected set of question IDs.

However, a set of questions alone does not look like a real exam paper.

Therefore, SmartPaper has a separate **composer stage**.

The composer:

1. Groups questions by question type.
2. Creates sections.
3. Adds section instructions.
4. Calculates section mark subtotals.
5. Orders sections logically.
6. Orders questions consistently.

The current section structure is:

```text
SECTION A — MCQ

SECTION B — SHORT ANSWER

SECTION C — LONG ANSWER
```

This separation between **selection** and **composition** is intentional.

The solver decides:

> Which questions should be selected?

The composer decides:

> How should those questions be presented to a teacher/student?

---

# Why Separate Solver and Composer?

This is an important architectural decision.

A solver should focus on mathematical feasibility.

A composer should focus on presentation.

If these responsibilities were mixed together, the generation logic would become harder to maintain.

Instead:

```text
Selection
   ↓
Question IDs
   ↓
Composition
   ↓
Teacher-friendly paper
```

This makes it easier to change the paper format without changing the optimization algorithm.

---

# Question Swapping

SmartPaper also supports replacing one question without regenerating the entire paper.

API:

```http
POST /paper/swap
```

Request:

```json
{
  "paper_id": "...",
  "question_id": "..."
}
```

The backend searches for an unused compatible question and replaces the selected question.

The frontend then updates:

```text
questions
+
section question_ids
```

without rebuilding the entire paper.

This matches the teacher workflow described in the assignment:

> "Can a teacher regenerate / swap one question without redoing the whole paper?"

---

# Paper Structure

The generated paper is intentionally designed to look like an actual examination paper rather than a dashboard.

It contains:

* Paper title
* Subject
* Total marks
* Number of questions
* Student name
* Roll number
* Date
* Class
* General instructions
* Section headings
* Question numbers
* Marks per question
* MCQ options
* Section mark subtotals

Example:

```text
                    QUESTION PAPER

Subject: General Science          Total Marks: 40

Name: ___________________         Roll No: __________

Date: ___________________         Class: ____________

GENERAL INSTRUCTIONS

1. Read all questions carefully before answering.
2. Answer all questions according to the instructions.
3. Marks allotted to each question are indicated.

----------------------------------------------------

SECTION A — MCQ                              16 Marks

1. Which of the following...                    [1 Mark]

   A. ...
   B. ...
   C. ...
   D. ...

----------------------------------------------------

SECTION B — SHORT ANSWER                      12 Marks

17. Explain the process of...                   [3 Marks]

----------------------------------------------------

SECTION C — LONG ANSWER                       12 Marks

21. Describe and explain...                     [5 Marks]
```

---

# PDF Export

The frontend also provides PDF export.

The PDF implementation uses:

* `html2canvas`
* `jsPDF`

Instead of simply taking one screenshot of the entire page, the application creates a PDF-specific representation and handles pagination.

Question cards are measured and positioned so that questions and their options are kept together as much as possible.

This helps avoid situations where:

```text
Question
---------
page break
---------
Options
```

appear on different pages.

The generated file is:

```text
smartpaper-question-paper.pdf
```

---

# API Endpoints

## Generate Paper

```http
POST /paper/generate?seed=42
```

Generates a new question paper.

---

## Get Paper

```http
GET /paper/{paper_id}
```

Returns a previously generated paper.

---

## Swap Question

```http
POST /paper/swap
```

Replaces one selected question with another compatible unused question.

---

# Example Generate Request

```json
{
  "total_marks": 40,
  "difficulty_mix": {
    "easy": 30,
    "medium": 50,
    "hard": 20
  },
  "topic_weightage": {
    "physics": 40,
    "chemistry": 30,
    "biology": 30
  },
  "qtype_mix": {
    "mcq": 40,
    "short": 40,
    "long": 20
  }
}
```

---

# Example Response Concept

```json
{
  "paper_id": "...",
  "total_marks": 40,
  "questions": [],
  "sections": [],
  "constraint_report": {
    "requested_total_marks": 40,
    "actual_total_marks": 40,
    "deviations": [],
    "warnings": []
  }
}
```

The `constraint_report` makes the solver's result transparent to the frontend.

---

# Why I Used Optimization Instead of an LLM

The central problem is not:

> "Write a question."

The central problem is:

> "Select a combination of existing questions that satisfies multiple mathematical constraints."

For this reason, a deterministic optimization approach is more appropriate for the core generation engine.

### Optimization provides

* Deterministic constraint handling
* Exact total-mark control
* Explicit infeasibility handling
* Reproducibility through seeds
* Transparent deviation reporting
* Easier testing

### Where an LLM could help

An LLM could be useful for:

* Generating new questions
* Rewriting questions
* Creating question variations
* Generating explanations
* Enriching a question bank
* Creating questions from a syllabus/topic description

However, the LLM should not be responsible for guaranteeing the mathematical constraints.

A future architecture could therefore be:

```text
LLM
 │
 ├── Generate / enrich questions
 │
 ▼
Question Bank
 │
 ▼
MILP Solver
 │
 ▼
Final Paper
```

This would combine generative AI with deterministic constraint satisfaction.

---

# Handling Impossible Constraints

This was one of the main challenges of the assignment.

Suppose the teacher requests:

```text
40 marks

Hard = 20%
```

which means approximately:

```text
8 marks of Hard questions
```

But the available question bank may not contain enough suitable Hard questions.

SmartPaper does not simply ignore the requirement.

Instead:

```text
Requested constraints
        ↓
Check available questions
        ↓
Build optimization model
        ↓
Find feasible combination
        ↓
Minimize deviations
        ↓
Return constraint report
```

The frontend then informs the teacher that the generated paper contains constraint notes.

This is preferable to silently changing the requested distribution.

---

# Technology Stack

## Frontend

* React
* React Router
* Tailwind CSS
* Lucide React
* React Hot Toast
* html2canvas
* jsPDF

## Backend

* Python
* FastAPI
* Pydantic
* SciPy
* NumPy

## Optimization

* Mixed Integer Linear Programming
* Binary decision variables
* Constraint equations
* Deviation variables
* Objective minimization

---

# Why FastAPI?

FastAPI was chosen because the backend is primarily an API-driven service.

Advantages:

* Automatic request validation
* Pydantic integration
* Automatic OpenAPI/Swagger documentation
* Type hints
* Simple REST endpoint implementation
* Good fit for Python optimization libraries

Swagger documentation is available through FastAPI's built-in API documentation during development.

---

# Why React?

React provides a clean way to manage:

* Constraint input state
* Validation state
* Loading state
* Generated paper state
* Swap state
* Constraint warning modal
* Responsive paper preview

The application separates reusable UI components from page-level logic.

---

# Frontend Component Architecture

```text
Home
│
├── Navbar
├── ConstraintSection
│   └── PercentageInput
├── ConstraintModal
│
└── Paper
    ├── PaperHeader
    ├── PaperSection
    │   └── QuestionCard
    ├── ConstraintReport
    └── PdfButton
```

This keeps individual UI responsibilities small and reusable.

---

# Backend Architecture

The backend separates the main responsibilities into different stages.

```text
API Layer
   │
   ▼
Validation
   │
   ▼
Question Selection / Solver
   │
   ▼
Selection Result
   │
   ▼
Composer
   │
   ▼
Paper Response
```

Important backend modules include:

```text
validator.py
exact_solver.py
composer.py
```

### `validator.py`

Responsible for validating the generation request and checking basic feasibility/reachability.

### `exact_solver.py`

Responsible for the mathematical optimization problem.

It creates the MILP model, applies constraints, minimizes deviations, and returns the selected questions.

### `composer.py`

Responsible for converting the selected question IDs into a teacher-friendly paper structure.

---

# Testing

The backend includes automated tests for core functionality.

The goal is to test things such as:

* Request validation
* Solver behavior
* Paper generation
* Constraint handling
* Invalid configurations
* API behavior

Testing the solver separately from the presentation layer also makes the core generation logic easier to verify.

---

# Current Limitations

The current implementation intentionally keeps the scope small.

### 1. Question bank is limited

The quality of generated papers depends heavily on the available question bank.

If the bank does not contain enough questions for a requested combination, the solver can only find the closest feasible result.

With more time, I would build a larger and more diverse question bank.

---

### 2. In-memory storage

Generated papers are currently stored in memory.

This means data will not persist after the backend restarts.

A production version could use:

```text
PostgreSQL
+
SQLAlchemy
```

for persistent storage.

---

### 3. Limited subject/topic configuration

The current demo uses a predefined set of topics and question types.

A future version could allow teachers to:

* Create subjects
* Add topics
* Upload question banks
* Define custom marks
* Define custom question types

---

### 4. Question generation is not yet dynamic

The current core system selects questions from an existing question bank.

A future version could use an LLM to generate new questions when the existing pool is insufficient.

The generated questions would still need to pass validation before entering the solver's question pool.

---

### 5. Swap availability depends on the question bank

A swap is only possible when a suitable unused alternative exists.

If no compatible question is available, the system reports the failure instead of producing an invalid replacement.

---

# What I Am Proud Of

The part I am most proud of is the **constraint-handling architecture**.

Instead of implementing something like:

```python
random.choice(questions)
```

the system models paper generation as an optimization problem.

The solver simultaneously considers:

```text
Total Marks
     +
Difficulty
     +
Topics
     +
Question Types
     +
Question Availability
```

and produces a measurable constraint report.

I also separated **question selection from paper composition**, which allows the system to solve the mathematical problem first and then turn the result into a realistic examination paper.

---

# What Is Still Weak

The weakest part of the current implementation is the **limited question bank and persistence layer**.

The optimization engine can only work with the questions available to it.

A larger production system would need:

* A persistent database
* A much larger question bank
* Better question metadata
* Duplicate detection
* Difficulty calibration
* Subject/syllabus management
* Teacher authentication
* Persistent generated-paper history

The current implementation intentionally focuses on solving the core assignment problem rather than building a complete education platform.

---

# Future Improvements

With more development time, I would add:

### Question Bank Management

```text
Upload CSV / Excel / JSON
        ↓
Validate Questions
        ↓
Store in Database
        ↓
Index by Metadata
```

### AI Question Generation

Use an LLM to generate questions based on:

* Subject
* Topic
* Difficulty
* Question type
* Learning objective

Then validate and add them to the question bank.

### Persistent Storage

Move from:

```text
In-memory storage
```

to:

```text
PostgreSQL
```

with models for:

* Users
* Subjects
* Topics
* Questions
* Question Banks
* Generated Papers
* Paper Questions

### Better Teacher Controls

Allow teachers to configure:

* Custom subjects
* Custom topics
* Custom question types
* Section ordering
* Instructions
* Negative marking
* Optional questions
* Question numbering

---

# Running Locally

## Prerequisites

Install:

* Python 3.11+
* Node.js 18+
* npm

---

## Backend Setup

Navigate to the backend:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the FastAPI server:

```bash
uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

---

## Frontend Setup

Navigate to the frontend:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Create `.env`:

```env
VITE_BASE_URL=http://127.0.0.1:8000
```

Start the development server:

```bash
npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

# End-to-End Flow

The complete user journey is:

```text
1. Teacher opens SmartPaper
            ↓
2. Enters total marks
            ↓
3. Configures difficulty distribution
            ↓
4. Configures topic weightage
            ↓
5. Configures question-type distribution
            ↓
6. Frontend validates input
            ↓
7. FastAPI receives request
            ↓
8. Backend validates constraints
            ↓
9. MILP solver selects questions
            ↓
10. Deviations are calculated
            ↓
11. Composer builds paper sections
            ↓
12. Frontend displays realistic paper
            ↓
13. Teacher can swap a question
            ↓
14. Teacher can export PDF
```

---

# Design Philosophy

The project follows three main principles:

### Correctness

The system should respect mathematical constraints whenever the question bank allows it.

### Transparency

When constraints cannot be satisfied exactly, the system should tell the teacher instead of silently changing the requirements.

### Teacher-friendly output

The final result should look and behave like a real question paper rather than a raw list of selected questions.

---

# Assignment Requirements Mapping

| Assignment Requirement | SmartPaper Implementation                  |
| ---------------------- | ------------------------------------------ |
| Total marks            | Implemented                                |
| Difficulty mix         | Implemented                                |
| Topic weightage        | Implemented                                |
| Question-type mix      | Implemented                                |
| Valid paper generation | MILP-based solver                          |
| Impossible constraints | Deviation minimization + constraint report |
| Graceful handling      | Warning/deviation modal                    |
| Real paper structure   | Dedicated composer                         |
| Question swapping      | `/paper/swap`                              |
| Resulting breakdown    | Constraint report                          |
| PDF export             | html2canvas + jsPDF                        |
| Responsive UI          | React + Tailwind CSS                       |

---

# Conclusion

SmartPaper demonstrates that question-paper generation can be modeled as a **constraint optimization problem rather than simple random selection**.

The system combines:

```text
React
+
FastAPI
+
Pydantic
+
MILP Optimization
+
Question Bank
+
Paper Composition
+
PDF Export
```

The most important architectural decision is keeping **constraint satisfaction deterministic** while keeping the UI and paper composition flexible.

An LLM can be introduced later for question generation and enrichment, but the mathematical guarantee of the paper remains the responsibility of the optimization engine.
