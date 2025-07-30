from datetime import datetime
from enum import Enum
from typing import Annotated
from typing import List
from typing import Literal
from typing import Optional
from typing import TypeAlias
from typing import Union

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import confloat
from pydantic import conint
from pydantic import Discriminator
from pydantic import Field
from pydantic import field_validator
from pydantic import HttpUrl
from pydantic import UUID4

from superwise_api.models import SuperwiseEntity
from superwise_api.models.application.flowise import FlowiseCredentialUserInput
from superwise_api.models.context.context import ContextDef
from superwise_api.models.tool.tool import ToolDef


class ModelProvider(str, Enum):
    OPENAI = "OpenAI"
    OPENAI_COMPATIBLE = "OpenAICompatible"
    GOOGLE = "GoogleAI"
    ANTHROPIC = "Anthropic"
    VERTEX_AI_MODEL_GARDEN = "VertexAIModelGarden"


class OpenAIModelVersion(str, Enum):
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4_1 = "gpt-4.1"
    GPT_4_1_MINI = "gpt-4.1-mini"
    GPT_4_1_NANO = "gpt-4.1-nano"
    CHATGPT_4O_LATEST = "chatgpt-4o-latest"
    O1 = "o1"
    O1_MINI = "o1-mini"
    O1_PREVIEW = "o1-preview"
    O3_MINI = "o3-mini"


class GoogleModelVersion(str, Enum):
    GEMINI_1_5_FLASH = "models/gemini-1.5-flash"
    GEMINI_1_5_FLASH_8B = "models/gemini-1.5-flash-8b"
    GEMINI_1_5 = "models/gemini-1.5-pro"
    GEMINI_2_0_FLASH = "models/gemini-2.0-flash"
    GEMINI_2_0_FLASH_LITE = "models/gemini-2.0-flash-lite"
    GEMINI_2_0_FLASH_EXP = "models/gemini-2.0-flash-exp"
    GEMINI_2_0_FLASH_THINKING_EXP = "models/gemini-2.0-flash-thinking-exp"


class AnthropicModelVersion(str, Enum):
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet-latest"
    CLAUDE_3_7_SONNET = "claude-3-7-sonnet-latest"
    CLAUDE_3_5_HAIKU = "claude-3-5-haiku-latest"
    CLAUDE_3_OPUS = "claude-3-opus-latest"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"


class VertexAIModelGardenVersion(str, Enum):
    PLACEHOLDER = "placeholder"


class ApplicationStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    DEGRADED = "degraded"


class OpenAIParameters(BaseModel):
    temperature: confloat(ge=0, le=2) = 0
    top_p: confloat(ge=0, le=1) = 1


class OpenAICompatibleParameters(OpenAIParameters):
    top_p: Optional[confloat(ge=0, le=1)] = None
    top_k: Optional[conint(ge=1)] = None


class GoogleParameters(BaseModel):
    temperature: confloat(ge=0, le=1) = 0
    top_p: confloat(ge=0, le=1) = 1
    top_k: conint(ge=1) = 40


class AnthropicParameters(BaseModel):
    temperature: confloat(ge=0, le=1) = 0
    top_p: confloat(ge=0, le=1) = 1
    top_k: conint(ge=1) = 40


class VertexAIModelGardenParameters(BaseModel):
    pass


class BaseModelLLM(BaseModel):
    api_token: str

    @classmethod
    def from_dict(cls, obj: dict):
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return ModelLLM.model_validate(obj)

        _obj = ModelLLM.model_validate(
            {"provider": obj.get("provider"), "version": obj.get("version"), "api_token": obj.get("api_token")}
        )
        return _obj


class OpenAIModel(BaseModelLLM):
    provider: Literal[ModelProvider.OPENAI] = ModelProvider.OPENAI.value
    version: OpenAIModelVersion
    parameters: OpenAIParameters = Field(default_factory=OpenAIParameters)


class OpenAICompatibleModel(BaseModelLLM):
    provider: Literal[ModelProvider.OPENAI_COMPATIBLE] = ModelProvider.OPENAI_COMPATIBLE.value
    version: str
    parameters: OpenAICompatibleParameters = Field(default_factory=OpenAICompatibleParameters)
    base_url: str


class GoogleModel(BaseModelLLM):
    provider: Literal[ModelProvider.GOOGLE] = ModelProvider.GOOGLE.value
    version: GoogleModelVersion
    parameters: GoogleParameters = Field(default_factory=GoogleParameters)


class AnthropicModel(BaseModelLLM):
    provider: Literal[ModelProvider.ANTHROPIC] = ModelProvider.ANTHROPIC.value
    version: AnthropicModelVersion
    parameters: AnthropicParameters = Field(default_factory=AnthropicParameters)


class VertexAIModelGardenModel(BaseModelLLM):
    provider: Literal[ModelProvider.VERTEX_AI_MODEL_GARDEN] = ModelProvider.VERTEX_AI_MODEL_GARDEN.value
    version: VertexAIModelGardenVersion
    parameters: VertexAIModelGardenParameters = Field(default_factory=VertexAIModelGardenParameters)


ModelLLM = Annotated[
    Union[OpenAIModel, OpenAICompatibleModel, GoogleModel, AnthropicModel, VertexAIModelGardenModel],
    Field(..., discriminator="provider"),
]


class ApplicationType(str, Enum):
    REACT_AGENT = "ReactAgent"
    AI_ASSISTANT = "AIAssistant"
    BASIC_LLM = "BasicLLM"
    FLOWISE = "Flowise"


class ReactAgentConfig(SuperwiseEntity):
    type: Literal[ApplicationType.REACT_AGENT.value] = ApplicationType.REACT_AGENT.value
    tools: List[ToolDef]


AdvancedAgentConfig: TypeAlias = ReactAgentConfig


class ContextChainConfig(SuperwiseEntity):
    type: Literal[ApplicationType.AI_ASSISTANT.value] = ApplicationType.AI_ASSISTANT.value
    context: Optional[ContextDef]


AIAssistantConfig: TypeAlias = ContextChainConfig


class BasicLLMConfig(SuperwiseEntity):
    type: Literal[ApplicationType.BASIC_LLM.value] = ApplicationType.BASIC_LLM.value


class FlowiseConfigBase(SuperwiseEntity):
    type: Literal[ApplicationType.FLOWISE.value] = ApplicationType.FLOWISE.value
    flow_id: str | None = None
    url: str | None = None
    api_key: str | None = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v:
            return v
        HttpUrl(v)
        return v


class FlowiseGetCredentialSchema(FlowiseConfigBase):
    pass


class FlowiseAppConfig(FlowiseConfigBase):
    flowise_credentials: FlowiseCredentialUserInput | None = None


ADDITIONAL_CONFIG = Annotated[
    ReactAgentConfig | ContextChainConfig | BasicLLMConfig | FlowiseAppConfig, Discriminator("type")
]


class ApplicationBaseGuard(BaseModel):
    name: str
    tag: Literal["input"] | Literal["output"]
    model_config = ConfigDict(extra="allow")


class ApplicationAllowedTopicsGuard(ApplicationBaseGuard):
    topics: List[str]
    type: Literal["allowed_topics"] = Field(default="allowed_topics")
    model: OpenAIModel


class ApplicationRestrictedTopicsGuard(ApplicationBaseGuard):
    topics: List[str]
    type: Literal["restricted_topics"] = Field(default="restricted_topics")
    model: OpenAIModel


class ApplicationToxicityGuard(ApplicationBaseGuard):
    type: Literal["toxicity"] = Field(default="toxicity")
    threshold: float = 0.5
    validation_method: Literal["sentence"] | Literal["full"] = "sentence"


ApplicationGuard = Annotated[
    Union[ApplicationToxicityGuard, ApplicationAllowedTopicsGuard, ApplicationRestrictedTopicsGuard],
    Field(discriminator="type"),
]
ApplicationGuards = List[ApplicationGuard]


class Application(SuperwiseEntity):
    id: UUID4
    created_by: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    name: str = Field(..., min_length=1, max_length=95)
    llm_model: ModelLLM | None = Field(None, alias="model")
    prompt: str | None
    dataset_id: str
    additional_config: ADDITIONAL_CONFIG
    url: HttpUrl
    show_cites: bool = Field(default=False)
    status: ApplicationStatus = ApplicationStatus.UNKNOWN
    guards: ApplicationGuards
    api_token: UUID4

    @classmethod
    def from_dict(cls, obj: dict):
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return Application.model_validate(obj)

        _obj = Application.model_validate(
            {
                "id": obj.get("id"),
                "created_by": obj.get("created_by"),
                "created_at": obj.get("created_at"),
                "updated_at": obj.get("updated_at"),
                "name": obj.get("name"),
                "model": obj.get("model"),
                "prompt": obj.get("prompt"),
                "dataset_id": obj.get("dataset_id"),
                "additional_config": obj.get("additional_config"),
                "url": obj.get("url"),
                "show_cites": obj.get("show_cites"),
                "status": obj.get("status"),
                "guards": obj.get("guards"),
                "api_token": obj.get("api_token"),
            }
        )
        return _obj
