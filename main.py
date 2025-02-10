from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.LinkToken import router as link_token_router
from routes.mortgage import router as mortgage_router

# from routes.mortgage import router as mortgage_router  # 이 줄을 주석 처리하거나 제거
from routes.chatbot import router as chatbot_router
from routes.properties import router as properties_router

app = FastAPI(
    title="California Property Mortgage API",
    description="API for property search and mortgage analysis",
    version="1.0.0",
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
# app.include_router(mortgage_router)  # 이 줄을 주석 처리하거나 제거
app.include_router(chatbot_router)
app.include_router(properties_router)
app.include_router(mortgage_router)
