# 자주 쓰는 간단한 유틸 함수
import pandas as pd
import numpy as np

def df_to_dict_replace_nan(df: pd.DataFrame) -> list[dict]:
    # NaN → None으로 변환
    return df.replace({np.nan: None}).to_dict(orient="records")