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
                    "name": app_name,
                    "id": app_id
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
