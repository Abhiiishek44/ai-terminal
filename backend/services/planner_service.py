from dataclasses import dataclass
from typing import List, Optional

from services.dependency_detector import DependencyDetector


@dataclass
class PlanStep:
    id: int
    kind: str
    command: str
    description: str
    requires: List[str]


class PlannerService:
    """
    Creates a step-by-step executable plan from one natural language instruction.
    """

    def __init__(self, detector: Optional[DependencyDetector] = None):
        self.detector = detector or DependencyDetector()

    def build_plan(self, user_input: str, ai_command: str) -> List[PlanStep]:
        steps: List[PlanStep] = []
        text = user_input.lower()

        if "create" in text and "folder" in text:
            folder_name = self._extract_folder_name(user_input) or "new-project"
            steps.append(
                PlanStep(
                    id=len(steps) + 1,
                    kind="filesystem",
                    command=f"mkdir -p {folder_name}",
                    description=f"Create folder '{folder_name}'",
                    requires=[],
                )
            )
            steps.append(
                PlanStep(
                    id=len(steps) + 1,
                    kind="navigation",
                    command=f"cd {folder_name}",
                    description=f"Change directory to '{folder_name}'",
                    requires=[],
                )
            )

        detection = self.detector.detect(f"{user_input} {ai_command}")
        for dep in sorted(detection.dependencies):
            check_cmd = f"which {dep} || {dep} --version"
            steps.append(
                PlanStep(
                    id=len(steps) + 1,
                    kind="precheck",
                    command=check_cmd,
                    description=f"Check whether '{dep}' is available",
                    requires=[dep],
                )
            )

        steps.append(
            PlanStep(
                id=len(steps) + 1,
                kind="action",
                command=ai_command,
                description="Execute requested task",
                requires=sorted(detection.dependencies),
            )
        )
        return steps

    def _extract_folder_name(self, text: str) -> Optional[str]:
        # simple heuristic: "folder <name>" or "called <name>"
        lowered = text.lower()
        for marker in ["folder", "called", "named"]:
            if marker in lowered:
                tail = text[lowered.index(marker) + len(marker):].strip()
                if tail:
                    return tail.split()[0].strip("'\".,")
        return None
