import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
import requests
from datetime import datetime
from pydantic import BaseModel
import logging

app = FastAPI()
router = APIRouter()
logger = logging.getLogger(__name__)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 프로젝트 루트 디렉토리의 .env 파일 로드
env_path = Path(__file__).parents[1] / '.env'
load_dotenv(dotenv_path=env_path)

PLAID_API_KEY = os.getenv("Plaid_API_KEY")
FRED_API_KEY = os.getenv("FRED_API_KEY")

def get_plaid_sandbox_data(user_id: str) -> dict:
    """Plaid Sandbox API에서 사용자의 재무 정보 조회"""
    try:
        # Plaid API 엔드포인트 (Sandbox)
        url = "https://sandbox.plaid.com/auth/get"
        headers = {
            "Content-Type": "application/json",
            "PLAID-CLIENT-ID": PLAID_API_KEY,
            # 실제 구현시 필요한 추가 인증 정보 포함
        }
        
        response = requests.post(url, headers=headers, json={"user_id": user_id})
        if response.status_code == 200:
            data = response.json()
            return {
                "credit_score": data.get("credit_score", 700),  # 예시
                "accounts": data.get("accounts", []),
                "income": data.get("income", 0),
                "debt": data.get("debt", 0)
            }
        else:
            raise Exception("Plaid API 호출 실패")
    except Exception as e:
        print(f"Plaid API 에러: {str(e)}")
        # 테스트용 더미 데이터 반환
        return {
            "credit_score": 700,
            "accounts": [],
            "income": 50000,
            "debt": 10000
        }

def get_current_mortgage_rate() -> float:
    """FRED API에서 현재 모기지 금리 조회"""
    try:
        # FRED API 엔드포인트
        url = f"https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": "MORTGAGE30US",  # 30년 고정 모기지 금리
            "api_key": FRED_API_KEY,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 1
        }
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            latest_rate = float(data["observations"][0]["value"])
            return latest_rate
        else:
            raise Exception("FRED API 호출 실패")
    except Exception as e:
        print(f"FRED API 에러: {str(e)}")
        # 테스트용 기본 금리 반환
        return 3.5

@app.get("/api/mortgage-analysis/")
async def mortgage_analysis(
    user_id: str, 
    home_value: int,  # Zillow 대신 직접 전달받은 집값
    loan_amount: int, 
    down_payment: int
):
    try:
        # Plaid에서 사용자 재무 정보 조회
        plaid_data = get_plaid_sandbox_data(user_id)
        credit_score = plaid_data["credit_score"]
        income = plaid_data["income"]
        debt = plaid_data["debt"]

        # FRED에서 현재 모기지 금리 조회
        mortgage_rate = get_current_mortgage_rate()

        # 계산
        LTV = (loan_amount / home_value) * 100
        DTI = (debt / income) * 100
        monthly_payment = (loan_amount * (mortgage_rate/100/12)) / (1 - (1 + mortgage_rate/100/12)**(-360))

        # 승인 조건 체크
        conditions = {
            "credit_score": credit_score > 650,
            "dti": DTI < 43,
            "ltv": LTV < 80,
            "income_sufficient": monthly_payment < (income / 12) * 0.28
        }

        approval = "Approved" if all(conditions.values()) else "Rejected"
        
        return {
            "credit_score": credit_score,
            "home_value": home_value,
            "mortgage_rate": mortgage_rate,
            "monthly_payment": round(monthly_payment, 2),
            "LTV_ratio": round(LTV, 2),
            "DTI_ratio": round(DTI, 2),
            "approval_status": approval,
            "approval_details": {
                "신용점수 충족": "✅" if conditions["credit_score"] else "❌",
                "DTI 비율 충족": "✅" if conditions["dti"] else "❌",
                "LTV 비율 충족": "✅" if conditions["ltv"] else "❌",
                "소득 대비 월상환액 충족": "✅" if conditions["income_sufficient"] else "❌"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mortgage-rates/historical/")
async def get_historical_rates():
    """FRED API에서 역사적 모기지 금리 데이터 조회"""
    try:
        url = f"https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": "MORTGAGE30US",
            "api_key": FRED_API_KEY,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 12
        }
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            return [
                {
                    "date": item["date"],
                    "rate": float(item["value"])
                }
                for item in data["observations"]
            ]
        else:
            raise Exception("FRED API 호출 실패")
    except Exception as e:
        print(f"FRED API 에러: {str(e)}")
        # 테스트용 더미 데이터 반환
        return [
            {
                "date": f"2024-{month:02d}-01",
                "rate": 3.5 + (month * 0.1)
            }
            for month in range(1, 13)
        ]

class MortgageAnalysisRequest(BaseModel):
    home_value: float
    loan_amount: float
    down_payment: float
    annual_income: float
    total_debt: float
    credit_score: int

@router.post("/mortgage-analysis")
async def analyze_mortgage(request: MortgageAnalysisRequest):
    try:
        logger.info("Analyzing mortgage application")
        
        # DTI (Debt-to-Income) 비율 계산
        monthly_income = request.annual_income / 12
        dti_ratio = (request.total_debt / monthly_income) * 100
        
        # LTV (Loan-to-Value) 비율 계산
        ltv_ratio = (request.loan_amount / request.home_value) * 100
        
        # 월 상환액 계산 (30년 고정금리 기준, 연 3.5% 가정)
        annual_rate = 3.5
        monthly_rate = annual_rate / 12 / 100
        loan_term_months = 30 * 12
        
        monthly_payment = (
            request.loan_amount * 
            (monthly_rate * (1 + monthly_rate)**loan_term_months) / 
            ((1 + monthly_rate)**loan_term_months - 1)
        )
        
        # 승인 조건 검사
        approval_details = {
            "Credit Score": "✅ Sufficient" if request.credit_score >= 620 else "❌ Insufficient",
            "DTI Ratio": "✅ Acceptable" if dti_ratio <= 43 else "❌ Too High",
            "LTV Ratio": "✅ Within Limit" if ltv_ratio <= 80 else "❌ Too High",
            "Down Payment": "✅ Sufficient" if (request.down_payment / request.home_value * 100) >= 20 else "❌ Insufficient"
        }
        
        # 전체 승인 여부 결정
        is_approved = all(detail.startswith("✅") for detail in approval_details.values())
        
        return {
            "approval_status": "Approved" if is_approved else "Denied",
            "monthly_payment": round(monthly_payment, 2),
            "DTI_ratio": round(dti_ratio, 2),
            "LTV_ratio": round(ltv_ratio, 2),
            "approval_details": approval_details
        }
        
    except Exception as e:
        logger.error(f"Error analyzing mortgage: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))