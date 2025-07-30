"""
UCode Python SDK - Items Module

This module provides CRUD operations for items/objects,
equivalent to items.go in the original Go SDK.
"""

import json
from typing import Dict, List, Any, Tuple, Protocol
from urllib.parse import quote
from .models import (
    ActionBody, Request, Response, ClientApiResponse,
    GetListClientApiResponse, GetListAggregationClientApiResponse
)
from .builders import CreateItemBuilder, UpdateItemBuilder, DeleteItemBuilder
from .config import Config
from .helper import do_request

class ItemsI(Protocol):
    """
    ItemsI interface - equivalent to ItemsI interface in Go.
    Items interface defines methods related to item operations.
    """
    
    def create(self, data: Dict[str, Any]) -> 'CreateItemBuilder':
        """
        CreateObject is a function that creates new object.

        User disable_faas(False) method to enable faas: default True

        Works for [Mongo, Postgres]
        """
        ...
    
    def update(self, data: Dict[str, Any]) -> 'UpdateItemBuilder':
        """
        UpdateObject is a function that updates specific object or objects

        User disable_faas(False) method to enable faas: default True

        Works for [Mongo, Postgres]
        """
        ...
    
    def delete(self) -> 'DeleteItemBuilder':
        """
        Delete is a function that is used to delete one or multiple object
        User disable_faas(False) method to enable faas: default True
        map[guid]="actual_guid"

        Works for [Mongo, Postgres]
        """
        ...
    
    def get_list(self) -> 'GetListItemBuilder':
        """
        GetList is function that get list of objects from specific table using filter.

        sdk.items("table_name").get_list().page(1).limit(10).with_relations(True).filter({"field_name": "value"}).exec()
        
        It has three options: exec, exec_slim, exec_aggregation(use with pipelines)
        Exec option works slower because it gets all the information
        about the table, fields and view. User exec_slim for faster response.
        Works for [Mongo, Postgres]
        """
        ...
    
    def get_single(self, id: str) -> 'GetSingleItemBuilder':
        """
        GetSingleSlim is function that get one object with its fields.
        It is light and fast to use.

        guid="your_guid"
        sdk.items("table_name").get_single(guid).exec_slim()
        It has two options: exec, exec_slim

        Works for [Mongo, Postgres]
        """
        ...


class APIItem:
    """
    APIItem class - equivalent to APIItem struct in Go.
    """

    def __init__(self, sdk_instance, collection: str):
        """
        Initialize APIItem with SDK instance and collection name.
        
        Args:
            sdk_instance: The main SDK instance
            collection: Collection/table name
        """
        self.collection = collection
        self.config = sdk_instance.config()
        self._sdk = sdk_instance
        
    def create(self, data: Dict[str, Any]) -> 'CreateItemBuilder':
        """
        CreateObject is a function that creates new object.

        User disable_faas(False) method to enable faas: default True

        Works for [Mongo, Postgres]
        
        Args:
            data: Object data to create
            
        Returns:    
            CreateItemBuilder: Builder for create operation
        """
        return CreateItemBuilder(
            collection=self.collection,
            config=self.config,
            data=ActionBody(body=data, disable_faas=True)
        )
    
    def update(self, data: Dict[str, Any]) -> 'UpdateItemBuilder':
        """
        UpdateObject is a function that updates specific object or objects

        User disable_faas(False) method to enable faas: default True

        Works for [Mongo, Postgres]
        
        Args:
            data: Object data to update
            
        Returns:
            UpdateItemBuilder: Builder for update operation
        """
        return UpdateItemBuilder(
            collection=self.collection,
            config=self.config,
            data=ActionBody(body=data, disable_faas=True)
        )
    
    def delete(self) -> 'DeleteItemBuilder':
        """
        Delete is a function that is used to delete one or multiple object
        User disable_faas(False) method to enable faas: default True
        map[guid]="actual_guid"

        Works for [Mongo, Postgres]
        
        Returns:
            DeleteItemBuilder: Builder for delete operation
        """
        return DeleteItemBuilder(
            collection=self.collection,
            config=self.config,
            disable_faas=True
        )
    
    def get_list(self) -> 'GetListItemBuilder':
        """
        GetList is function that get list of objects from specific table using filter.

        sdk.items("table_name").get_list().page(1).limit(10).with_relations(True).filter({"field_name": "value"}).exec()
        
        It has three options: exec, exec_slim, exec_aggregation(use with pipelines)
        Exec option works slower because it gets all the information
        about the table, fields and view. User exec_slim for faster response.
        Works for [Mongo, Postgres]
        
        Returns:
            GetListItemBuilder: Builder for get list operation
        """
        return GetListItemBuilder(
            collection=self.collection,
            config=self.config,
            request=Request(data={}, is_cached=False)
        )
    
    def get_single(self, id: str) -> 'GetSingleItemBuilder':
        """
        GetSingleSlim is function that get one object with its fields.
        It is light and fast to use.

        guid="your_guid"
        sdk.items("table_name").get_single(guid).exec_slim()
        It has two options: exec, exec_slim

        Works for [Mongo, Postgres]
        
        Args:
            id: Object GUID
            
        Returns:
            GetSingleItemBuilder: Builder for get single operation
        """
        return GetSingleItemBuilder(
            collection=self.collection,
            config=self.config,
            guid=id
        )

class DeleteMultipleItemBuilder:
    """
    DeleteMultipleItemBuilder class - equivalent to DeleteMultipleItem struct operations in Go.
    """
    
    def __init__(self, collection: str, config: Config, disable_faas: bool, ids: List[str]):
        """
        Initialize DeleteMultipleItemBuilder.
        
        Args:
            collection: Collection/table name
            config: SDK configuration
            disable_faas: Whether to disable FaaS
            ids: List of item IDs to delete
        """
        self.collection = collection
        self.config = config
        self.disable_faas = disable_faas
        self.ids = ids
    
    def exec(self) -> Tuple[Response, Exception]:
        """
        Execute multiple delete request.
        
        Returns:
            Tuple of (Response, Exception)
        """
        from .helper import do_request
        
        response = Response(status="done", error="", data={})
        url = f"{self.config.base_url}/v2/items/{self.collection}?from-ofs={self.disable_faas}"
        
        app_id = self.config.app_id
        headers = {
            "authorization": "API-KEY",
            "X-API-KEY": app_id,
        }
        
        if len(self.ids) == 0:
            response.data = {
                "message": "Error while deleting objects",
                "error": "ids is empty"
            }
            response.status = "error"
            return response, Exception("ids is empty")
        
        try:
            do_request(
                url=url,
                method="DELETE",
                body={"ids": self.ids},
                headers=headers
            )
            
            return response, None
            
        except Exception as err:
            response.data = {
                "message": "Error while deleting objects",
                "error": str(err)
            }
            response.status = "error"
            return response, err


class GetSingleItemBuilder:
    """
    GetSingleItemBuilder class - equivalent to GetSingleItem struct operations in Go.
    """
    
    def __init__(self, collection: str, config: Config, guid: str):
        """
        Initialize GetSingleItemBuilder.
        
        Args:
            collection: Collection/table name
            config: SDK configuration
            guid: Item GUID
        """
        self.collection = collection
        self.config = config
        self.guid = guid
    
    def exec(self) -> Tuple[ClientApiResponse, Response, Exception]:
        """
        Execute get single request.
        
        Returns:
            Tuple of (ClientApiResponse, Response, Exception)
        """
        from .helper import do_request
        
        if self.guid == "":
            return (
                ClientApiResponse(),
                Response(status="error", error="", data={"message": "guid is empty"}),
                Exception("guid is empty")
            )
        
        response = Response(status="done", error="", data={})
        url = f"{self.config.base_url}/v2/items/{self.collection}/{self.guid}?from-ofs=true"
        
        app_id = self.config.app_id
        headers = {
            "authorization": "API-KEY",
            "X-API-KEY": app_id,
        }
        
        try:
            res_bytes = do_request(
                url=url,
                method="GET",
                body=None,
                headers=headers
            )
            
            get_object_dict = json.loads(res_bytes.decode('utf-8'))
            get_object = ClientApiResponse(**get_object_dict)
            
            return get_object, response, None
            
        except Exception as err:
            response.data = {
                "description": str(res_bytes) if 'res_bytes' in locals() else "",
                "message": "Can't sent request",
                "error": str(err)
            }
            response.status = "error"
            return ClientApiResponse(), response, err

class GetListItemBuilder:
    def __init__(self, collection: str, config: Config, request: Request):
        self.collection = collection
        self.config = config
        self.request = request
        self._limit = 0
        self._page = 0
    
    def limit(self, limit: int) -> 'GetListItemBuilder':
        """
        Set limit for pagination.
        
        Args:
            limit: Number of items per page
            
        Returns:
            GetListItemBuilder: Self for chaining
        """
        if limit <= 0:
            limit = 10
        self._limit = limit
        self.request.data["offset"] = (self._page - 1) * limit
        self.request.data["limit"] = limit
        return self
    
    def page(self, page: int) -> 'GetListItemBuilder':
        """
        Set page for pagination.
        
        Args:
            page: Page number
            
        Returns:
            GetListItemBuilder: Self for chaining
        """
        if page <= 0:
            page = 1
        self._page = page
        self.request.data["offset"] = (page - 1) * self._limit
        return self
    
    def filter(self, filter: Dict[str, Any]) -> 'GetListItemBuilder':
        """
        Set filters for the query.
        
        Args:
            filter: Filter parameters
            
        Returns:
            GetListItemBuilder: Self for chaining
        """
        for key, value in filter.items():
            self.request.data[key] = value
        return self
    
    def search(self, search: str) -> 'GetListItemBuilder':
        """
        Set search term.
        
        Args:
            search: Search term
            
        Returns:
            GetListItemBuilder: Self for chaining
        """
        self.request.data["search"] = search
        return self
    
    def sort(self, sort: Dict[str, Any]) -> 'GetListItemBuilder':
        """
        Set sort parameters.
        
        Args:
            sort: Sort parameters
            
        Returns:
            GetListItemBuilder: Self for chaining
        """
        self.request.data["order"] = sort
        return self
    
    def view_fields(self, fields: List[str]) -> 'GetListItemBuilder':
        """
        Set view fields.
        
        Args:
            fields: List of field names
            
        Returns:
            GetListItemBuilder: Self for chaining
        """
        self.request.data["view_fields"] = fields
        return self
    
    def pipelines(self, query: Dict[str, Any]) -> 'GetListAggregationBuilder':
        """
        Set aggregation pipelines.
        
        Args:
            query: Pipeline query
            
        Returns:
            GetListAggregationBuilder: Builder for aggregation
        """
        return GetListAggregationBuilder(
            collection=self.collection,
            config=self.config,
            request=Request(data=query, is_cached=False)
        )
    
    def with_relations(self, with_: bool) -> 'GetListItemBuilder':
        """
        Set whether to include relations.
        
        Args:
            with: Whether to include relations
            
        Returns:
            GetListItemBuilder: Self for chaining
        """
        self.request.data["with_relations"] = with_
        return self
    
    def exec(self) -> Tuple[GetListClientApiResponse, Response, Exception]:
        """
        Execute get list request.
        
        Returns:
            Tuple of (GetListClientApiResponse, Response, Exception)
        """
        from .helper import do_request
        
        response = Response(status="done", error="", data={})
        url = f"{self.config.base_url}/v2/items/{self.collection}?from-ofs=true"
        
        try:
            req_object_bytes = json.dumps(self.request.data).encode('utf-8')
        except Exception as err:
            response.data = {
                "message": "Error while marshalling request getting list slim object",
                "error": str(err)
            }
            response.status = "error"
            return FlexibleResponse({}), response, err
        
        if self._page == 0:
            self._page = 1
        
        if self._limit == 0:
            self._limit = 10
        
        encoded_data = quote(req_object_bytes.decode('utf-8'))
        url = f"{url}&data={encoded_data}&offset={(self._page-1)*self._limit}&limit={self._limit}"
        
        app_id = self.config.app_id
        headers = {
            "authorization": "API-KEY",
            "X-API-KEY": app_id,
        }
        
        try:
            get_list_response_bytes = do_request(
                url=url,
                method="GET",
                body=None,
                headers=headers
            )
            
            list_slim_dict = json.loads(get_list_response_bytes.decode('utf-8'))
            
            # Create a flexible response object instead of strict dataclass
            class FlexibleResponse:
                def __init__(self, data_dict):
                    self.raw_data = data_dict
                    self.data = self._parse_data(data_dict)
                
                def _parse_data(self, data_dict):
                    class DataWrapper:
                        def __init__(self, d):
                            if isinstance(d, dict):
                                for key, value in d.items():
                                    if isinstance(value, dict):
                                        setattr(self, key, DataWrapper(value))
                                    else:
                                        setattr(self, key, value)
                            else:
                                self.value = d
                    
                    return DataWrapper(data_dict)
            
            list_slim = FlexibleResponse(list_slim_dict)
            
            return list_slim, response, None
            
        except Exception as err:
            response.data = {
                "description": str(get_list_response_bytes) if 'get_list_response_bytes' in locals() else "",
                "message": "Can't sent request",
                "error": str(err)
            }
            response.status = "error"
            return GetListClientApiResponse(), response, err


class GetListAggregationBuilder:
    """
    GetListAggregationBuilder class - equivalent to GetListAggregation struct operations in Go.
    """
    
    def __init__(self, collection: str, config: Config, request: Request):
        """
        Initialize GetListAggregationBuilder.
        
        Args:
            collection: Collection/table name
            config: SDK configuration
            request: Request object with aggregation data
        """
        self.collection = collection
        self.config = config
        self.request = request
    
    def exec_aggregation(self) -> Tuple[GetListAggregationClientApiResponse, Response, Exception]:
        """
        Execute aggregation request.
        
        Returns:
            Tuple of (GetListAggregationClientApiResponse, Response, Exception)
        """
        from .helper import do_request
        
        response = Response(status="done", error="", data={})
        url = f"{self.config.base_url}/v2/items/{self.collection}/aggregation"
        
        app_id = self.config.app_id
        headers = {
            "authorization": "API-KEY",
            "X-API-KEY": app_id,
        }
        
        try:
            get_list_aggregation_response_bytes = do_request(
                url=url,
                method="POST",
                body=self.request,
                headers=headers
            )
            
            get_list_aggregation_dict = json.loads(get_list_aggregation_response_bytes.decode('utf-8'))
            get_list_aggregation = GetListAggregationClientApiResponse(**get_list_aggregation_dict)
            
            return get_list_aggregation, response, None
            
        except Exception as err:
            response.data = {
                "description": str(get_list_aggregation_response_bytes) if 'get_list_aggregation_response_bytes' in locals() else "",
                "message": "Can't sent request",
                "error": str(err)
            }
            response.status = "error"
            return GetListAggregationClientApiResponse(), response, err


# Aliases for compatibility
Items = APIItem
ItemsInterface = ItemsI


__all__ = [
    'ItemsI',
    'APIItem',
    'Items',
    'ItemsInterface',
    'CreateItemBuilder',
    'UpdateItemBuilder',
    'DeleteItemBuilder',
    'DeleteMultipleItemBuilder',
    'GetSingleItemBuilder',
    'GetListItemBuilder',
    'GetListAggregationBuilder'
]