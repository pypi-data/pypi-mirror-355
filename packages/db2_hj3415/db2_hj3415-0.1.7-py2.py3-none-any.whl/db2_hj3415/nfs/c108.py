from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, UpdateOne, DESCENDING
import pandas as pd
from datetime import datetime, timezone, timedelta

from db2_hj3415.nfs import DATE_FORMAT, DB_NAME, C108
from db2_hj3415.common.db_ops import get_collection
from utils_hj3415 import setup_logger

mylogger = setup_logger(__name__, 'WARNING')

COL_NAME = 'c108'


async def save(code: str, data: pd.DataFrame, client: AsyncIOMotorClient) -> dict:
    if data is None or data.empty:
        print("데이터 없음 - 저장 생략")
        return {"status": "unchanged"}

    collection = get_collection(client, DB_NAME, COL_NAME)

    await collection.create_index(
        [("코드", ASCENDING), ("날짜", ASCENDING), ("제목", ASCENDING)],
        unique=True
    )

    # NaN -> None 변환
    df = data.where(pd.notnull(data), None)
    operations = []
    inserted, updated, skipped = 0, 0, 0

    for _, row in df.iterrows():
        try:
            date_str = str(row["날짜"])
            date_obj = datetime.strptime(date_str, DATE_FORMAT).replace(tzinfo=timezone.utc)

            doc = row.to_dict()
            doc["코드"] = code
            doc["날짜"] = date_obj

            filter_ = {"코드": code, "날짜": date_obj, "제목": doc["제목"]}
            operations.append(UpdateOne(filter_, {"$set": doc}, upsert=True))
        except Exception as e:
            print(f"변환 에러 - {row.get('제목', '제목 없음')}: {e}")
            continue

    if operations:
        result = await collection.bulk_write(operations, ordered=False)
        inserted = result.upserted_count
        updated = result.modified_count
        print(f"[{code}] 저장 완료: inserted={inserted}, updated={updated}")
    else:
        print(f"[{code}] 저장할 작업 없음")

    return {"inserted": inserted, "updated": updated}


async def save_many(many_data: dict[str, pd.DataFrame], client: AsyncIOMotorClient) -> dict:
    total_result = {"inserted": 0, "updated": 0, "skipped": 0, "errors": []}

    for code, df in many_data.items():
        if df is None:
            print(f"[{code}] 리포트 없음 - 건너뜀")
            continue

        try:
            result = await save(code, df, client)
            total_result["inserted"] += result.get("inserted", 0)
            total_result["updated"] += result.get("updated", 0)
            total_result["skipped"] += result.get("skipped", 0)
        except Exception as e:
            print(f"[{code}] 저장 실패: {e}")
            total_result["errors"].append({"code": code, "error": str(e)})

    return total_result


async def get_latest(code: str, client: AsyncIOMotorClient, days:int = 30) -> list[C108]:
    """
    최근 N일 이내의 C108 리포트 도큐먼트를 조회합니다.

    Args:
        code (str): 종목 코드 (예: "005930").
        client (AsyncIOMotorClient): 비동기 MongoDB 클라이언트.
        days (int, optional): 현재 시점에서 며칠 전까지의 데이터를 조회할지 설정합니다. 기본값은 30일.

    Returns:
        list[C108]: 조건에 해당하는 C108 도큐먼트 리스트. 일치하는 문서가 없을 경우 빈 리스트를 반환합니다.
    """
    collection = get_collection(client, DB_NAME, COL_NAME)
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)

    cursor = collection.find(
        {
            "코드": code,
            "날짜": {"$gte": cutoff}
        }
    ).sort("날짜", DESCENDING)

    docs = await cursor.to_list(length=None)
    if not docs:
        return []
    else:
        c108s = []
        for doc in docs:
            doc["_id"] = str(doc["_id"])
            c108s.append(C108(**doc))
        return c108s


