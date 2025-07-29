# AutoGen Core Serialization of Basic Python Types

## Summary

After analyzing the autogen_core module, here's how basic Python types like strings are handled in the serialization system:

## Key Components

### 1. `_type_name` Function
Located in `autogen_core._serialization`, this function determines the type name for serialization:

```python
def _type_name(cls: type[Any] | Any) -> str:
    # For protobuf messages, uses DESCRIPTOR.full_name
    # For types (classes), returns cls.__name__
    # For instances, returns cls.__class__.__name__
```

For basic Python types:
- `_type_name("hello")` returns `"str"`
- `_type_name(42)` returns `"int"`
- `_type_name(3.14)` returns `"float"`
- `_type_name(True)` returns `"bool"`

### 2. SerializationRegistry
The registry manages serializers but **does NOT include default serializers for primitive types**:
- No built-in serializers for str, int, float, bool, list, dict, etc.
- Only provides serializers for dataclasses, Pydantic models, and protobuf messages via `try_get_known_serializers_for_type()`

### 3. Message Serializers
AutoGen Core provides three main serializer classes:
- `DataclassJsonMessageSerializer` - for dataclasses
- `PydanticJsonMessageSerializer` - for Pydantic BaseModel subclasses  
- `ProtobufMessageSerializer` - for protobuf Message instances

## Handling Primitive Types

### Problem
When you try to send a raw string through the runtime:
```python
await runtime.send_message("hello", recipient=agent_id)
```

The runtime will:
1. Call `_type_name("hello")` → returns `"str"`
2. Try to find a serializer for type `"str"` with content type `"application/json"`
3. **Fail** with: `ValueError: Unknown type str with content type application/json`

### Solutions

#### 1. Wrap primitives in dataclasses or Pydantic models:
```python
from dataclasses import dataclass
from pydantic import BaseModel

@dataclass
class StringMessage:
    value: str

class PydanticString(BaseModel):
    value: str
```

#### 2. Create custom serializers for primitive types:
```python
import json
from autogen_core import MessageSerializer

class StringSerializer(MessageSerializer[str]):
    @property
    def data_content_type(self) -> str:
        return "application/json"
    
    @property
    def type_name(self) -> str:
        return "str"
    
    def deserialize(self, payload: bytes) -> str:
        return json.loads(payload.decode("utf-8"))
    
    def serialize(self, message: str) -> bytes:
        return json.dumps(message).encode("utf-8")

# Register with runtime
runtime.add_message_serializer(StringSerializer())
```

## Why the Samples Work

The UpperAgent example appears to handle raw strings:
```python
async def on_message(self, message: str, ctx: MessageContext):
    return message.upper()
```

However, this likely only works in specific scenarios:
1. **Local runtime**: Messages passed as Python objects without serialization
2. **Custom serializers**: The samples may register string serializers (not shown in the code)
3. **Special handling**: The HTTP runtime might have undocumented string handling

## Best Practices

1. **Always use structured messages** (dataclasses or Pydantic models) for cross-process communication
2. **Register appropriate serializers** when using the HTTP runtime
3. **Don't rely on primitive type serialization** without explicit serializer registration

## Example: Proper Message Definition

```python
from dataclasses import dataclass
from pydantic import BaseModel

# Option 1: Dataclass
@dataclass
class TextMessage:
    content: str

# Option 2: Pydantic  
class TextRequest(BaseModel):
    text: str

class TextResponse(BaseModel):
    result: str

# Register serializers
runtime.add_message_serializer([
    DataclassJsonMessageSerializer(TextMessage),
    PydanticJsonMessageSerializer(TextRequest),
    PydanticJsonMessageSerializer(TextResponse),
])
```

This approach ensures reliable serialization across different runtime implementations and network boundaries.