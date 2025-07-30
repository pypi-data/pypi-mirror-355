from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import InsertOne
from db2_hj3415.nfs import Dart, DB_NAME, get_collection

COL_NAME = "dart"

async def save_many(many_data: list[Dart], client: AsyncIOMotorClient) -> dict:
    if not many_data:
        return {"inserted_count": 0, "skipped": 0}

    collection = get_collection(client, DB_NAME, COL_NAME)

    # unique index 보장용 (이미 설정되었는지 확인)
    await collection.create_index("rcept_no", unique=True)

    ops = []
    skipped = 0

    for item in many_data:
        doc = item.model_dump(mode="json", exclude={"id"})  # _id는 제외
        ops.append(InsertOne(doc))

    try:
        result = await collection.bulk_write(ops, ordered=False)
        return {"inserted_count": result.inserted_count, "skipped": skipped}
    except Exception as e:
        return {"error": str(e)}
