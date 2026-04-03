# GitHub Actions 配置说明

## PyPI 自动发布配置

### 配置方式说明

本项目使用 **OpenID Connect (OIDC) Trusted Publishers** 方式发布到 PyPI，这是最安全的方式，**无需配置 API Token**！

### ✅ 方式一：OIDC Trusted Publishers（推荐）

这是更安全的现代化方式，不需要管理长期 token。

#### 配置步骤：

1. **登录到 [PyPI](https://pypi.org/)**

2. **如果项目已存在**：
   - 进入项目页面：`https://pypi.org/manage/project/commandchat/settings/`
   - 找到 "Publishing" 部分
   - 点击 "Add a new publisher"

3. **如果项目不存在**（首次发布）：
   - 访问：https://pypi.org/manage/account/publishing/
   - 点击 "Add a new pending publisher"

4. **填写 Trusted Publisher 信息**：
   ```
   PyPI Project Name: commandchat
   Owner: xoto (你的 GitHub 用户名或组织名)
   Repository name: commandchat (你的仓库名)
   Workflow name: publish-to-pypi.yml
   Environment name: (留空)
   ```

5. **保存配置**

✅ 完成！现在无需任何 token，GitHub Actions 会通过 OIDC 自动验证并发布。

### 🔑 方式二：API Token（备选）

如果你更倾向使用传统的 API Token 方式：

#### 1. 获取 PyPI API Token

1. 登录到 [PyPI](https://pypi.org/)
2. 进入账户设置 -> API tokens
3. 创建一个新的 API token
   - Token 名称：例如 "GitHub Actions - commandchat"
   - Scope: 选择 "Entire account" 或者只针对 "commandchat" 项目
4. 复制生成的 token（格式类似：`pypi-...`）

#### 2. 在 GitHub 仓库中配置 Secret

1. 打开 GitHub 仓库页面
2. 进入 Settings -> Secrets and variables -> Actions
3. 点击 "New repository secret"
4. 添加以下 secret：
   - Name: `PYPI_API_TOKEN`
   - Value: 粘贴你在 PyPI 获取的 API token

#### 3. 修改 workflow 文件

将 `.github/workflows/publish-to-pypi.yml` 中的发布步骤改为：

```yaml
- name: Publish to PyPI using Token
  env:
    TWINE_USERNAME: __token__
    TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
  run: |
    pip install twine
    twine upload dist/*
```

并移除 `permissions` 部分。

### 工作流程说明

`publish-to-pypi.yml` 工作流会在以下情况下触发：

- 直接 push 到 master 分支
- Pull Request merge 到 master 分支

工作流会执行以下步骤：

1. 检出代码
2. 设置 Python 环境（Python 3.11）
3. 安装构建依赖（build）
4. 构建包（wheel 和 source distribution）
5. 通过 OIDC 自动验证身份并上传到 PyPI

### 注意事项

1. **版本号管理**: 每次发布前请确保更新 `pyproject.toml` 中的版本号，PyPI 不允许重复上传相同版本
2. **首次发布**: 如果这是项目的首次发布，请先在 PyPI 手动创建项目或使用 TestPyPI 测试
3. **测试环境**: 建议先使用 [TestPyPI](https://test.pypi.org/) 进行测试

### 使用 TestPyPI 测试（可选）

如果想先在测试环境验证，可以：

1. 在 TestPyPI 创建账户并获取 token
2. 在 GitHub 添加 `TEST_PYPI_API_TOKEN` secret
3. 创建一个单独的测试工作流或修改现有工作流

### 手动发布（备选方案）

如果需要手动发布，可以执行：

```bash
# 安装构建工具
pip install build twine

# 构建包
python -m build

# 检查构建
twine check dist/*

# 上传到 PyPI
twine upload dist/*
```

