from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import health, paper, swap


app = FastAPI(
    title="Smart Question Paper Generator",
    description=(
        "Constraint-aware Science question paper generator "
        "with exact question selection and single-question swapping."
    ),
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://question-paper-generator-zeta.vercel.app/",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(health.router)
app.include_router(paper.router)
app.include_router(swap.router)
