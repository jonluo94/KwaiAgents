import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Callable

import pluggy

from .config import MEMORY_TYPE

hookspec = pluggy.HookspecMarker("agentmemory")
hookimpl = pluggy.HookimplMarker("agentmemory")


class ClientFactorySpec:
    @hookspec
    def declare_client(self, factory_map: Dict[str, Callable]):
        return factory_map


class ChromaFactory:
    @hookimpl
    def declare_client(self, factory_map: Dict[str, Callable]):
        def make_chroma_client():
            from .chroma_memory import create_client
            return create_client()

        factory_map["CHROMA"] = make_chroma_client
        return factory_map


class PostgresFactory:
    @hookimpl
    def declare_client(self, factory_map: Dict[str, Callable]):
        def make_postgres_client():
            from .postgres_memory import create_client
            return create_client()

        factory_map["POSTGRES"] = make_postgres_client
        return factory_map


plugin_manager = None


def get_plugin_manager():
    global plugin_manager
    if plugin_manager is not None:
        return plugin_manager
    pm = pluggy.PluginManager("agentmemory")
    pm.add_hookspecs(ClientFactorySpec)
    pm.register(ChromaFactory())
    pm.register(PostgresFactory())
    pm.load_setuptools_entrypoints("agentmemory")
    plugin_manager = pm
    return plugin_manager


class CollectionMemory(ABC):
    @abstractmethod
    def count(self):
        raise NotImplementedError()

    @abstractmethod
    def add(self, ids, documents=None, metadatas=None, embeddings=None):
        raise NotImplementedError()

    @abstractmethod
    def get(
            self,
            ids=None,
            where=None,
            limit=None,
            offset=None,
            where_document=None,
            include=["metadatas", "documents"],
    ):
        raise NotImplementedError()

    @abstractmethod
    def peek(self, limit=10):
        raise NotImplementedError()

    @abstractmethod
    def query(
            self,
            query_embeddings=None,
            query_texts=None,
            n_results=10,
            where=None,
            where_document=None,
            include=["metadatas", "documents", "distances"],
    ):
        raise NotImplementedError()

    @abstractmethod
    def update(self, ids, documents=None, metadatas=None, embeddings=None):
        raise NotImplementedError()

    @abstractmethod
    def upsert(self, ids, documents=None, metadatas=None, embeddings=None):
        raise NotImplementedError()

    @abstractmethod
    def delete(self, ids=None, where=None, where_document=None):
        raise NotImplementedError()


@dataclass
class AgentCollection():
    name: str


class AgentMemory(ABC):
    @abstractmethod
    def get_or_create_collection(self, category, metadata=None) -> CollectionMemory:
        raise NotImplementedError()

    @abstractmethod
    def delete_collection(self, category):
        raise NotImplementedError()

    @abstractmethod
    def list_collections(self) -> List[AgentCollection]:
        raise NotImplementedError()


def get_client(memory_type=None):
    memory_type = memory_type or MEMORY_TYPE

    factory_map = {}
    pm = get_plugin_manager()
    pm.hook.declare_client(factory_map=factory_map)
    if memory_type not in factory_map:
        raise RuntimeError("Unknown client type: {memory_type}")
    client = factory_map[memory_type]()

    return client
