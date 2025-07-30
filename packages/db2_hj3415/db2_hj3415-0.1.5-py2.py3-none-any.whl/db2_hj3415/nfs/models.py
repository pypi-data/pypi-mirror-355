from pydantic import BaseModel, Field, field_serializer, ConfigDict, field_validator
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

class 항목값y(BaseModel):
    항목: str
    전년대비: float | None
    전년대비_1: float | None = Field(default=None, alias="전년대비 1")

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow"
    )

class 항목값q(BaseModel):
    항목: str
    전분기대비: float | None

    model_config = ConfigDict(extra="allow")


class C103(BaseModel):
    id: str | None = Field(alias="_id")
    코드: str
    날짜: datetime
    손익계산서q: list[항목값q]
    손익계산서y: list[항목값y]
    재무상태표q: list[항목값q]
    재무상태표y: list[항목값y]
    현금흐름표q: list[항목값q]
    현금흐름표y: list[항목값y]

    @field_serializer("날짜")
    def serialize_date(self, v: datetime) -> str:
        return v.isoformat()

    model_config = ConfigDict(populate_by_name=True)


class C104(BaseModel):
    id: str | None = Field(alias="_id")
    코드: str
    날짜: datetime

    수익성y: list[항목값y] | None = None
    성장성y: list[항목값y] | None = None
    안정성y: list[항목값y] | None = None
    활동성y: list[항목값y] | None = None
    가치분석y: list[항목값y] | None = None

    수익성q: list[항목값q] | None = None
    성장성q: list[항목값q] | None = None
    안정성q: list[항목값q] | None = None
    활동성q: list[항목값q] | None = None
    가치분석q: list[항목값q] | None = None

    @field_serializer("날짜")
    def serialize_date(self, v: datetime) -> str:
        return v.isoformat()

    model_config = ConfigDict(populate_by_name=True)


class 기업데이터(BaseModel):
    항목: str
    항목2: str

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow"
    )

class C106(BaseModel):
    id: str | None = Field(alias="_id")
    코드: str
    날짜: datetime

    q: list[기업데이터]
    y: list[기업데이터]

    @field_serializer("날짜")
    def serialize_date(self, v: datetime) -> str:
        return v.isoformat()

    model_config = ConfigDict(populate_by_name=True)


class C108(BaseModel):
    id: str | None = Field(alias="_id")
    코드: str
    날짜: datetime

    제목: str | None = None
    내용: list[str] | None = None
    목표가: int | None = None
    분량: str | None = None
    작성자: str | None = None
    제공처: str | None = None
    투자의견: str | None = None

    # 날짜 필드 ISO 직렬화
    @field_serializer("날짜")
    def serialize_date(self, v: datetime) -> str:
        return v.isoformat()

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True
    )

class Dart(BaseModel):
    id: str | None = Field(alias="_id")
    코드: str = Field(default=None, alias="stock_code") # 종목 코드 (6자리)
    날짜: datetime = Field(default=None, alias="rcept_dt") # 접수 일자 (YYYYMMDD)

    corp_cls: str  # 기업 구분 (예: 'K', 'Y', 'N')
    corp_code: str  # 고유 회사 코드 (8자리)
    corp_name: str  # 회사 이름
    flr_nm: str  # 제출자 (예: '코스닥시장본부')
    rcept_no: str  # 접수 번호
    report_nm: str  # 보고서 이름
    rm: str  # 비고 (예: '코')

    @field_validator("날짜", mode="before")
    @classmethod
    def parse_date(cls, v: str) -> datetime:
        """YYYYMMDD 형식의 문자열을 datetime 객체로 변환"""
        return datetime.strptime(v, "%Y%m%d")

    # 날짜 필드 ISO 직렬화
    @field_serializer("날짜")
    def serialize_date(self, v: datetime) -> str:
        return v.isoformat()

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True
    )