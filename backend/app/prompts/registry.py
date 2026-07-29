from dataclasses import dataclass
from pathlib import Path
from string import Template


@dataclass(frozen=True)
class PromptTemplate:
    name: str
    version: str
    content: str

    @property
    def prompt_id(self) -> str:
        return f"{self.name}@{self.version}"

    def render(self, **values: object) -> str:
        return Template(self.content).safe_substitute(
            {key: str(value) for key, value in values.items()}
        )


class PromptRegistry:
    def __init__(self, template_dir: Path | None = None):
        self.template_dir = template_dir or Path(__file__).parent / "templates"
        self._cache: dict[str, PromptTemplate] = {}

    def get(self, name: str, version: str = "v1") -> PromptTemplate:
        prompt_id = f"{name}@{version}"
        if prompt_id in self._cache:
            return self._cache[prompt_id]

        path = self.template_dir / f"{name}.{version}.md"
        if not path.exists():
            raise FileNotFoundError(f"Prompt template not found: {path}")

        template = PromptTemplate(name=name, version=version, content=path.read_text())
        self._cache[prompt_id] = template
        return template

