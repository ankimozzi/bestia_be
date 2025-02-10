from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import requests
import os
from dotenv import load_dotenv
from pathlib import Path
import logging
import uuid
from pydantic import BaseModel
from plaid.api import plaid_api
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.configuration import Configuration
from plaid.api_client import ApiClient

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app을 APIRouter로 변경
router = APIRouter(
    tags=["plaid"],
    responses={404: {"description": "Not found"}}
)

# 환경 변수 로드
env_path = Path(__file__).parents[1] / '.env'
load_dotenv(dotenv_path=env_path)

# 환경 변수 검증
def validate_env_vars():
    required_vars = ["PLAID_CLIENT_ID", "PLAID_SECRET"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# 앱 시작 시 환경 변수 검증
validate_env_vars()

# 환경 변수에서 Plaid 인증 정보 가져오기
PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET")
PLAID_ENV = "sandbox"
PLAID_BASE_URL = "https://sandbox.plaid.com"

# Plaid 클라이언트 초기화
configuration = Configuration(
    host=PLAID_BASE_URL,
    api_key={
        'clientId': PLAID_CLIENT_ID,
        'secret': PLAID_SECRET,
    }
)

api_client = ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

class PublicTokenRequest(BaseModel):
    public_token: str

    class Config:
        schema_extra = {
            "example": {
                "public_token": "public-sandbox-0000000000"
            }
        }

class LinkTokenResponse(BaseModel):
    link_token: str
    expiration: str
    request_id: str

class AccountResponse(BaseModel):
    access_token: str
    accounts: list
    income: float
    debt: float
    credit_score: int

@router.get("/create_link_token",
    response_model=LinkTokenResponse,
    summary="Create Plaid Link token",
    description="Creates a Link token for Plaid integration",
    responses={
        200: {
            "description": "Successfully created Link token",
            "content": {
                "application/json": {
                    "example": {
                        "link_token": "link-sandbox-xxx",
                        "expiration": "2024-02-10T12:00:00Z",
                        "request_id": "abc123"
                    }
                }
            }
        },
        500: {"description": "Plaid API error"}
    }
)
async def create_link_token():
    try:
        # Link 토큰 생성 요청
        request = LinkTokenCreateRequest(
            products=[Products("auth")],
            client_name="Bestia Mortgage",
            country_codes=[CountryCode('US')],
            language='en',
            user=LinkTokenCreateRequestUser(
                client_user_id=str(uuid.uuid4())  # 임시 사용자 ID 생성
            )
        )
        
        response = client.link_token_create(request)
        return {"link_token": response['link_token']}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/set_access_token",
    response_model=Dict[str, str],
    summary="Exchange public token for access token",
    description="Exchanges a public token from Plaid Link for an access token",
    responses={
        200: {
            "description": "Successfully exchanged tokens",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "access-sandbox-xxx",
                        "item_id": "item-sandbox-xxx",
                        "property_id": "prop123"
                    }
                }
            }
        },
        400: {"description": "Missing public token"},
        500: {"description": "Plaid API error"}
    }
)
async def set_access_token(request_data: dict):
    try:
        public_token = request_data.get('public_token')
        if not public_token:
            raise HTTPException(status_code=400, detail="Missing public token")

        # public_token을 access_token으로 교환
        exchange_request = ItemPublicTokenExchangeRequest(
            public_token=public_token
        )
        exchange_response = client.item_public_token_exchange(exchange_request)
        
        access_token = exchange_response['access_token']
        item_id = exchange_response['item_id']

        # 여기서 access_token을 저장하거나 다른 처리를 할 수 있습니다
        # 예: 데이터베이스에 저장

        return {
            "access_token": access_token,
            "item_id": item_id,
            "property_id": request_data.get('property_id')
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/exchange_token", 
    response_model=AccountResponse,
    summary="Exchange public token for access token",
    description="Exchanges a public token for an access token and returns account data")
async def exchange_token(request: PublicTokenRequest):
    """
    Exchanges a public token for an access token
    
    Args:
        request (PublicTokenRequest): The public token from Plaid Link
    
    Returns:
        AccountResponse: Account data including access token and financial information
    
    Raises:
        HTTPException: If the token exchange fails
    """
    try:
        logger.info("Exchanging public token for access token")
        url = f"{PLAID_BASE_URL}/item/public_token/exchange"
        
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={
                "client_id": PLAID_CLIENT_ID,
                "secret": PLAID_SECRET,
                "public_token": request.public_token
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Token exchange failed: {response.text}"
            )
            
        # Sandbox 테스트 데이터 추가
        return {
            "access_token": response.json().get("access_token"),
            "accounts": [],
            # 테스트용 더미 데이터
            "income": 120000,  # 연봉 $120,000
            "debt": 15000,    # 부채 $15,000
            "credit_score": 720  # 신용점수 720
        }

    except Exception as e:
        logger.error(f"Token exchange error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/accounts/{access_token}",
    response_model=Dict[str, Any],
    summary="Get account information",
    description="Retrieves account information using an access token")
async def get_accounts(access_token: str):
    """
    Retrieves account information from Plaid
    
    Args:
        access_token (str): The access token for the Plaid API
    
    Returns:
        Dict[str, Any]: Account information from Plaid
    
    Raises:
        HTTPException: If the account fetch fails
    """
    try:
        logger.info("Fetching account information")
        response = requests.post(
            f"https://{PLAID_ENV}.plaid.com/accounts/balance/get",
            headers={"Content-Type": "application/json"},
            json={
                "client_id": PLAID_CLIENT_ID,
                "secret": PLAID_SECRET,
                "access_token": access_token
            }
        )
        
        if response.status_code != 200:
            logger.error(f"Account fetch failed: {response.text}")
            raise HTTPException(status_code=400, detail="계좌 정보 조회 실패")
            
        return response.json()

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching accounts: {str(e)}")
        raise HTTPException(status_code=503, detail="Plaid 서비스 연결 실패")
    except Exception as e:
        logger.error(f"Account fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail="내부 서버 오류")