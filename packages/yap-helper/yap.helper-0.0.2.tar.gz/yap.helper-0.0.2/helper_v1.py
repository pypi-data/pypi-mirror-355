from dataclasses import dataclass, field
import json
import os
from typing import Any, Dict

@dataclass
class TagProvInstance:
    data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_json_file(cls, filepath: str) -> "TagProvInstance":
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls(data)

    def get_tag(self, tag_name: str) -> Any:
        return self.data.get(tag_name)

    def update_tag(self, tag_name: str, value: Any) -> None:
        self.data[tag_name] = value

    def to_json_file(self, filepath: str) -> None:
        with open(filepath, 'w') as f:
            json.dump(self.data, f, indent=2)
