import json
from . import (
    create_memory,
    get_memories,
    wipe_all_memories,
    search_memory,
    wipe_category,
)
from .base import get_client
from .memory import search_similar_memory
from ..utils.file_utils import calculate_file_hash


def export_memory_to_json(include_embeddings=False):
    """
    Export all memories to a dictionary, optionally including embeddings.

    Arguments:
        include_embeddings (bool, optional): Whether to include memory embeddings in the output.
                                             Defaults to True.

    Returns:
        dict: A dictionary with collection names as keys and lists of memories as values.

    Example:
        >>> export_memory_to_json()
    """

    collections = get_client().list_collections()

    collections_dict = {}

    # Iterate over all collections
    for collection in collections:
        collection_name = collection.name
        collections_dict[collection_name] = []

        # Get all memories from the current collection
        memories = get_memories(collection_name, include_embeddings=include_embeddings)
        for memory in memories:
            # Append each memory to its corresponding collection list
            collections_dict[collection_name].append(memory)

    return collections_dict


def export_memory_to_file(path="./memory.json", include_embeddings=False):
    """
    Export all memories to a JSON file, optionally including embeddings.

    Arguments:
        path (str, optional): The path to the output file. Defaults to "./memory.json".
        include_embeddings (bool, optional): Whether to include memory embeddings in the output.
                                             Defaults to True.

    Example:
        >>> export_memory_to_file(path="/path/to/output.json")
    """

    # Export the database to a dictionary
    collections_dict = export_memory_to_json(include_embeddings)

    print('collections_dict')
    print(collections_dict)

    # Write the dictionary to a JSON file
    with open(path, "w") as outfile:
        json.dump(collections_dict, outfile, ensure_ascii=False)


def import_json_to_memory(data, replace=True):
    """
    Import memories from a dictionary into the current database.

    Arguments:
        data (dict): A dictionary with collection names as keys and lists of memories as values.
        replace (bool, optional): Whether to replace existing memories. If True, all existing memories
                                  will be deleted before import. Defaults to True.

    Example:
        >>> import_json_to_memory(data)
    """

    # If replace flag is set to True, wipe out all existing memories
    if replace:
        wipe_all_memories()

    # Iterate over all collections in the input data
    for category in data:
        # Iterate over all memories in the current collection
        for memory in data[category]:
            # Create a new memory in the current category
            create_memory(
                category,
                text=memory["document"],
                metadata=memory["metadata"],
                id=memory["id"],
                embedding=memory.get("embedding", None),
            )


def import_file_to_memory(path="./memory.json", replace=True):
    """
    Import memories from a JSON file into the current database.

    Arguments:
        path (str, optional): The path to the input file. Defaults to "./memory.json".
        replace (bool, optional): Whether to replace existing memories. If True, all existing memories
                                  will be deleted before import. Defaults to True.

    Example:
        >>> import_file_to_memory(path="/path/to/input.json")
    """

    # Read the input JSON file
    with open(path, "r") as infile:
        data = json.load(infile)

    # Import the data into the database
    import_json_to_memory(data, replace)


def initialize_knowledge_txt_to_memory(path="knowledge.txt", category: str = "knowledge"):
    # 计算文件哈系
    knowledge_file_hash = calculate_file_hash(path)
    # 判断是文件是否改变
    memories = search_similar_memory(category, knowledge_file_hash, 1, 1)
    if len(memories) == 1 and memories[0]["distance"] == 0:
        return
    print(f"initialize knowledge {path} to memory: {knowledge_file_hash}")
    # 不存在或发生改变则 重建知识库memory
    wipe_category(category)

    with open(path, 'r') as file:
        lines = file.readlines()
    lines = [knowledge_file_hash] + lines
    for line in lines:
        create_memory(category, line.replace("\n", ""))