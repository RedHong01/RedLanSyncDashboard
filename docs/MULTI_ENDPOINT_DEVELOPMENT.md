# 多端开发 / Multi-Endpoint Development

本项目支持在 Windows 和 macOS 上同时开发，但每台机器都应使用自己的 Git checkout。不要把 `.git` 目录放进 Syncthing 同步文件夹，也不要用 Syncthing 直接同步同一个 Git 工作树。

This project supports development from Windows and macOS, but every machine should use its own Git checkout. Do not put the `.git` directory inside a Syncthing shared project folder, and do not use Syncthing to synchronize the same Git working tree.

## 推荐工作流 / Recommended Workflow

1. 在每台电脑上单独 clone GitHub 仓库。
   Clone the GitHub repository separately on each computer.
2. 用 GitHub Desktop、Git CLI 或其他 Git 客户端提交和 push/pull。
   Commit and push/pull with GitHub Desktop, Git CLI, or another Git client.
3. 用 Syncthing 同步大型工程资产和规范化副本，不同步仓库运行时 secret。
   Use Syncthing for large project assets and normalized copies, not runtime secrets.
4. 在开始工作前 pull，在切换电脑前 push。
   Pull before starting work and push before switching machines.

## GitHub Desktop / GitHub Desktop

Windows 上可以直接把本地仓库加入 GitHub Desktop：

On Windows, add the local checkout to GitHub Desktop:

```powershell
& "$env:LOCALAPPDATA\GitHubDesktop\bin\github.bat" open "D:\ArtCenter\RedLanSyncDashboard"
```

也可以在 GitHub Desktop 中选择 `File -> Add local repository`，然后选择仓库路径。

Alternatively, use `File -> Add local repository` in GitHub Desktop and select the checkout path.

## 网页客户端地址 / Web Client URL

网页客户端是同一个 Mac 控制端页面，不会在 Windows companion agent 上另起一个独立控制台。Windows companion installer 会把工具名别名写入 hosts，因此日常入口是：

The web client is the same Mac-hosted dashboard, not a separate dashboard served by the Windows companion agent. The Windows companion installer writes the tool-name alias into hosts, so the daily entry point is:

```text
http://red-lan-sync.local:8765
```

如果别名不可用，Windows 浏览器打开 Pairing 页面显示的 Mac 局域网地址，例如：

If the alias is unavailable, open the Mac LAN URL shown on the Pairing page, for example:

```text
http://192.168.0.243:8765
```

`http://127.0.0.1:8765` 只适用于正在运行控制台的那台电脑；在 Windows 上它会指向 Windows 自己。

`http://127.0.0.1:8765` only works on the computer running the dashboard; on Windows it points back to Windows itself.

Windows 本机 companion 页面仍然在 `http://127.0.0.1:8766`，只负责唤醒、状态和跳转；其中的 `打开网页管理端` 按钮会重定向到当前配置的 dashboard URL。

The Windows local companion page remains at `http://127.0.0.1:8766` for wake, status, and redirect helpers only; its `Open Dashboard` button redirects to the configured dashboard URL.

## 换行和文件类型 / Line Endings and File Types

仓库包含 `.gitattributes` 和 `.editorconfig`：

The repository includes `.gitattributes` and `.editorconfig`:

- Python、JavaScript、HTML、CSS、JSON、Markdown 和 shell 脚本使用 LF。
- Python, JavaScript, HTML, CSS, JSON, Markdown, and shell scripts use LF.
- PowerShell、Batch 和 CMD 脚本使用 CRLF。
- PowerShell, Batch, and CMD scripts use CRLF.
- 设计、视频、音频和工程二进制文件标记为 binary，避免 Git 尝试转换。
- Design, video, audio, and project binaries are marked binary to prevent text conversion.

如果 GitHub Desktop 显示大量“整文件变化”，先检查是不是换行设置造成的，不要直接提交这类噪声变更。

If GitHub Desktop shows many whole-file changes, check line-ending settings before committing noisy diffs.

## 配置与 Secret / Config and Secrets

这些文件是本机运行时文件，不应该提交：

These files are local runtime files and should not be committed:

- `config.json`
- `runtime-state.json`
- `windows/agent-config.generated.json`
- `C:\ProgramData\RedLanSyncAgent\agent-config.json`

`agent-config.generated.json` 包含 companion token，只用于把 Windows agent 安装到某台电脑。

`agent-config.generated.json` contains the companion token and is only used to install the Windows agent on a specific machine.

## Syncthing 文件夹策略 / Syncthing Folder Strategy

`lan-sync` 可以继续作为轻量交换区，但大型工程应该注册为独立 Syncthing 文件夹：

`lan-sync` can remain a lightweight exchange area, but large projects should be registered as independent Syncthing folders:

- Mac: `/Users/<user>/LanSyncProjects/<project>` 或规范化副本路径。
- Mac: `/Users/<user>/LanSyncProjects/<project>` or a normalized-copy path.
- Windows: `D:\LanSyncProjects\<project>` 或用户选择的目标磁盘。
- Windows: `D:\LanSyncProjects\<project>` or another selected target disk.

避免长期把独立工程文件夹嵌套在另一个 Syncthing 文件夹里。迁移时可以临时从 `lan-sync` 读取种子副本，但最终建议把大型项目作为独立文件夹管理。

Avoid keeping independent project folders nested inside another Syncthing folder long-term. During migration, it is fine to seed from `lan-sync`, but large projects should ultimately be managed as independent folders.

## 多端同时编辑 / Concurrent Editing

Syncthing 会同步文件，不会像 Git 那样合并同一个文件的并发编辑。

Syncthing synchronizes files; it does not merge concurrent edits like Git.

- 文档、脚本和配置改动走 Git。
- Use Git for documents, scripts, and config changes.
- 大型工程资产一次尽量只在一台机器上打开和保存。
- Open and save large project assets from one machine at a time when possible.
- 对 After Effects、Logic、PSD 等包式或二进制工程，切换电脑前确认 Syncthing 已完成。
- For After Effects, Logic, PSD, and other package/binary projects, wait for Syncthing to finish before switching machines.
