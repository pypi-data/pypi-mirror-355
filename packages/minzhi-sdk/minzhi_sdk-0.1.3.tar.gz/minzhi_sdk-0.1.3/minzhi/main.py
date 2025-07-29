from typing import Any, Dict
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
        return invoke(
            self.businessId,
            "selectPage",
            {
                "current": current,
                "pageSize": pageSize,
            },
            self.businessId
        )

    @logger.catch
    def selectAll(self)-> Dict[str, Any]:
        """
        查询所有
        Returns:
            Dict[str, Any]: 查询结果
        """
        return invoke(
            self.table_name,
            "selectAll",
            {},
            self.businessId
        )

    @logger.catch
    def selectOne(self, query: Dict[str, Any])-> Dict[str, Any]:
        """
        根据id查询
        Args:
            query: 查询条件
        Returns:
            Dict[str, Any]: 查询结果
        """
        query_str = " and ".join([f"{k} = '{v}'" for k, v in query.items()])
        return invoke(
            self.table_name,
            "selectOne",
            query_str,
            self.businessId
        )