from alpaka.funcs import execute, subscribe, aexecute, asubscribe
from rath.scalars import IDCoercible, ID
from typing import (
    List,
    AsyncIterator,
    Iterable,
    Literal,
    Optional,
    Any,
    Tuple,
    Iterator,
)
from pydantic import Field, BaseModel, ConfigDict
from enum import Enum
from datetime import datetime
from alpaka.rath import AlpakaRath


class FeatureType(str, Enum):
    """The type of the thinking block"""

    EMBEDDING = "EMBEDDING"
    CHATTING = "CHATTING"
    CHAT = "CHAT"


class Role(str, Enum):
    """The type of the message sender"""

    SYSTEM = "SYSTEM"
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    TOOL = "TOOL"
    FUNCTION = "FUNCTION"


class ToolType(str, Enum):
    """The type of the tool"""

    FUNCTION = "FUNCTION"


class OffsetPaginationInput(BaseModel):
    """No documentation"""

    offset: int
    limit: Optional[int] = None
    model_config = ConfigDict(
        frozen=True, extra="forbid", populate_by_name=True, use_enum_values=True
    )


class RoomFilter(BaseModel):
    """Room(id, title, description, creator)"""

    search: Optional[str] = None
    ids: Optional[Tuple[ID, ...]] = None
    and_: Optional["RoomFilter"] = Field(alias="AND", default=None)
    or_: Optional["RoomFilter"] = Field(alias="OR", default=None)
    not_: Optional["RoomFilter"] = Field(alias="NOT", default=None)
    distinct: Optional[bool] = Field(alias="DISTINCT", default=None)
    model_config = ConfigDict(
        frozen=True, extra="forbid", populate_by_name=True, use_enum_values=True
    )


class ChromaCollectionFilter(BaseModel):
    """Filter for ChromaCollection"""

    search: Optional[str] = None
    ids: Optional[Tuple[ID, ...]] = None
    and_: Optional["ChromaCollectionFilter"] = Field(alias="AND", default=None)
    or_: Optional["ChromaCollectionFilter"] = Field(alias="OR", default=None)
    not_: Optional["ChromaCollectionFilter"] = Field(alias="NOT", default=None)
    distinct: Optional[bool] = Field(alias="DISTINCT", default=None)
    model_config = ConfigDict(
        frozen=True, extra="forbid", populate_by_name=True, use_enum_values=True
    )


class LLMModelFilter(BaseModel):
    """Filter for LLMModel"""

    ids: Optional[Tuple[ID, ...]] = None
    search: Optional[str] = None
    and_: Optional["LLMModelFilter"] = Field(alias="AND", default=None)
    or_: Optional["LLMModelFilter"] = Field(alias="OR", default=None)
    not_: Optional["LLMModelFilter"] = Field(alias="NOT", default=None)
    distinct: Optional[bool] = Field(alias="DISTINCT", default=None)
    model_config = ConfigDict(
        frozen=True, extra="forbid", populate_by_name=True, use_enum_values=True
    )


class ProviderInput(BaseModel):
    """A large language model to change with"""

    description: Optional[str] = None
    name: str
    api_key: Optional[str] = Field(alias="apiKey", default=None)
    api_base: Optional[str] = Field(alias="apiBase", default=None)
    additional_config: Optional[Any] = Field(alias="additionalConfig", default=None)
    model_config = ConfigDict(
        frozen=True, extra="forbid", populate_by_name=True, use_enum_values=True
    )


class StructureInput(BaseModel):
    """A function definition for a large language model"""

    identifier: str
    object: str
    model_config = ConfigDict(
        frozen=True, extra="forbid", populate_by_name=True, use_enum_values=True
    )


class ChatInput(BaseModel):
    """A chat message input"""

    model: ID
    messages: Tuple["ChatMessageInput", ...]
    tools: Optional[Tuple["ToolInput", ...]] = None
    temperature: Optional[float] = None
    model_config = ConfigDict(
        frozen=True, extra="forbid", populate_by_name=True, use_enum_values=True
    )


class ChatMessageInput(BaseModel):
    """A chat message input"""

    role: Role
    content: Optional[str] = None
    name: Optional[str] = None
    tool_call_id: Optional[str] = Field(alias="toolCallId", default=None)
    function_call: Optional["FunctionCallInput"] = Field(
        alias="functionCall", default=None
    )
    tool_calls: Optional[Tuple["ToolCallInput", ...]] = Field(
        alias="toolCalls", default=None
    )
    model_config = ConfigDict(
        frozen=True, extra="forbid", populate_by_name=True, use_enum_values=True
    )


class FunctionCallInput(BaseModel):
    """A function call input"""

    name: str
    arguments: str
    model_config = ConfigDict(
        frozen=True, extra="forbid", populate_by_name=True, use_enum_values=True
    )


class ToolCallInput(BaseModel):
    """A tool call input"""

    id: str
    function: FunctionCallInput
    type: ToolType
    model_config = ConfigDict(
        frozen=True, extra="forbid", populate_by_name=True, use_enum_values=True
    )


class ToolInput(BaseModel):
    """A large language model function call"""

    type: ToolType
    function: "FunctionDefinitionInput"
    model_config = ConfigDict(
        frozen=True, extra="forbid", populate_by_name=True, use_enum_values=True
    )


class FunctionDefinitionInput(BaseModel):
    """A large language model function defintion"""

    name: str
    description: Optional[str] = None
    parameters: Optional[Any] = None
    model_config = ConfigDict(
        frozen=True, extra="forbid", populate_by_name=True, use_enum_values=True
    )


class PullInput(BaseModel):
    """No documentation"""

    model_name: str = Field(alias="modelName")
    model_config = ConfigDict(
        frozen=True, extra="forbid", populate_by_name=True, use_enum_values=True
    )


class ChromaCollectionInput(BaseModel):
    """No documentation"""

    name: str
    embedder: ID
    description: Optional[str] = None
    is_public: Optional[bool] = Field(alias="isPublic", default=None)
    model_config = ConfigDict(
        frozen=True, extra="forbid", populate_by_name=True, use_enum_values=True
    )


class AddDocumentsToCollectionInput(BaseModel):
    """No documentation"""

    collection: ID
    documents: Tuple["DocumentInput", ...]
    model_config = ConfigDict(
        frozen=True, extra="forbid", populate_by_name=True, use_enum_values=True
    )


class DocumentInput(BaseModel):
    """A document to put into the vector database"""

    content: str
    structure: Optional[StructureInput] = None
    id: Optional[str] = None
    metadata: Optional[Any] = None
    model_config = ConfigDict(
        frozen=True, extra="forbid", populate_by_name=True, use_enum_values=True
    )


class MessageAgentRoom(BaseModel):
    """Room(id, title, description, creator)"""

    typename: Literal["Room"] = Field(alias="__typename", default="Room", exclude=True)
    id: ID
    model_config = ConfigDict(frozen=True)


class MessageAgent(BaseModel):
    """Agent(id, room, name, client, user)"""

    typename: Literal["Agent"] = Field(
        alias="__typename", default="Agent", exclude=True
    )
    id: ID
    room: MessageAgentRoom
    model_config = ConfigDict(frozen=True)


class Message(BaseModel):
    """Message represent the message of an agent on a room"""

    typename: Literal["Message"] = Field(
        alias="__typename", default="Message", exclude=True
    )
    id: ID
    text: str
    "A clear text representation of the rich comment"
    agent: MessageAgent
    "The user that created this comment"
    model_config = ConfigDict(frozen=True)


class ListMessageAgent(BaseModel):
    """Agent(id, room, name, client, user)"""

    typename: Literal["Agent"] = Field(
        alias="__typename", default="Agent", exclude=True
    )
    id: ID
    model_config = ConfigDict(frozen=True)


class ListMessage(BaseModel):
    """Message represent the message of an agent on a room"""

    typename: Literal["Message"] = Field(
        alias="__typename", default="Message", exclude=True
    )
    id: ID
    text: str
    "A clear text representation of the rich comment"
    agent: ListMessageAgent
    "The user that created this comment"
    model_config = ConfigDict(frozen=True)


class Document(BaseModel):
    """No documentation"""

    typename: Literal["Document"] = Field(
        alias="__typename", default="Document", exclude=True
    )
    id: str
    content: str
    metadata: Optional[Any] = Field(default=None)
    distance: Optional[float] = Field(default=None)
    model_config = ConfigDict(frozen=True)


class ChromaCollection(BaseModel):
    """A collection of documents searchable by string"""

    typename: Literal["ChromaCollection"] = Field(
        alias="__typename", default="ChromaCollection", exclude=True
    )
    id: ID
    name: str
    description: str
    created_at: datetime = Field(alias="createdAt")
    model_config = ConfigDict(frozen=True)


class Room(BaseModel):
    """Room(id, title, description, creator)"""

    typename: Literal["Room"] = Field(alias="__typename", default="Room", exclude=True)
    id: ID
    title: str
    "The Title of the Room"
    description: str
    model_config = ConfigDict(frozen=True)


class ProviderModels(BaseModel):
    """A LLM model to chage with"""

    typename: Literal["LLMModel"] = Field(
        alias="__typename", default="LLMModel", exclude=True
    )
    id: ID
    model_id: str = Field(alias="modelId")
    features: Tuple[FeatureType, ...]
    "The features supported by the model"
    model_config = ConfigDict(frozen=True)


class Provider(BaseModel):
    """A provider of LLMs"""

    typename: Literal["Provider"] = Field(
        alias="__typename", default="Provider", exclude=True
    )
    id: str
    name: str
    models: Tuple[ProviderModels, ...]
    model_config = ConfigDict(frozen=True)


class ChatResponseUsage(BaseModel):
    """No documentation"""

    typename: Literal["Usage"] = Field(
        alias="__typename", default="Usage", exclude=True
    )
    prompt_tokens: int = Field(alias="promptTokens")
    completion_tokens: int = Field(alias="completionTokens")
    total_tokens: int = Field(alias="totalTokens")
    model_config = ConfigDict(frozen=True)


class ChatResponseChoicesMessageFunctioncall(BaseModel):
    """The type of the tool"""

    typename: Literal["FunctionCall"] = Field(
        alias="__typename", default="FunctionCall", exclude=True
    )
    name: str
    arguments: str
    model_config = ConfigDict(frozen=True)


class ChatResponseChoicesMessageToolcallsFunction(BaseModel):
    """The type of the tool"""

    typename: Literal["FunctionCall"] = Field(
        alias="__typename", default="FunctionCall", exclude=True
    )
    name: str
    arguments: str
    model_config = ConfigDict(frozen=True)


class ChatResponseChoicesMessageToolcalls(BaseModel):
    """A function definition for a large language model"""

    typename: Literal["ToolCall"] = Field(
        alias="__typename", default="ToolCall", exclude=True
    )
    id: str
    type: ToolType
    function: ChatResponseChoicesMessageToolcallsFunction
    model_config = ConfigDict(frozen=True)


class ChatResponseChoicesMessage(BaseModel):
    """No documentation"""

    typename: Literal["ChatMessage"] = Field(
        alias="__typename", default="ChatMessage", exclude=True
    )
    role: Role
    content: Optional[str] = Field(default=None)
    name: Optional[str] = Field(default=None)
    tool_call_id: Optional[str] = Field(default=None, alias="toolCallId")
    function_call: Optional[ChatResponseChoicesMessageFunctioncall] = Field(
        default=None, alias="functionCall"
    )
    tool_calls: Optional[Tuple[ChatResponseChoicesMessageToolcalls, ...]] = Field(
        default=None, alias="toolCalls"
    )
    model_config = ConfigDict(frozen=True)


class ChatResponseChoices(BaseModel):
    """No documentation"""

    typename: Literal["Choice"] = Field(
        alias="__typename", default="Choice", exclude=True
    )
    index: int
    finish_reason: Optional[str] = Field(default=None, alias="finishReason")
    message: ChatResponseChoicesMessage
    model_config = ConfigDict(frozen=True)


class ChatResponse(BaseModel):
    """No documentation"""

    typename: Literal["ChatResponse"] = Field(
        alias="__typename", default="ChatResponse", exclude=True
    )
    id: str
    object: str
    created: int
    model: str
    usage: Optional[ChatResponseUsage] = Field(default=None)
    choices: Tuple[ChatResponseChoices, ...]
    model_config = ConfigDict(frozen=True)


class LLMModelProvider(BaseModel):
    """A provider of LLMs"""

    typename: Literal["Provider"] = Field(
        alias="__typename", default="Provider", exclude=True
    )
    id: str
    name: str
    model_config = ConfigDict(frozen=True)


class LLMModelEmbedderfor(BaseModel):
    """A collection of documents searchable by string"""

    typename: Literal["ChromaCollection"] = Field(
        alias="__typename", default="ChromaCollection", exclude=True
    )
    id: ID
    name: str
    model_config = ConfigDict(frozen=True)


class LLMModel(BaseModel):
    """A LLM model to chage with"""

    typename: Literal["LLMModel"] = Field(
        alias="__typename", default="LLMModel", exclude=True
    )
    id: ID
    provider: LLMModelProvider
    features: Tuple[FeatureType, ...]
    "The features supported by the model"
    embedder_for: Tuple[LLMModelEmbedderfor, ...] = Field(alias="embedderFor")
    "The collections that can be embedded with this model"
    model_config = ConfigDict(frozen=True)


class SendMutation(BaseModel):
    """No documentation found for this operation."""

    send: Message

    class Arguments(BaseModel):
        """Arguments for Send"""

        text: str
        room: ID
        agent_id: str = Field(alias="agentId")
        attach_structures: Optional[List[StructureInput]] = Field(
            alias="attachStructures", default=None
        )
        model_config = ConfigDict(populate_by_name=True)

    class Meta:
        """Meta class for Send"""

        document = "fragment Message on Message {\n  id\n  text\n  agent {\n    id\n    room {\n      id\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nmutation Send($text: String!, $room: ID!, $agentId: String!, $attachStructures: [StructureInput!]) {\n  send(\n    input: {text: $text, room: $room, agentId: $agentId, attachStructures: $attachStructures}\n  ) {\n    ...Message\n    __typename\n  }\n}"


class AddDocumentsToCollectionMutation(BaseModel):
    """No documentation found for this operation."""

    add_documents_to_collection: Tuple[Document, ...] = Field(
        alias="addDocumentsToCollection"
    )

    class Arguments(BaseModel):
        """Arguments for AddDocumentsToCollection"""

        input: AddDocumentsToCollectionInput
        model_config = ConfigDict(populate_by_name=True)

    class Meta:
        """Meta class for AddDocumentsToCollection"""

        document = "fragment Document on Document {\n  id\n  content\n  metadata\n  distance\n  __typename\n}\n\nmutation AddDocumentsToCollection($input: AddDocumentsToCollectionInput!) {\n  addDocumentsToCollection(input: $input) {\n    ...Document\n    __typename\n  }\n}"


class CreateCollectionMutation(BaseModel):
    """No documentation found for this operation."""

    create_collection: ChromaCollection = Field(alias="createCollection")

    class Arguments(BaseModel):
        """Arguments for CreateCollection"""

        input: ChromaCollectionInput
        model_config = ConfigDict(populate_by_name=True)

    class Meta:
        """Meta class for CreateCollection"""

        document = "fragment ChromaCollection on ChromaCollection {\n  id\n  name\n  description\n  createdAt\n  __typename\n}\n\nmutation CreateCollection($input: ChromaCollectionInput!) {\n  createCollection(input: $input) {\n    ...ChromaCollection\n    __typename\n  }\n}"


class EnsureCollectionMutation(BaseModel):
    """No documentation found for this operation."""

    ensure_collection: ChromaCollection = Field(alias="ensureCollection")

    class Arguments(BaseModel):
        """Arguments for EnsureCollection"""

        input: ChromaCollectionInput
        model_config = ConfigDict(populate_by_name=True)

    class Meta:
        """Meta class for EnsureCollection"""

        document = "fragment ChromaCollection on ChromaCollection {\n  id\n  name\n  description\n  createdAt\n  __typename\n}\n\nmutation EnsureCollection($input: ChromaCollectionInput!) {\n  ensureCollection(input: $input) {\n    ...ChromaCollection\n    __typename\n  }\n}"


class CreateRoomMutation(BaseModel):
    """No documentation found for this operation."""

    create_room: Room = Field(alias="createRoom")

    class Arguments(BaseModel):
        """Arguments for CreateRoom"""

        title: Optional[str] = Field(default=None)
        description: Optional[str] = Field(default=None)
        model_config = ConfigDict(populate_by_name=True)

    class Meta:
        """Meta class for CreateRoom"""

        document = "fragment Room on Room {\n  id\n  title\n  description\n  __typename\n}\n\nmutation CreateRoom($title: String, $description: String) {\n  createRoom(input: {title: $title, description: $description}) {\n    ...Room\n    __typename\n  }\n}"


class PullMutationPull(BaseModel):
    """No documentation"""

    typename: Literal["OllamaPullResult"] = Field(
        alias="__typename", default="OllamaPullResult", exclude=True
    )
    status: str
    detail: Optional[str] = Field(default=None)
    model_config = ConfigDict(frozen=True)


class PullMutation(BaseModel):
    """No documentation found for this operation."""

    pull: PullMutationPull

    class Arguments(BaseModel):
        """Arguments for Pull"""

        input: PullInput
        model_config = ConfigDict(populate_by_name=True)

    class Meta:
        """Meta class for Pull"""

        document = "mutation Pull($input: PullInput!) {\n  pull(input: $input) {\n    status\n    detail\n    __typename\n  }\n}"


class CreateProviderMutation(BaseModel):
    """No documentation found for this operation."""

    create_provider: Provider = Field(alias="createProvider")

    class Arguments(BaseModel):
        """Arguments for CreateProvider"""

        input: ProviderInput
        model_config = ConfigDict(populate_by_name=True)

    class Meta:
        """Meta class for CreateProvider"""

        document = "fragment Provider on Provider {\n  id\n  name\n  models {\n    id\n    modelId\n    features\n    __typename\n  }\n  __typename\n}\n\nmutation CreateProvider($input: ProviderInput!) {\n  createProvider(input: $input) {\n    ...Provider\n    __typename\n  }\n}"


class ChatMutation(BaseModel):
    """No documentation found for this operation."""

    chat: ChatResponse

    class Arguments(BaseModel):
        """Arguments for Chat"""

        input: ChatInput
        model_config = ConfigDict(populate_by_name=True)

    class Meta:
        """Meta class for Chat"""

        document = "fragment ChatResponse on ChatResponse {\n  id\n  object\n  created\n  model\n  usage {\n    promptTokens\n    completionTokens\n    totalTokens\n    __typename\n  }\n  choices {\n    index\n    finishReason\n    message {\n      role\n      content\n      name\n      toolCallId\n      functionCall {\n        name\n        arguments\n        __typename\n      }\n      toolCalls {\n        id\n        type\n        function {\n          name\n          arguments\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nmutation Chat($input: ChatInput!) {\n  chat(input: $input) {\n    ...ChatResponse\n    __typename\n  }\n}"


class QueryDocumentsQuery(BaseModel):
    """No documentation found for this operation."""

    documents: Tuple[Document, ...]

    class Arguments(BaseModel):
        """Arguments for QueryDocuments"""

        collection: ID
        query_texts: List[str] = Field(alias="queryTexts")
        n_results: Optional[int] = Field(alias="nResults", default=None)
        where: Optional[Any] = Field(default=None)
        model_config = ConfigDict(populate_by_name=True)

    class Meta:
        """Meta class for QueryDocuments"""

        document = "fragment Document on Document {\n  id\n  content\n  metadata\n  distance\n  __typename\n}\n\nquery QueryDocuments($collection: ID!, $queryTexts: [String!]!, $nResults: Int, $where: JSON) {\n  documents(\n    collection: $collection\n    queryTexts: $queryTexts\n    nResults: $nResults\n    where: $where\n  ) {\n    ...Document\n    __typename\n  }\n}"


class GetChromaCollectionQuery(BaseModel):
    """No documentation found for this operation."""

    chroma_collection: ChromaCollection = Field(alias="chromaCollection")

    class Arguments(BaseModel):
        """Arguments for GetChromaCollection"""

        id: ID
        model_config = ConfigDict(populate_by_name=True)

    class Meta:
        """Meta class for GetChromaCollection"""

        document = "fragment ChromaCollection on ChromaCollection {\n  id\n  name\n  description\n  createdAt\n  __typename\n}\n\nquery GetChromaCollection($id: ID!) {\n  chromaCollection(id: $id) {\n    ...ChromaCollection\n    __typename\n  }\n}"


class SearchChromaCollectionQueryOptions(BaseModel):
    """A collection of documents searchable by string"""

    typename: Literal["ChromaCollection"] = Field(
        alias="__typename", default="ChromaCollection", exclude=True
    )
    value: ID
    label: str
    model_config = ConfigDict(frozen=True)


class SearchChromaCollectionQuery(BaseModel):
    """No documentation found for this operation."""

    options: Tuple[SearchChromaCollectionQueryOptions, ...]

    class Arguments(BaseModel):
        """Arguments for SearchChromaCollection"""

        search: Optional[str] = Field(default=None)
        values: Optional[List[ID]] = Field(default=None)
        model_config = ConfigDict(populate_by_name=True)

    class Meta:
        """Meta class for SearchChromaCollection"""

        document = "query SearchChromaCollection($search: String, $values: [ID!]) {\n  options: chromaCollections(\n    filters: {search: $search, ids: $values}\n    pagination: {limit: 10}\n  ) {\n    value: id\n    label: name\n    __typename\n  }\n}"


class ListChromaCollectionsQuery(BaseModel):
    """No documentation found for this operation."""

    chroma_collections: Tuple[ChromaCollection, ...] = Field(alias="chromaCollections")

    class Arguments(BaseModel):
        """Arguments for ListChromaCollections"""

        filter: Optional[ChromaCollectionFilter] = Field(default=None)
        pagination: Optional[OffsetPaginationInput] = Field(default=None)
        model_config = ConfigDict(populate_by_name=True)

    class Meta:
        """Meta class for ListChromaCollections"""

        document = "fragment ChromaCollection on ChromaCollection {\n  id\n  name\n  description\n  createdAt\n  __typename\n}\n\nquery ListChromaCollections($filter: ChromaCollectionFilter, $pagination: OffsetPaginationInput) {\n  chromaCollections(filters: $filter, pagination: $pagination) {\n    ...ChromaCollection\n    __typename\n  }\n}"


class GetRoomQuery(BaseModel):
    """No documentation found for this operation."""

    room: Room

    class Arguments(BaseModel):
        """Arguments for GetRoom"""

        id: ID
        model_config = ConfigDict(populate_by_name=True)

    class Meta:
        """Meta class for GetRoom"""

        document = "fragment Room on Room {\n  id\n  title\n  description\n  __typename\n}\n\nquery GetRoom($id: ID!) {\n  room(id: $id) {\n    ...Room\n    __typename\n  }\n}"


class SearchRoomsQueryOptions(BaseModel):
    """Room(id, title, description, creator)"""

    typename: Literal["Room"] = Field(alias="__typename", default="Room", exclude=True)
    value: ID
    label: str
    "The Title of the Room"
    description: str
    model_config = ConfigDict(frozen=True)


class SearchRoomsQuery(BaseModel):
    """No documentation found for this operation."""

    options: Tuple[SearchRoomsQueryOptions, ...]

    class Arguments(BaseModel):
        """Arguments for SearchRooms"""

        search: Optional[str] = Field(default=None)
        values: Optional[List[ID]] = Field(default=None)
        model_config = ConfigDict(populate_by_name=True)

    class Meta:
        """Meta class for SearchRooms"""

        document = "query SearchRooms($search: String, $values: [ID!]) {\n  options: rooms(\n    filters: {search: $search, ids: $values}\n    pagination: {limit: 10}\n  ) {\n    value: id\n    label: title\n    description: description\n    __typename\n  }\n}"


class ListRoomsQuery(BaseModel):
    """No documentation found for this operation."""

    rooms: Tuple[Room, ...]

    class Arguments(BaseModel):
        """Arguments for ListRooms"""

        filter: Optional[RoomFilter] = Field(default=None)
        pagination: Optional[OffsetPaginationInput] = Field(default=None)
        model_config = ConfigDict(populate_by_name=True)

    class Meta:
        """Meta class for ListRooms"""

        document = "fragment Room on Room {\n  id\n  title\n  description\n  __typename\n}\n\nquery ListRooms($filter: RoomFilter, $pagination: OffsetPaginationInput) {\n  rooms(filters: $filter, pagination: $pagination) {\n    ...Room\n    __typename\n  }\n}"


class GetLLMModelQuery(BaseModel):
    """No documentation found for this operation."""

    llm_model: LLMModel = Field(alias="llmModel")

    class Arguments(BaseModel):
        """Arguments for GetLLMModel"""

        id: ID
        model_config = ConfigDict(populate_by_name=True)

    class Meta:
        """Meta class for GetLLMModel"""

        document = "fragment LLMModel on LLMModel {\n  id\n  provider {\n    id\n    name\n    __typename\n  }\n  features\n  embedderFor {\n    id\n    name\n    __typename\n  }\n  __typename\n}\n\nquery GetLLMModel($id: ID!) {\n  llmModel(id: $id) {\n    ...LLMModel\n    __typename\n  }\n}"


class SearchLLMModelsQueryOptions(BaseModel):
    """A LLM model to chage with"""

    typename: Literal["LLMModel"] = Field(
        alias="__typename", default="LLMModel", exclude=True
    )
    value: ID
    label: str
    model_config = ConfigDict(frozen=True)


class SearchLLMModelsQuery(BaseModel):
    """No documentation found for this operation."""

    options: Tuple[SearchLLMModelsQueryOptions, ...]

    class Arguments(BaseModel):
        """Arguments for SearchLLMModels"""

        search: Optional[str] = Field(default=None)
        values: Optional[List[ID]] = Field(default=None)
        model_config = ConfigDict(populate_by_name=True)

    class Meta:
        """Meta class for SearchLLMModels"""

        document = "query SearchLLMModels($search: String, $values: [ID!]) {\n  options: llmModels(\n    filters: {search: $search, ids: $values}\n    pagination: {limit: 10}\n  ) {\n    value: id\n    label: modelId\n    __typename\n  }\n}"


class ListLLModelsQuery(BaseModel):
    """No documentation found for this operation."""

    llm_models: Tuple[LLMModel, ...] = Field(alias="llmModels")

    class Arguments(BaseModel):
        """Arguments for ListLLModels"""

        filter: Optional[LLMModelFilter] = Field(default=None)
        pagination: Optional[OffsetPaginationInput] = Field(default=None)
        model_config = ConfigDict(populate_by_name=True)

    class Meta:
        """Meta class for ListLLModels"""

        document = "fragment LLMModel on LLMModel {\n  id\n  provider {\n    id\n    name\n    __typename\n  }\n  features\n  embedderFor {\n    id\n    name\n    __typename\n  }\n  __typename\n}\n\nquery ListLLModels($filter: LLMModelFilter, $pagination: OffsetPaginationInput) {\n  llmModels(filters: $filter, pagination: $pagination) {\n    ...LLMModel\n    __typename\n  }\n}"


class WatchRoomSubscriptionRoom(BaseModel):
    """No documentation"""

    typename: Literal["RoomEvent"] = Field(
        alias="__typename", default="RoomEvent", exclude=True
    )
    message: Optional[ListMessage] = Field(default=None)
    model_config = ConfigDict(frozen=True)


class WatchRoomSubscription(BaseModel):
    """No documentation found for this operation."""

    room: WatchRoomSubscriptionRoom

    class Arguments(BaseModel):
        """Arguments for WatchRoom"""

        room: ID
        agent_id: ID = Field(alias="agentId")
        model_config = ConfigDict(populate_by_name=True)

    class Meta:
        """Meta class for WatchRoom"""

        document = "fragment ListMessage on Message {\n  id\n  text\n  agent {\n    id\n    __typename\n  }\n  __typename\n}\n\nsubscription WatchRoom($room: ID!, $agentId: ID!) {\n  room(room: $room, agentId: $agentId) {\n    message {\n      ...ListMessage\n      __typename\n    }\n    __typename\n  }\n}"


async def asend(
    text: str,
    room: ID,
    agent_id: str,
    attach_structures: Optional[List[StructureInput]] = None,
    rath: Optional[AlpakaRath] = None,
) -> Message:
    """Send


    Args:
        text (str): No description
        room (ID): No description
        agent_id (str): No description
        attach_structures (Optional[List[StructureInput]], optional): No description.
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Message
    """
    return (
        await aexecute(
            SendMutation,
            {
                "text": text,
                "room": room,
                "agentId": agent_id,
                "attachStructures": attach_structures,
            },
            rath=rath,
        )
    ).send


def send(
    text: str,
    room: ID,
    agent_id: str,
    attach_structures: Optional[List[StructureInput]] = None,
    rath: Optional[AlpakaRath] = None,
) -> Message:
    """Send


    Args:
        text (str): No description
        room (ID): No description
        agent_id (str): No description
        attach_structures (Optional[List[StructureInput]], optional): No description.
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Message
    """
    return execute(
        SendMutation,
        {
            "text": text,
            "room": room,
            "agentId": agent_id,
            "attachStructures": attach_structures,
        },
        rath=rath,
    ).send


async def aadd_documents_to_collection(
    collection: IDCoercible,
    documents: Iterable[DocumentInput],
    rath: Optional[AlpakaRath] = None,
) -> Tuple[Document, ...]:
    """AddDocumentsToCollection


    Args:
        collection: The `ID` scalar type represents a unique identifier, often used to refetch an object or as key for a cache. The ID type appears in a JSON response as a String; however, it is not intended to be human-readable. When expected as an input type, any string (such as `"4"`) or integer (such as `4`) input value will be accepted as an ID. (required)
        documents: A document to put into the vector database (required) (list) (required)
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        List[Document]
    """
    return (
        await aexecute(
            AddDocumentsToCollectionMutation,
            {"input": {"collection": collection, "documents": documents}},
            rath=rath,
        )
    ).add_documents_to_collection


def add_documents_to_collection(
    collection: IDCoercible,
    documents: Iterable[DocumentInput],
    rath: Optional[AlpakaRath] = None,
) -> Tuple[Document, ...]:
    """AddDocumentsToCollection


    Args:
        collection: The `ID` scalar type represents a unique identifier, often used to refetch an object or as key for a cache. The ID type appears in a JSON response as a String; however, it is not intended to be human-readable. When expected as an input type, any string (such as `"4"`) or integer (such as `4`) input value will be accepted as an ID. (required)
        documents: A document to put into the vector database (required) (list) (required)
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        List[Document]
    """
    return execute(
        AddDocumentsToCollectionMutation,
        {"input": {"collection": collection, "documents": documents}},
        rath=rath,
    ).add_documents_to_collection


async def acreate_collection(
    name: str,
    embedder: IDCoercible,
    description: Optional[str] = None,
    is_public: Optional[bool] = None,
    rath: Optional[AlpakaRath] = None,
) -> ChromaCollection:
    """CreateCollection


    Args:
        name: The `String` scalar type represents textual data, represented as UTF-8 character sequences. The String type is most often used by GraphQL to represent free-form human-readable text. (required)
        embedder: The `ID` scalar type represents a unique identifier, often used to refetch an object or as key for a cache. The ID type appears in a JSON response as a String; however, it is not intended to be human-readable. When expected as an input type, any string (such as `"4"`) or integer (such as `4`) input value will be accepted as an ID. (required)
        description: The `String` scalar type represents textual data, represented as UTF-8 character sequences. The String type is most often used by GraphQL to represent free-form human-readable text.
        is_public: The `Boolean` scalar type represents `true` or `false`.
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        ChromaCollection
    """
    return (
        await aexecute(
            CreateCollectionMutation,
            {
                "input": {
                    "name": name,
                    "embedder": embedder,
                    "description": description,
                    "isPublic": is_public,
                }
            },
            rath=rath,
        )
    ).create_collection


def create_collection(
    name: str,
    embedder: IDCoercible,
    description: Optional[str] = None,
    is_public: Optional[bool] = None,
    rath: Optional[AlpakaRath] = None,
) -> ChromaCollection:
    """CreateCollection


    Args:
        name: The `String` scalar type represents textual data, represented as UTF-8 character sequences. The String type is most often used by GraphQL to represent free-form human-readable text. (required)
        embedder: The `ID` scalar type represents a unique identifier, often used to refetch an object or as key for a cache. The ID type appears in a JSON response as a String; however, it is not intended to be human-readable. When expected as an input type, any string (such as `"4"`) or integer (such as `4`) input value will be accepted as an ID. (required)
        description: The `String` scalar type represents textual data, represented as UTF-8 character sequences. The String type is most often used by GraphQL to represent free-form human-readable text.
        is_public: The `Boolean` scalar type represents `true` or `false`.
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        ChromaCollection
    """
    return execute(
        CreateCollectionMutation,
        {
            "input": {
                "name": name,
                "embedder": embedder,
                "description": description,
                "isPublic": is_public,
            }
        },
        rath=rath,
    ).create_collection


async def aensure_collection(
    name: str,
    embedder: IDCoercible,
    description: Optional[str] = None,
    is_public: Optional[bool] = None,
    rath: Optional[AlpakaRath] = None,
) -> ChromaCollection:
    """EnsureCollection


    Args:
        name: The `String` scalar type represents textual data, represented as UTF-8 character sequences. The String type is most often used by GraphQL to represent free-form human-readable text. (required)
        embedder: The `ID` scalar type represents a unique identifier, often used to refetch an object or as key for a cache. The ID type appears in a JSON response as a String; however, it is not intended to be human-readable. When expected as an input type, any string (such as `"4"`) or integer (such as `4`) input value will be accepted as an ID. (required)
        description: The `String` scalar type represents textual data, represented as UTF-8 character sequences. The String type is most often used by GraphQL to represent free-form human-readable text.
        is_public: The `Boolean` scalar type represents `true` or `false`.
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        ChromaCollection
    """
    return (
        await aexecute(
            EnsureCollectionMutation,
            {
                "input": {
                    "name": name,
                    "embedder": embedder,
                    "description": description,
                    "isPublic": is_public,
                }
            },
            rath=rath,
        )
    ).ensure_collection


def ensure_collection(
    name: str,
    embedder: IDCoercible,
    description: Optional[str] = None,
    is_public: Optional[bool] = None,
    rath: Optional[AlpakaRath] = None,
) -> ChromaCollection:
    """EnsureCollection


    Args:
        name: The `String` scalar type represents textual data, represented as UTF-8 character sequences. The String type is most often used by GraphQL to represent free-form human-readable text. (required)
        embedder: The `ID` scalar type represents a unique identifier, often used to refetch an object or as key for a cache. The ID type appears in a JSON response as a String; however, it is not intended to be human-readable. When expected as an input type, any string (such as `"4"`) or integer (such as `4`) input value will be accepted as an ID. (required)
        description: The `String` scalar type represents textual data, represented as UTF-8 character sequences. The String type is most often used by GraphQL to represent free-form human-readable text.
        is_public: The `Boolean` scalar type represents `true` or `false`.
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        ChromaCollection
    """
    return execute(
        EnsureCollectionMutation,
        {
            "input": {
                "name": name,
                "embedder": embedder,
                "description": description,
                "isPublic": is_public,
            }
        },
        rath=rath,
    ).ensure_collection


async def acreate_room(
    title: Optional[str] = None,
    description: Optional[str] = None,
    rath: Optional[AlpakaRath] = None,
) -> Room:
    """CreateRoom


    Args:
        title (Optional[str], optional): No description.
        description (Optional[str], optional): No description.
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Room
    """
    return (
        await aexecute(
            CreateRoomMutation, {"title": title, "description": description}, rath=rath
        )
    ).create_room


def create_room(
    title: Optional[str] = None,
    description: Optional[str] = None,
    rath: Optional[AlpakaRath] = None,
) -> Room:
    """CreateRoom


    Args:
        title (Optional[str], optional): No description.
        description (Optional[str], optional): No description.
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Room
    """
    return execute(
        CreateRoomMutation, {"title": title, "description": description}, rath=rath
    ).create_room


async def apull(model_name: str, rath: Optional[AlpakaRath] = None) -> PullMutationPull:
    """Pull


    Args:
        model_name: The `String` scalar type represents textual data, represented as UTF-8 character sequences. The String type is most often used by GraphQL to represent free-form human-readable text. (required)
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        PullMutationPull
    """
    return (
        await aexecute(PullMutation, {"input": {"modelName": model_name}}, rath=rath)
    ).pull


def pull(model_name: str, rath: Optional[AlpakaRath] = None) -> PullMutationPull:
    """Pull


    Args:
        model_name: The `String` scalar type represents textual data, represented as UTF-8 character sequences. The String type is most often used by GraphQL to represent free-form human-readable text. (required)
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        PullMutationPull
    """
    return execute(PullMutation, {"input": {"modelName": model_name}}, rath=rath).pull


async def acreate_provider(
    name: str,
    description: Optional[str] = None,
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    additional_config: Optional[Any] = None,
    rath: Optional[AlpakaRath] = None,
) -> Provider:
    """CreateProvider


    Args:
        description: The `String` scalar type represents textual data, represented as UTF-8 character sequences. The String type is most often used by GraphQL to represent free-form human-readable text.
        name: The `String` scalar type represents textual data, represented as UTF-8 character sequences. The String type is most often used by GraphQL to represent free-form human-readable text. (required)
        api_key: The `String` scalar type represents textual data, represented as UTF-8 character sequences. The String type is most often used by GraphQL to represent free-form human-readable text.
        api_base: The `String` scalar type represents textual data, represented as UTF-8 character sequences. The String type is most often used by GraphQL to represent free-form human-readable text.
        additional_config: The `JSON` scalar type represents JSON values as specified by [ECMA-404](https://ecma-international.org/wp-content/uploads/ECMA-404_2nd_edition_december_2017.pdf).
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Provider
    """
    return (
        await aexecute(
            CreateProviderMutation,
            {
                "input": {
                    "description": description,
                    "name": name,
                    "apiKey": api_key,
                    "apiBase": api_base,
                    "additionalConfig": additional_config,
                }
            },
            rath=rath,
        )
    ).create_provider


def create_provider(
    name: str,
    description: Optional[str] = None,
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    additional_config: Optional[Any] = None,
    rath: Optional[AlpakaRath] = None,
) -> Provider:
    """CreateProvider


    Args:
        description: The `String` scalar type represents textual data, represented as UTF-8 character sequences. The String type is most often used by GraphQL to represent free-form human-readable text.
        name: The `String` scalar type represents textual data, represented as UTF-8 character sequences. The String type is most often used by GraphQL to represent free-form human-readable text. (required)
        api_key: The `String` scalar type represents textual data, represented as UTF-8 character sequences. The String type is most often used by GraphQL to represent free-form human-readable text.
        api_base: The `String` scalar type represents textual data, represented as UTF-8 character sequences. The String type is most often used by GraphQL to represent free-form human-readable text.
        additional_config: The `JSON` scalar type represents JSON values as specified by [ECMA-404](https://ecma-international.org/wp-content/uploads/ECMA-404_2nd_edition_december_2017.pdf).
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Provider
    """
    return execute(
        CreateProviderMutation,
        {
            "input": {
                "description": description,
                "name": name,
                "apiKey": api_key,
                "apiBase": api_base,
                "additionalConfig": additional_config,
            }
        },
        rath=rath,
    ).create_provider


async def achat(
    model: IDCoercible,
    messages: Iterable[ChatMessageInput],
    tools: Optional[Iterable[ToolInput]] = None,
    temperature: Optional[float] = None,
    rath: Optional[AlpakaRath] = None,
) -> ChatResponse:
    """Chat


    Args:
        model: The `ID` scalar type represents a unique identifier, often used to refetch an object or as key for a cache. The ID type appears in a JSON response as a String; however, it is not intended to be human-readable. When expected as an input type, any string (such as `"4"`) or integer (such as `4`) input value will be accepted as an ID. (required)
        messages: A chat message input (required) (list) (required)
        tools: A large language model function call (required) (list)
        temperature: The `Float` scalar type represents signed double-precision fractional values as specified by [IEEE 754](https://en.wikipedia.org/wiki/IEEE_floating_point).
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        ChatResponse
    """
    return (
        await aexecute(
            ChatMutation,
            {
                "input": {
                    "model": model,
                    "messages": messages,
                    "tools": tools,
                    "temperature": temperature,
                }
            },
            rath=rath,
        )
    ).chat


def chat(
    model: IDCoercible,
    messages: Iterable[ChatMessageInput],
    tools: Optional[Iterable[ToolInput]] = None,
    temperature: Optional[float] = None,
    rath: Optional[AlpakaRath] = None,
) -> ChatResponse:
    """Chat


    Args:
        model: The `ID` scalar type represents a unique identifier, often used to refetch an object or as key for a cache. The ID type appears in a JSON response as a String; however, it is not intended to be human-readable. When expected as an input type, any string (such as `"4"`) or integer (such as `4`) input value will be accepted as an ID. (required)
        messages: A chat message input (required) (list) (required)
        tools: A large language model function call (required) (list)
        temperature: The `Float` scalar type represents signed double-precision fractional values as specified by [IEEE 754](https://en.wikipedia.org/wiki/IEEE_floating_point).
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        ChatResponse
    """
    return execute(
        ChatMutation,
        {
            "input": {
                "model": model,
                "messages": messages,
                "tools": tools,
                "temperature": temperature,
            }
        },
        rath=rath,
    ).chat


async def aquery_documents(
    collection: ID,
    query_texts: List[str],
    n_results: Optional[int] = None,
    where: Optional[Any] = None,
    rath: Optional[AlpakaRath] = None,
) -> Tuple[Document, ...]:
    """QueryDocuments


    Args:
        collection (ID): No description
        query_texts (List[str]): No description
        n_results (Optional[int], optional): No description.
        where (Optional[Any], optional): No description.
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        List[Document]
    """
    return (
        await aexecute(
            QueryDocumentsQuery,
            {
                "collection": collection,
                "queryTexts": query_texts,
                "nResults": n_results,
                "where": where,
            },
            rath=rath,
        )
    ).documents


def query_documents(
    collection: ID,
    query_texts: List[str],
    n_results: Optional[int] = None,
    where: Optional[Any] = None,
    rath: Optional[AlpakaRath] = None,
) -> Tuple[Document, ...]:
    """QueryDocuments


    Args:
        collection (ID): No description
        query_texts (List[str]): No description
        n_results (Optional[int], optional): No description.
        where (Optional[Any], optional): No description.
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        List[Document]
    """
    return execute(
        QueryDocumentsQuery,
        {
            "collection": collection,
            "queryTexts": query_texts,
            "nResults": n_results,
            "where": where,
        },
        rath=rath,
    ).documents


async def aget_chroma_collection(
    id: ID, rath: Optional[AlpakaRath] = None
) -> ChromaCollection:
    """GetChromaCollection


    Args:
        id (ID): No description
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        ChromaCollection
    """
    return (
        await aexecute(GetChromaCollectionQuery, {"id": id}, rath=rath)
    ).chroma_collection


def get_chroma_collection(
    id: ID, rath: Optional[AlpakaRath] = None
) -> ChromaCollection:
    """GetChromaCollection


    Args:
        id (ID): No description
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        ChromaCollection
    """
    return execute(GetChromaCollectionQuery, {"id": id}, rath=rath).chroma_collection


async def asearch_chroma_collection(
    search: Optional[str] = None,
    values: Optional[List[ID]] = None,
    rath: Optional[AlpakaRath] = None,
) -> Tuple[SearchChromaCollectionQueryOptions, ...]:
    """SearchChromaCollection


    Args:
        search (Optional[str], optional): No description.
        values (Optional[List[ID]], optional): No description.
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        List[SearchChromaCollectionQueryChromacollections]
    """
    return (
        await aexecute(
            SearchChromaCollectionQuery, {"search": search, "values": values}, rath=rath
        )
    ).options


def search_chroma_collection(
    search: Optional[str] = None,
    values: Optional[List[ID]] = None,
    rath: Optional[AlpakaRath] = None,
) -> Tuple[SearchChromaCollectionQueryOptions, ...]:
    """SearchChromaCollection


    Args:
        search (Optional[str], optional): No description.
        values (Optional[List[ID]], optional): No description.
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        List[SearchChromaCollectionQueryChromacollections]
    """
    return execute(
        SearchChromaCollectionQuery, {"search": search, "values": values}, rath=rath
    ).options


async def alist_chroma_collections(
    filter: Optional[ChromaCollectionFilter] = None,
    pagination: Optional[OffsetPaginationInput] = None,
    rath: Optional[AlpakaRath] = None,
) -> Tuple[ChromaCollection, ...]:
    """ListChromaCollections


    Args:
        filter (Optional[ChromaCollectionFilter], optional): No description.
        pagination (Optional[OffsetPaginationInput], optional): No description.
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        List[ChromaCollection]
    """
    return (
        await aexecute(
            ListChromaCollectionsQuery,
            {"filter": filter, "pagination": pagination},
            rath=rath,
        )
    ).chroma_collections


def list_chroma_collections(
    filter: Optional[ChromaCollectionFilter] = None,
    pagination: Optional[OffsetPaginationInput] = None,
    rath: Optional[AlpakaRath] = None,
) -> Tuple[ChromaCollection, ...]:
    """ListChromaCollections


    Args:
        filter (Optional[ChromaCollectionFilter], optional): No description.
        pagination (Optional[OffsetPaginationInput], optional): No description.
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        List[ChromaCollection]
    """
    return execute(
        ListChromaCollectionsQuery,
        {"filter": filter, "pagination": pagination},
        rath=rath,
    ).chroma_collections


async def aget_room(id: ID, rath: Optional[AlpakaRath] = None) -> Room:
    """GetRoom


    Args:
        id (ID): No description
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Room
    """
    return (await aexecute(GetRoomQuery, {"id": id}, rath=rath)).room


def get_room(id: ID, rath: Optional[AlpakaRath] = None) -> Room:
    """GetRoom


    Args:
        id (ID): No description
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        Room
    """
    return execute(GetRoomQuery, {"id": id}, rath=rath).room


async def asearch_rooms(
    search: Optional[str] = None,
    values: Optional[List[ID]] = None,
    rath: Optional[AlpakaRath] = None,
) -> Tuple[SearchRoomsQueryOptions, ...]:
    """SearchRooms


    Args:
        search (Optional[str], optional): No description.
        values (Optional[List[ID]], optional): No description.
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        List[SearchRoomsQueryRooms]
    """
    return (
        await aexecute(
            SearchRoomsQuery, {"search": search, "values": values}, rath=rath
        )
    ).options


def search_rooms(
    search: Optional[str] = None,
    values: Optional[List[ID]] = None,
    rath: Optional[AlpakaRath] = None,
) -> Tuple[SearchRoomsQueryOptions, ...]:
    """SearchRooms


    Args:
        search (Optional[str], optional): No description.
        values (Optional[List[ID]], optional): No description.
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        List[SearchRoomsQueryRooms]
    """
    return execute(
        SearchRoomsQuery, {"search": search, "values": values}, rath=rath
    ).options


async def alist_rooms(
    filter: Optional[RoomFilter] = None,
    pagination: Optional[OffsetPaginationInput] = None,
    rath: Optional[AlpakaRath] = None,
) -> Tuple[Room, ...]:
    """ListRooms


    Args:
        filter (Optional[RoomFilter], optional): No description.
        pagination (Optional[OffsetPaginationInput], optional): No description.
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        List[Room]
    """
    return (
        await aexecute(
            ListRoomsQuery, {"filter": filter, "pagination": pagination}, rath=rath
        )
    ).rooms


def list_rooms(
    filter: Optional[RoomFilter] = None,
    pagination: Optional[OffsetPaginationInput] = None,
    rath: Optional[AlpakaRath] = None,
) -> Tuple[Room, ...]:
    """ListRooms


    Args:
        filter (Optional[RoomFilter], optional): No description.
        pagination (Optional[OffsetPaginationInput], optional): No description.
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        List[Room]
    """
    return execute(
        ListRoomsQuery, {"filter": filter, "pagination": pagination}, rath=rath
    ).rooms


async def aget_llm_model(id: ID, rath: Optional[AlpakaRath] = None) -> LLMModel:
    """GetLLMModel


    Args:
        id (ID): No description
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        LLMModel
    """
    return (await aexecute(GetLLMModelQuery, {"id": id}, rath=rath)).llm_model


def get_llm_model(id: ID, rath: Optional[AlpakaRath] = None) -> LLMModel:
    """GetLLMModel


    Args:
        id (ID): No description
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        LLMModel
    """
    return execute(GetLLMModelQuery, {"id": id}, rath=rath).llm_model


async def asearch_llm_models(
    search: Optional[str] = None,
    values: Optional[List[ID]] = None,
    rath: Optional[AlpakaRath] = None,
) -> Tuple[SearchLLMModelsQueryOptions, ...]:
    """SearchLLMModels


    Args:
        search (Optional[str], optional): No description.
        values (Optional[List[ID]], optional): No description.
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        List[SearchLLMModelsQueryLlmmodels]
    """
    return (
        await aexecute(
            SearchLLMModelsQuery, {"search": search, "values": values}, rath=rath
        )
    ).options


def search_llm_models(
    search: Optional[str] = None,
    values: Optional[List[ID]] = None,
    rath: Optional[AlpakaRath] = None,
) -> Tuple[SearchLLMModelsQueryOptions, ...]:
    """SearchLLMModels


    Args:
        search (Optional[str], optional): No description.
        values (Optional[List[ID]], optional): No description.
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        List[SearchLLMModelsQueryLlmmodels]
    """
    return execute(
        SearchLLMModelsQuery, {"search": search, "values": values}, rath=rath
    ).options


async def alist_ll_models(
    filter: Optional[LLMModelFilter] = None,
    pagination: Optional[OffsetPaginationInput] = None,
    rath: Optional[AlpakaRath] = None,
) -> Tuple[LLMModel, ...]:
    """ListLLModels


    Args:
        filter (Optional[LLMModelFilter], optional): No description.
        pagination (Optional[OffsetPaginationInput], optional): No description.
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        List[LLMModel]
    """
    return (
        await aexecute(
            ListLLModelsQuery, {"filter": filter, "pagination": pagination}, rath=rath
        )
    ).llm_models


def list_ll_models(
    filter: Optional[LLMModelFilter] = None,
    pagination: Optional[OffsetPaginationInput] = None,
    rath: Optional[AlpakaRath] = None,
) -> Tuple[LLMModel, ...]:
    """ListLLModels


    Args:
        filter (Optional[LLMModelFilter], optional): No description.
        pagination (Optional[OffsetPaginationInput], optional): No description.
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        List[LLMModel]
    """
    return execute(
        ListLLModelsQuery, {"filter": filter, "pagination": pagination}, rath=rath
    ).llm_models


async def awatch_room(
    room: ID, agent_id: ID, rath: Optional[AlpakaRath] = None
) -> AsyncIterator[WatchRoomSubscriptionRoom]:
    """WatchRoom


    Args:
        room (ID): No description
        agent_id (ID): No description
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        WatchRoomSubscriptionRoom
    """
    async for event in asubscribe(
        WatchRoomSubscription, {"room": room, "agentId": agent_id}, rath=rath
    ):
        yield event.room


def watch_room(
    room: ID, agent_id: ID, rath: Optional[AlpakaRath] = None
) -> Iterator[WatchRoomSubscriptionRoom]:
    """WatchRoom


    Args:
        room (ID): No description
        agent_id (ID): No description
        rath (alpaka.rath.AlpakaRath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        WatchRoomSubscriptionRoom
    """
    for event in subscribe(
        WatchRoomSubscription, {"room": room, "agentId": agent_id}, rath=rath
    ):
        yield event.room


AddDocumentsToCollectionInput.model_rebuild()
ChatInput.model_rebuild()
ChatMessageInput.model_rebuild()
ChromaCollectionFilter.model_rebuild()
LLMModelFilter.model_rebuild()
RoomFilter.model_rebuild()
ToolInput.model_rebuild()
