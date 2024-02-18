from dotenv import load_dotenv

from .memory import (
    create_memory,
    create_unique_memory,
    get_memories,
    search_memory,
    search_similar_memory,
    get_memory,
    update_memory,
    delete_memory,
    delete_memories,
    delete_similar_memories,
    count_memories,
    wipe_category,
    wipe_all_memories,
)

from .helpers import (
    chroma_collection_to_list,
    list_to_chroma_collection,
)

from .persistence import (
    export_memory_to_json,
    export_memory_to_file,
    import_json_to_memory,
    import_file_to_memory,
)

from .base import (
    get_client,
    hookimpl,
)

from .embedding import (
    init_embedding,
)

load_dotenv()

__all__ = [
    "create_memory",
    "create_unique_memory",
    "get_memories",
    "search_memory",
    "get_memory",
    "update_memory",
    "delete_memory",
    "delete_memories",
    "delete_similar_memories",
    "count_memories",
    "wipe_category",
    "wipe_all_memories",
    "chroma_collection_to_list",
    "list_to_chroma_collection",
    "export_memory_to_json",
    "export_memory_to_file",
    "import_json_to_memory",
    "import_file_to_memory",
    "get_client",
    "hookimpl",
    "init_embedding",
]
