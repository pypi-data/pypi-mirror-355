from rich import print as rprint
import pytest
from pydantic import BaseModel, ValidationInfo, model_validator
from typing import Self


@pytest.fixture(scope="session")
def api_key():
    return "your_api_key_here"


@pytest.fixture(scope="session")
def api_base():
    return "https://ark.cn-beijing.volces.com/api/v3"


@pytest.fixture(scope="session")
def model():
    return "deepseek-v3-250324"


@pytest.fixture(scope="session")
def messages():
    return [{"role": "user", "content": "Hello, how are you?"}]


class ResponseModel(BaseModel):
    content: str


class ResponseModel2(BaseModel):
    content: str

    @model_validator(mode="after")
    def check_info(self, info: ValidationInfo) -> Self:
        if info.context:
            rprint(f"{info.context=}")
        return self


@pytest.fixture(scope="session")
def context():
    return {"test": "context"}


@pytest.fixture(scope="session", params=[ResponseModel, ResponseModel2])
def response_model(request):
    return request.param


@pytest.fixture(scope="session", params=["instructor", None])
def guided_backend(request):
    yield request.param
