from dataclasses import dataclass, field
from typing import Dict, List, Set


@dataclass
class DependencyResult:
    dependencies: Set[str] = field(default_factory=set)
    inferred_package_managers: Set[str] = field(default_factory=set)


class DependencyDetector:
    """
    Generic dependency detector based on command/user intent tokens.
    """

    def __init__(self):
        self.tool_map: Dict[str, List[str]] = {
            "pandas": ["python", "pip"],
            "numpy": ["python", "pip"],
            "pip": ["python", "pip"],
            "python": ["python", "pip"],
            "npm": ["node", "npm"],
            "node": ["node", "npm"],
            "yarn": ["node", "yarn"],
            "pnpm": ["node", "pnpm"],
            "docker": ["docker"],
            "docker-compose": ["docker", "docker-compose"],
            "git": ["git"],
            "go": ["go"],
            "cargo": ["rust", "cargo"],
            "rust": ["rust", "cargo"],
            "java": ["java", "javac"],
            "maven": ["java", "mvn"],
            "gradle": ["java", "gradle"],
        }

    def detect(self, text: str) -> DependencyResult:
        tokens = set(part.strip().lower() for part in text.replace("\n", " ").split())
        result = DependencyResult()

        for token in tokens:
            clean = token.strip(" ,.;:\"'()[]{}")
            if clean in self.tool_map:
                for dep in self.tool_map[clean]:
                    result.dependencies.add(dep)
                if clean in {"pip", "npm", "pnpm", "yarn", "maven", "gradle", "cargo"}:
                    result.inferred_package_managers.add(clean)

        if "npm" in text.lower() or "npx" in text.lower():
            result.dependencies.update({"node", "npm"})
        if "pip install" in text.lower():
            result.dependencies.update({"python", "pip"})

        return result
