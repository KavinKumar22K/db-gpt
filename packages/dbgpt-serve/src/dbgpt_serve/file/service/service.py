import logging
from typing import BinaryIO, List, Optional, Tuple

from fastapi import HTTPException, UploadFile

from dbgpt.component import SystemApp
from dbgpt.core.interface.file import FileMetadata, FileStorageClient, FileStorageURI
from dbgpt.storage.metadata import BaseDao
from dbgpt.util.tracer import trace
from dbgpt_serve.core import BaseService

from ..api.schemas import (
    FileMetadataResponse,
    ServeRequest,
    ServerResponse,
    UploadFileResponse,
)
from ..config import SERVE_SERVICE_COMPONENT_NAME, ServeConfig
from ..models.models import ServeDao, ServeEntity

logger = logging.getLogger(__name__)


class Service(BaseService[ServeEntity, ServeRequest, ServerResponse]):
    """The service class for File"""

    name = SERVE_SERVICE_COMPONENT_NAME

    def __init__(
        self, system_app: SystemApp, config: ServeConfig, dao: Optional[ServeDao] = None
    ):
        self._system_app = None
        self._serve_config: ServeConfig = config
        self._dao: ServeDao = dao
        super().__init__(system_app)

    def init_app(self, system_app: SystemApp) -> None:
        """Initialize the service

        Args:
            system_app (SystemApp): The system app
        """
        super().init_app(system_app)
        self._dao = self._dao or ServeDao(self._serve_config)
        self._system_app = system_app

    @property
    def dao(self) -> BaseDao[ServeEntity, ServeRequest, ServerResponse]:
        """Returns the internal DAO."""
        return self._dao

    @property
    def config(self) -> ServeConfig:
        """Returns the internal ServeConfig."""
        return self._serve_config

    @property
    def file_storage_client(self) -> FileStorageClient:
        """Returns the internal FileStorageClient.

        Returns:
            FileStorageClient: The internal FileStorageClient
        """
        file_storage_client = FileStorageClient.get_instance(
            self._system_app, default_component=None
        )
        if file_storage_client:
            return file_storage_client
        else:
            from ..serve import Serve

            file_storage_client = Serve.get_instance(
                self._system_app
            ).file_storage_client
            self._system_app.register_instance(file_storage_client)
            return file_storage_client

    @trace("upload_files")
    def upload_files(
        self,
        bucket: str,
        files: List[UploadFile],
        user_name: Optional[str] = None,
        sys_code: Optional[str] = None,
    ) -> List[UploadFileResponse]:
        """Upload files by a list of UploadFile."""
        results = []
        for file in files:
            file_name = file.filename
            logger.info(f"Uploading file {file_name} to bucket {bucket} for user {user_name}")
            
            # Create user-specific bucket path
            user_bucket = f"{bucket}_{user_name}" if user_name else bucket
            
            custom_metadata = {
                "user_name": user_name,
                "sys_code": sys_code,
                "original_bucket": bucket,
            }
            uri = self.file_storage_client.save_file(
                user_bucket,
                file_name,
                file_data=file.file,
                custom_metadata=custom_metadata,
            )
            parsed_uri = FileStorageURI.parse(uri)
            logger.info(f"Uploaded file {file_name} to user bucket {user_bucket}, uri={uri}")
            results.append(
                UploadFileResponse(
                    file_name=file_name,
                    file_id=parsed_uri.file_id,
                    bucket=user_bucket,
                    uri=uri,
                )
            )
        return results

    def list_user_files(
        self, user_name: str, bucket: Optional[str] = None
    ) -> List[Dict]:
        """List files for a specific user."""
        try:
            # Query files from database where user_name matches
            with self.dao.session(commit=False) as session:
                query = session.query(self.dao.model_class).filter_by(user_name=user_name)
                if bucket:
                    # For user isolation, we need to check both original bucket and user bucket
                    user_bucket = f"{bucket}_{user_name}"
                    query = query.filter(
                        (self.dao.model_class.bucket == bucket) |
                        (self.dao.model_class.bucket == user_bucket)
                    )
                
                files = query.all()
                return [
                    {
                        "file_id": file.file_id,
                        "file_name": file.file_name,
                        "bucket": file.bucket,
                        "uri": file.uri,
                        "file_size": file.file_size,
                        "gmt_created": file.gmt_created.isoformat() if file.gmt_created else None,
                    }
                    for file in files
                ]
        except Exception as e:
            logger.error(f"Failed to list user files: {e}")
            return []

    def delete_user_file(self, user_name: str, file_id: str) -> bool:
        """Delete a file owned by a specific user."""
        try:
            with self.dao.session() as session:
                file_entity = (
                    session.query(self.dao.model_class)
                    .filter_by(user_name=user_name, file_id=file_id)
                    .first()
                )
                
                if file_entity:
                    # Delete from storage
                    self.file_storage_client.delete_file(file_entity.uri)
                    # Delete from database
                    session.delete(file_entity)
                    logger.info(f"Deleted file {file_id} for user {user_name}")
                    return True
                else:
                    logger.warning(f"File {file_id} not found for user {user_name}")
                    return False
        except Exception as e:
            logger.error(f"Failed to delete user file: {e}")
            return False

    @trace("download_file")
    def download_file(self, bucket: str, file_id: str) -> Tuple[BinaryIO, FileMetadata]:
        """Download a file by file_id."""
        return self.file_storage_client.get_file_by_id(bucket, file_id)

    def delete_file(self, bucket: str, file_id: str) -> None:
        """Delete a file by file_id."""
        self.file_storage_client.delete_file_by_id(bucket, file_id)

    def get_file_metadata(
        self,
        uri: Optional[str] = None,
        bucket: Optional[str] = None,
        file_id: Optional[str] = None,
    ) -> Optional[FileMetadataResponse]:
        """Get the metadata of a file by file_id."""
        if uri:
            parsed_uri = FileStorageURI.parse(uri)
            bucket, file_id = parsed_uri.bucket, parsed_uri.file_id
        if not (bucket and file_id):
            raise ValueError("Either uri or bucket and file_id must be provided.")
        metadata = self.file_storage_client.storage_system.get_file_metadata(
            bucket, file_id
        )
        if not metadata:
            raise HTTPException(
                status_code=404,
                detail=f"File metadata not found: bucket={bucket}, file_id={file_id}, "
                f"uri={uri}",
            )
        return FileMetadataResponse(
            file_name=metadata.file_name,
            file_id=metadata.file_id,
            bucket=metadata.bucket,
            uri=metadata.uri,
            file_size=metadata.file_size,
            user_name=metadata.user_name,
            sys_code=metadata.sys_code,
        )
