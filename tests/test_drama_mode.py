from studio_os_video import Character, VideoPipeline


def test_drama_project_has_series_characters_and_episodes():
    pipeline = VideoPipeline()
    project = pipeline.create_drama_project(
        title="失踪的录音",
        genre="都市悬疑",
        prompt="一名记者追查一段改变案件的录音",
        episode_count=3,
        characters=[Character.create("林夏", "protagonist")],
    )
    assert project.mode == "drama"
    assert project.series["episode_count"] == 3
    assert len(project.series["episodes"]) == 3
    assert project.series["characters"][0]["name"] == "林夏"

