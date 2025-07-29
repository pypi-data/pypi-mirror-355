from __future__ import annotations

import typing as t

import typing_extensions as te

if t.TYPE_CHECKING:
    from .tools import Tool, ToolExecutionResponse


class BeforeExecute(t.Protocol):
    """
    A modifier that is called before the tool is executed.
    """

    def __call__(
        self,
        tool: str,
        toolkit: str,
        params: t.Dict,
    ) -> t.Dict: ...


class AfterExecute(t.Protocol):
    """
    A modifier that is called after the tool is executed.
    """

    def __call__(
        self,
        tool: str,
        toolkit: str,
        response: ToolExecutionResponse,
    ) -> ToolExecutionResponse: ...


class SchemaModifier(t.Protocol):
    """
    A modifier that is called to modify the schema of the tool.
    """

    def __call__(self, tool: "Tool") -> "Tool": ...


ModifierSlug: t.TypeAlias = str

AfterExecuteModifierL: t.TypeAlias = t.Literal["after_execute"]
BeforeExecuteModifierL: t.TypeAlias = t.Literal["before_execute"]
SchemaModifierL: t.TypeAlias = t.Literal["schema"]

ModifierReturnType = t.TypeVar(
    "ModifierReturnType", t.Dict, "ToolExecutionResponse", "Tool"
)
ModifierCallable = t.Callable[[ModifierReturnType], ModifierReturnType]


# NOTE: This is rushed implementation, will be refactored later
class Modifier(t.Generic[ModifierReturnType]):
    def __init__(
        self,
        modifier: t.Optional[ModifierCallable[ModifierReturnType]],
        type_: AfterExecuteModifierL | BeforeExecuteModifierL | SchemaModifierL,
        tools: t.List[str],
        toolkits: t.List[str],
    ) -> None:
        self.modifier = modifier
        self.tools = tools
        self.type = type_
        self.toolkits = toolkits

    def apply(
        self,
        type_: str,
        slug: str,
        data: ModifierReturnType,
    ) -> ModifierReturnType:
        if self.modifier is None:
            raise ValueError("Modifier is not provided")

        # If no tools or toolkits are provided, apply the modifier to all tools
        if self.type == type_ and len(self.tools) == 0 and len(self.toolkits) == 0:
            return self.modifier(data)

        # If the modifier is not the same type, or the slug is not in the tools or toolkits, return the data as is
        if self.type != type_ or slug not in self.tools and slug not in self.toolkits:
            return data

        # Apply the modifier to the data
        return self.modifier(data)

    def __call__(self, modifier: ModifierCallable[ModifierReturnType]) -> te.Self:
        self.modifier = modifier
        return self


def wrap_modifier(
    modifier: t.Optional[ModifierCallable[ModifierReturnType]],
    type_: AfterExecuteModifierL | BeforeExecuteModifierL | SchemaModifierL,
    tools: t.Optional[t.List[str]],
    toolkits: t.Optional[t.List[str]],
) -> Modifier:
    if modifier is not None:
        return Modifier(
            modifier=modifier,
            type_=type_,
            tools=tools or [],
            toolkits=toolkits or [],
        )

    if tools is not None or toolkits is not None:
        return Modifier(
            modifier=None,
            type_=type_,
            tools=tools or [],
            toolkits=toolkits or [],
        )

    raise ValueError("Either tools or toolkits must be provided")


@t.overload
def after_execute(
    modifier: t.Optional[AfterExecute],
) -> Modifier["ToolExecutionResponse"]: ...


@t.overload
def after_execute(
    *,
    tools: t.Optional[t.List[str]] = None,
    toolkits: t.Optional[t.List[str]] = None,
) -> t.Callable[[AfterExecute], Modifier["ToolExecutionResponse"]]: ...


def after_execute(
    modifier: t.Optional[AfterExecute] = None,
    *,
    tools: t.Optional[t.List[str]] = None,
    toolkits: t.Optional[t.List[str]] = None,
) -> (
    Modifier["ToolExecutionResponse"]
    | t.Callable[[AfterExecute], Modifier["ToolExecutionResponse"]]
):
    if modifier is not None:
        return Modifier(
            modifier=modifier,
            type_="after_execute",
            tools=tools or [],
            toolkits=toolkits or [],
        )

    if tools is not None or toolkits is not None:
        return Modifier(
            modifier=None,
            type_="after_execute",
            tools=tools or [],
            toolkits=toolkits or [],
        )

    raise ValueError("Either tools or toolkits must be provided")


@t.overload
def before_execute(modifier: t.Optional[BeforeExecute]) -> Modifier: ...


@t.overload
def before_execute(
    *,
    tools: t.Optional[t.List[str]] = None,
    toolkits: t.Optional[t.List[str]] = None,
) -> Modifier[t.Dict]: ...


def before_execute(
    modifier: t.Optional[BeforeExecute] = None,
    *,
    tools: t.Optional[t.List[str]] = None,
    toolkits: t.Optional[t.List[str]] = None,
):
    return wrap_modifier(
        modifier=modifier,
        type_="before_execute",
        tools=tools,
        toolkits=toolkits,
    )


@t.overload
def schema_modifier(modifier: t.Optional[SchemaModifier]) -> Modifier[Tool]: ...


@t.overload
def schema_modifier(
    *,
    tools: t.Optional[t.List[str]] = None,
    toolkits: t.Optional[t.List[str]] = None,
) -> Modifier[Tool]: ...


def schema_modifier(
    modifier: t.Optional[SchemaModifier] = None,
    *,
    tools: t.Optional[t.List[str]] = None,
    toolkits: t.Optional[t.List[str]] = None,
):
    return wrap_modifier(
        modifier=modifier,
        type_="schema",
        tools=tools,
        toolkits=toolkits,
    )


Modifiers = t.List[Modifier]


@t.overload
def apply_modifier_by_type(
    modifiers: Modifiers,
    slug: str,
    *,
    type: BeforeExecuteModifierL,
    request: t.Dict,
) -> t.Dict: ...


@t.overload
def apply_modifier_by_type(
    modifiers: Modifiers,
    slug: str,
    *,
    type: AfterExecuteModifierL,
    response: "ToolExecutionResponse",
) -> "ToolExecutionResponse": ...


@t.overload
def apply_modifier_by_type(
    modifiers: Modifiers,
    slug: str,
    *,
    type: t.Literal["schema"],
    schema: "Tool",
) -> "Tool": ...


def apply_modifier_by_type(
    modifiers: Modifiers,
    slug: str,
    *,
    type: t.Literal["before_execute", "after_execute", "schema"],
    schema: t.Optional["Tool"] = None,
    request: t.Optional[t.Dict] = None,
    response: t.Optional["ToolExecutionResponse"] = None,
) -> t.Union[t.Dict, "ToolExecutionResponse", "Tool"]:
    """Apply a modifier to a tool."""
    data = t.cast(dict, schema or request or response or {})
    for modifier in modifiers:
        data = modifier.apply(type_=type, slug=slug, data=data)
    return data


class ToolOptions(te.TypedDict):
    modify_schema: te.NotRequired[t.Dict[ModifierSlug, ExecuteModifier]]
