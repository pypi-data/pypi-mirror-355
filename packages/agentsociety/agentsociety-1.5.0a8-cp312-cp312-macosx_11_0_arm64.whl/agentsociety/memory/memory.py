import asyncio
from collections import defaultdict, deque
from collections.abc import Callable, Sequence
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Literal, Optional, Union

from langchain_core.embeddings import Embeddings

from ..environment import Environment
from ..logger import get_logger
from ..utils.decorators import lock_decorator
from .const import *
from .faiss_query import FaissQuery
from .profile import ProfileMemory
from .self_define import DynamicMemory
from .state import StateMemory


from ..memory.const import SocialRelation


class MemoryTag(str, Enum):
    """Memory tag enumeration class"""

    MOBILITY = "mobility"
    SOCIAL = "social"
    ECONOMY = "economy"
    COGNITION = "cognition"
    OTHER = "other"
    EVENT = "event"


@dataclass
class MemoryNode:
    """
    A data class representing a memory node.

    - **Attributes**:
        - `tag`: The tag associated with the memory node.
        - `day`: Day of the event or memory.
        - `t`: Time stamp or order.
        - `location`: Location where the event occurred.
        - `description`: Description of the memory.
        - `cognition_id`: ID related to cognitive memory (optional).
        - `id`: Unique ID for this memory node (optional).
    """

    tag: MemoryTag
    day: int
    t: int
    location: str
    description: str
    cognition_id: Optional[int] = None  # ID related to cognitive memory
    id: Optional[int] = None  # Unique ID for the memory node


class StreamMemory:
    """
    A class used to store and manage time-ordered stream information.

    - **Attributes**:
        - `_memories`: A deque to store memory nodes with a maximum length limit.
        - `_memory_id_counter`: An internal counter to generate unique IDs for each new memory node.
        - `_faiss_query`: The Faiss query object for search functionality.
        - `_embedding_model`: The embedding model object for vectorizing text or other data.
        - `_agent_id`: Identifier for the agent owning these memories.
        - `_status_memory`: The status memory object.
        - `_simulator`: The simulator object.
    """

    def __init__(
        self,
        agent_id: int,
        environment: Environment,
        faiss_query: FaissQuery,
        embedding_model: Embeddings,
        max_len: int = 1000,
    ):
        """
        Initialize an instance of StreamMemory.

        - **Args**:
            - `agent_id` (int): The ID of the agent.
            - `environment` (Environment): The environment object.
            - `faiss_query` (FaissQuery): The Faiss query object.
            - `embedding_model` (Embeddings): The embedding model object.
            - `max_len` (int): Maximum length of the deque. Default is 1000.
        """
        self._memories: deque = deque(maxlen=max_len)  # Limit the maximum storage
        self._memory_id_counter: int = 0  # Used for generating unique IDs
        self._agent_id = agent_id
        self._status_memory = None
        self._environment = environment
        self._faiss_query = faiss_query
        self._embedding_model = embedding_model

    @property
    def faiss_query(
        self,
    ) -> FaissQuery:
        """
        Get the Faiss query object.

        - **Returns**:
            - `FaissQuery`: Instance of the Faiss query object.
        """
        assert self._faiss_query is not None
        return self._faiss_query

    @property
    def status_memory(
        self,
    ):
        """
        Get the status memory object.

        - **Returns**:
            - `StatusMemory`: Instance of the status memory object.
        """
        assert self._status_memory is not None
        return self._status_memory

    def set_status_memory(self, status_memory):
        """
        Set the status memory object.

        - **Args**:
            - `status_memory` (StatusMemory): Status memory object.
        """
        self._status_memory = status_memory

    async def _add_memory(self, tag: MemoryTag, description: str) -> int:
        """
        A generic method for adding a memory node and returning the memory node ID.

        - **Args**:
            - `tag` (MemoryTag): The tag associated with the memory node.
            - `description` (str): Description of the memory.

        - **Returns**:
            - `int`: The unique ID of the newly added memory node.
        """
        day, t = self._environment.get_datetime()
        position = await self.status_memory.get("position")
        if "aoi_position" in position:
            location = position["aoi_position"]["aoi_id"]
        elif "lane_position" in position:
            location = position["lane_position"]["lane_id"]
        else:
            location = "unknown"

        current_id = self._memory_id_counter
        self._memory_id_counter += 1
        memory_node = MemoryNode(
            tag=tag,
            day=day,
            t=t,
            location=location,
            description=description,
            id=current_id,
        )
        self._memories.append(memory_node)

        # create embedding for new memories
        if self._embedding_model and self._faiss_query:
            await self.faiss_query.add_documents(
                agent_id=self._agent_id,
                documents=description,
                extra_tags={
                    "type": "stream",
                    "tag": tag,
                    "day": day,
                    "time": t,
                },
            )

        return current_id

    async def add_cognition(self, description: str) -> int:
        """
        Add a cognition memory node.

        - **Args**:
            - `description` (str): Description of the cognition memory.

        - **Returns**:
            - `int`: The unique ID of the newly added cognition memory node.
        """
        return await self._add_memory(MemoryTag.COGNITION, description)

    async def add_social(self, description: str) -> int:
        """
        Add a social memory node.

        - **Args**:
            - `description` (str): Description of the social memory.

        - **Returns**:
            - `int`: The unique ID of the newly added social memory node.
        """
        return await self._add_memory(MemoryTag.SOCIAL, description)

    async def add_economy(self, description: str) -> int:
        """
        Add an economy memory node.

        - **Args**:
            - `description` (str): Description of the economy memory.

        - **Returns**:
            - `int`: The unique ID of the newly added economy memory node.
        """
        return await self._add_memory(MemoryTag.ECONOMY, description)

    async def add_mobility(self, description: str) -> int:
        """
        Add a mobility memory node.

        - **Args**:
            - `description` (str): Description of the mobility memory.

        - **Returns**:
            - `int`: The unique ID of the newly added mobility memory node.
        """
        return await self._add_memory(MemoryTag.MOBILITY, description)

    async def add_event(self, description: str) -> int:
        """
        Add an event memory node.

        - **Args**:
            - `description` (str): Description of the event memory.

        - **Returns**:
            - `int`: The unique ID of the newly added event memory node.
        """
        return await self._add_memory(MemoryTag.EVENT, description)

    async def add_other(self, description: str) -> int:
        """
        Add an other type memory node.

        - **Args**:
            - `description` (str): Description of the other type memory.

        - **Returns**:
            - `int`: The unique ID of the newly added other type memory node.
        """
        return await self._add_memory(MemoryTag.OTHER, description)

    async def get_related_cognition(self, memory_id: int) -> Union[MemoryNode, None]:
        """
        Retrieve the related cognition memory node by its ID.

        - **Args**:
            - `memory_id` (int): The ID of the memory to find related cognition for.

        - **Returns**:
            - `Optional[MemoryNode]`: The related cognition memory node, if found; otherwise, None.
        """
        for memory in self._memories:
            if memory.cognition_id == memory_id:
                for cognition_memory in self._memories:
                    if (
                        cognition_memory.tag == MemoryTag.COGNITION
                        and memory.cognition_id is not None
                    ):
                        return cognition_memory
        return None

    async def format_memory(self, memories: list[MemoryNode]) -> str:
        """
        Format a list of memory nodes into a readable string representation.

        - **Args**:
            - `memories` (list[MemoryNode]): List of MemoryNode objects to format.

        - **Returns**:
            - `str`: A formatted string containing the details of each memory node.
        """
        formatted_results = []
        for memory in memories:
            memory_tag = memory.tag
            memory_day = memory.day
            memory_time_seconds = memory.t
            cognition_id = memory.cognition_id

            # Format time
            if memory_time_seconds != "unknown":
                hours = memory_time_seconds // 3600
                minutes = (memory_time_seconds % 3600) // 60
                seconds = memory_time_seconds % 60
                memory_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                memory_time = "unknown"

            memory_location = memory.location

            # Add cognition information (if exists)
            cognition_info = ""
            if cognition_id is not None:
                cognition_memory = await self.get_related_cognition(cognition_id)
                if cognition_memory:
                    cognition_info = (
                        f"\n  Related cognition: {cognition_memory.description}"
                    )

            formatted_results.append(
                f"- [{memory_tag}]: {memory.description} [day: {memory_day}, time: {memory_time}, "
                f"location: {memory_location}]{cognition_info}"
            )
        return "\n".join(formatted_results)

    async def get_by_ids(self, memory_ids: Union[int, list[int]]) -> str:
        """Retrieve memories by specified IDs"""
        memories = [memory for memory in self._memories if memory.id in memory_ids]
        sorted_results = sorted(memories, key=lambda x: (x.day, x.t), reverse=True)
        return await self.format_memory(sorted_results)

    async def search(
        self,
        query: str,
        tag: Optional[MemoryTag] = None,
        top_k: int = 3,
        day_range: Optional[tuple[int, int]] = None,
        time_range: Optional[tuple[int, int]] = None,
    ) -> str:
        """
        Search stream memory with optional filters and return formatted results.

        - **Args**:
            - `query` (str): The text to use for searching.
            - `tag` (Optional[MemoryTag], optional): Filter memories by this tag. Defaults to None.
            - `top_k` (int, optional): Number of top relevant memories to return. Defaults to 3.
            - `day_range` (Optional[tuple[int, int]], optional): Tuple of start and end days for filtering. Defaults to None.
            - `time_range` (Optional[tuple[int, int]], optional): Tuple of start and end times for filtering. Defaults to None.

        - **Returns**:
            - `str`: Formatted string of the search results.
        """
        filter_dict: dict[str, Any] = {"type": "stream"}

        if tag:
            filter_dict["tag"] = tag

        # Add time range filter
        if day_range:
            start_day, end_day = day_range
            filter_dict["day"] = lambda x: start_day <= x <= end_day

        if time_range:
            start_time, end_time = time_range
            filter_dict["time"] = lambda x: start_time <= x <= end_time

        top_results = await self.faiss_query.similarity_search(
            query=query,
            agent_id=self._agent_id,
            k=top_k,
            return_score_type="similarity_score",
            filter=filter_dict,
        )

        # Sort results by time (first by day, then by time)
        sorted_results = sorted(
            top_results,
            key=lambda x: (x[2].get("day", 0), x[2].get("time", 0)),
            reverse=True,
        )

        formatted_results = []
        for content, score, metadata in sorted_results:
            memory_tag = metadata.get("tag", "unknown")
            memory_day = metadata.get("day", "unknown")
            memory_time_seconds = metadata.get("time", "unknown")
            cognition_id = metadata.get("cognition_id", None)

            # Format time
            if memory_time_seconds != "unknown":
                hours = memory_time_seconds // 3600
                minutes = (memory_time_seconds % 3600) // 60
                seconds = memory_time_seconds % 60
                memory_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                memory_time = "unknown"

            memory_location = metadata.get("location", "unknown")

            # Add cognition information (if exists)
            cognition_info = ""
            if cognition_id is not None:
                cognition_memory = await self.get_related_cognition(cognition_id)
                if cognition_memory:
                    cognition_info = (
                        f"\n  Related cognition: {cognition_memory.description}"
                    )

            formatted_results.append(
                f"- [{memory_tag}]: {content} [day: {memory_day}, time: {memory_time}, "
                f"location: {memory_location}]{cognition_info}"
            )
        return "\n".join(formatted_results)

    async def search_today(
        self,
        query: str = "",  # Optional query text
        tag: Optional[MemoryTag] = None,
        top_k: int = 100,  # Default to a larger number to ensure all memories of the day are retrieved
    ) -> str:
        """Search all memory events from today

        - **Args**:
            query: Optional query text, returns all memories of the day if empty
            tag: Optional memory tag for filtering specific types of memories
            top_k: Number of most relevant memories to return, defaults to 100

        - **Returns**:
            str: Formatted text of today's memories
        """
        current_day, _ = self._environment.get_datetime()
        # Use the search method, setting day_range to today
        return await self.search(
            query=query, tag=tag, top_k=top_k, day_range=(current_day, current_day)
        )

    async def add_cognition_to_memory(
        self, memory_id: Union[int, list[int]], cognition: str
    ) -> None:
        """
        Add cognition to existing memory nodes.

        - **Args**:
            - `memory_id` (Union[int, list[int]]): ID or list of IDs of the memories to which cognition will be added.
            - `cognition` (str): Description of the cognition to add.
        """
        # Convert a single ID into a list for unified processing
        memory_ids = [memory_id] if isinstance(memory_id, int) else memory_id

        # Find all corresponding memories
        target_memories = []
        for memory in self._memories:
            if memory.id in memory_ids:
                target_memories.append(memory)

        if not target_memories:
            raise ValueError(f"No memories found with ids {memory_ids}")

        # Add cognitive memory
        cognition_id = await self._add_memory(MemoryTag.COGNITION, cognition)

        # Update the cognition_id of all original memories
        for target_memory in target_memories:
            target_memory.cognition_id = cognition_id

    async def get_all(self) -> list[dict]:
        """
        Retrieve all stream memory nodes as dictionaries.

        - **Returns**:
            - `list[dict]`: List of all memory nodes as dictionaries.
        """
        return [
            {
                "id": memory.id,
                "cognition_id": memory.cognition_id,
                "tag": memory.tag.value,
                "location": memory.location,
                "description": memory.description,
                "day": memory.day,
                "t": memory.t,
            }
            for memory in self._memories
        ]


class StatusMemory:
    """Combine existing three types of memories into a single interface."""

    def __init__(
        self,
        agent_id: int,
        environment: Environment,
        faiss_query: FaissQuery,
        embedding_model: Embeddings,
        profile: ProfileMemory,
        state: StateMemory,
        dynamic: DynamicMemory,
    ):
        """
        Initialize the StatusMemory with three types of memory.

        - **Args**:
            - `agent_id` (int): The ID of the agent.
            - `environment` (Environment): The environment object.
            - `faiss_query` (FaissQuery): The Faiss query object.
            - `embedding_model` (Embeddings): The embedding model object.
            - `profile`: Profile memory instance.
            - `state`: State memory instance.
            - `dynamic`: Dynamic memory instance.
        """
        self.profile = profile
        self.state = state
        self.dynamic = dynamic
        self._faiss_query = faiss_query
        self._embedding_model = embedding_model
        self._environment = environment
        self._agent_id = agent_id
        self._semantic_templates = {}  # User-configurable templates
        self._embedding_fields = {}  # Fields that require embedding
        self._embedding_field_to_doc_id = defaultdict(str)  # Newly added
        self.watchers = {}  # Newly added
        self._lock = asyncio.Lock()  # Newly added

    @property
    def faiss_query(
        self,
    ) -> FaissQuery:
        """Get the Faiss query component."""
        assert self._faiss_query is not None
        return self._faiss_query

    async def initialize_embeddings(self) -> None:
        """Initialize embeddings for all fields that require them."""

        # Retrieve all status information
        profile, state, dynamic = await self.export()

        # Create embeddings for each field that requires it
        for key, value in profile[0].items():
            if self.should_embed(key):
                semantic_text = self._generate_semantic_text(key, value)
                doc_ids = await self.faiss_query.add_documents(
                    agent_id=self._agent_id,
                    documents=semantic_text,
                    extra_tags={
                        "type": "profile_state",
                        "key": key,
                    },
                )
                self._embedding_field_to_doc_id[key] = doc_ids[0]

        for key, value in state[0].items():
            if self.should_embed(key):
                semantic_text = self._generate_semantic_text(key, value)
                doc_ids = await self.faiss_query.add_documents(
                    agent_id=self._agent_id,
                    documents=semantic_text,
                    extra_tags={
                        "type": "profile_state",
                        "key": key,
                    },
                )
                self._embedding_field_to_doc_id[key] = doc_ids[0]

        for key, value in dynamic[0].items():
            if self.should_embed(key):
                semantic_text = self._generate_semantic_text(key, value)
                doc_ids = await self.faiss_query.add_documents(
                    agent_id=self._agent_id,
                    documents=semantic_text,
                    extra_tags={
                        "type": "profile_state",
                        "key": key,
                    },
                )
                self._embedding_field_to_doc_id[key] = doc_ids[0]

    def _get_memory_type_by_key(self, key: str) -> str:
        """Determine the type of memory based on the key name."""
        try:
            if key in self.profile.__dict__:
                return "profile"
            elif key in self.state.__dict__:
                return "state"
            else:
                return "dynamic"
        except:
            return "dynamic"

    def set_semantic_templates(self, templates: dict[str, str]):
        """
        Set the semantic templates for generating embedding text.

        - **Args**:
            - `templates` (Dict[str, str]): A dictionary of key-value pairs where keys are field names and values are template strings.
        """
        self._semantic_templates = templates

    def _generate_semantic_text(self, key: str, value: Any) -> str:
        """
        Generate semantic text for a given key and value.

        If a custom template exists for the key, it uses that template;
        otherwise, it uses a default template "My {key} is {value}".

        - **Args**:
            - `key` (str): The name of the field.
            - `value` (Any): The value associated with the field.

        - **Returns**:
            - `str`: The generated semantic text.
        """
        if key in self._semantic_templates:
            return self._semantic_templates[key].format(value)
        return f"My {key} is {value}"

    @lock_decorator
    async def search(
        self, query: str, top_k: int = 3, filter: Optional[dict] = None
    ) -> str:
        """
        Search for relevant memories based on the provided query.

        - **Args**:
            - `query` (str): The text query to search for.
            - `top_k` (int, optional): Number of top relevant memories to return. Defaults to 3.
            - `filter` (Optional[dict], optional): Additional filters for the search. Defaults to None.

        - **Returns**:
            - `str`: Formatted string of the search results.
        """
        filter_dict = {"type": "profile_state"}
        if filter is not None:
            filter_dict.update(filter)
        top_results: list[tuple[str, Optional[float], dict]] = (
            await self.faiss_query.similarity_search(
                query=query,
                agent_id=self._agent_id,
                k=top_k,
                return_score_type="similarity_score",
                filter=filter_dict,
            )
        )
        # formatted results
        formatted_results = []
        for content, score, metadata in top_results:
            formatted_results.append(f"- {content} ")

        return "\n".join(formatted_results)

    def set_embedding_fields(self, embedding_fields: Dict[str, bool]):
        """
        Set which fields require embeddings.

        - **Args**:
            - `embedding_fields` (Dict[str, bool]): Dictionary indicating whether each field should be embedded.
        """
        self._embedding_fields = embedding_fields

    def should_embed(self, key: str) -> bool:
        """
        Determine if a given field requires an embedding.

        - **Args**:
            - `key` (str): The name of the field.

        - **Returns**:
            - `bool`: True if the field should be embedded, False otherwise.
        """
        return self._embedding_fields.get(key, False)

    @lock_decorator
    async def get(
        self,
        key: Any,
        default_value: Optional[Any] = None,
        mode: Union[Literal["read only"], Literal["read and write"]] = "read only",
    ) -> Any:
        """
        Retrieve a value from the memory.

        - **Args**:
            - `key` (Any): The key to retrieve.
            - `default_value` (Optional[Any], optional): Default value if the key is not found. Defaults to None.
            - `mode` (Union[Literal["read only"], Literal["read and write"]], optional): Access mode for the value. Defaults to "read only".

        - **Returns**:
            - `Any`: The retrieved value or the default value if the key is not found.

        - **Raises**:
            - `ValueError`: If an invalid mode is provided.
            - `KeyError`: If the key is not found in any of the memory sections and no default value is provided.
        """
        if mode == "read only":
            process_func = deepcopy
        elif mode == "read and write":
            process_func = lambda x: x
        else:
            raise ValueError(f"Invalid get mode `{mode}`!")

        for mem in [self.state, self.profile, self.dynamic]:
            try:
                value = await mem.get(key)
                return process_func(value)
            except KeyError:
                continue
        if default_value is None:
            raise KeyError(f"No attribute `{key}` in memories!")
        else:
            return default_value

    @lock_decorator
    async def update(
        self,
        key: Any,
        value: Any,
        mode: Union[Literal["replace"], Literal["merge"]] = "replace",
        store_snapshot: bool = False,
        protect_llm_read_only_fields: bool = True,
    ) -> None:
        """
        Update a value in the memory and refresh embeddings if necessary.

        - **Args**:
            - `key` (Any): The key to update.
            - `value` (Any): The new value to set.
            - `mode` (Union[Literal["replace"], Literal["merge"]], optional): Update mode. Defaults to "replace".
            - `store_snapshot` (bool, optional): Whether to store a snapshot. Defaults to False.
            - `protect_llm_read_only_fields` (bool, optional): Whether to protect certain fields from being updated. Defaults to True.

        - **Raises**:
            - `ValueError`: If an invalid update mode is provided.
            - `KeyError`: If the key is not found in any of the memory sections.
        """
        if protect_llm_read_only_fields:
            if any(key in _attrs for _attrs in [STATE_ATTRIBUTES]):
                get_logger().warning(f"Trying to write protected key `{key}`!")
                return

        for mem in [self.state, self.profile, self.dynamic]:
            try:
                original_value = await mem.get(key)
                if mode == "replace":
                    await mem.update(key, value, store_snapshot)
                    if self.should_embed(key) and self._embedding_model:
                        semantic_text = self._generate_semantic_text(key, value)

                        # delete old embedding
                        orig_doc_id = self._embedding_field_to_doc_id[key]
                        if orig_doc_id:
                            await self.faiss_query.delete_documents(
                                to_delete_ids=[orig_doc_id],
                            )

                        # add new embedding
                        doc_ids = await self.faiss_query.add_documents(
                            agent_id=self._agent_id,
                            documents=semantic_text,
                            extra_tags={
                                "type": self._get_memory_type(mem),
                                "key": key,
                            },
                        )
                        self._embedding_field_to_doc_id[key] = doc_ids[0]

                    if key in self.watchers:
                        for callback in self.watchers[key]:
                            asyncio.create_task(callback())

                elif mode == "merge":
                    if isinstance(original_value, set):
                        original_value.update(set(value))
                    elif isinstance(original_value, dict):
                        original_value.update(dict(value))
                    elif isinstance(original_value, list):
                        original_value.extend(list(value))
                    elif isinstance(original_value, deque):
                        original_value.extend(deque(value))
                    else:
                        get_logger().debug(
                            f"Type of {type(original_value)} does not support mode `merge`, using `replace` instead!"
                        )
                        await mem.update(key, value, store_snapshot)
                    if self.should_embed(key) and self._embedding_model:
                        semantic_text = self._generate_semantic_text(key, value)
                        doc_ids = await self.faiss_query.add_documents(
                            agent_id=self._agent_id,
                            documents=f"{key}: {str(original_value)}",
                            extra_tags={
                                "type": self._get_memory_type(mem),
                                "key": key,
                            },
                        )
                        self._embedding_field_to_doc_id[key] = doc_ids[0]
                    if key in self.watchers:
                        for callback in self.watchers[key]:
                            asyncio.create_task(callback())
                else:
                    raise ValueError(f"Invalid update mode `{mode}`!")
                return
            except KeyError:
                continue
        raise KeyError(f"No attribute `{key}` in memories!")

    def _get_memory_type(self, mem: Any) -> str:
        """
        Determine the type of memory.

        - **Args**:
            - `mem` (Any): The memory instance to check.

        - **Returns**:
            - `str`: The type of memory ("state", "profile", or "dynamic").
        """
        if mem is self.state:
            return "state"
        elif mem is self.profile:
            return "profile"
        else:
            return "dynamic"

    @lock_decorator
    async def add_watcher(self, key: str, callback: Callable) -> None:
        """
        Add a watcher for value changes on a specific key.

        - **Args**:
            - `key` (str): The key to watch.
            - `callback` (Callable): The function to call when the watched key's value changes.
        """
        if key not in self.watchers:
            self.watchers[key] = []
        self.watchers[key].append(callback)

    async def export(
        self,
    ) -> tuple[Sequence[dict], Sequence[dict], Sequence[dict]]:
        """
        Export the current state of all memory sections.

        - **Returns**:
            - `Tuple[Sequence[Dict], Sequence[Dict], Sequence[Dict]]`: A tuple containing the exported data from profile, state, and dynamic memory sections.
        """
        return (
            await self.profile.export(),
            await self.state.export(),
            await self.dynamic.export(),
        )

    async def load(
        self,
        snapshots: tuple[Sequence[dict], Sequence[dict], Sequence[dict]],
        reset_memory: bool = True,
    ) -> None:
        """
        Load snapshot memories into all sections.

        - **Args**:
            - `snapshots` (Tuple[Sequence[Dict], Sequence[Dict], Sequence[Dict]]): The exported snapshots to load.
            - `reset_memory` (bool, optional): Whether to reset previous memory. Defaults to True.
        """
        _profile_snapshot, _state_snapshot, _dynamic_snapshot = snapshots
        for _snapshot, _mem in zip(
            [_profile_snapshot, _state_snapshot, _dynamic_snapshot],
            [self.state, self.profile, self.dynamic],
        ):
            if _snapshot:
                await _mem.load(snapshots=_snapshot, reset_memory=reset_memory)


class Memory:
    """
    A class to manage different types of memory (state, profile, dynamic).

    - **Attributes**:
        - `_state` (`StateMemory`): Stores state-related data.
        - `_profile` (`ProfileMemory`): Stores profile-related data.
        - `_dynamic` (`DynamicMemory`): Stores dynamically configured data.

    - **Methods**:
        - `set_search_components`: Sets the search components for stream and status memory.

    """

    def __init__(
        self,
        agent_id: int,
        environment: Environment,
        faiss_query: FaissQuery,
        embedding_model: Embeddings,
        config: Optional[dict[Any, Any]] = None,
        profile: Optional[dict[Any, Any]] = None,
        base: Optional[dict[Any, Any]] = None,
        activate_timestamp: bool = False,
    ) -> None:
        """
        Initializes the Memory with optional configuration.

        - **Description**:
            Sets up the memory management system by initializing different memory types (state, profile, dynamic)
            and configuring them based on provided parameters. Also initializes watchers and locks for thread-safe operations.

        - **Args**:
            - `agent_id` (int): The ID of the agent.
            - `environment` (Environment): The environment object.
            - `faiss_query` (FaissQuery): The Faiss query object.
            - `embedding_model` (Embeddings): The embedding model object.
            - `config` (Optional[dict[Any, Any]], optional):
                Configuration dictionary for dynamic memory, where keys are field names and values can be tuples or callables.
                Defaults to None.
            - `profile` (Optional[dict[Any, Any]], optional): Dictionary for profile attributes.
                Defaults to None.
            - `base` (Optional[dict[Any, Any]], optional): Dictionary for base attributes from City Simulator.
                Defaults to None.
            - `activate_timestamp` (bool): Flag to enable timestamp storage in MemoryUnit.
                Defaults to False.

        - **Returns**:
            - `None`
        """
        self.watchers: dict[str, list[Callable]] = {}
        self._lock = asyncio.Lock()
        self._agent_id = agent_id
        self._environment = environment
        self._embedding_model = embedding_model
        self._faiss_query = faiss_query
        self._semantic_templates: dict[str, str] = {}
        _dynamic_config: dict[Any, Any] = {}
        _state_config: dict[Any, Any] = {}
        _profile_config: dict[Any, Any] = {}
        self._embedding_fields: dict[str, bool] = {}
        self._embedding_field_to_doc_id: dict[Any, str] = defaultdict(str)

        if config is not None:
            for k, v in config.items():
                try:
                    # Handle configurations of different lengths
                    if isinstance(v, tuple):
                        if len(v) == 4:  # (_type, _value, enable_embedding, template)
                            _type, _value, enable_embedding, template = v
                            self._embedding_fields[k] = enable_embedding
                            self._semantic_templates[k] = template
                        elif len(v) == 3:  # (_type, _value, enable_embedding)
                            _type, _value, enable_embedding = v
                            self._embedding_fields[k] = enable_embedding
                        else:  # (_type, _value)
                            _type, _value = v
                            self._embedding_fields[k] = False
                    else:
                        _type = type(v)
                        _value = v
                        self._embedding_fields[k] = False

                    # Process type conversion
                    try:
                        if isinstance(_type, type):
                            _value = _type(_value)
                        else:
                            if isinstance(_type, deque):
                                _type.extend(_value)
                                _value = deepcopy(_type)
                            else:
                                get_logger().warning(
                                    f"type `{_type}` is not supported!"
                                )
                    except TypeError as e:
                        get_logger().warning(f"Type conversion failed for key {k}: {e}")
                except TypeError as e:
                    if isinstance(v, type):
                        _value = v()
                    else:
                        _value = v
                    self._embedding_fields[k] = False

                if (
                    k in PROFILE_ATTRIBUTES
                    or k in STATE_ATTRIBUTES
                    or k == TIME_STAMP_KEY
                ) and k != "id":
                    get_logger().warning(f"key `{k}` already declared in memory!")
                    continue

                _dynamic_config[k] = deepcopy(_value)

        # Initialize various types of memories
        self._dynamic = DynamicMemory(
            required_attributes=_dynamic_config, activate_timestamp=activate_timestamp
        )

        if profile is not None:
            for k, v in profile.items():
                if k not in PROFILE_ATTRIBUTES:
                    get_logger().warning(f"key `{k}` is not a correct `profile` field!")
                    continue
                try:
                    # Handle configuration tuple formats
                    if isinstance(v, tuple):
                        if len(v) == 4:  # (_type, _value, enable_embedding, template)
                            _type, _value, enable_embedding, template = v
                            self._embedding_fields[k] = enable_embedding
                            self._semantic_templates[k] = template
                        elif len(v) == 3:  # (_type, _value, enable_embedding)
                            _type, _value, enable_embedding = v
                            self._embedding_fields[k] = enable_embedding
                        else:  # (_type, _value)
                            _type, _value = v
                            self._embedding_fields[k] = True

                        # Process type conversion
                        try:
                            if isinstance(_type, type):
                                _value = _type(_value)
                            else:
                                if k == "social_network":
                                    _value = [SocialRelation(**_v) for _v in _value]
                                elif isinstance(_type, deque):
                                    _type.extend(_value)
                                    _value = deepcopy(_type)
                                else:
                                    get_logger().warning(
                                        f"[Profile] type `{_type}` is not supported!"
                                    )
                        except TypeError as e:
                            get_logger().warning(
                                f"Type conversion failed for key {k}: {e}"
                            )
                    else:
                        # Maintain compatibility with simple key-value pairs
                        if k == "social_network":
                            _value = [SocialRelation(**_v) for _v in v]
                        else:
                            _value = v
                        self._embedding_fields[k] = False
                except TypeError as e:
                    if isinstance(v, type):
                        _value = v()
                    else:
                        _value = v
                    self._embedding_fields[k] = False

                _profile_config[k] = deepcopy(_value)
        self._profile = ProfileMemory(
            msg=_profile_config, activate_timestamp=activate_timestamp
        )
        if base is not None:
            for k, v in base.items():
                if k not in STATE_ATTRIBUTES:
                    get_logger().warning(f"key `{k}` is not a correct `base` field!")
                    continue
                _state_config[k] = v

        self._state = StateMemory(
            msg=_state_config, activate_timestamp=activate_timestamp
        )

        # Combine StatusMemory and pass embedding_fields information
        self._status = StatusMemory(
            agent_id=self._agent_id,
            environment=self._environment,
            faiss_query=self._faiss_query,
            embedding_model=self._embedding_model,
            profile=self._profile,
            state=self._state,
            dynamic=self._dynamic,
        )
        self._status.set_embedding_fields(self._embedding_fields)
        self._status.set_semantic_templates(self._semantic_templates)

        # Add StreamMemory
        self._stream = StreamMemory(
            agent_id=self._agent_id,
            environment=self._environment,
            faiss_query=self._faiss_query,
            embedding_model=self._embedding_model,
        )
        self._stream.set_status_memory(self._status)

    @property
    def status(self) -> StatusMemory:
        return self._status

    @property
    def stream(self) -> StreamMemory:
        return self._stream

    @property
    def embedding_model(self):
        """
        Access the embedding model used in the memory system.

        - **Description**:
            - Property that provides access to the embedding model.

        - **Returns**:
            - `Embeddings`: The embedding model instance.
        """
        return self._embedding_model

    @property
    def agent_id(self):
        """
        Access the agent ID.

        - **Description**:
            - Property that provides access to the agent ID.

        - **Returns**:
            - `int`: The agent's identifier.
        """
        return self._agent_id

    @property
    def faiss_query(self) -> FaissQuery:
        """
        Access the FaissQuery component.

        - **Description**:
            - Property that provides access to the FaissQuery component. Raises an error if accessed before assignment.

        - **Raises**:
            - `RuntimeError`: If the FaissQuery has not been set yet.

        - **Returns**:
            - `FaissQuery`: The FaissQuery instance.
        """
        return self._faiss_query

    async def initialize_embeddings(self):
        """
        Initialize embeddings within the status memory.

        - **Description**:
            - Asynchronously initializes embeddings for the status memory component, which prepares the system for performing searches.

        - **Returns**:
        """
        await self._status.initialize_embeddings()
