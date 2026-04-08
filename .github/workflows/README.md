# GitHub Actions 配置说明

## PyPI 自动发布

仓库里的 `.github/workflows/publish-to-pypi.yml` 使用 **PyPI Trusted Publishing（OIDC）** 发布，无需长期保存 API Token。

## PyPI 首页内容从哪里来？

PyPI 项目页的长描述来自 `pyproject.toml` 里的 `project.readme` 配置。

当前配置指向：

```toml
readme = { file = "README.md", content-type = "text/markdown" }
```

所以：

- 修改 `README.md`
- 升级 `pyproject.toml` 中的版本号
- 触发一次新的 PyPI 发布

就会同步更新 PyPI 首页内容。

## 工作流触发方式

- push 到 `master`
- 手动触发 `workflow_dispatch`

## 工作流会执行什么

1. 检出代码
2. 设置 Python 3.11
3. 对比 `pyproject.toml` 版本和 PyPI 当前版本
4. 若版本有变化，则安装构建依赖
5. 构建 sdist 和 wheel
6. 执行 `twine check dist/*`
7. 通过 OIDC 发布到 PyPI

如果版本未变化，工作流会正常结束，但跳过发布。

## OIDC Trusted Publisher 配置

在 PyPI 中添加 Trusted Publisher 时，请填写与你当前 GitHub 仓库完全一致的信息：

```text
PyPI Project Name: commandchat
Owner: <your-github-user-or-org>
Repository name: <your-repository-name>
Workflow name: publish-to-pypi.yml
Environment name: (leave empty)
```

> `Owner` 和 `Repository name` 必须以你的实际仓库为准，不要直接照抄示例值。

## 首次发布 / 常见注意事项

1. 每次发布前必须升级 `pyproject.toml` 中的 `project.version`
2. PyPI 不允许重复上传同一版本
3. 首次接入时建议先用 TestPyPI 验证流程

## 手动构建检查

```bash
python3 -m pip install build twine
python3 -m build
python3 -m twine check dist/*
```

## Token 方案（备选）

如果你不想使用 OIDC，可以参考 `publish-to-pypi-token.yml.example` 改成 Token 发布模式。

