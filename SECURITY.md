# 安全 / Security

本项目设计用于可信任的本地局域网。

This project is intended for trusted local networks.

## 不要暴露到公网 / Do Not Expose It to the Public Internet

控制台可以触发本地文件操作、Syncthing 配置变更和 Wake-on-LAN 数据包。请只在可信局域网内运行，或放在你自己控制的 VPN 后面。

The dashboard can trigger local file operations, Syncthing configuration changes, and Wake-on-LAN packets. Run it only on a trusted LAN or behind your own VPN.

## 密钥与私有配置 / Secrets

不要提交：

Do not commit:

- `config.json`
- `runtime-state.json`
- `windows/agent-config.generated.json`
- Syncthing API keys
- shared companion tokens
- browser session cookies created by `/auth`

这些文件默认已被 `.gitignore` 忽略。

These files are ignored by default.

Mac/Windows 的 `SystemSync` 启动器会读取本机配置中的 token，访问控制端的 `/auth` 入口，并让浏览器保存一个 HttpOnly 会话 cookie。这个 cookie 只用于可信局域网内的网页操作授权；不要把带 token 的 URL 截图、转发或公开。

The Mac/Windows `SystemSync` launchers read the local configured token, open the controller through `/auth`, and store an HttpOnly browser session cookie. This cookie only authorizes dashboard actions on a trusted LAN; do not screenshot, forward, or publish token-bearing URLs.

## 报告安全问题 / Reporting Issues

社区版本中，如果发现安全问题，请先私下联系仓库维护者，再创建公开 issue。

For community releases, report security issues privately to the repository maintainer before opening a public issue.
