# 자주 쓰는 간단한 유틸 함수
import pandas as pd
import numpy as np

def df_to_dict_replace_nan(df: pd.DataFrame) -> list[dict]:
    # NaN → None으로 변환
    return df.replace({np.nan: None}).to_dict(orient="records")

import json
from bson import json_util
from pydantic import BaseModel

def pretty_print(obj):
    if isinstance(obj, BaseModel):
        # Pydantic 모델이면 dict로 변환
        data = obj.model_dump(by_alias=True)
    elif isinstance(obj, list) and all(isinstance(o, BaseModel) for o in obj):
        # 리스트 안에 BaseModel만 있다면 변환
        data = [o.model_dump(by_alias=True) for o in obj]
    else:
        # 일반 dict나 기타 객체
        data = obj

    print(json.dumps(data, indent=2, ensure_ascii=False, default=json_util.default))