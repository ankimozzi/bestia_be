import pandas as pd
from pathlib import Path

def process_california_data():
    # 현재 파일의 디렉토리 경로 가져오기
    current_dir = Path(__file__).parent
    
    # 입력 파일과 출력 파일의 경로 설정
    input_file = current_dir / "data" / "california_top_100.csv"
    output_file = current_dir / "data" / "california_properties.csv"
    
    # Zillow 데이터 읽기
    zillow_data = pd.read_csv(input_file)
    
    # 필요한 컬럼만 선택
    properties_data = zillow_data[[
        'RegionID', 'RegionName', 'City', 'State', 
        'Metro', 'CountyName'
    ]].copy()
    
    # RegionName을 zipcode로 컬럼명 변경
    properties_data = properties_data.rename(columns={'RegionName': 'zipcode'})
    
    # 가장 최근 가격 데이터 컬럼 찾기
    price_columns = [col for col in zillow_data.columns if col.startswith('20')]
    latest_price_column = sorted(price_columns)[-1]
    
    # 최근 가격 데이터 추가
    properties_data['price'] = zillow_data[latest_price_column]
    
    # 위치 정보 생성 (캘리포니아 주요 도시 위치 기반)
    city_locations = {
        'Los Angeles': {'lat': 34.0522, 'lng': -118.2437},
        'San Diego': {'lat': 32.7157, 'lng': -117.1611},
        'San Jose': {'lat': 37.3382, 'lng': -121.8863},
        'San Francisco': {'lat': 37.7749, 'lng': -122.4194},
        'Sacramento': {'lat': 38.5816, 'lng': -121.4944},
        'Oakland': {'lat': 37.8044, 'lng': -122.2712},
        'Bakersfield': {'lat': 35.3733, 'lng': -119.0187},
        'Fresno': {'lat': 36.7378, 'lng': -119.7871},
        'Long Beach': {'lat': 33.7701, 'lng': -118.1937},
        'Santa Ana': {'lat': 33.7455, 'lng': -117.8677}
    }
    
    def get_location(row):
        city = row['City']
        if city in city_locations:
            base_location = city_locations[city]
            # 같은 도시 내에서 약간의 변동을 주어 마커가 겹치지 않도록 함
            lat_offset = (row['RegionID'] % 100) * 0.0001  # 오프셋 값을 줄임
            lng_offset = (row['RegionID'] % 100) * 0.0001  # 오프셋 값을 줄임
            return pd.Series({
                'latitude': base_location['lat'] + lat_offset,
                'longitude': base_location['lng'] + lng_offset
            })
        else:
            # 알 수 없는 도시는 NaN 반환
            return pd.Series({'latitude': None, 'longitude': None})
    
    # 위치 정보 추가
    properties_data[['latitude', 'longitude']] = properties_data.apply(get_location, axis=1)
    
    # NaN 값이 있는 행 제거
    properties_data = properties_data.dropna(subset=['latitude', 'longitude'])
    
    # 컬럼 순서 재배열
    properties_data = properties_data[[
        'RegionID', 'zipcode', 'City', 'State', 'price', 'latitude', 'longitude'
    ]]
    
    # CSV 파일로 저장
    properties_data.to_csv(output_file, index=False)
    print(f"Processed {len(properties_data)} California properties")
    print(f"Data saved to {output_file}")

if __name__ == "__main__":
    process_california_data() 