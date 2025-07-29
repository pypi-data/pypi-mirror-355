## 快速开始使用 MCP 客户端

1. 从[元器智能体平台](https://yuanqi.tencent.com/)获取你需要插件的 API 密钥。
2. 安装`uv`（Python包管理器），使用`curl -LsSf https://astral.sh/uv/install.sh | sh`安装或查看`uv` [仓库](https://github.com/astral-sh/uv)获取其他安装方法。
3. **重要提示: 每个元器插件的ID和密钥都不相同**，两者需要匹配，否则会有 `token验证失败` 的错误

### Claude Desktop

前往`Claude > Settings > Developer > Edit Config > claude_desktop_config.json`包含以下内容：

```
{
  "mcpServers": {
    "hunyuanTCTravel": {
      "command": "uvx",
      "args": [
        "hunyuan-mcp-tc-travel"
      ],
      "env": {
        "API_KEY": "填写你调用的插件Token"
      }
    }
  }
}
```

⚠️ 注意：API_KEY需要与插件匹配。如果出现“token验证失败”错误，请检查您的API_KEY和插件。
如果你使用Windows，你需要在Claude Desktop中启用"开发者模式"才能使用MCP服务器。点击左上角汉堡菜单中的"Help"，然后选择"Enable Developer Mode"。

### Cursor

前往`Cursor -> Preferences -> Cursor Settings -> MCP -> Add new global MCP Server`添加上述配置。


## Transport

我们仅支持 stdio 传输方式
