from pydantic import BaseModel, Field, field_serializer, ConfigDict
from datetime import datetime

class C101(BaseModel):
    id: str | None = Field(alias="_id")
    날짜: datetime
    코드: str
    bps: int | None
    eps: int | None
    pbr: float | None
    per: float | None
    개요: str | None
    거래대금: int | None
    거래량: int | None
    발행주식: int | None
    배당수익률: float | None
    베타52주: float | None
    수익률: float | None
    수익률1M: float | None
    수익률1Y: float | None
    수익률3M: float | None
    수익률6M: float | None
    시가총액: int | None
    업종: str | None
    업종per: float | None
    외국인지분율: float | None
    유동비율: float | None
    전일대비: int | None
    종목명: str | None
    주가: int | None
    최고52: int | None
    최저52: int | None

    @field_serializer("날짜")
    def serialize_날짜(self, value: datetime) -> str:
        return value.isoformat()

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
    )

class C103재무항목y(BaseModel):
    항목: str
    전년대비: float | None
    전년대비_1: float | None = Field(default=None, alias="전년대비 1")

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow"
    )

class C103재무항목q(BaseModel):
    항목: str
    전분기대비: float | None

    model_config = ConfigDict(extra="allow")  # 나머지 키들 허용

class C103(BaseModel):
    id: str = Field(alias="_id")
    코드: str
    날짜: datetime
    손익계산서q: list[C103재무항목q]
    손익계산서y: list[C103재무항목y]
    재무상태표q: list[C103재무항목q]
    재무상태표y: list[C103재무항목y]
    현금흐름표q: list[C103재무항목q]
    현금흐름표y: list[C103재무항목y]

    @field_serializer("날짜")
    def serialize_date(self, v: datetime) -> str:
        return v.isoformat()

    model_config = ConfigDict(populate_by_name=True)