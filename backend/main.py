from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from LinkToken import router as link_token_router
from mortgage import router as mortgage_router
from chatbot import router as chatbot_router
from routes import properties

app = FastAPI(
    title="California Property Mortgage API",
    description="API for property search and mortgage analysis",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 추가
app.include_router(link_token_router, prefix="/api")
app.include_router(mortgage_router, prefix="/api")
app.include_router(chatbot_router)
app.include_router(properties.router)