from fastapi import APIRouter, Response
import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/properties")
async def get_properties(response: Response):
    try:
        # 캐시 방지를 위한 헤더 설정
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        # CSV 파일 경로 (파일 이름 수정)
        csv_path = Path(__file__).parents[1] / "data" / "california_properties.csv"
        logger.info(f"Reading CSV file from: {csv_path}")

        if not csv_path.exists():
            logger.error(f"CSV file not found at: {csv_path}")
            return {"properties": []}

        # CSV 파일 읽기 (처음 5개 행만)
        df = pd.read_csv(csv_path).head(5)
        logger.info(f"Loaded {len(df)} properties from CSV")

        # 필요한 형식으로 데이터 변환
        properties = []
        for index, row in df.iterrows():
            try:
                lat = float(row["latitude"])
                lng = float(row["longitude"])

                property_data = {
                    "id": int(row["RegionID"]),
                    "position": {"lat": lat, "lng": lng},
                    "title": f"Property in {row['City']}",
                    "price": f"${int(float(row['price'])):,}",
                    "address": f"{row['City']}, {row['State']}, {row['zipcode']}",
                    "city": row["City"],
                    "state": row["State"],
                    "zipcode": str(row["zipcode"]),
                }
                properties.append(property_data)
                logger.info(f"Processed property {index + 1}: {property_data}")

            except (ValueError, KeyError) as e:
                logger.error(f"Error processing row {index}: {e}")
                continue

        logger.info(f"Successfully processed {len(properties)} properties")
        return {"properties": properties}

    except Exception as e:
        logger.error(f"Failed to process properties: {e}")
        raise
