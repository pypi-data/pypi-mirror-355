from deepdiff import DeepDiff
from pymongo import ASCENDING, DESCENDING
from motor.motor_asyncio import AsyncIOMotorClient
import pprint
import pandas as pd
import json
from db2_hj3415.nfs import DB_NAME
from db2_hj3415.common.db_ops import get_collection
from datetime import datetime, timezone

from utils_hj3415 import setup_logger

mylogger = setup_logger(__name__, 'WARNING')


async def _compare_and_log_diff(code: str, new_doc: dict, latest_doc: dict | None, client: AsyncIOMotorClient) -> bool:
    """
    최신 문서와 새 문서를 비교하여 변경 사항이 있는 경우만 로그에 기록하고 True를 반환합니다.

    - "_id"와 "날짜" 필드는 비교 대상에서 제외합니다.
    - 변경된 항목이 있으면 MongoDB의 "change_log" 컬렉션에 차이(diff)를 기록합니다.
    - 변경 사항이 없으면 저장하지 않고 False를 반환합니다.

    Parameters:
        code (str): 비교 대상이 되는 종목 코드
        new_doc (dict): 새로 생성된 문서
        latest_doc (dict | None): 기존의 최신 문서 (없을 수 있음)
        client (AsyncIOMotorClient): 몽고 클라이언트

    Returns:
        bool: 변경 사항이 있으면 True, 없으면 False
    """
    if not latest_doc:
        return True

    latest_doc.pop("_id", None)
    latest_doc.pop("날짜", None)
    new_copy = dict(new_doc)
    new_copy.pop("날짜", None)

    diff = DeepDiff(latest_doc, new_copy, ignore_order=True)
    if not diff:
        print(f"{code} 기존 문서와 동일 - 저장하지 않음")
        return False

    print("변경된 항목:")
    for change_type, changes in diff.items():
        print(f"- {change_type}:")
        for path, value in changes.items():
            print(f"  {path}: {value}")

    await client[DB_NAME]["change_log"].insert_one({
        "코드": code,
        "변경시각": datetime.now(timezone.utc),
        "변경내용": json.loads(diff.to_json())
    })

    return True


def _prepare_c10346_document(code: str, data: dict[str, pd.DataFrame]) -> dict:
    """
    종목 코드와 여러 페이지의 DataFrame 데이터를 바탕으로 MongoDB에 저장할 문서(dict)를 생성합니다.

    각 DataFrame은 null 값을 None으로 변환한 후, 레코드(행) 단위의 딕셔너리 리스트로 변환됩니다.
    생성된 문서에는 '코드', '날짜', 그리고 각 페이지 이름을 키로 하는 데이터가 포함됩니다.

    Args:
        code (str): 종목 코드 (6자리 문자열).
        data (dict[str, pd.DataFrame]): 페이지 이름을 키로 하고, 해당 페이지의 데이터를 담은 DataFrame을 값으로 가지는 딕셔너리.

    Returns:
        dict: MongoDB에 저장 가능한 형식의 문서. 예: {
            "코드": "005930",
            "날짜": <datetime>,
            "재무상태표y": <DataFrame>,
            "손익계산서y": <DataFrame>,
            ...
        }
    """
    now = datetime.now(timezone.utc)
    document = {"코드": code, "날짜": now}
    for page, df in data.items():
        if isinstance(df, pd.DataFrame):
            document[page] = df.where(pd.notnull(df), None).to_dict(orient="records")
    return document


async def save(col: str, code: str, data: dict[str, pd.DataFrame], client: AsyncIOMotorClient) -> dict:
    collection = get_collection(client, DB_NAME, col)

    await collection.create_index([("코드", ASCENDING), ("날짜", ASCENDING)], unique=True)

    document = _prepare_c10346_document(code, data)
    latest_doc = await collection.find_one({"코드": code}, sort=[("날짜", DESCENDING)])

    need_save = await _compare_and_log_diff(code, document, latest_doc, client)
    if not need_save:
        return {"status": "unchanged"}

    result = await collection.insert_one(document)
    print(f"삽입됨:  {DB_NAME}.{collection.name} / {code} (id={result.inserted_id})")
    del_result = await collection.delete_many({
        "_id": {"$in": [
            doc["_id"] for doc in await collection.find({"코드": code}).sort("날짜", DESCENDING).skip(2).to_list(length=None)
        ]}
    })
    print(f"삭제된 이전 문서 수: {del_result.deleted_count}")

    return {"status": "inserted", "id": str(result.inserted_id)}


async def save_many(col: str, many_data: dict[str, dict[str, pd.DataFrame]], client: AsyncIOMotorClient) -> list[dict]:
    collection = get_collection(client, DB_NAME, col)
    await collection.create_index([("코드", ASCENDING), ("날짜", ASCENDING)], unique=True)

    results = []

    for code, data in many_data.items():
        document = _prepare_c10346_document(code, data)
        latest_doc = await collection.find_one({"코드": code}, sort=[("날짜", DESCENDING)])
        need_save = await _compare_and_log_diff(code, document, latest_doc, client)

        if not need_save:
            results.append({"code": code, "status": "unchanged"})
            continue

        result = await collection.insert_one(document)
        await collection.delete_many({
            "_id": {"$in": [
                doc["_id"] for doc in await collection.find({"코드": code}).sort("날짜", DESCENDING).skip(2).to_list(length=None)
            ]}
        })

        results.append({"code": code, "status": "inserted", "id": str(result.inserted_id)})

    pprint.pprint(results)
    return results


async def get_latest(col: str, code: str, page: str, client: AsyncIOMotorClient) -> pd.DataFrame | None:
    collection = get_collection(client, DB_NAME, col)

    # 최신 날짜 기준으로 정렬하여 1건만 조회
    latest_doc = await collection.find_one(
        {"코드": code},
        sort=[("날짜", DESCENDING)]
    )

    if not latest_doc or page not in latest_doc:
        print(f"문서 없음 또는 '{page}' 항목 없음")
        return None

        # records → DataFrame
    records = latest_doc[page]
    df = pd.DataFrame(records)
    return df


async def has_doc_changed(col: str, code: str, client: AsyncIOMotorClient) -> bool:
    """
    MongoDB에서 특정 컬렉션과 종목 코드에 대해 최신 두 개의 문서를 비교하여 변경 여부를 확인합니다.

    비교 대상 문서가 두 개 미만이면 True를 반환하여 새 문서로 간주합니다.
    비교는 `_id`, `날짜` 필드를 제외하고 수행하며, 변경 내용이 있을 경우 change_log에 기록됩니다.

    Args:
        col (str): 컬렉션 이름 (예: 'c103' 'c104', 'c106'등).
        code (str): 종목 코드 (6자리 문자열).
        client (AsyncIOMotorClient): MongoDB 비동기 클라이언트 인스턴스.

    Returns:
        bool: 문서가 변경되었는지 여부. True면 변경됨 또는 비교 불가 상태.
    """
    collection = get_collection(client, DB_NAME, col)

    # 최신 문서 2개 조회 (내림차순)
    docs = await collection.find({"코드": code}).sort("날짜", DESCENDING).limit(2).to_list(length=2)

    if len(docs) < 2:
        print(f"{code} 문서가 1개 이하임 - 비교 불가")
        return True  # 비교할 게 없으면 새로 저장해야 하므로 True

    new_doc, latest_doc = docs[0], docs[1]

    new_doc.pop("_id", None)
    new_doc.pop("날짜", None)
    latest_doc.pop("_id", None)
    latest_doc.pop("날짜", None)

    mylogger.debug(new_doc)
    mylogger.debug(latest_doc)

    # 비교 함수 호출
    return await _compare_and_log_diff(code, new_doc, latest_doc, client)



