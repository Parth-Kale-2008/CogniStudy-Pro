"""
Vector Store Management using FAISS.
Provides multi-tenant indexing, persistent storage, metadata tracking, and similarity search.
"""

import json
import os
import shutil
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

from app.config import settings
from app.core.logging import logger
from app.rag.embeddings import get_embedding_provider


class VectorStoreManager:
    """
    Manages FAISS vector databases isolated per user/tenant.
    Maintains document metadata registries for tracking uploaded files.
    """

    def __init__(self, base_storage_dir: Optional[str] = None):
        self.base_storage_dir = base_storage_dir or settings.INDEX_STORAGE_DIR
        os.makedirs(self.base_storage_dir, exist_ok=True)
        self.embedding_provider = get_embedding_provider()

    def _get_user_path(self, user_id: str) -> str:
        safe_user_id = "".join(c for c in str(user_id) if c.isalnum() or c in ("-", "_"))
        return os.path.join(self.base_storage_dir, safe_user_id or "default")

    def _get_metadata_file(self, user_id: str) -> str:
        return os.path.join(self._get_user_path(user_id), "documents_metadata.json")

    def _load_metadata(self, user_id: str) -> List[Dict[str, Any]]:
        meta_file = self._get_metadata_file(user_id)
        if os.path.exists(meta_file):
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error reading metadata for user {user_id}: {e}")
        return []

    def _save_metadata(self, user_id: str, metadata_list: List[Dict[str, Any]]) -> None:
        user_path = self._get_user_path(user_id)
        os.makedirs(user_path, exist_ok=True)
        meta_file = self._get_metadata_file(user_id)
        try:
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(metadata_list, f, indent=2)
        except Exception as e:
            logger.error(f"Error writing metadata for user {user_id}: {e}")

    def add_documents(
        self,
        user_id: str,
        documents: List[Document],
        doc_metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Indexes documents into user's private FAISS vector store.
        Returns the number of indexed chunks.
        """
        if not documents:
            return 0

        user_path = self._get_user_path(user_id)
        os.makedirs(user_path, exist_ok=True)

        index_file = os.path.join(user_path, "index.faiss")

        if os.path.exists(index_file):
            try:
                db = FAISS.load_local(
                    user_path,
                    self.embedding_provider,
                    allow_dangerous_deserialization=True
                )
                db.add_documents(documents)
            except Exception as e:
                logger.warning(f"Could not load existing user index ({e}). Rebuilding new index.")
                db = FAISS.from_documents(documents, self.embedding_provider)
        else:
            db = FAISS.from_documents(documents, self.embedding_provider)

        db.save_local(user_path)

        if doc_metadata:
            current_meta = self._load_metadata(user_id)
            current_meta.append(doc_metadata)
            self._save_metadata(user_id, current_meta)

        logger.info(f"Indexed {len(documents)} chunks for user '{user_id}' in {user_path}")
        return len(documents)

    def similarity_search(self, user_id: str, query: str, k: int = 4) -> List[Document]:
        """
        Searches the user's vector store. If not found, checks the global default index.
        """
        user_path = self._get_user_path(user_id)
        user_index = os.path.join(user_path, "index.faiss")

        # Fallback to root or default index if user has not uploaded any docs yet
        default_index = os.path.join(settings.DEFAULT_INDEX_DIR, "index.faiss")

        target_dir = None
        if os.path.exists(user_index):
            target_dir = user_path
        elif os.path.exists(default_index):
            target_dir = settings.DEFAULT_INDEX_DIR

        if not target_dir:
            return []

        try:
            db = FAISS.load_local(
                target_dir,
                self.embedding_provider,
                allow_dangerous_deserialization=True
            )
            return db.similarity_search(query, k=k)
        except Exception as e:
            logger.error(f"FAISS search failed for user '{user_id}': {e}", exc_info=True)
            return []

    def get_user_documents(self, user_id: str) -> List[Dict[str, Any]]:
        return self._load_metadata(user_id)

    def clear_user_index(self, user_id: str) -> bool:
        """
        Deletes user's vector store index and metadata.
        """
        user_path = self._get_user_path(user_id)
        if os.path.exists(user_path):
            try:
                shutil.rmtree(user_path)
                logger.info(f"Purged index for user '{user_id}'")
                return True
            except Exception as e:
                logger.error(f"Error purging index for user '{user_id}': {e}")
                return False
        return True

    def count_tenants(self) -> int:
        """
        Counts active user tenant directories.
        """
        if not os.path.exists(self.base_storage_dir):
            return 0
        return len([d for d in os.listdir(self.base_storage_dir) if os.path.isdir(os.path.join(self.base_storage_dir, d))])
