from copy import deepcopy

from ..models.project import VideoProject


class InMemoryProjectStore:
    """Small store used by the MVP; replace with SQLite for production."""

    def __init__(self) -> None:
        self._projects: dict[str, VideoProject] = {}

    def save(self, project: VideoProject) -> VideoProject:
        self._projects[project.project_id] = deepcopy(project)
        return project

    def get(self, project_id: str) -> VideoProject:
        return deepcopy(self._projects[project_id])

