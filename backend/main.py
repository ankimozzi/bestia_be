from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from pathlib import Path
import pandas as pd

# 프로젝트 루트 디렉토리의 .env 파일 로드
env_path = Path(__file__).parents[1] / '.env'
load_dotenv(dotenv_path=env_path)

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Vite 기본 포트 추가
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 변수로 데이터 저장
property_data = None

# 데이터 로드
@app.on_event("startup")
async def load_data():
    global property_data
    current_dir = Path(__file__).parent
    csv_path = current_dir / "data" / "california_properties.csv"
    
    if not csv_path.exists():
        # 데이터 파일이 없으면 데이터 처리 실행
        from data_processor import process_california_data
        process_california_data()
        
    property_data = pd.read_csv(csv_path)
    print(f"Loaded {len(property_data)} California properties")

@app.get("/api/properties")
async def get_properties(
    ne_lat: float = None, 
    ne_lng: float = None,
    sw_lat: float = None, 
    sw_lng: float = None
):
    if property_data is None:
        return {"error": "No data loaded"}
        
    filtered_data = property_data
    
    if all([ne_lat, ne_lng, sw_lat, sw_lng]):
        filtered_data = property_data[
            (property_data['latitude'] <= ne_lat) &
            (property_data['latitude'] >= sw_lat) &
            (property_data['longitude'] <= ne_lng) &
            (property_data['longitude'] >= sw_lng)
        ]
    
    return {
        "properties": filtered_data.to_dict(orient='records')
    }

@app.get("/admin/{path:path}")
async def admin_not_found(path: str):
    raise HTTPException(status_code=403, detail="Admin access not allowed")

@app.get("/favicon.ico")
async def favicon():
    raise HTTPException(status_code=404, detail="Favicon not found") 