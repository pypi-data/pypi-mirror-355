import uuid

from typing import Dict, List, Optional

from clipped.compact.pydantic import StrictStr
from clipped.types.uuids import UUIDStr

from polyaxon._schemas.base import BaseSchemaModel
from traceml.artifacts.enums import V1ArtifactKind


class V1RunArtifact(BaseSchemaModel):
    _IDENTIFIER = "artifact"

    name: Optional[StrictStr] = None
    kind: Optional[V1ArtifactKind] = None
    path: Optional[StrictStr] = None
    state: Optional[UUIDStr] = None
    summary: Optional[Dict] = None
    meta_info: Optional[Dict] = None
    run: Optional[UUIDStr] = None
    connection: Optional[StrictStr] = None
    is_input: Optional[bool] = None

    @classmethod
    def from_model(cls, model):
        return cls(
            name=model.name,
            kind=model.kind,
            path=model.path,
            state=model.state,
            summary=model.summary,
            # connection=model.connection,  # TODO: enable
        )

    def get_state(self, namespace: uuid.UUID):
        if self.state:
            return self.state
        summary = self.summary or {}
        content = str(summary)
        if not summary.get("hash") and self.path:
            content += self.path
        return uuid.uuid5(namespace, content)


class V1RunArtifacts(BaseSchemaModel):
    _IDENTIFIER = "artifacts"

    artifacts: Optional[List[V1RunArtifact]]
