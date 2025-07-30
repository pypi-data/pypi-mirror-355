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

import io
import contextlib

def _dispatch(method: str, args: list, kwargs: dict) -> dict:
    if not hasattr(lumerpy, method):
        return {"error": f"method '{method}' not found in lumerpy"}

    fn = getattr(lumerpy, method)
    if not callable(fn):
        return {"error": f"attribute '{method}' exists but is not callable"}

    try:
        sig = inspect.signature(fn)
        bound = sig.bind_partial(*args, **kwargs)
        bound.apply_defaults()

        # ➜ 捕获 print 的输出
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            result = fn(*bound.args, **bound.kwargs)

        captured = buf.getvalue().strip()

        # 决定最终 result
        if result is not None:
            payload = result
        elif captured:
            payload = captured
        else:
            payload = None

        # 序列化安全处理
        try:
            json.dumps(payload)
            return {"result": payload}
        except TypeError:
            return {"result": repr(payload)}

    except Exception as exc:
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
