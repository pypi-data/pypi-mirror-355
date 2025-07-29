import pytest
from rich import print as rprint

from wujing.llm.internal.oai_with_instructor import oai_with_instructor


@pytest.mark.skip()
def test_oai_call(api_key, api_base, model, messages, response_model):
    resp = oai_with_instructor(
        api_key=api_key,
        api_base=api_base,
        model=model,
        messages=messages,
        response_model=response_model,
        context=None,
    )

    rprint(f"{type(resp)=}, {resp=}")
