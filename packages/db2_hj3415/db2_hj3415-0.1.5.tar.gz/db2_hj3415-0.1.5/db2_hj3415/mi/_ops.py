from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from pymongo import UpdateOne
import pandas as pd

from db2_hj3415.mi import DB_NAME, DATE_FORMAT
from db2_hj3415.common.db_ops import get_collection

from utils_hj3415 import setup_logger

mylogger = setup_logger(__name__, 'WARNING')


async def _save_one_collection(collection_name: str, doc: dict, client: AsyncIOMotorClient):
    """단일 컬렉션에 대해 날짜 기준으로 문서 저장."""
    try:
        collection = get_collection(client, DB_NAME, collection_name)
        date_str = doc.get("날짜")
        if not date_str:
            print(f"{collection_name}: 날짜 없음, 저장 건너뜀")
            return

        date_obj = datetime.strptime(date_str, DATE_FORMAT)
        doc["날짜"] = date_obj
        mylogger.debug(f"{collection_name} - 원본 날짜 문자열: {date_str}")

        await collection.create_index("날짜", unique=True)

        result = await collection.update_one(
            {"날짜": date_obj},
            {"$set": doc},
            upsert=True
        )

        status = "삽입" if result.upserted_id else "업데이트"
        print(f"{collection_name}: {status}")

    except Exception as e:
        print(f"{collection_name}: 오류 - {e}")


async def save(data: dict[str, dict], client: AsyncIOMotorClient):
    '''
    전체 mi collection 데이터를 전달받아 저장하는 함수
    '''
    for collection_name, doc in data.items():
        await _save_one_collection(collection_name, doc, client)


async def find(col: str, date_str: str, client: AsyncIOMotorClient):
    collection = get_collection(client, DB_NAME, col)
    date_obj = datetime.strptime(date_str, DATE_FORMAT)
    doc = await collection.find_one({"날짜": date_obj})
    mylogger.debug(f"{col} 날짜 타입 확인:", doc["날짜"], repr(doc["날짜"]))
    if doc:
        print(f"조회 결과 ({col}): {doc}")
    else:
        print(f"{col} 컬렉션에 {date_str} 날짜 데이터 없음")


async def delete(col: str, date_str: str, client: AsyncIOMotorClient):
    collection = get_collection(client, DB_NAME, col)
    date_obj = datetime.strptime(date_str, DATE_FORMAT)
    result = await collection.delete_one({"날짜": date_obj})
    if result.deleted_count > 0:
        print(f"{col}: {date_str} 데이터 삭제 완료")
    else:
        print(f"{col}: 삭제할 데이터 없음")


async def _save_market_history_type1(df: pd.DataFrame, market: str, numeric_columns: list | None, client: AsyncIOMotorClient):
    if df.empty:
        print("빈 데이터프레임입니다.")
        return {"inserted": 0, "updated": 0}

    db = client[DB_NAME]
    collection = db[market]

    # 컬럼 정리
    df.columns = df.columns.str.strip()

    # 날짜 파싱
    try:
        df["날짜"] = pd.to_datetime(df["날짜"], format=DATE_FORMAT, utc=True)
    except Exception as e:
        print(f"날짜 파싱 실패: {e}")
        return {"inserted": 0, "updated": 0}

    # 숫자형 변환
    if numeric_columns:
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

    # dict 변환
    records = df.to_dict(orient="records")

    # 인덱스 (1회만)
    await collection.create_index("날짜", unique=True)

    # upsert 준비
    operations = []
    for r in records:
        if "날짜" not in r:
            print("날짜 필드 없음 - 건너뜀:", r)
            continue
        operations.append(UpdateOne({"날짜": r["날짜"]}, {"$set": r}, upsert=True))

    # 실행
    if operations:
        result = await collection.bulk_write(operations)
        print(f"{market}: upsert 완료 - 삽입 {result.upserted_count}, 수정 {result.modified_count}")
        return {"inserted": result.upserted_count, "updated": result.modified_count}
    else:
        print("실행할 작업이 없습니다.")
        return {"inserted": 0, "updated": 0}

