from motor.motor_asyncio import AsyncIOMotorClient
from db2_hj3415.nfs import DB_NAME


async def get_all_codes(client: AsyncIOMotorClient) -> list[str]:
    """
    c103, c104, c106 컬렉션에 모두 존재하는 코드의 리스트를 반환함.

    Args:
        client (AsyncIOMotorClient): MongoDB 비동기 클라이언트 객체

    Returns:
        list[str]: c103, c104, c106 컬렉션에 공통으로 존재하는 종목 코드 리스트
    """
    db = client[DB_NAME]

    collections = ['c103', 'c104', 'c106']

    # 첫 컬렉션으로 초기화
    s = set(await db[collections[0]].distinct("코드"))

    for col in collections[1:]:
        codes = await db[col].distinct("코드")
        s &= set(codes)

    return list(s)


async def delete_code_from_all_collections(code: str, client: AsyncIOMotorClient) -> dict[str, int]:
    db = client[DB_NAME]

    collections = ['c101', 'c103', 'c104', 'c106', 'c108']

    deleted_counts = {}

    for col in collections:
        result = await db[col].delete_many({"코드": code})
        deleted_counts[col] = result.deleted_count

    print(f"삭제된 도큐먼트 갯수: {deleted_counts}")
    return deleted_counts

