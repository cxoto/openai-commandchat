# PyPI 自动发布快速配置指南

## 🚀 推荐：使用 OIDC（无需 Token）

### 步骤 1：在 PyPI 配置 Trusted Publisher

访问以下网址之一：

**如果 `commandchat` 项目已存在：**

```text
https://pypi.org/manage/project/commandchat/settings/
```

点击 **Add a new publisher**。

**如果是首次发布（项目还不存在）：**

```text
https://pypi.org/manage/account/publishing/
```

点击 **Add a new pending publisher**。

### 步骤 2：填写配置信息

请填写与你实际 GitHub 仓库匹配的值：

```text
PyPI Project Name: commandchat
Owner: <your-github-user-or-org>
Repository name: <your-repository-name>
Workflow name: publish-to-pypi.yml
Environment name: (留空)
```

> `Owner` 和 `Repository name` 必须与真实仓库完全一致。

### 步骤 3：保存

点击 **Add** 保存配置。

### 步骤 4：发布

之后只要：

1. 更新 `README.md`（如果你想同步更新 PyPI 首页内容）
2. 更新 `pyproject.toml` 里的版本号
3. push 到 `master`，或手动触发工作流

就会自动发布到 PyPI。

---

## 📝 为什么 PyPI 首页会更新？

因为包元数据里的 `project.readme` 指向 `README.md`，发布新版本时 PyPI 会重新渲染该文件：

```toml
readme = { file = "README.md", content-type = "text/markdown" }
```

所以你修改 `README.md` 后，只要发布新版本，PyPI 项目页内容就会同步更新。

---

## 🔄 当前工作流会做什么

`publish-to-pypi.yml` 会：

1. 检查版本号是否真的变更
2. 构建 sdist 和 wheel
3. 执行 `twine check dist/*`
4. 使用 OIDC 发布到 PyPI

如果版本未变化，工作流会跳过发布。

---

## 🔑 备选：使用 API Token

如果 OIDC 配置有问题，也可以使用传统 Token 方式：

1. 在 PyPI 创建 API Token：<https://pypi.org/manage/account/token/>
2. 在 GitHub 仓库添加 Secret：
   - `Settings -> Secrets and variables -> Actions`
   - Name: `PYPI_API_TOKEN`
   - Value: 你的 PyPI token
3. 使用 `publish-to-pypi-token.yml.example` 作为替代方案

---

## ✅ 重要提示

- 每次发布前必须更新 `pyproject.toml` 中的版本号
- PyPI 不允许重复上传相同版本
- 建议使用语义化版本号，例如 `0.0.14 -> 0.0.15`
- 建议首次先用 TestPyPI 验证

