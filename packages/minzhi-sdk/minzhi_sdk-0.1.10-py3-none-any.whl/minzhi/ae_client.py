from typing import Any, Dict, List
from loguru import logger
from .typeconv import res, invoke, invoke_enum


class AEClient:
    """
    AE Client
    """

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
    
    @logger.catch
    def deleteByIds(self, ids: List[str])-> Dict[str, Any]:
        """
        根据id删除
        Args:
            ids: 要删除的id列表
        Returns:
            Dict[str, Any]: 删除结果
        """
        data = ids
        return invoke(
            self.table_name,
            "deleteByIds",
            data,
            self.businessId
        )
    
    @logger.catch
    def delete(self, fields: List[str], query: Dict[str, Any])-> Dict[str, Any]:
        """
        根据条件删除
        Args:
            fields: 显示字段
            query: 查询条件
        Returns:
            Dict[str, Any]: 删除结果
        """
        query_str = " and ".join([f"{k} = '{v}'" for k, v in query.items()])
        data = {
            "query": query_str,
            "shows": fields
        }
        return invoke(
            self.table_name,
            "delete",
            data,
            self.businessId
        )
    
    @logger.catch
    def updateMany(self, data: Dict[str, Any])-> Dict[str, Any]:
        """
        批量更新
        Args:
            data: 更新数据
        Returns:
            Dict[str, Any]: 更新结果
        """
        return invoke(
            self.table_name,
            "updateMany",
            data,
            self.businessId
        )
    
    @logger.catch
    def insertMany(self, data: List[Dict[str, Any]])-> Dict[str, Any]:
        """
        批量插入
        Args:
            data: 插入数据
        Returns:
            Dict[str, Any]: 插入结果
        """
        return invoke(
            self.table_name,
            "insertMany",
            data,
            self.businessId
        )
    
    @logger.catch
    def insertOrUpdate(self, data: Dict[str, Any])-> Dict[str, Any]:
        """
        插入或更新
        Args:
            data: 插入或更新数据
        Returns:
            Dict[str, Any]: 插入或更新结果
        """
        return invoke(
            self.table_name,
            "insertOrUpdate",
            data,
            self.businessId
        )
    
    @logger.catch
    def insertOne(self, data: Dict[str, Any])-> Dict[str, Any]:
        """
        插入一条数据
        Args:
            data: 插入数据
        Returns:
            Dict[str, Any]: 插入结果
        """
        return invoke(
            self.table_name,
            "insertOne",
            data,
            self.businessId
        )
    
    @logger.catch
    def getEnum(self, enum_name: str)-> Dict[str, Any]:
        """
        获取枚举
        Args:
            enum_name: 枚举名称
        Returns:
            Dict[str, Any]: 枚举结果
        """
        result = invoke_enum(
            enum_name,
            self.businessId
        )
        if result and result.get("code") == 200 and result.get("body"):
            temp_list = result.get("body").get("enum_infos")

            info_dict = {

            }
            for index in range(len(temp_list)):
                temp_dict = {
                    temp_list[index]["title"]: temp_list[index]["value"]
                }
                info_dict.update(temp_dict)
            return info_dict

