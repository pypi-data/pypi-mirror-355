import time
from fastmcp import FastMCP
from typing import Dict, Any, List

from src.tools.keep import Keep
from src.tools.new_open import NewOpen

# Create an MCP server
mcp = FastMCP(
    name="tdsaas-mcp",
    instructions="Tongda’s SaaS product displays operational data via the Model Context Protocol (MCP)",
)

@mcp.tool()
def get_new_open_user_list(days: int) -> List[Dict[str, Any]]:
    """获取新开通的客户列表

    Args:
        days: 天数，从今天开始往前推days天，最大支持60天，最小支持1天

    Returns:
        List[Dict[str, Any]]: 新开通的客户列表 - [
            "total_number": 总数量,
            "trial_info": {
                "trial_number": 试用数量,
                "trial_list": [{
                    "name": 客户名称
                }]
            },
            "paid_info": {
                "paid_number": 付费数量,
                "paid_list": [{
                    "name": 客户名称,
                    "sku_name": 所购买的商品名称,
                    "create_at": 开通时间,
                    "expired_at": 到期时间
                }]
            }
        ]
    """
    if days > 60 or days < 1:
        raise ValueError("days must be between 1 and 60")

    new_open = NewOpen()
    return new_open.get_new_open_user_list(days)

@mcp.tool()
def get_all_keep_user_list() -> List[Dict[str, Any]]:
    """获取所有续费客户列表

    Returns:
        List[Dict[str, Any]]: 续费客户列表 - [
            "total_number": 总数量,
            "keep_info": {
                "keep_number": 续费数量,
                "keep_list": [{
                    "name": 续费客户名称,
                    "sku_name": 所购买的商品名称,
                    "create_at": 开通时间,
                    "expired_at": 到期时间
                }]
            },
            "unused_keep_info": {
                "unused_keep_number": 2025年1月以后未再产生数据的续费客户（不活跃客户）数量，需警惕客户不再续签风险
                "unused_keep_list": [{
                    "name": 不活跃客户名称,
                    "sku_name": 所购买的商品名称,
                    "create_at": 开通时间,
                    "expired_at": 到期时间,
                    "count_run_id": 2025年1月以后产生数据的数量
                }]
            ]
        ]
    """
    keep = Keep()
    return keep.get_all_keep_user_list()

@mcp.tool()
def get_to_be_renew_user_list(days: int) -> List[Dict[str, Any]]:
    """获取待续费的客户列表

    Args:
        days: 天数，从今天开始往前推days天，最大支持60天，最小支持1天

    Returns:
        List[Dict[str, Any]]: 待续费的客户列表 - [
            "total_number": 总数量,
            "to_be_renew_list": [
                {
                    "name": 客户名称,
                    "sku_name": 所购买的商品名称,
                    "create_at": 开通时间,
                    "expired_at": 到期时间,
                    "is_active": 是否活跃
                }
            ]
        ]
    """
    if days > 60 or days < 1:
        raise ValueError("days must be between 1 and 60")

    keep = Keep()
    return keep.get_to_be_renew_user_list(days)

@mcp.tool()
def get_user_detail(corp_name: str) -> List[Dict[str, Any]]:
    """获取客户详情，包括客户名称、所购买的商品名称、到期时间、近30天数据使用量、上个30天数据使用量、数据使用量变化率

    Args:
        corp_name: 客户名称

    Returns:
        List[Dict[str, Any]]: 客户信息 - [
            {
                "corp_name": 客户全称,
                "sku_name": 所购买的商品名称,
                "create_at": 开通时间,
                "expired_at": 到期时间,
                "nearly30_days_data_usage": 近30天数据使用量,
                "last30_days_data_usage": 上一个30天数据使用量,
                "data_usage_change_rate": 数据使用量变化率,
            }
        ]
    """
    keep = Keep()
    return keep.get_user_detail(corp_name)

@mcp.tool()
def get_current_time() -> str:
    """获取当前时间
    """
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def main():
    """Run the MCP server"""
    mcp.run()

if __name__ == "__main__":
    main()