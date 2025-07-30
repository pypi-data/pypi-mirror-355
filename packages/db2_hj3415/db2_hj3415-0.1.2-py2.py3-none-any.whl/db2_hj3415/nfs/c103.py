from motor.motor_asyncio import AsyncIOMotorClient
import pandas as pd

from db2_hj3415.nfs import _c10346
from utils_hj3415 import setup_logger

mylogger = setup_logger(__name__, 'WARNING')

COL_NAME = "c103"


async def save(code: str, data: dict[str, pd.DataFrame], client: AsyncIOMotorClient) -> dict:
    return await _c10346.save(COL_NAME, code, data, client)


async def save_many(many_data: dict[str, dict[str, pd.DataFrame]], client: AsyncIOMotorClient) -> list[dict]:
    return await _c10346.save_many(COL_NAME, many_data, client)


async def get_latest(code: str, page: str, client: AsyncIOMotorClient) -> pd.DataFrame | None:
    return await _c10346.get_latest(COL_NAME, code, page, client)


async def has_doc_changed(code: str, client: AsyncIOMotorClient) -> bool:
    """
    C103 컬렉션에서 종목 코드에 대해 최신 두 개의 문서를 비교하여 변경 여부를 확인합니다.

    비교 대상 문서가 두 개 미만이면 True를 반환하여 새 문서로 간주합니다.
    비교는 `_id`, `날짜` 필드를 제외하고 수행하며, 변경 내용이 있을 경우 change_log에 기록됩니다.

    Args:
        code (str): 종목 코드 (6자리 문자열).
        client (AsyncIOMotorClient): MongoDB 비동기 클라이언트 인스턴스.

    Returns:
        bool: 문서가 변경되었는지 여부. True면 변경됨 또는 비교 불가 상태.
    """
    return await _c10346.has_doc_changed(COL_NAME, code, client)