![BungleCat](https://socialify.git.ci/adk23333/BungleCat/image?description=1&font=Bitter&forks=1&issues=1&language=1&name=1&owner=1&pattern=Signal&pulls=1&stargazers=1&theme=Light)

---

## 部署教程

### 准备环境
1. 安装 Python 3.10+
2. 安装 UV 等支持 pyproject 的包管理工具
3. 一个灵活的大脑

### 快速开始

克隆项目到本地
```shell
git clone https://github.com/adk23333/BungleCat.git
cd BungleCat
```

#### 使用uv
创建虚拟环境
```shell
uv venv
```

安装依赖
```shell
uv pip sync
```

运行程序
```shell
source .venv/bin/activate
python server.py
```
