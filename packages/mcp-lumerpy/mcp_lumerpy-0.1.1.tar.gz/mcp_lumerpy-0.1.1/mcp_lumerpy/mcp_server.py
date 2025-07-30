"""
mcp_server.py  ‒  M C P   w r a p p e r   f o r   l u m e r p y
---------------------------------------------------------------
启动方式（Trae / uvx）：
    uvx mcp-lumerpy               ← 会调用 main()

⤷ 交互协议（stdin / stdout / JSON）：
    请求 : {"method": "func_name", "args": [...], "kwargs": {...}}
    响应 : {"result": <repr>}     （成功）
            或
           {"error":  "<msg>"}    （失败）
"""
from __future__ import annotations

import json
import sys
import inspect
import traceback

import lumerpy  # 依赖你的主功能库


def _dispatch(method: str, args: list, kwargs: dict) -> dict:
    """
    尝试在 lumerpy 顶层找到同名可调用对象并执行。
    返回 dict（result / error），供 main() 序列化成 JSON。
    """
    if not hasattr(lumerpy, method):
        return {"error": f"method '{method}' not found in lumerpy"}

    fn = getattr(lumerpy, method)
    if not callable(fn):
        return {"error": f"attribute '{method}' exists but is not callable"}

    # 尝试调用
    try:
        # 支持无 *args / **kwargs 的调用
        sig = inspect.signature(fn)
        bound = sig.bind_partial(*args, **kwargs)  # 会抛 TypeError 如参数不匹配
        bound.apply_defaults()
        result = fn(*bound.args, **bound.kwargs)
        # 尝试让可序列化，若失败就用 repr()
        try:
            json.dumps(result)
            return {"result": result}
        except TypeError:
            return {"result": repr(result)}
    except Exception as exc:  # 捕获全部，返回 error
        tb = traceback.format_exc(limit=2)
        return {"error": f"{exc.__class__.__name__}: {exc}", "traceback": tb}


def main() -> None:
    """
    进程主循环：逐行读取 JSON，请求→调用→回写 JSON。
    Trae/uvx 通过 stdin/stdout 与之通信。
    """
    for line in sys.stdin:                       # 阻塞等待 Trae 输入
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            method: str = req.get("method", "")
            args: list = req.get("args", []) or []
            kwargs: dict = req.get("kwargs", {}) or {}

            resp = _dispatch(method, args, kwargs)
        except Exception as exc:
            resp = {"error": f"Bad request: {exc}"}

        # 回写响应并立即 flush
        sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
