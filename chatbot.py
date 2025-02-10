from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from typing import Dict, Any
from openai import OpenAI
import os
from dotenv import load_dotenv
from pathlib import Path
from collections import defaultdict

# 로거 설정
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# 환경 변수 로드
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# OpenAI API 키 설정
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OpenAI API key not found")

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=api_key)
logger.info("OpenAI client initialized successfully")

# FastAPI 라우터 설정
router = APIRouter(
    prefix="/api/chat",
    tags=["chatbot"],
    responses={404: {"description": "Not found"}}
)

# 대화 요청 및 응답 모델 정의
class ChatMessage(BaseModel):
    content: str
    mortgage_data: Dict[str, Any] = None

class ChatResponse(BaseModel):
    content: str

# 대화 기록 저장소
conversation_history = defaultdict(list)

# 시스템 메시지 설정
def create_system_prompt():
    return """You are Bestie, a Senior Mortgage Advisor specializing in real estate and mortgage consulting. Your role is to provide users with clear, accurate, and professional responses about:
    1. Mortgage calculations and monthly payments
    2. Home affordability assessments based on income and credit score
    3. Credit score impact on mortgage rates
    4. Real estate market trends
    5. Legal considerations when buying or selling a property

    When discussing monthly payments:
    - Calculate and break down monthly payments (principal, interest, taxes, insurance)
    - Use the provided property price and an estimated rate of 0.4% for monthly payment calculations
    - Explain each component of the payment

    When discussing credit scores:
    - Provide specific advice based on the user's credit score
    - Explain how their score affects interest rates
    - Suggest ways to improve their score if needed

    When providing property analysis:
    - Reference the specific property details provided (address, price)
    - Consider the user's financial information (annual income, credit score)
    - Provide personalized recommendations based on their financial situation

    Always:
    - Be polite and professional
    - Sign your responses as "Bestie, Senior Mortgage Advisor"
    - Provide detailed, structured explanations
    - Ask follow-up questions to better understand the user's needs
    - Format numbers with appropriate commas and currency symbols (e.g., $500,000)
    """
    
@router.post("/with-history", 
    response_model=ChatResponse,
    summary="Chat with AI assistant",
    description="""
    Send a message to the AI assistant and get a response.
    The assistant uses conversation history and mortgage data to provide contextual responses.
    """,
    responses={
        200: {
            "description": "Successful response from AI",
            "content": {
                "application/json": {
                    "example": {
                        "content": "Based on your mortgage data..."
                    }
                }
            }
        },
        400: {"description": "Missing mortgage data"},
        500: {"description": "OpenAI API error"}
    }
)
async def chat_with_mortgage_info(message: ChatMessage):
    try:
        logger.info(f"Received message: {message.content}")

        if not message.mortgage_data:
            logger.warning("No mortgage data provided")
            raise HTTPException(status_code=400, detail="Mortgage data is required")
            
        user_id = message.mortgage_data.get("userId", "default")
        conversation_history[user_id].append({"role": "user", "content": message.content})

        system_prompt = create_system_prompt()
        messages = [{"role": "system", "content": system_prompt}] + conversation_history[user_id][-5:]

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=300,
                presence_penalty=0.6,
                frequency_penalty=0.3
            )

            if response and response.choices:
                bot_response = response.choices[0].message.content.strip()
            else:
                bot_response = "No response available."

            conversation_history[user_id].append({"role": "assistant", "content": bot_response})
            return ChatResponse(content=bot_response)

        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))