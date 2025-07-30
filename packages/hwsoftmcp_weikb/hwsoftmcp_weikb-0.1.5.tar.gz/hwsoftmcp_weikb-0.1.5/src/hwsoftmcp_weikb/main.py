
import httpx
from mcp.server.fastmcp import FastMCP
import os
import uuid
mcp = FastMCP("Demo")

host = os.getenv("server_url","http://192.168.3.23:30012")

# @mcp.tool()
# async def chat_knowledge_base(question: str) -> str:
#     """输入问题，由知识库进行回答

#     Args:
#         question: 检索内容

#     Returns:
#         str: 检索结果
#     """
#     url = f"{host}/api/v1/chat/completions"
    
#     stream = False
    
#     appType = "knowledge"
#     chatId = str(uuid.uuid4())
#     # env 参数
#     systemCode = os.getenv("systemCode")
#     kbIds = os.getenv("kbIds")
#     if kbIds is not None:
#         if kbIds == "":
#             kbIds = None
#         else:
#             kbIds = kbIds.split(",")
#     fieldIds = os.getenv("fieldIds")
#     if fieldIds is not None:
#         if fieldIds == "":
#             fieldIds = None
#         else:
#             fieldIds = fieldIds.split(",")
#     knowledge = os.getenv("knowledge")
#     model = os.getenv("model","Qwen3-30B-A3B")
#     replyOrigin = os.getenv("replyOrigin",1)
   
#     data = {
#         "question": question,
#         "knowledge": knowledge,
#         "stream": stream,
#         "model": model,
#         "appType": appType,
#         "chatId": chatId,
#         "systemCode": systemCode,
#         "kbIds": kbIds,
#         "fieldIds": fieldIds,
#         "replyOrigin": replyOrigin
#     }
#     async with httpx.AsyncClient(timeout=120) as client:
#         response = await client.post(url, json=data)
#         # 解析结果
#         try:
#             result = response.json()
#             content = result["choices"][0]["message"]["content"]
#             return content
#         except Exception as e:
#             return response.text


@mcp.tool()
async def search_knowledge_base(question: str) -> str:
    """输入关键词，查询知识库进行检索，返回检索结果

    Args:
        question: 检索关键词

    Returns:
        str: 检索结果
    """
    url = f"{host}/api/v1/chat/queryKnowledge"
    
    # env 参数
    systemCode = os.getenv("systemCode")
    kbIds = os.getenv("kbIds")
    if kbIds is not None:
        if kbIds == "":
            kbIds = None
        else:
            kbIds = kbIds.split(",")
    fieldIds = os.getenv("fieldIds")
    if fieldIds is not None:
        if fieldIds == "":
            fieldIds = None
        else:
            fieldIds = fieldIds.split(",")
    knowledge = os.getenv("knowledge")
   
    data = {
        "question": question,
        "systemCode": systemCode,
        "fileIds": fieldIds,
        "includeFeatures": False,
        "searchType": "hybrid",  #vector": 向量检索- "text": 全文检索- "hybrid": 混合检索（默认）
        "size": 10,
        "minScore": 0.6,
        "rerank": True,
        "useLLMExtractMeta": True,
        "backgroundKnowledge": knowledge
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, json=data)
        return response.text


def main():
    """Entry point for the MCP Ops Toolkit"""
    mcp.run(transport='stdio')

if __name__ == "__main__":
   import asyncio   
   import os
   os.environ["server_url"] = "http://192.168.3.23:30012"
   os.environ["systemCode"] = "luzhiliang-001"
   os.environ["kbIds"] = ""
   os.environ["fieldIds"] = "doc-2025060050001,doc-2025060050002,doc-2025060050003"
   os.environ["knowledge"] = "1,2,3"
   os.environ["model"] = "Qwen3-30B-A3B"
   ret = asyncio.run(search_knowledge_base("2024年 中国企业 网络攻击 事件"))
   print(ret)