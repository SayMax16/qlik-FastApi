"""Qlik Sense Engine API client."""

import json
import websocket
import ssl
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import logging
import os
import re

from src.api.core.config import Settings
from src.api.clients.base import BaseClient

logger = logging.getLogger(__name__)


class QlikEngineClient(BaseClient):
    """Client for Qlik Sense Engine API using WebSocket."""

    def __init__(self, settings: Settings):
        """
        Initialize Qlik Engine API client.

        Args:
            settings: Application settings containing Qlik Sense configuration
        """
        super().__init__(settings)
        self.ws = None
        self.request_id = 0
        self.ws_timeout_seconds = settings.QLIK_WS_TIMEOUT
        self.ws_retries = 2  # Default retries

    def _get_next_request_id(self) -> int:
        """Get next request ID for JSON-RPC."""
        self.request_id += 1
        return self.request_id

    def connect(self, app_id: Optional[str] = None) -> None:
        """
        Connect to Engine API via WebSocket.

        Args:
            app_id: Optional application ID (not used in connection, kept for compatibility)

        Raises:
            ConnectionError: If connection fails after all retry attempts
        """
        # Try different WebSocket endpoints
        server_host = self.settings.QLIK_SENSE_HOST

        # Order and count of endpoints controlled by retries setting
        endpoints_all = [
            f"wss://{server_host}:{self.settings.QLIK_ENGINE_PORT}/app/engineData",
            f"wss://{server_host}:{self.settings.QLIK_ENGINE_PORT}/app",
            f"ws://{server_host}:{self.settings.QLIK_ENGINE_PORT}/app/engineData",
            f"ws://{server_host}:{self.settings.QLIK_ENGINE_PORT}/app",
        ]
        endpoints_to_try = endpoints_all[: max(1, min(self.ws_retries, len(endpoints_all)))]

        # Setup SSL context
        ssl_context = ssl.create_default_context()
        if not self.settings.QLIK_VERIFY_SSL:
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

        # Load certificates
        cert_path, key_path, ca_path = self.settings.get_cert_paths()
        if cert_path.exists() and key_path.exists():
            ssl_context.load_cert_chain(str(cert_path), str(key_path))

        if ca_path.exists():
            ssl_context.load_verify_locations(str(ca_path))

        # Headers for authentication
        headers = [
            f"X-Qlik-User: UserDirectory={self.settings.QLIK_USER_DIRECTORY}; UserId={self.settings.QLIK_USER_ID}"
        ]

        last_error = None
        for url in endpoints_to_try:
            try:
                if url.startswith("wss://"):
                    self.ws = websocket.create_connection(
                        url, sslopt={"context": ssl_context}, header=headers, timeout=self.ws_timeout_seconds
                    )
                else:
                    self.ws = websocket.create_connection(
                        url, header=headers, timeout=self.ws_timeout_seconds
                    )

                # Initial recv to establish session
                self.ws.recv()
                return  # Success
            except Exception as e:
                last_error = e
                if self.ws:
                    try:
                        self.ws.close()
                    except Exception:
                        pass
                    self.ws = None
                continue

        raise ConnectionError(
            f"Failed to connect to Engine API. Last error: {str(last_error)}"
        )

    def disconnect(self) -> None:
        """Disconnect from Engine API."""
        if self.ws:
            self.ws.close()
            self.ws = None

    def send_request(
        self, method: str, params: List[Any] = None, handle: int = -1
    ) -> Dict[str, Any]:
        """
        Send JSON-RPC 2.0 request to Qlik Engine API and return response.

        Args:
            method: Engine API method name
            params: Method parameters list
            handle: Object handle for scoped operations (-1 for global)

        Returns:
            Response dictionary from Engine API

        Raises:
            ConnectionError: If not connected to Engine API
            Exception: If Engine API returns an error
        """
        if not self.ws:
            raise ConnectionError("Not connected to Engine API")

        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_request_id(),
            "handle": handle,
            "method": method,
            "params": params or [],
        }

        self.ws.send(json.dumps(request))

        while True:
            data = self.ws.recv()
            if "result" in data or "error" in data:
                break

        response = json.loads(data)

        if "error" in response:
            raise Exception(f"Engine API error: {response['error']}")

        return response.get("result", {})

    def get_doc_list(self) -> List[Dict[str, Any]]:
        """
        Get list of available documents.

        Returns:
            List of document information dictionaries
        """
        try:
            result = self.send_request("GetDocList")
            doc_list = result.get("qDocList", [])

            if isinstance(doc_list, list):
                return doc_list
            else:
                return []

        except Exception as e:
            return []

    def open_doc(self, app_id: str, no_data: bool = True) -> Dict[str, Any]:
        """
        Open Qlik Sense application document.

        Args:
            app_id: Application ID to open
            no_data: If True, open without loading data (faster for metadata operations)

        Returns:
            Response with document handle

        Raises:
            Exception: If opening document fails
        """
        try:
            if no_data:
                return self.send_request("OpenDoc", [app_id, "", "", "", True])
            else:
                return self.send_request("OpenDoc", [app_id])
        except Exception as e:
            # If app is already open, try to get existing handle
            if "already open" in str(e).lower():
                try:
                    doc_list = self.get_doc_list()
                    for doc in doc_list:
                        if doc.get("qDocId") == app_id:
                            return {
                                "qReturn": {
                                    "qHandle": doc.get("qHandle", -1),
                                    "qGenericId": app_id
                                }
                            }
                except:
                    pass
            raise e

    def close_doc(self, app_handle: int) -> bool:
        """
        Close application document.

        Args:
            app_handle: Document handle to close

        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.send_request("CloseDoc", [], handle=app_handle)
            return result.get("qReturn", {}).get("qSuccess", False)
        except Exception:
            return False

    def get_active_doc(self) -> Dict[str, Any]:
        """
        Get currently active document if any.

        Returns:
            Active document information or empty dict
        """
        try:
            result = self.send_request("GetActiveDoc")
            return result
        except Exception:
            return {}

    def get_app_properties(self, app_handle: int) -> Dict[str, Any]:
        """
        Get app properties.

        Args:
            app_handle: Application handle

        Returns:
            App properties dictionary
        """
        return self.send_request("GetAppProperties", handle=app_handle)

    def get_script(self, app_handle: int) -> str:
        """
        Get load script.

        Args:
            app_handle: Application handle

        Returns:
            Load script as string
        """
        result = self.send_request("GetScript", [], handle=app_handle)
        return result.get("qScript", "")

    def set_script(self, app_handle: int, script: str) -> bool:
        """
        Set load script.

        Args:
            app_handle: Application handle
            script: Load script content

        Returns:
            True if successful, False otherwise
        """
        result = self.send_request("SetScript", [script], handle=app_handle)
        return result.get("qReturn", {}).get("qSuccess", False)

    def do_save(self, app_handle: int, file_name: Optional[str] = None) -> bool:
        """
        Save app.

        Args:
            app_handle: Application handle
            file_name: Optional file name

        Returns:
            True if successful, False otherwise
        """
        params = {}
        if file_name:
            params["qFileName"] = file_name
        result = self.send_request("DoSave", params, handle=app_handle)
        return result.get("qReturn", {}).get("qSuccess", False)

    def get_objects(
        self, app_handle: int, object_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get app objects.

        Args:
            app_handle: Application handle
            object_type: Optional filter by object type

        Returns:
            List of object information dictionaries
        """
        if object_type:
            params = {
                "qOptions": {
                    "qTypes": [object_type],
                    "qIncludeSessionObjects": True,
                    "qData": {},
                }
            }
        else:
            params = {
                "qOptions": {
                    "qIncludeSessionObjects": True,
                    "qData": {},
                }
            }

        logger.debug(f"get_objects params: {params}")

        result = self.send_request("GetObjects", params, handle=app_handle)

        if "error" in str(result) or "Missing Types" in str(result):
            logger.debug(f"get_objects error result: {result}")

        return result.get("qList", {}).get("qItems", [])

    def get_sheets(self, app_handle: int) -> List[Dict[str, Any]]:
        """
        Get app sheets.

        Args:
            app_handle: Application handle

        Returns:
            List of sheet information dictionaries
        """
        try:
            sheet_list_def = {
                "qInfo": {"qType": "SheetList"},
                "qAppObjectListDef": {
                    "qType": "sheet",
                    "qData": {
                        "title": "/qMetaDef/title",
                        "description": "/qMetaDef/description",
                        "thumbnail": "/thumbnail",
                        "cells": "/cells",
                        "rank": "/rank",
                        "columns": "/columns",
                        "rows": "/rows"
                    }
                }
            }

            create_result = self.send_request("CreateSessionObject", [sheet_list_def], handle=app_handle)

            if "qReturn" not in create_result or "qHandle" not in create_result["qReturn"]:
                logger.warning(f"Failed to create SheetList object: {create_result}")
                return []

            sheet_list_handle = create_result["qReturn"]["qHandle"]
            layout_result = self.send_request("GetLayout", [], handle=sheet_list_handle)
            if "qLayout" not in layout_result or "qAppObjectList" not in layout_result["qLayout"]:
                logger.warning(f"No sheet list in layout: {layout_result}")
                return []

            sheets = layout_result["qLayout"]["qAppObjectList"]["qItems"]
            logger.info(f"Found {len(sheets)} sheets")
            return sheets

        except Exception as e:
            logger.error(f"get_sheets exception: {str(e)}")
            return []

    def get_fields(self, app_handle: int) -> Dict[str, Any]:
        """
        Get app fields using GetTablesAndKeys method.

        Args:
            app_handle: Application handle

        Returns:
            Dictionary with fields information, tables count, and total fields
        """
        try:
            result = self.send_request(
                "GetTablesAndKeys",
                [
                    {"qcx": 1000, "qcy": 1000},  # Max dimensions
                    {"qcx": 0, "qcy": 0},  # Min dimensions
                    30,  # Max tables
                    True,  # Include system tables
                    False,  # Include hidden fields
                ],
                handle=app_handle,
            )

            fields_info = []

            if "qtr" in result:
                for table in result["qtr"]:
                    table_name = table.get("qName", "Unknown")

                    if "qFields" in table:
                        for field in table["qFields"]:
                            field_info = {
                                "field_name": field.get("qName", ""),
                                "table_name": table_name,
                                "data_type": field.get("qType", ""),
                                "is_key": field.get("qIsKey", False),
                                "is_system": field.get("qIsSystem", False),
                                "is_hidden": field.get("qIsHidden", False),
                                "is_semantic": field.get("qIsSemantic", False),
                                "distinct_values": field.get("qnTotalDistinctValues", 0),
                                "present_distinct_values": field.get("qnPresentDistinctValues", 0),
                                "rows_count": field.get("qnRows", 0),
                                "subset_ratio": field.get("qSubsetRatio", 0),
                                "key_type": field.get("qKeyType", ""),
                                "tags": field.get("qTags", []),
                            }
                            fields_info.append(field_info)

            return {
                "fields": fields_info,
                "tables_count": len(result.get("qtr", [])),
                "total_fields": len(fields_info),
            }

        except Exception as e:
            return {"error": str(e), "details": "Error in get_fields method"}

    def get_tables(self, app_handle: int) -> List[Dict[str, Any]]:
        """
        Get app tables.

        Args:
            app_handle: Application handle

        Returns:
            List of table information dictionaries
        """
        result = self.send_request("GetTablesList", handle=app_handle)
        return result.get("qtr", [])

    def create_session_object(
        self, app_handle: int, obj_def: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create session object.

        Args:
            app_handle: Application handle
            obj_def: Object definition dictionary

        Returns:
            Response with object handle
        """
        return self.send_request(
            "CreateSessionObject", {"qProp": obj_def}, handle=app_handle
        )

    def get_object(self, app_handle: int, object_id: str) -> Dict[str, Any]:
        """
        Get object by ID.

        Args:
            app_handle: Application handle
            object_id: Object ID

        Returns:
            Object information dictionary
        """
        return self.send_request("GetObject", {"qId": object_id}, handle=app_handle)

    def evaluate_expression(self, app_handle: int, expression: str) -> Any:
        """
        Evaluate expression.

        Args:
            app_handle: Application handle
            expression: Qlik expression to evaluate

        Returns:
            Evaluation result
        """
        result = self.send_request(
            "Evaluate", {"qExpression": expression}, handle=app_handle
        )
        return result.get("qReturn", {})

    def select_in_field(
        self, app_handle: int, field_name: str, values: List[str], toggle: bool = False
    ) -> bool:
        """
        Select values in field.

        Args:
            app_handle: Application handle
            field_name: Field name
            values: List of values to select
            toggle: Whether to toggle selection

        Returns:
            True if successful, False otherwise
        """
        params = {"qFieldName": field_name, "qValues": values, "qToggleMode": toggle}
        result = self.send_request("SelectInField", params, handle=app_handle)
        return result.get("qReturn", False)

    def clear_selections(self, app_handle: int, locked_also: bool = False) -> bool:
        """
        Clear all selections.

        Args:
            app_handle: Application handle
            locked_also: Whether to clear locked selections too

        Returns:
            True if successful, False otherwise
        """
        params = {"qLockedAlso": locked_also}
        result = self.send_request("ClearAll", params, handle=app_handle)
        return result.get("qReturn", False)

    def get_current_selections(self, app_handle: int) -> List[Dict[str, Any]]:
        """
        Get current selections.

        Args:
            app_handle: Application handle

        Returns:
            List of current selections
        """
        result = self.send_request("GetCurrentSelections", handle=app_handle)
        return result.get("qSelections", [])

    def create_hypercube(
        self,
        app_handle: int,
        dimensions: List[str],
        measures: List[str],
        max_rows: int = 1000,
    ) -> Dict[str, Any]:
        """
        Create hypercube for data extraction with proper structure.

        Args:
            app_handle: Application handle
            dimensions: List of dimension field expressions
            measures: List of measure expressions
            max_rows: Maximum number of rows to fetch

        Returns:
            Dictionary containing hypercube data and metadata
        """
        try:
            hypercube_def = {
                "qDimensions": [
                    {
                        "qDef": {
                            "qFieldDefs": [dim],
                            "qSortCriterias": [
                                {
                                    "qSortByState": 0,
                                    "qSortByFrequency": 0,
                                    "qSortByNumeric": 1,
                                    "qSortByAscii": 1,
                                    "qSortByLoadOrder": 0,
                                    "qSortByExpression": 0,
                                    "qExpression": {"qv": ""},
                                }
                            ],
                        },
                        "qNullSuppression": False,
                        "qIncludeElemValue": True,
                    }
                    for dim in dimensions
                ],
                "qMeasures": [
                    {
                        "qDef": {"qDef": measure, "qLabel": f"Measure_{i}"},
                        "qSortBy": {"qSortByNumeric": -1, "qSortByLoadOrder": 0},
                    }
                    for i, measure in enumerate(measures)
                ],
                "qInitialDataFetch": [
                    {
                        "qTop": 0,
                        "qLeft": 0,
                        "qHeight": max_rows,
                        "qWidth": len(dimensions) + len(measures),
                    }
                ],
                "qSuppressZero": False,
                "qSuppressMissing": False,
                "qMode": "S",
                "qInterColumnSortOrder": list(range(len(dimensions) + len(measures))),
            }

            obj_def = {
                "qInfo": {
                    "qId": f"hypercube-{len(dimensions)}d-{len(measures)}m",
                    "qType": "HyperCube",
                },
                "qHyperCubeDef": hypercube_def,
            }

            result = self.send_request(
                "CreateSessionObject", [obj_def], handle=app_handle
            )

            if "qReturn" not in result or "qHandle" not in result["qReturn"]:
                return {"error": "Failed to create hypercube", "response": result}

            cube_handle = result["qReturn"]["qHandle"]

            layout = self.send_request("GetLayout", [], handle=cube_handle)

            if "qLayout" not in layout or "qHyperCube" not in layout["qLayout"]:
                return {"error": "No hypercube in layout", "layout": layout}

            hypercube = layout["qLayout"]["qHyperCube"]

            return {
                "hypercube_handle": cube_handle,
                "hypercube_data": hypercube,
                "dimensions": dimensions,
                "measures": measures,
                "total_rows": hypercube.get("qSize", {}).get("qcy", 0),
                "total_columns": hypercube.get("qSize", {}).get("qcx", 0),
            }

        except Exception as e:
            return {"error": str(e), "details": "Error in create_hypercube method"}

    def get_hypercube_data(
        self,
        hypercube_handle: int,
        page_top: int = 0,
        page_height: int = 1000,
        page_left: int = 0,
        page_width: int = 50,
    ) -> Dict[str, Any]:
        """
        Get data from existing hypercube with pagination.

        Args:
            hypercube_handle: Hypercube object handle
            page_top: Starting row
            page_height: Number of rows
            page_left: Starting column
            page_width: Number of columns

        Returns:
            Hypercube data dictionary
        """
        try:
            params = [
                {
                    "qPath": "/qHyperCubeDef",
                    "qPages": [
                        {
                            "qTop": page_top,
                            "qLeft": page_left,
                            "qHeight": page_height,
                            "qWidth": page_width,
                        }
                    ],
                }
            ]

            result = self.send_request(
                "GetHyperCubeData", params, handle=hypercube_handle
            )
            return result

        except Exception as e:
            return {"error": str(e), "details": "Error in get_hypercube_data method"}

    def get_field_values(
        self,
        app_handle: int,
        field_name: str,
        max_values: int = 100,
        include_frequency: bool = True,
    ) -> Dict[str, Any]:
        """
        Get field values with frequency information using ListObject.

        Args:
            app_handle: Application handle
            field_name: Field name
            max_values: Maximum number of values to return
            include_frequency: Whether to include frequency information

        Returns:
            Dictionary with field values and metadata
        """
        try:
            list_def = {
                "qInfo": {"qId": f"field-values-{field_name}", "qType": "ListObject"},
                "qListObjectDef": {
                    "qStateName": "$",
                    "qLibraryId": "",
                    "qDef": {
                        "qFieldDefs": [field_name],
                        "qFieldLabels": [],
                        "qSortCriterias": [
                            {
                                "qSortByState": 0,
                                "qSortByFrequency": 1 if include_frequency else 0,
                                "qSortByNumeric": 1,
                                "qSortByAscii": 1,
                                "qSortByLoadOrder": 0,
                                "qSortByExpression": 0,
                                "qExpression": {"qv": ""},
                            }
                        ],
                    },
                    "qInitialDataFetch": [
                        {"qTop": 0, "qLeft": 0, "qHeight": max_values, "qWidth": 1}
                    ],
                },
            }

            result = self.send_request(
                "CreateSessionObject", [list_def], handle=app_handle
            )

            if "qReturn" not in result or "qHandle" not in result["qReturn"]:
                return {"error": "Failed to create session object", "response": result}

            list_handle = result["qReturn"]["qHandle"]

            layout = self.send_request("GetLayout", [], handle=list_handle)

            if "qLayout" not in layout or "qListObject" not in layout["qLayout"]:
                try:
                    self.send_request(
                        "DestroySessionObject",
                        [f"field-values-{field_name}"],
                        handle=app_handle,
                    )
                except:
                    pass
                return {"error": "No list object in layout", "layout": layout}

            list_object = layout["qLayout"]["qListObject"]
            values_data = []

            for page in list_object.get("qDataPages", []):
                for row in page.get("qMatrix", []):
                    if row and len(row) > 0:
                        cell = row[0]
                        value_info = {
                            "value": cell.get("qText", ""),
                            "state": cell.get("qState", "O"),
                            "numeric_value": cell.get("qNum", None),
                            "is_numeric": cell.get("qIsNumeric", False),
                        }

                        if "qFrequency" in cell:
                            value_info["frequency"] = cell.get("qFrequency", 0)

                        values_data.append(value_info)

            field_info = {
                "field_name": field_name,
                "values": values_data,
                "total_values": list_object.get("qSize", {}).get("qcy", 0),
                "returned_count": len(values_data),
                "dimension_info": list_object.get("qDimensionInfo", {}),
            }

            try:
                self.send_request(
                    "DestroySessionObject",
                    [f"field-values-{field_name}"],
                    handle=app_handle,
                )
            except Exception as cleanup_error:
                field_info["cleanup_warning"] = str(cleanup_error)

            return field_info

        except Exception as e:
            return {"error": str(e), "details": "Error in get_field_values method"}

    def get_measures(self, app_handle: int) -> List[Dict[str, Any]]:
        """
        Get master measures using GetAllInfos + GetMeasure + GetLayout.

        Args:
            app_handle: Application handle

        Returns:
            List of measure information dictionaries
        """
        try:
            all_infos_result = self.send_request("GetAllInfos", [], handle=app_handle)
            if "qInfos" not in all_infos_result:
                return []

            measures = []
            for info in all_infos_result["qInfos"]:
                if info.get("qType") == "measure":
                    measure_id = info.get("qId")
                    if measure_id:
                        try:
                            measure_result = self.send_request("GetMeasure", [measure_id], handle=app_handle)
                            if "qReturn" in measure_result:
                                measure_handle = measure_result["qReturn"]["qHandle"]
                                if measure_handle:
                                    layout_result = self.send_request("GetLayout", [], handle=measure_handle)
                                    if "qLayout" in layout_result:
                                        layout = layout_result["qLayout"]
                                        measure_data = {
                                            "qInfo": layout.get("qInfo", {}),
                                            "qMeta": layout.get("qMeta", {}),
                                            "qMeasure": layout.get("qMeasure", {}),
                                            "qData": {}
                                        }
                                        measures.append(measure_data)
                                    else:
                                        measures.append({
                                            "qInfo": info,
                                            "qMeta": {"title": f"Measure {measure_id}"},
                                            "qMeasure": {},
                                            "qData": {}
                                        })
                                else:
                                    measures.append({
                                        "qInfo": info,
                                        "qMeta": {"title": f"Measure {measure_id}"},
                                        "qMeasure": {},
                                        "qData": {}
                                    })
                            else:
                                measures.append({
                                    "qInfo": info,
                                    "qMeta": {"title": f"Measure {measure_id}"},
                                    "qMeasure": {},
                                    "qData": {}
                                })
                        except Exception as e:
                            logger.warning(f"Could not get details for measure {measure_id}: {e}")
                            measures.append({
                                "qInfo": info,
                                "qMeta": {"title": f"Measure {measure_id}"},
                                "qMeasure": {},
                                "qData": {}
                            })

            return measures
        except Exception as e:
            logger.error(f"Error getting measures with GetAllInfos: {e}")
            try:
                result = self.send_request("GetMeasureList", handle=app_handle)
                return result.get("qMeasureList", {}).get("qItems", [])
            except Exception as e2:
                logger.error(f"Error getting measures with GetMeasureList: {e2}")
                return []

    def get_dimensions(self, app_handle: int) -> List[Dict[str, Any]]:
        """
        Get master dimensions.

        Args:
            app_handle: Application handle

        Returns:
            List of dimension information dictionaries
        """
        result = self.send_request("GetDimensionList", handle=app_handle)
        return result.get("qDimensionList", {}).get("qItems", [])

    def get_variables(self, app_handle: int) -> List[Dict[str, Any]]:
        """
        Get variables.

        Args:
            app_handle: Application handle

        Returns:
            List of variable information dictionaries
        """
        result = self.send_request("GetVariableList", handle=app_handle)
        return result.get("qVariableList", {}).get("qItems", [])

    def _extract_fields_from_expression(self, expression: str) -> List[str]:
        """
        Extract field names from a complex expression.

        Args:
            expression: Qlik expression

        Returns:
            List of field names found in expression
        """
        fields = []
        if not expression:
            return fields
        bracket_fields = re.findall(r'\[([^\]]+)\]', expression)
        fields.extend(bracket_fields)
        return list(set(fields))
