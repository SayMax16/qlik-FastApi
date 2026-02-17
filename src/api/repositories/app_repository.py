"""Repository for Qlik Sense application operations."""
from typing import List, Dict, Optional
import logging

from src.api.repositories.base import BaseRepository
from src.api.clients.qlik_repository import QlikRepositoryClient
from src.api.clients.qlik_engine import QlikEngineClient
from src.api.core.config import settings

logger = logging.getLogger(__name__)


class AppRepository(BaseRepository):
    """Repository for managing Qlik Sense applications."""

    def __init__(
        self,
        repository_client: QlikRepositoryClient,
        engine_client: QlikEngineClient
    ):
        """
        Initialize AppRepository with required clients.

        Args:
            repository_client: Client for Qlik Repository API operations
            engine_client: Client for Qlik Engine API operations
        """
        self.repository_client = repository_client
        self.engine_client = engine_client

    def get_app_id_by_name(self, app_name: str) -> Optional[str]:
        """
        Get application ID from application name using settings.app_mappings.

        Args:
            app_name: Name of the application

        Returns:
            Application ID if found, None otherwise
        """
        try:
            app_id = settings.get_app_id(app_name)
            if app_id:
                logger.info(f"Found app ID '{app_id}' for app name '{app_name}'")
            else:
                logger.warning(f"No app ID found for app name '{app_name}'")
            return app_id
        except Exception as e:
            logger.error(f"Error getting app ID for '{app_name}': {str(e)}")
            return None

    def get_app_metadata(self, app_id: str) -> Dict:
        """
        Get application metadata from Repository API.

        Args:
            app_id: ID of the application

        Returns:
            Dictionary containing app metadata
        """
        try:
            logger.info(f"Fetching metadata for app ID '{app_id}'")
            app_data = self.repository_client.get_app_by_id(app_id)

            # Extract relevant metadata
            metadata = {
                "id": app_data.get("id", app_id),
                "name": app_data.get("name", ""),
                "description": app_data.get("description", ""),
                "published": app_data.get("published", False),
                "stream": app_data.get("stream", {}),
                "owner": app_data.get("owner", {}),
                "created_date": app_data.get("createdDate", ""),
                "modified_date": app_data.get("modifiedDate", ""),
                "file_size": app_data.get("fileSize", 0)
            }

            logger.info(f"Successfully retrieved metadata for app '{metadata.get('name')}'")
            return metadata
        except Exception as e:
            logger.error(f"Error fetching app metadata for '{app_id}': {str(e)}")
            raise

    def list_all_apps(self) -> List[Dict]:
        """
        List all available applications from settings.app_mappings.

        Returns:
            List of dictionaries containing app information
        """
        try:
            app_mappings = settings.app_mappings or {}
            apps = []

            for app_name, app_id in app_mappings.items():
                apps.append({
                    "qDocId": app_id,
                    "qDocName": app_name,
                    "qTitle": app_name,
                    "qThumbnail": None,
                    "qLastReloadTime": None,
                    "qModifiedDate": None,
                    "qFileSize": None,
                    "published": False,
                    "stream_name": None
                })

            logger.info(f"Found {len(apps)} apps in configuration")
            return apps
        except Exception as e:
            logger.error(f"Error listing apps: {str(e)}")
            return []

    def get_app_fields(self, app_id: str) -> List[Dict]:
        """
        Get all fields in an application.

        Args:
            app_id: ID of the application

        Returns:
            List of dictionaries containing field information
        """
        try:
            logger.info(f"Fetching fields for app ID '{app_id}'")

            # Connect to engine
            self.engine_client.connect()

            try:
                # Open the app
                app = self.engine_client.open_doc(app_id)

                # Get field list
                field_list = app.GetFieldList()

                fields = []
                for field_info in field_list:
                    fields.append({
                        "name": field_info.get("qName", ""),
                        "src_tables": field_info.get("qSrcTables", []),
                        "is_system": field_info.get("qIsSystem", False),
                        "is_hidden": field_info.get("qIsHidden", False),
                        "is_semantic": field_info.get("qIsSemantic", False),
                        "distinct_count": field_info.get("qCardinal", 0),
                        "total_count": field_info.get("qTotalCount", 0),
                        "tags": field_info.get("qTags", [])
                    })

                logger.info(f"Found {len(fields)} fields in app '{app_id}'")
                return fields
            finally:
                # Always disconnect
                self.engine_client.disconnect()

        except Exception as e:
            logger.error(f"Error fetching fields for app '{app_id}': {str(e)}")
            raise

    def get_app_tables(self, app_id: str) -> List[str]:
        """
        Get all table names in an application.

        Args:
            app_id: ID of the application

        Returns:
            List of table names
        """
        try:
            logger.info(f"Fetching tables for app ID '{app_id}'")

            # Connect to engine
            self.engine_client.connect()

            try:
                # Open the app
                app = self.engine_client.open_doc(app_id)

                # Get table list
                table_list = app.GetTableList()

                tables = []
                for table_info in table_list:
                    table_name = table_info.get("qName", "")
                    if table_name:
                        tables.append(table_name)

                logger.info(f"Found {len(tables)} tables in app '{app_id}'")
                return tables
            finally:
                # Always disconnect
                self.engine_client.disconnect()

        except Exception as e:
            logger.error(f"Error fetching tables for app '{app_id}': {str(e)}")
            raise

    def check_connection(self) -> bool:
        """
        Test Qlik Sense connection.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            logger.info("Testing Qlik Sense connection")

            # Try to connect to engine
            self.engine_client.connect()

            try:
                # Try to get engine version to verify connection
                version = self.engine_client.get_engine_version()
                logger.info(f"Successfully connected to Qlik Engine version: {version}")
                return True
            finally:
                # Disconnect
                self.engine_client.disconnect()

        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False

    def get_object_definition(self, app_id: str, object_id: str) -> Dict:
        """
        Get dimensions and measures from a Qlik object (chart, table, etc.).

        Args:
            app_id: ID of the application
            object_id: ID of the object

        Returns:
            Dictionary containing dimensions and measures with their definitions
        """
        try:
            logger.info(f"Fetching object definition for '{object_id}' in app '{app_id}'")

            # Connect to engine
            self.engine_client.connect()

            try:
                # Open the app
                result = self.engine_client.open_doc(app_id, no_data=False)
                app_handle = result['qReturn']['qHandle']

                # Get the object
                obj_response = self.engine_client.send_request('GetObject', [object_id], handle=app_handle)
                obj_handle = obj_response['qReturn']['qHandle']

                # Get object info
                obj_info_response = self.engine_client.send_request('GetInfo', handle=obj_handle)
                obj_info = obj_info_response.get('qInfo', {})
                obj_type = obj_info.get('qType', 'unknown')

                # Get properties with full definitions
                properties = self.engine_client.send_request('GetProperties', handle=obj_handle)
                props = properties.get('qProp', {})
                hc_def = props.get('qHyperCubeDef', {})

                # Extract dimensions
                dimensions = []
                for dim_def in hc_def.get('qDimensions', []):
                    field_defs = dim_def.get('qDef', {}).get('qFieldDefs', [])
                    field_labels = dim_def.get('qDef', {}).get('qFieldLabels', [])

                    field = field_defs[0] if field_defs else None
                    label = field_labels[0] if field_labels else None

                    if field:
                        dimensions.append({
                            'field': field,
                            'label': label if label else field
                        })

                # Extract measures
                measures = []
                for measure_def in hc_def.get('qMeasures', []):
                    expression = measure_def.get('qDef', {}).get('qDef', '')
                    label = measure_def.get('qDef', {}).get('qLabel', '')
                    num_format = measure_def.get('qDef', {}).get('qNumFormat')

                    if expression:
                        measures.append({
                            'expression': expression,
                            'label': label if label else expression,
                            'number_format': num_format
                        })

                logger.info(f"Found {len(dimensions)} dimensions and {len(measures)} measures in object '{object_id}'")

                return {
                    'object_id': object_id,
                    'object_type': obj_type,
                    'app_id': app_id,
                    'dimensions': dimensions,
                    'measures': measures
                }

            finally:
                # Always disconnect
                self.engine_client.disconnect()

        except Exception as e:
            logger.error(f"Error fetching object definition for '{object_id}': {str(e)}")
            raise

    def get_pivot_object_data(self, app_id: str, object_id: str, page: int = 1, page_size: int = 100, selections: Dict = None, bookmark_id: str = None) -> Dict:
        """
        Get data from a pivot-table object using GetHyperCubePivotData.

        This is much faster than creating a session hypercube for pivot objects
        because it reads from the already-computed Qlik pivot table.

        When a bookmark_id is supplied, it is applied to the app session before
        fetching data so the pivot reflects the bookmarked filter state. This is
        critical for tables with many dimensions where an unfiltered pivot would
        be too large to compute.

        Args:
            app_id: ID of the application
            object_id: ID of the pivot table object
            page: Page number (1-based)
            page_size: Number of rows per page
            selections: Optional dict of field selections
            bookmark_id: Optional bookmark ID to apply before fetching

        Returns:
            Dictionary containing data rows with pagination
        """
        try:
            logger.info(f"Fetching pivot data from object '{object_id}' in app '{app_id}'")
            if bookmark_id:
                logger.info(f"Will apply bookmark '{bookmark_id}' before fetching")

            self.engine_client.connect()

            try:
                result = self.engine_client.open_doc(app_id, no_data=False)
                app_handle = result['qReturn']['qHandle']

                pivot_data = self.engine_client.get_pivot_data(
                    app_handle=app_handle,
                    object_id=object_id,
                    page=page,
                    page_size=page_size,
                    selections=selections or {},
                    bookmark_id=bookmark_id
                )

                if 'error' in pivot_data:
                    raise Exception(f"Pivot data error: {pivot_data['error']}")

                return pivot_data

            finally:
                self.engine_client.disconnect()

        except Exception as e:
            logger.error(f"Error fetching pivot data from '{object_id}': {str(e)}")
            raise

    def get_object_data(self, app_id: str, object_id: str, page: int = 1, page_size: int = 100, filters: Dict = None, selections: Dict = None) -> Dict:
        """
        Get actual data from a Qlik object with dimensions and measures.

        Args:
            app_id: ID of the application
            object_id: ID of the object
            page: Page number (1-based)
            page_size: Number of rows per page
            filters: Optional dictionary of field filters for client-side filtering (field_name: value)
            selections: Optional dictionary of field selections to apply in Qlik before retrieving data (field_name: [values])

        Returns:
            Dictionary containing data rows with dimension and measure values
        """
        try:
            logger.info(f"Fetching data from object '{object_id}' in app '{app_id}'")
            if filters:
                logger.info(f"Will apply client-side filters: {filters}")
            if selections:
                logger.info(f"Will apply Qlik selections: {selections}")

            # Connect to engine
            self.engine_client.connect()

            try:
                # Open the app
                result = self.engine_client.open_doc(app_id, no_data=False)
                app_handle = result['qReturn']['qHandle']

                # Apply Qlik selections if provided
                if selections:
                    for field_name, field_values in selections.items():
                        # Ensure field_values is a list
                        if not isinstance(field_values, list):
                            field_values = [field_values]

                        logger.info(f"Applying selection on field '{field_name}' with values: {field_values}")
                        try:
                            self.engine_client.select_values(app_handle, field_name, field_values)
                        except Exception as sel_error:
                            logger.warning(f"Failed to apply selection on '{field_name}': {str(sel_error)}")

                # Get the object
                obj_response = self.engine_client.send_request('GetObject', [object_id], handle=app_handle)
                obj_handle = obj_response['qReturn']['qHandle']

                # Get properties to extract dimensions and measures
                properties = self.engine_client.send_request('GetProperties', handle=obj_handle)
                props = properties.get('qProp', {})
                hc_def = props.get('qHyperCubeDef', {})

                # Extract dimension fields and labels
                dim_fields = []
                dim_labels = []
                for dim_def in hc_def.get('qDimensions', []):
                    field = dim_def.get('qDef', {}).get('qFieldDefs', [None])[0]
                    label = dim_def.get('qDef', {}).get('qFieldLabels', [None])[0]
                    if field:
                        dim_fields.append(field)
                        dim_labels.append(label if label else field)

                # Extract measure expressions and labels
                measure_expressions = []
                measure_labels = []
                for measure_def in hc_def.get('qMeasures', []):
                    expression = measure_def.get('qDef', {}).get('qDef', '')
                    label = measure_def.get('qDef', {}).get('qLabel', '')
                    if expression:
                        measure_expressions.append(expression)
                        measure_labels.append(label if label else expression)

                logger.info(f"Object has {len(dim_fields)} dimensions and {len(measure_expressions)} measures")

                # Create hypercube to get data - same method for all objects
                logger.info(f"Creating hypercube with {len(dim_fields)} dimensions and {len(measure_expressions)} measures")

                # Fetch more rows if filters are applied to allow client-side filtering
                fetch_rows = 1000 if filters else page_size
                hypercube_result = self.engine_client.create_hypercube(
                    app_handle=app_handle,
                    dimensions=dim_fields,
                    measures=measure_expressions,
                    max_rows=fetch_rows
                )

                if 'error' in hypercube_result:
                    raise Exception(f"Failed to create hypercube: {hypercube_result['error']}")

                # Extract data from hypercube
                hypercube_data = hypercube_result.get('hypercube_data', {})
                data_pages = hypercube_data.get('qDataPages', [])

                all_rows = []
                if data_pages:
                    matrix = data_pages[0].get('qMatrix', [])

                    for row in matrix:
                        row_data = {}

                        # Add dimension values
                        for i, label in enumerate(dim_labels):
                            if i < len(row):
                                cell = row[i]
                                row_data[label] = cell.get('qText', '')

                        # Add measure values
                        for i, label in enumerate(measure_labels):
                            cell_index = len(dim_labels) + i
                            if cell_index < len(row):
                                cell = row[cell_index]
                                # Try to get numeric value first, fallback to text
                                value = cell.get('qNum', None)
                                if value is None or str(value).lower() == 'nan':
                                    value = cell.get('qText', '')
                                row_data[label] = value

                        all_rows.append(row_data)

                # Apply client-side filters if provided
                filtered_rows = all_rows
                if filters:
                    # Map field names to their display labels
                    field_to_label = dict(zip(dim_fields, dim_labels))

                    for field_name, field_value in filters.items():
                        # Get the label that corresponds to this field
                        filter_label = field_to_label.get(field_name, field_name)

                        logger.info(f"Filtering by {filter_label} (field: {field_name}) = {field_value}")
                        filtered_rows = [
                            row for row in filtered_rows
                            if str(row.get(filter_label, '')).strip() == str(field_value).strip()
                        ]

                # Apply pagination to filtered results
                total_rows = len(filtered_rows)
                total_pages = (total_rows + page_size - 1) // page_size if total_rows > 0 else 1
                offset = (page - 1) * page_size
                data_rows = filtered_rows[offset:offset + page_size]

                logger.info(f"Retrieved {len(data_rows)} rows from object '{object_id}' (page {page}/{total_pages}, total {total_rows} rows)")

                return {
                    'object_id': object_id,
                    'app_id': app_id,
                    'data': data_rows,
                    'pagination': {
                        'page': page,
                        'page_size': page_size,
                        'total_rows': total_rows,
                        'total_pages': total_pages,
                        'has_next': page < total_pages,
                        'has_previous': page > 1
                    }
                }

            finally:
                # Clear selections if they were applied
                if selections:
                    try:
                        logger.info("Clearing selections before disconnect")
                        self.engine_client.clear_all(app_handle)
                    except Exception as clear_error:
                        logger.warning(f"Failed to clear selections: {str(clear_error)}")

                # Always disconnect
                self.engine_client.disconnect()

        except Exception as e:
            logger.error(f"Error fetching data from object '{object_id}': {str(e)}")
            raise
