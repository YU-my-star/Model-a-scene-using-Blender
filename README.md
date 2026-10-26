# Blender 通用场景搭建 Skill

面向 AI 代理的 Blender 建模与渲染工作流，用于创建、修改和交付可编辑的三维场景。

**技能名称：`blender-build-and-render`**

适用于室内、建筑、展厅、产品展示、自然环境、街区和动画场景。可以从空场景开始，也可以复用已有 `.blend` 工程。静态模型、场景预览图、动画和视频按任务需要生成，参数与保存位置均可配置。

本仓库提供工作流、按需参考和检查脚本。使用时，由 AI 代理结合用户要求与本机环境，编写并执行实际建模、场景修改或渲染操作。

## 可以做什么

- **检查现有工程**：读取单位、相机、集合、材质、动画、外部依赖和渲染设置。
- **搭建或修改场景**：先验证尺寸、布局与空间关系，再完善几何和场景细节。
- **完成视觉表达**：根据参考和用途调整材质、灯光、环境、构图与镜头。
- **按需制作动画**：处理物体运动、相机漫游、流程演示及其他场景动画。
- **组织渲染任务**：先验证小样，再按规模安排分段、缓存和失败恢复。
- **核验实际成果**：检查工程可打开性、资源完整性、画面问题，以及视频帧数、时间连续性和定格一致性。

道路与导航实验作为可选模块保留；普通场景任务只读取通用部分。技能不预设某个社区、目的地、软件路径、分辨率、帧率或视频时长。

## 工作方式

```text
理解需求与检查环境
        ↓
检查已有工程，或建立新场景
        ↓
白模与空间关系验证
        ↓
几何、材质、灯光和镜头完善
        ↓
按需加入运动与动画
        ↓
代表性小样检查
        ↓
保存工程、生成成果并核验交付
```

已有工程优先增量修改，通常另存新版本。照片级写实、示意表达、静态模型和实验材料采用各自的验收要求；场景美术效果需要结合实际图像检查。

## 目录结构

```text
skill-blender/
├── README.md
├── .gitignore
├── .gitattributes
└── blender-build-and-render/
    ├── SKILL.md
    ├── agents/
    │   └── openai.yaml
    ├── references/
    │   ├── scene-quality.md
    │   ├── animation-rendering.md
    │   └── driving-navigation.md
    └── scripts/
        ├── inspect_scene.py
        └── verify_media.py
```

| 文件 | 用途 |
| --- | --- |
| [SKILL.md](blender-build-and-render/SKILL.md) | 技能入口、通用流程与交付要求 |
| [openai.yaml](blender-build-and-render/agents/openai.yaml) | 技能显示名称、简介与默认调用提示 |
| [scene-quality.md](blender-build-and-render/references/scene-quality.md) | 几何、材质、灯光、镜头、依赖与画面质量 |
| [animation-rendering.md](blender-build-and-render/references/animation-rendering.md) | 动画求值、分段渲染、编码、裁切与定格核验 |
| [driving-navigation.md](blender-build-and-render/references/driving-navigation.md) | 按需加载的道路、车辆与导航实验案例 |
| [inspect_scene.py](blender-build-and-render/scripts/inspect_scene.py) | 在 Blender 中读取工程并输出场景清单 |
| [verify_media.py](blender-build-and-render/scripts/verify_media.py) | 使用 FFmpeg 解码视频并核验实际参数 |

## 环境要求

| 组件 | 使用场合 |
| --- | --- |
| 支持本地 Skills 的 AI 代理 | 读取工作流，执行建模与渲染任务；安装示例以 Codex 为例 |
| Blender | 实际建模、场景编辑、渲染，以及运行场景清单脚本 |
| Python 3 | 单独运行视频核验脚本时使用 |
| FFmpeg | 执行视频解码和定格一致性核验时使用 |

附带脚本使用 Python 标准库及 Blender 自带的 `bpy`，无需另外安装第三方 Python 包。`inspect_scene.py` 应由 Blender 执行；普通 Python 环境不自带 `bpy`。

已在 **Blender 4.5.3 LTS** 和 **Python 3.12.14** 环境完成辅助工具测试。其他版本使用时，应核对相应 API 和可用渲染设置。

## 安装到 Codex

下载或克隆本仓库后，复制内部的 **`blender-build-and-render` 文件夹**，保持 `SKILL.md`、`agents`、`references` 和 `scripts` 的相对位置。

Codex 当前官方文档列出的用户级目录为 `~/.agents/skills`，项目级目录为 `.agents/skills`；可以根据使用范围选择。参见 [OpenAI 官方技能文档](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)。

### Windows

将技能文件夹放在：

```text
%USERPROFILE%\.agents\skills\blender-build-and-render\
```

安装后应存在：

```text
%USERPROFILE%\.agents\skills\blender-build-and-render\SKILL.md
```

### macOS / Linux

对应位置为：

```text
~/.agents/skills/blender-build-and-render/SKILL.md
```

### 仅在某个项目中使用

将技能文件夹放入目标项目：

```text
your-project/
└── .agents/
    └── skills/
        └── blender-build-and-render/
            └── SKILL.md
```

Codex 会发现相应目录中的技能；如安装后未显示，可重新启动 Codex。部分客户端版本使用其他技能目录时，遵循该客户端的目录约定，避免在多个位置重复安装同名技能。发现方式见 [OpenAI 官方说明](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)。

## 使用示例

在 Codex CLI 或 IDE 中，可以用 `$blender-build-and-render` 显式调用；也可以描述与技能范围相符的场景任务。其他客户端使用各自的技能选择方式。参见 [官方调用说明](https://learn.chatgpt.com/docs/build-skills#how-chatgpt-and-codex-use-skills)。

### 从零搭建展厅

```text
使用 $blender-build-and-render，根据参考图片搭建一个现代展厅。
先验证空间比例与展陈布局，再完善材质、自然光和灯光。
交付可编辑的 Blender 工程，以及三个代表性视角的预览图。
```

### 修改现有室内场景

```text
使用 $blender-build-and-render，先检查我提供的 .blend 工程。
保留现有布局，将材质调整为木质与浅色石材，改善日间采光。
另存新版本，检查纹理依赖，并提供修改后的预览图。
```

### 产品演示动画

```text
使用 $blender-build-and-render，为现有产品模型制作装配演示动画。
先检查部件尺寸、运动路径和镜头，再生成完整动画。
保存可编辑工程，并说明实际输出参数和检查结果。
```

### 建筑或自然环境场景

```text
使用 $blender-build-and-render，搭建一个临水建筑与周边自然环境。
按真实比例处理地形、建筑、步道和植被，使用统一日间光照。
先输出关键视角小样，检查后继续完善最终场景与渲染图。
```

## 辅助工具

以下命令在仓库根目录执行。将输入文件、可执行程序和输出路径替换为实际值；若 `blender`、`python` 或 `ffmpeg` 未加入环境变量，使用其完整路径。

### 读取 Blender 场景清单

```sh
blender --background "path/to/scene.blend" --python-exit-code 1 --python "blender-build-and-render/scripts/inspect_scene.py" -- --report "work/scene_inventory.json" --hash-source
```

输出包含活动场景、单位、相机、对象、可见性、材质、外部资源、重复稳定 ID、动画与渲染参数。默认最多输出 200 条对象详情，`--object-limit 0` 可取消此限制。

该工具读取场景数据并写入 JSON 清单，不保存或修改输入 `.blend`。它不替代碰撞检测、模拟求值或画面验收。

### 核验视频与末帧定格

```sh
python "blender-build-and-render/scripts/verify_media.py" --ffmpeg ffmpeg --video "path/to/video.mp4" --expected-width 1920 --expected-height 1080 --expected-fps 24 --expected-frames 120 --freeze "path/to/last_frame.png" --report "work/media_check.json"
```

这里的参数演示一个 1920×1080、24 帧/秒、120 帧的片段，执行时按实际交付要求替换。支持 `30000/1001` 等有理数帧率；`--freeze` 可省略，尺寸、帧率和帧数的预期值也均为可选参数。

脚本检查解码帧、尺寸、帧率与时间戳；提供定格图时，进一步比较它与视频最后一帧的 RGB 像素。退出码 `0` 表示通过，`2` 表示核验失败，具体原因保存在 JSON 的 `issues` 中。

## 已完成的工具验证

- 在实际 Blender 小型工程中识别相机、有效输出尺寸、渲染可见性、缺失素材与重复 ID，并核对输入工程哈希。
- 核验 24 帧/秒短视频的完整解码、均匀时间戳与末帧定格。
- 验证工具能够拒绝错误的预期帧数、不同源帧的定格和损坏视频。
- 验证 `30000/1001` 分数帧率，以及技能内部文件引用与 Python 语法。

这些测试覆盖附带工具的上述功能。实际场景的造型、真实感、空间关系和运动质量仍需针对任务检查。

## 上传到 GitHub

1. 在 GitHub 新建或打开目标仓库。
2. 通过 **Add file → Upload files** 上传本目录中的 `README.md`、两个 Git 配置文件和整个 `blender-build-and-render` 文件夹，保持上面的目录结构。
3. 检查仓库根目录的 README 能正常显示，填写提交说明并提交更改。操作参见 [GitHub 官方文件上传说明](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository)。

实际模型、纹理、项目数据、缓存与渲染结果由具体任务另行组织；本仓库的 `.gitignore` 已列出常见生成物，方便保持技能源码仓库简洁。
