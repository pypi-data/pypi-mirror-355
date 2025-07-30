# !/usr/bin/env python3
from typing import Dict, Any
from mcp.server import FastMCP
from .pandas_sandbox import PandasSandbox

# 创建全局沙盒实例
sandbox = PandasSandbox()

mcp = FastMCP("mcp-excel-tools")


@mcp.tool()
async def load_and_exec(file: str, code: str) -> Dict[str, Any]:
    # 创建沙盒实例
    sandbox = PandasSandbox()

    # 加载Excel文件
    sandbox.load_excel_file(file)

    # 执行pandas代码
    result = sandbox.execute_code(code)

    return result


def main():
    mcp.run(transport="stdio")


if __name__ == '__main__':
    main()
