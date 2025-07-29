from dataclasses import dataclass, asdict


@dataclass
class Task:
    content: str = ""
    done: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Task":
        return Task(content=data.get("content", ""), done=data.get("done", False))
