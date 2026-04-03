# PyPI 自动发布快速配置指南

## 🚀 推荐：使用 OIDC（无需 Token）

### 步骤 1：在 PyPI 配置 Trusted Publisher

访问以下网址之一：

**如果 commandchat 项目已存在：**
```
https://pypi.org/manage/project/commandchat/settings/
```
点击 "Add a new publisher"

**如果是首次发布（项目不存在）：**
```
https://pypi.org/manage/account/publishing/
```
点击 "Add a new pending publisher"

### 步骤 2：填写配置信息

```
PyPI Project Name: commandchat
Owner: xoto
Repository name: commandchat
Workflow name: publish-to-pypi.yml
Environment name: (留空)
```

### 步骤 3：保存

点击 "Add" 保存配置。

### 步骤 4：发布

现在只需要将代码 merge 到 master 分支，就会自动发布到 PyPI！

---

## 🔑 备选：使用 API Token

如果 OIDC 配置有问题，可以使用传统的 Token 方式：

1. 在 PyPI 创建 API Token: https://pypi.org/manage/account/token/
2. 在 GitHub 仓库添加 Secret:
   - Settings -> Secrets and variables -> Actions
   - Name: `PYPI_API_TOKEN`
   - Value: 你的 PyPI token
3. 使用 `publish-to-pypi-token.yml.example` 替代当前的 workflow

---

## 📝 重要提示

- ⚠️ 每次发布前必须更新 `pyproject.toml` 中的版本号
- ⚠️ PyPI 不允许重复上传相同版本
- ✅ 建议使用语义化版本号（如 0.0.13 -> 0.0.14）

---

## 🔍 优势对比

| 特性 | OIDC | API Token |
|------|------|-----------|
| 安全性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 配置复杂度 | 简单 | 简单 |
| Token 管理 | 无需管理 | 需要定期轮换 |
| 泄露风险 | 无 | 有 |
| PyPI 推荐 | ✅ | - |

推荐使用 OIDC 方式！

