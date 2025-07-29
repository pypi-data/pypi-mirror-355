# python toolkit


import rich
from wujing.llm.oai_client import llm_call
from functools import partial


to_llm_qwen = partial(
    llm_call,
    model="Qwen2.5-72B-Instruct",
    max_tokens=8 * 1024,
    api_key="sk-xylx1.t!@#",
    api_base="http://127.0.0.1:8001/v1",
    cache_enabled=False,
)


def send_req(messages, llm_fn=to_llm_qwen):
    rst = llm_fn(
        messages=messages,
    )
    return rst


llm_rst = send_req(
    messages=[
        {
            "role": "user",
            "content": "who are you",
        },
    ]
)

rich.print(llm_rst)