![BungleCat](https://socialify.git.ci/adk23333/BungleCat/image?description=1&font=Bitter&forks=1&issues=1&language=1&name=1&owner=1&pattern=Signal&pulls=1&stargazers=1&theme=Light)

---
# 开发目的
[aiotieba](https://github.com/lumina37/aiotieba)是一个非常方便的用于调用贴吧接口的python包，同时[koishi](https://koishi.chat/zh-CN/)是一个非常优秀的多平台bot开发框架，本项目用于帮助尝试将二者结合。

同时其它语言的开发者也可通过 HTTP 或 WebSocket 调用本库，以实现更便捷的贴吧操作。

# 部署教程

## 准备环境
1. 安装 Python 3.10+
2. 安装 UV 等支持 pyproject 的包管理工具
3. 一个灵活的大脑

## 快速开始

克隆项目到本地
```shell
git clone https://github.com/adk23333/BungleCat.git
cd BungleCat
```

### 使用uv
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
uv run server.py
```

# 配置文件
```toml
# config.toml
bduss = "your bduss"
fnames=["心灵鸡汤"]
http_callback_url = ["http://127.0.0.1:3000/callback"]
reverse_ws_url = ["http://example.com/ws", "ws://example.com"]
```

# Feature
- [X] HTTP 接口
- [X] HTTP 回调接口
- [X] WebSocket 接口
- [X] 反向 WebSocket 接口
- [X] 支持 aiotieba 所有接口
- [ ] 实现自己的 api
- [ ] 切换账号

# 鸣谢
本项目依赖以下开源项目：
* [aiotieba](https://github.com/lumina37/aiotieba)

参考项目：
* [NoneBot](https://github.com/nonebot/nonebot2) 提供了HTTP和WS接口的实现思路

感谢以下产品对 BungleCat 项目提供的支持：
<p align="center">
  <a href="https://github.com/">
      <img src="https://avatars.githubusercontent.com/u/9919?s=200&v=4" height="80" alt="GitHub">
  </a>&nbsp;&nbsp;&nbsp;&nbsp;
  <a href="https://www.jetbrains.com/">
    <img src="https://resources.jetbrains.com/storage/products/company/brand/logos/jb_beam.svg" height="80" alt="JetBrains" >
  </a>
</p>

感谢以下开发者对 BungleCat 作出的贡献：

<a href="https://github.com/adk23333/BungleCat/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=adk23333/BungleCat&max=1000" alt="contributors" />
</a>

# License
请看 [LICENSE](./LICENSE)

# 免责声明
本项目仅供学习交流使用，请勿用于非法用途。请勿以本项目进行违反百度贴吧用户协议的行为，或向任何第三方提供任何形式的相关服务。由以上行为导致的所有损失，本项目不承担任何责任。
