from ..models.project import ProjectStatus, VideoProject
from ..models.shot import Shot
from ..providers.base import Renderer, VideoProvider
from ..providers.mock import MockRenderer, MockVideoProvider
from ..storage.memory import InMemoryProjectStore
from ..media_box.capabilities import CapabilityRegistry, MediaCapabilities
from ..media_box.planner import RuntimePlanner
from ..models.drama import Character, DramaSeries, Episode


class VideoPipeline:
    """Idempotent MVP pipeline: plan, storyboard, generate, render."""

    def __init__(self, store: InMemoryProjectStore | None = None, provider: VideoProvider | None = None, renderer: Renderer | None = None, capabilities: CapabilityRegistry | None = None):
        self.store = store or InMemoryProjectStore()
        self.provider = provider or MockVideoProvider()
        self.renderer = renderer or MockRenderer()
        self.capabilities = capabilities or CapabilityRegistry(MediaCapabilities("mock-media-box", "ready"))
        self.planner = RuntimePlanner()

    def create_project(self, prompt: str, **kwargs) -> VideoProject:
        project = VideoProject.create(prompt, **kwargs)
        self.store.save(project)
        return project

    def create_drama_project(self, title: str, genre: str, prompt: str, episode_count: int = 1, episode_duration_sec: int = 90, characters: list[Character] | None = None) -> VideoProject:
        """Create a drama-mode project while reusing the normal media pipeline."""
        series = DramaSeries.create(title, genre, episode_count=episode_count, episode_duration_sec=episode_duration_sec, characters=characters or [])
        series.episodes = [Episode(f"{series.series_id}_ep_{i:02d}", i, f"第{i}集") for i in range(1, episode_count + 1)]
        project = self.create_project(prompt, duration_sec=episode_duration_sec, mode="drama", series=series.to_dict())
        project.script = {"mode": "drama", "series_id": series.series_id, "title": title, "genre": genre}
        project.touch()
        self.store.save(project)
        return project

    def plan(self, project_id: str) -> VideoProject:
        project = self.store.get(project_id)
        project.script = {"title": project.prompt, "narration": project.prompt}
        project.status = ProjectStatus.SCRIPT_READY
        project.touch()
        self.store.save(project)
        return project

    def refresh_execution_plan(self, project_id: str, quality: str = "normal") -> VideoProject:
        project = self.store.get(project_id)
        if not self.capabilities.current.video_models:
            # Mock mode remains usable before a real media box is connected.
            project.runtime_plan = {"video_model": "mock-video", "shot_duration_sec": 4, "resolution": "mock"}
            reason = "no live media-box models; using mock provider"
        else:
            execution = self.planner.make_plan(project, self.capabilities, quality)
            project.runtime_plan = execution.to_dict()
            reason = execution.reason
        project.decision_log.append({"reason": reason, "runtime_plan": project.runtime_plan})
        project.touch()
        self.store.save(project)
        return project

    def storyboard(self, project_id: str, shot_count: int = 3) -> VideoProject:
        project = self.store.get(project_id)
        duration = round(project.duration_sec / shot_count, 2)
        project.shots = [
            Shot(
                shot_id=f"{project.project_id}_shot_{i + 1:02d}",
                index=i + 1,
                duration_sec=duration,
                purpose="建立场景" if i == 0 else "展示核心信息" if i < shot_count - 1 else "收束并行动召唤",
                visual_prompt=f"{project.prompt}; shot {i + 1}, cinematic, coherent visual identity",
                narration=project.prompt if i == 0 else None,
                subtitle=project.prompt if i == 0 else None,
            )
            for i in range(shot_count)
        ]
        project.status = ProjectStatus.STORYBOARD_READY
        project.touch()
        self.store.save(project)
        return project

    def generate_assets(self, project_id: str) -> VideoProject:
        project = self.store.get(project_id)
        for shot in project.shots:
            if shot.assets:
                continue
            result = self.provider.generate(shot.visual_prompt, shot.duration_sec, project.aspect_ratio)
            shot.assets.append(result.uri)
            shot.status = "asset_ready"
            project.assets.append({"shot_id": shot.shot_id, "artifact_id": result.artifact_id, "uri": result.uri})
        project.touch()
        self.store.save(project)
        return project

    def render(self, project_id: str) -> VideoProject:
        project = self.store.get(project_id)
        project.status = ProjectStatus.RENDERING
        result = self.renderer.render(project.project_id, [shot.to_dict() for shot in project.shots])
        project.renders.append({"artifact_id": result.artifact_id, "uri": result.uri, "provider": result.provider})
        project.status = ProjectStatus.COMPLETED
        project.touch()
        self.store.save(project)
        return project
