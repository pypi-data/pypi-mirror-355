from typing import Any, Dict, List
from loguru import logger
from minzhi import res, invoke, invoke_enum
import requests
import json




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


class CmdbClient:
    """
    CMDB Client
    """
    def __init__(self, view_id: str, CMDB_SERVER: str, APPID: str, APPSECRET: str):
        self.SERVER = CMDB_SERVER
        # appid
        self.appid = APPID
        # appSecret
        self.appSecret = APPSECRET
        # view id：连接器id
        self.view_id = view_id
        self.HEADERS = {
            "Authorization": self.get_token()
        }

    @logger.catch
    def get_token(self):
        url = f"{self.SERVER}/api/v2/auth/login"
        data = {
            "appId": self.appid,
            "appSecret": self.appSecret
        }
        logger.debug(f"CmdbAPI -> get_token url: {url}")
        logger.debug(f"CmdbAPI -> get_token data: {json.dumps(data)}")
        response = requests.post(url=url, json=data, verify=False)
        logger.debug(f"CmdbAPI -> get_token Res: {response.text}")
        return response.json().get('Authorization')

    @logger.catch
    def get_all_data(self, startPage=1, pageSize=1000, queryKey=None):
        url = f"{self.SERVER}/api/v2/data/view"

        # 查询条件
        queryCondition = []
        if queryKey is not None:
            queryCondition.extend(queryKey) if isinstance(queryKey, list) else queryCondition.append(queryKey)

        logger.debug(f"CmdbAPI -> get_all_data url: {url}")
        logger.debug(f"CmdbAPI -> get_all_data headers: {self.HEADERS}")
        data = {
            "moduleName": "",
            "name": "",
            "pageSize": pageSize,
            "queryCondition": queryCondition,
            "startPage": startPage,
            "viewid": self.view_id
        }
        logger.debug(f"CmdbAPI -> get_all_data data: {json.dumps(data)}")
        response_data = []
        while True:
            response = requests.post(url=url, headers=self.HEADERS, json=data, verify=False).json()
            total = response.get("total")
            response_data += response.get("content")
            if len(response_data) < total:
                data['startPage'] += 1
                logger.debug("get next request %s" % data['startPage'])
            else:
                logger.debug("get {0} instances length: {1}".format(self.view_id, len(response_data)))
                break
        logger.debug(f"CmdbAPI -> get_all_data Res: {json.dumps(response_data)}")
        return response_data

    @logger.catch
    def import_data(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """导入数据"""
        url = f"{self.SERVER}/api/v2/data/storage"
        logger.debug(f"CmdbAPI -> import_data url: {url}")
        logger.debug(f"CmdbAPI -> import_data headers: {self.HEADERS}")
        data = {
            "mid": self.view_id,
            "data": data
        }
        logger.debug(f"CmdbAPI -> import_data data: {json.dumps(data)}")
        response = requests.post(url=url, headers=self.HEADERS, json=data, verify=False)
        logger.debug(f"CmdbAPI -> import_data Res: {response.text}")
        return response.json()