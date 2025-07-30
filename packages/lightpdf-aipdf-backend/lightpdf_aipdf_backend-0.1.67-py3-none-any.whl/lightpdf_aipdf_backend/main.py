import os
import asyncio
import sys
import uvicorn
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
import argparse
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from .state import set_mcp_session, get_openai_client
from .app import app
from .tools import get_tools

async def main():
    """应用主入口"""
    # 打印版本号
    try:
        import importlib.metadata
        version = importlib.metadata.version("lightpdf-aipdf-backend")
        print(f"LightPDF AI-PDF Backend v{version}", file=sys.stderr)
    except Exception as e:
        print("LightPDF AI-PDF Backend (版本信息获取失败)", file=sys.stderr)
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="LightPDF AI-PDF Backend服务")
    parser.add_argument("-p", "--port", type=int, default=3300, help="指定后端服务监听端口，默认3300")
    parser.add_argument("-s", "--sse", action="store_true", default=False, help="使用SSE方式连接MCP服务器，而非启动内嵌的MCP服务器")
    parser.add_argument("-m", "--mcp-port", type=int, default=3301, help="指定MCP服务器的端口号，仅在SSE模式下有效，默认3301")
    args = parser.parse_args()
    
    # 更新全局变量
    port = args.port
    use_sse = args.sse
    mcp_port = args.mcp_port
    
    # 初始化 OpenAI 客户端 - 只需调用get_openai_client即可
    get_openai_client()
    
    if use_sse:
        # 使用SSE连接MCP服务器
        mcp_url = f"http://127.0.0.1:{mcp_port}/sse/"
        print(f"使用SSE连接MCP服务器: {mcp_url}", file=sys.stderr)
        try:
            # 启动 MCP 会话 (SSE方式)
            async with sse_client(mcp_url) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    # 设置全局 MCP 会话
                    set_mcp_session(session)

                    print(f"正在启动服务，监听端口: {port}")
                    # 启动 FastAPI 服务器
                    config = uvicorn.Config(app, port=port)
                    server = uvicorn.Server(config)
                    await server.serve()
        except Exception as e:
            print(f"SSE连接MCP服务器失败: {e}", file=sys.stderr)
            print("请确保MCP服务器已经以SSE模式启动", file=sys.stderr)
            sys.exit(1)
    else:
        # 准备 MCP 服务参数 (STDIO方式)
        server_params = StdioServerParameters(
            command="uvx",
            args=["-n", "../../mcp_server/dist/lightpdf_aipdf_mcp-0.0.1-py3-none-any.whl"] if os.getenv("DEBUG") else ["lightpdf-aipdf-mcp@latest"],
            env={
                **dict(filter(lambda x: x[1] is not None, {
                    "API_ENDPOINT": os.getenv("API_ENDPOINT"),
                    "API_KEY": os.getenv("API_KEY"),
                    "DEBUG": os.getenv("DEBUG"),
                }.items()))
            }
        )
        
        # 启动 MCP 会话 (STDIO方式)
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                # 设置全局 MCP 会话
                set_mcp_session(session)

                print(f"正在启动服务，监听端口: {port}")
                # 启动 FastAPI 服务器
                config = uvicorn.Config(app, host="0.0.0.0", port=port)
                server = uvicorn.Server(config)
                await server.serve()

# 确保与原始 main 函数相同
if __name__ == "__main__":
    # 启动服务
    asyncio.run(main()) 