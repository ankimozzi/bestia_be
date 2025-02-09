from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from LinkToken import router as link_token_router
import pandas as pd
from pathlib import Path
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="California Property Mortgage API",
    description="API for property search and mortgage analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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

# Properties 엔드포인트
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

# LinkToken 라우터 포함
app.include_router(link_token_router, prefix="/api")

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="California Property Mortgage API",
        version="1.0.0",
        description="API for property search and mortgage analysis",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)