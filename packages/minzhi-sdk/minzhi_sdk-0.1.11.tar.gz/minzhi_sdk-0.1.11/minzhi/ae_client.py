from typing import Any, Dict, List
from loguru import logger


class Result:
    def __init__(self, data):
        self.data = data

    def check(self, required_keys=None):
        if required_keys:
            if not isinstance(self.data, dict):
                raise ValueError("数据必须是 dict")
            for key in required_keys:
                if key not in self.data:
                    raise ValueError(f"缺少字段: {key}")
        return self  # 支持链式调用

    def to_json(self):
        import json
        return json.dumps(self.data, ensure_ascii=False)



class AEClient:
    """
    AE Client
    """

    def __init__(self, businessId: str, table_name: str):
        self.businessId = businessId
        self.table_name = table_name
        self.res = self._get_res()
        self.invoke = self._get_invoke()
        self.invoke_enum = self._get_invoke_enum()

    @logger.catch
    def _get_res(self) -> Dict[str, Any]:
        try:
            from TypeConversion import res
            return res
        except ImportError as e:
            logger.error(f"TypeConversion 未注入: {e}")
            raise

    @logger.catch
    def _get_invoke(self):
        try:
            from TypeConversion import invoke
            return invoke
        except ImportError as e:
            logger.error(f"TypeConversion 未注入: {e}")
            raise
    
    @logger.catch
    def _get_invoke_enum(self):
        try:
            from TypeConversion import invoke_enum
            return invoke_enum
        except ImportError as e:
            logger.error(f"TypeConversion 未注入: {e}")
            raise

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
        result = self.invoke(
            self.table_name,
            "selectPage",
            data,
            self.businessId
        )
        return Result(result)
    
    
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
        result = self.invoke(
            self.table_name,
            "selectAll",
            data,
            self.businessId
        )
        return Result(result)
    

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
        result = self.invoke(
            self.table_name,
            "deleteByIds",
            data,
            self.businessId
        )
        return Result(result)
    
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
        result = self.invoke(
            self.table_name,
            "delete",
            data,
            self.businessId
        )
        return Result(result)
    
    @logger.catch
    def updateMany(self, data: Dict[str, Any])-> Dict[str, Any]:
        """
        批量更新
        Args:
            data: 更新数据
        Returns:
            Dict[str, Any]: 更新结果
        """
        result = self.invoke(
            self.table_name,
            "updateMany",
            data,
            self.businessId
        )
        return Result(result)
    
    @logger.catch
    def insertMany(self, data: List[Dict[str, Any]])-> Dict[str, Any]:
        """
        批量插入
        Args:
            data: 插入数据
        Returns:
            Dict[str, Any]: 插入结果
        """
        result = self.invoke(
            self.table_name,
            "insertMany",
            data,
            self.businessId
        )
        return Result(result)
    @logger.catch
    def insertOrUpdate(self, data: Dict[str, Any])-> Dict[str, Any]:
        """
        插入或更新
        Args:
            data: 插入或更新数据
        Returns:
            Dict[str, Any]: 插入或更新结果
        """
        result = self.invoke(
            self.table_name,
            "insertOrUpdate",
            data,
            self.businessId
        )
        return Result(result)
    
    @logger.catch
    def insertOne(self, data: Dict[str, Any])-> Dict[str, Any]:
        """
        插入一条数据
        Args:
            data: 插入数据
        Returns:
            Dict[str, Any]: 插入结果
        """
        result = self.invoke(
            self.table_name,
            "insertOne",
            data,
            self.businessId
        )
        return Result(result)

    @logger.catch
    def getEnum(self, enum_name: str)-> Dict[str, Any]:
        """
        获取枚举
        Args:
            enum_name: 枚举名称
        Returns:
            Dict[str, Any]: 枚举结果
        """
        result = self.invoke_enum(
            enum_name,
            self.businessId
        )
        return Result(result)
        # if result and result.get("code") == 200 and result.get("body"):
        #     temp_list = result.get("body").get("enum_infos")

        #     info_dict = {

        #     }
        #     for index in range(len(temp_list)):
        #         temp_dict = {
        #             temp_list[index]["title"]: temp_list[index]["value"]
        #         }
        #         info_dict.update(temp_dict)
        #     return info_dict

