from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import chatbot
import mortgage
import LinkToken
from routes import properties
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Bestia Real Estate API",
    description="""
    Bestia Real Estate API provides endpoints for real estate services including:
    - Property management
    - Mortgage calculations
    - ChatGPT integration for real estate advice
    - Plaid integration for financial data
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정 수정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 origin 허용
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메소드 허용
    allow_headers=["*"],  # 모든 헤더 허용
    expose_headers=["*"]  # 모든 헤더 노출
)

# 라우터 등록
app.include_router(chatbot.router)
app.include_router(properties.router)
app.include_router(LinkToken.router)
app.include_router(mortgage.router)
