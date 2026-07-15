from studio_os_video import VideoPipeline


pipeline = VideoPipeline()
project = pipeline.create_project(
    "展示一款帮助创作者快速完成视频的智能盒子",
    aspect_ratio="9:16",
    duration_sec=30,
    platform="douyin",
)
pipeline.refresh_execution_plan(project.project_id)
pipeline.plan(project.project_id)
pipeline.storyboard(project.project_id, shot_count=3)
pipeline.generate_assets(project.project_id)
completed = pipeline.render(project.project_id)
print(completed.to_dict())
