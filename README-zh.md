[English](README.md) | [中文](README-zh.md)

# CommandChat

`commandchat` 提供了 `occ` 命令行工具，用来在终端里和 OpenAI 或 Azure OpenAI 模型交互。

## 功能特性

- 使用 `occ chat` 进行终端聊天
- 通过 profile 管理多个 OpenAI / Azure OpenAI 配置
- 内置 Prompt 模板，也支持自定义 Prompt
- 可以为单次命令指定 Prompt，也可以给 profile 设置默认 Prompt
- 提供实验性的图片生成命令

## 环境要求

- Python 3.8 及以上
- 已安装 `pip`
- 可用的 OpenAI API Key 或 Azure OpenAI 配置

## 安装

```bash
pip3 install commandchat
```

如果你本地有多个 Python 版本，也可以这样安装：

```bash
python3 -m pip install commandchat
```

## 快速开始

### 1. 先完成配置

```bash
occ configure
```

该命令会进入交互式配置流程，并把本地配置写入 `~/.occ/`。

### 2. 开始聊天

```bash
occ chat "你好，请简单介绍一下你自己。"
```

也可以直接进入交互式多行输入模式：

```bash
occ chat
```

在交互式聊天里，可以使用这些快捷命令：

- `/`：打开快捷命令菜单
- `/pmp`、`/p` 或 `/prompt`：列出并切换当前会话使用的 Prompt
- `/m` 或 `/model`：列出并切换当前会话使用的模型
- `/q`：退出当前聊天
- `/help`：再次显示帮助信息

使用 `/pmp` 切换 Prompt 或 `/m` 切换模型时，CLI 都会询问你是保留当前上下文，还是直接开启一个新的聊天上下文（新的 session id）。

交互式聊天底部会显示当前的 prompt、model 和 session id 状态栏。

### 3. 使用 Prompt 模板

```bash
occ prompt list
occ chat -pt translate "你好世界"
occ chat -pt improve "I wants to go to school yesterday"
```

### 4. 使用多个 profile

```bash
occ configure profile -p work
occ configure list
occ chat -p work "帮我总结一下今天的待办事项"
```

## 常用命令

| 命令 | 说明 |
| --- | --- |
| `occ configure` | 打开交互式配置菜单 |
| `occ configure profile -p <name>` | 创建或更新某个 profile |
| `occ configure list` | 查看已配置的 profile |
| `occ configure delete <name>` | 删除某个 profile |
| `occ chat "message"` | 单次发送消息 |
| `occ chat` | 进入交互式聊天 |
| `occ chat -p <profile> -m <model> "message"` | 指定 profile / model 聊天 |
| `occ chat -pt <prompt_key> "message"` | 使用指定 Prompt 模板聊天 |
| `occ chat` + `/` | 打开交互式快捷命令菜单 |
| `occ chat` + `/pmp` / `/p` / `/prompt` | 在交互式聊天中切换 Prompt |
| `occ chat` + `/m` / `/model` | 在交互式聊天中切换模型 |
| `occ prompt list` | 查看 Prompt 模板列表 |
| `occ prompt show <key>` | 查看 Prompt 详情 |
| `occ prompt add <key> -n <name> -d <desc> -s <prompt>` | 添加自定义 Prompt |
| `occ image -desc "..." -size m` | 生成图片 |

## 本地生成的文件

- `~/.occ/config`：profile 和模型配置
- `~/.occ/prompts.json`：自定义 Prompt 模板

## 打包与 PyPI 说明

项目现在以 `pyproject.toml` 作为唯一的打包元数据来源。

- `README.md` 被配置为 `project.readme`，因此 PyPI 项目页会渲染它作为首页内容。
- `README-zh.md` 继续保留在 GitHub 仓库中，作为中文文档。
- 如果你想更新 PyPI 首页内容，需要修改 `README.md`，并在 `pyproject.toml` 中升级版本号后重新发布。

### GitHub Actions 自动发布

仓库中已经包含 `.github/workflows/publish-to-pypi.yml`。

当代码 push 到 `master`，或手动触发工作流时，它会：

1. 检查 `pyproject.toml` 中的版本号是否变化
2. 基于 `pyproject.toml` 构建 sdist 和 wheel
3. 执行 `twine check dist/*`
4. 通过 PyPI Trusted Publishing（OIDC）发布到 PyPI

由于包元数据已经指向 `README.md`，每次发布新版本时，PyPI 首页描述也会一并更新。

> 注意：PyPI 只能展示一个长描述文件，所以首页内容会使用 `README.md`，不会同时展示 `README-zh.md`。

## 手动构建

```bash
python3 -m pip install build twine
python3 -m build
python3 -m twine check dist/*
```

## 卸载

```bash
pip3 uninstall commandchat
```

## 反馈或问题

- `xxx.tao.c@gmail.com`
- `xoto@outlook.be`

## License

MIT
