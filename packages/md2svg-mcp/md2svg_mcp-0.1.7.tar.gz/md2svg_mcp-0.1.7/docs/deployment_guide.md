# 操作手册：用 FastMCP 打包 Markdown 转 SVG 项目并发布到 PyPI 和 mcp.so

---

## 一、准备项目环境


### 1.1 安装依赖

* 安装 Python 3.11+（建议使用虚拟环境）
* 安装 `fastmcp` 和 `uv` 工具（假设你已有）

```bash
pip install fastmcp uv
```

## 二、使用 `uv` 构建项目包

`uv` 是 FastMCP 团队的一个工具，用于快速打包和发布 Python 项目。

### 2.1 项目配置

初始化项目：

```bash
uv init
```

确保 `pyproject.toml` 文件存在且配置正确

### 2.2 运行构建命令

在项目根目录执行：

```bash
uv build
```

这会自动：

* 读取 `pyproject.toml`
* 构建 `.tar.gz` 和 `.whl` 安装包

构建成功后会生成 `dist/` 目录，里面有打包好的文件。


## 三、发布到 PyPI

### 3.1 准备 PyPI 账号

* 注册一个 PyPI 账号 [https://pypi.org/account/register/](https://pypi.org/account/register/)
* 创建 API Token（推荐）

### 3.2 上传包


```bash
uv publish --token xxx
```

上传成功后，包就能被 `pip install md2svg-mcp` 安装了。并且可以使用`uvx md2svg-mcp`来运行你的工具。


## 四、发布到 MCP.SO（FastMCP 平台）

### 4.1 账号注册与登录

* 注册并登录 [https://mcp.so/](https://mcp.so/) 
* 点击 Submit，填写信息，发布


