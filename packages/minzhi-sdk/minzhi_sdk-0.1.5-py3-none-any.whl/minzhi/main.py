from typing import Any, Dict, List
from loguru import logger
from minzhi import res, invoke, invoke_enum




class AE:
    """AE CLient"""

    def __init__(self, businessId: str, table_name: str):
        self.businessId = businessId
        self.table_name = table_name

    @logger.catch
    def selectPage(self, current: int, pageSize: int)-> Dict[str, Any]:
        """
        分页查询
        Args:
            current: 当前页码
            pageSize: 每页条数
        Returns:
            Dict[str, Any]: 查询结果
        """
        data = {
            "current": current,
            "pageSize": pageSize,
        }
        return invoke(
            self.table_name,
            "selectPage",
            data,
            self.businessId
        )

    @logger.catch
    def selectAll(self, fields: List[str], query: Dict[str, Any])-> Dict[str, Any]:
        """
        查询所有
        Returns:
            Dict[str, Any]: 查询结果
        """
        query_str = " and ".join([f"{k} = '{v}'" for k, v in query.items()])
        data = {
            "query": query_str,
            "shows": fields
        }
        return invoke(
            self.table_name,
            "selectAll",
            data,
            self.businessId
        )