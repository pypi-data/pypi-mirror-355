from rich import print as rprint

from wujing.llm.oai_client import llm_call


def test_llm_call(api_key, api_base, model, messages, response_model, context, guided_backend):
    resp = llm_call(
        api_key=api_key,
        api_base=api_base,
        model=model,
        messages=messages,
        response_model=response_model,
        context=context,
        guided_backend=guided_backend,
        cache_enabled=False,
    )

    rprint(f"{type(resp)=}, {resp=}")
