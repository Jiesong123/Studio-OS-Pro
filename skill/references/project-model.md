# 项目模型

规范项目对象定义在 `schemas/video-project.schema.json` 中。

必填字段包括 `project_id`、`prompt`、`aspect_ratio`、`duration_sec`、`status`、`shots` 和 `renders`。镜头是最小修改单元。素材应保留 Provider、artifact ID、URI 以及来源镜头 ID。

MVP 允许的状态：`created`、`script_ready`、`storyboard_ready`、`rendering`、`completed`、`failed`。
