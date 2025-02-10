from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from typing import Dict, Any
import openai  # OpenAI import 방식 변경
import os
from dotenv import load_dotenv
from pathlib import Path

# 로거 설정
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# 환경 변수 로드
env_path = Path(__file__).parents[1] / ".env"
load_dotenv(dotenv_path=env_path)

# OpenAI API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

router = APIRouter(tags=["chatbot"], responses={404: {"description": "Not found"}})


class ChatMessage(BaseModel):
    content: str
    mortgage_data: Dict[str, Any] = None


class ChatResponse(BaseModel):
    content: str


# 대화 기록 저장소
conversation_history = {}


def get_mock_response(message: str, mortgage_data: Dict[str, Any]) -> str:
    """임시 응답 생성 함수"""
    if not mortgage_data:
        return "I need your mortgage application data to provide specific advice. Could you please provide that information?"

    property_info = mortgage_data.get("propertyInfo", {})
    financial_info = mortgage_data.get("financialInfo", {})

    if "payment" in message.lower():
        monthly_payment = property_info.get("price", 0) * 0.004
        return f"""Based on your property price of ${property_info.get('price', 0):,}, 
        your estimated monthly payment would be ${monthly_payment:,.2f}.
        This includes principal, interest, taxes, and insurance.
        
        Would you like to know more about the breakdown of these costs?
        
        Best regards,
        Bestie, Senior Mortgage Advisor"""

    elif "credit" in message.lower():
        credit_score = financial_info.get("credit_score", 0)
        return f"""Your credit score of {credit_score} is in good range. 
        This should help you qualify for competitive interest rates. 
        
        Would you like to explore the loan options available to you?
        
        Best regards,
        Bestie, Senior Mortgage Advisor"""

    else:
        return f"""Thank you for your question about "{message}". 
        
        Based on your application:
        - Property: {property_info.get('address')}
        - Price: ${property_info.get('price', 0):,}
        - Annual Income: ${financial_info.get('annual_income', 0):,}
        
        What specific aspect would you like to know more about?
        
        Best regards,
        Bestie, Senior Mortgage Advisor"""


def create_system_prompt(mortgage_data: Dict[str, Any]) -> str:
    """시스템 프롬프트 생성 함수"""
    property_info = mortgage_data.get("propertyInfo", {})
    financial_info = mortgage_data.get("financialInfo", {})

    return f"""You are Bestie, a friendly and knowledgeable Senior Mortgage Advisor. 
    You're helping a client with their mortgage application for:
    
    Property Details:
    - Address: {property_info.get('address', 'Not provided')}
    - Price: ${property_info.get('price', 0):,}
    
    Financial Information:
    - Annual Income: ${financial_info.get('annual_income', 0):,}
    - Credit Score: {financial_info.get('credit_score', 'Not provided')}
    
    Please provide helpful, accurate, and professional advice based on this information.
    Keep responses concise but informative, and always maintain a friendly, professional tone.
    Sign off each response with 'Best regards, Bestie, Senior Mortgage Advisor'"""


@router.post("/api/chat/with-history", response_model=ChatResponse)
async def chat_with_history(message: ChatMessage):
    try:
        logger.info(f"Starting chat with message: {message.content}")

        if not message.mortgage_data:
            raise HTTPException(status_code=400, detail="Mortgage data is required")

        user_id = message.mortgage_data.get("userId", "default")

        if user_id not in conversation_history:
            conversation_history[user_id] = []
            logger.info(f"Created new conversation history for user {user_id}")

        conversation_history[user_id].append(
            {"role": "user", "content": message.content}
        )

        system_prompt = create_system_prompt(message.mortgage_data)
        logger.info(f"Generated system prompt: {system_prompt[:100]}...")

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                *conversation_history[user_id][-5:],
            ]

            logger.info(f"Sending messages to OpenAI: {messages}")

            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=300,
                presence_penalty=0.6,
                frequency_penalty=0.3,
            )

            bot_response = completion.choices[0].message.content
            logger.info(f"Received response from OpenAI: {bot_response[:100]}...")

            conversation_history[user_id].append(
                {"role": "assistant", "content": bot_response}
            )

            return ChatResponse(content=bot_response)

        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
