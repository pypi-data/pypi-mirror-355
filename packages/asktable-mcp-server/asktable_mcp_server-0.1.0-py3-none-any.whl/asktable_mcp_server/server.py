from fastmcp import FastMCP, Image,Context
import io
from asktable import Asktable
from asktable_mcp_server.tools import get_asktable_data, get_asktable_sql
from fastmcp.server.auth import BearerAuthProvider
from fastmcp.server.auth.providers.bearer import RSAKeyPair
import os
import asyncio

mcp = FastMCP(name="Asktable server")

@mcp.tool()
async def get_sql(query: str) -> str:
    """
    根据用户查询生成对应的SQL语句
    不需要指定数据源ID，该函数已在内部指定了数据源ID，直接发起请求即可
    该函数将用户的查询转换为SQL语句，仅返回SQL文本，不执行查询。
    
    :param query: 用户的查询内容
                  示例：
                  - "我需要查询昨天的订单总金额的sql"
                  - "我要找出销售额前10的产品的sql"
                  - "统计每个部门的员工数量的sql"
    :return: 生成的SQL语句字符串
    
    使用场景：
        - 需要查看生成的SQL语句
        - 需要手动修改或优化SQL
        - 仅需要SQL文本而不需要执行结果
    """
    # ds_id = datasource_id or default_datasource_id
    message = await get_asktable_sql(api_key = os.getenv('api_key'), datasource_id= os.getenv('datasource_id') ,question = query)
    return message


@mcp.tool()
async def get_datasouce_data(query: str) -> str:
    """
    根据用户的问题，直接返回数据结果
    不需要指定数据源ID，该函数已在内部指定了数据源ID，直接发起请求即可
    该函数执行用户的查询并返回实际的数据结果或答案，而不是SQL语句。
    
    :param query: 用户的查询内容
                  示例：
                  - "昨天的订单总金额是多少"
                  - "列出销售额前10的产品"
                  - "每个部门有多少员工"
    :return: 查询的实际结果
    
    使用场景：
        - 需要直接获取查询答案
        - 需要查看实际数据结果
        - 不关心SQL细节，只要最终答案
    """
    # ds_id = datasource_id or default_datasource_id
    message = await get_asktable_data(api_key = os.getenv('api_key'), datasource_id= os.getenv('datasource_id') ,question = query)
    return message

def main():
    mcp.run()

if __name__ == "__main__":
    main()
