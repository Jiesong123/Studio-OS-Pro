from studio_os_video import VideoPipeline


def test_mvp_pipeline_is_resumable_and_renders():
    pipeline = VideoPipeline()
    project = pipeline.create_project("智能盒子产品介绍", duration_sec=30)
    pipeline.plan(project.project_id)
    pipeline.storyboard(project.project_id, shot_count=3)
    first = pipeline.generate_assets(project.project_id)
    second = pipeline.generate_assets(project.project_id)
    assert len(first.assets) == 3
    assert len(second.assets) == 3
    assert len(second.shots[0].assets) == 1
    completed = pipeline.render(project.project_id)
    assert completed.status == "completed"
    assert completed.renders[0]["uri"].endswith(".mp4")

