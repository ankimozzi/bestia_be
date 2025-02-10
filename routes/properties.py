from fastapi import APIRouter, Response, HTTPException
import pandas as pd
from pathlib import Path
import logging
import os
from typing import List, Optional
from pydantic import BaseModel

# Pydantic 모델 정의
class PropertyDetails(BaseModel):
    square_feet: Optional[int] = None
    year_built: Optional[int] = None

class PropertyResponse(BaseModel):
    id: str
    region_id: int
    region_name: str
    city: str
    state: str
    metro: str
    county_name: str
    price: float
    latitude: float
    longitude: float
    zipcode: str
    details: Optional[PropertyDetails] = None

    class Config:
        from_attributes = True

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/api/properties",
    response_model=List[PropertyResponse],
    summary="Get all properties",
    description="Retrieves a list of all available properties",
    responses={
        200: {
            "description": "List of properties",
            "content": {
                "application/json": {
                    "example": [{
                        "id": "prop123",
                        "region_id": 12345,
                        "region_name": "San Francisco",
                        "city": "San Francisco",
                        "state": "CA",
                        "metro": "San Francisco Metro",
                        "county_name": "San Francisco County",
                        "price": 500000,
                        "latitude": 37.7749,
                        "longitude": -122.4194,
                        "zipcode": "94105"
                    }]
                }
            }
        }
    }
)
async def get_properties(response: Response):
    try:
        logger.info("Properties API called")  # API 호출 시작
        
        # 캐시 방지를 위한 헤더 설정
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        # CSV 파일 경로 변경
        csv_path = Path(__file__).parents[1] / 'data' / 'california_properties.csv'
        logger.info(f"CSV path: {csv_path}")
        logger.info(f"CSV exists: {csv_path.exists()}")  # 파일 존재 여부
        
        if not csv_path.exists():
            logger.error(f"CSV file not found at: {csv_path}")
            raise HTTPException(status_code=404, detail="Data file not found")

        # CSV 파일 읽기
        df = pd.read_csv(csv_path)
        logger.info(f"CSV loaded with {len(df)} rows")  # 로드된 행 수
        logger.info(f"CSV columns: {df.columns.tolist()}")  # 컬럼 목록
        logger.info(f"First row: {df.iloc[0].to_dict()}")  # 첫 번째 행
        
        # 데이터 변환
        properties = []
        for _, row in df.iterrows():
            try:
                property_data = {
                    "id": int(row['RegionID']),
                    "region_id": int(row['RegionID']),
                    "region_name": str(row['City']),
                    "city": str(row['City']),
                    "state": str(row['State']),
                    "metro": f"{row['City']} Metro",
                    "county_name": f"{row['City']} County",
                    "price": float(row['price']),
                    "latitude": float(row['latitude']),
                    "longitude": float(row['longitude']),
                    "zipcode": str(row['zipcode'])
                }
                logger.info(f"Processed property: {property_data}")  # 각 속성 데이터 로깅
                properties.append(property_data)
            except Exception as e:
                logger.error(f"Error processing row: {e}, Row data: {row}")
                continue
        
        logger.info(f"Returning {len(properties)} properties")  # 반환할 속성 수
        return {"properties": properties}
        
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 

@router.get("/api/properties/{property_id}",
    response_model=PropertyResponse,
    summary="Get property by ID",
    description="Retrieves detailed information about a specific property",
    responses={
        200: {
            "description": "Property details",
            "content": {
                "application/json": {
                    "example": {
                        "id": "prop123",
                        "address": "123 Main St",
                        "price": 500000,
                        "bedrooms": 3,
                        "bathrooms": 2,
                        "details": {
                            "square_feet": 2000,
                            "year_built": 2020
                        }
                    }
                }
            }
        },
        404: {"description": "Property not found"}
    }
)
async def get_property_by_id(property_id: str):
    try:
        # CSV 파일 경로
        csv_path = Path(__file__).parents[1] / 'data' / 'california_properties.csv'
        
        if not csv_path.exists():
            raise HTTPException(status_code=404, detail="Data file not found")

        # CSV 파일 읽기
        df = pd.read_csv(csv_path)
        
        # property_id로 속성 찾기
        property_row = df[df['RegionID'] == int(property_id)]
        
        if property_row.empty:
            raise HTTPException(status_code=404, detail="Property not found")
            
        row = property_row.iloc[0]
        
        return {
            "id": str(row['RegionID']),
            "region_id": int(row['RegionID']),
            "region_name": str(row['City']),
            "city": str(row['City']),
            "state": str(row['State']),
            "metro": f"{row['City']} Metro",
            "county_name": f"{row['City']} County",
            "price": float(row['price']),
            "latitude": float(row['latitude']),
            "longitude": float(row['longitude']),
            "zipcode": str(row['zipcode'])
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid property ID")
    except Exception as e:
        logger.error(f"Error getting property: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))