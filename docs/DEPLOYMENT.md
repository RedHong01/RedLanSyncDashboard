# 部署 / Deployment

## Mac 控制端 / Mac Controller

1. 安装并启动 Syncthing。 / Install and start Syncthing.
2. 复制 `config.example.json` 为 `config.json`。 / Copy `config.example.json` to `config.json`.
3. 填写本机和远端设备 ID、局域网 IP、MAC 地址和同步根目录。 / Fill in the local and remote device IDs, LAN IPs, MAC addresses, and sync roots.
4. 启动控制台。 / Start the dashboard:

```sh
python3 server.py
```

5. 安装为登录后自动启动服务。 / Install it as a login service:

```sh
./install-mac-service.sh
```

重复运行安装脚本会更新服务代码，但会保留安装目录中的 `config.json` 和 `runtime-state.json`。

Running the installer again updates the service code while preserving `config.json` and `runtime-state.json` in the installed directory.

6. 可选 Dock 快捷方式。脚本会生成 macOS `.icns` 图标并刷新 Dock；如果网页中已上传 PNG/JPG 自定义图标，脚本会优先使用它。 / Optional Dock shortcut. The script generates the macOS `.icns` icon and refreshes the Dock; if a PNG/JPG custom icon was uploaded from the web UI, the script uses it first:

```sh
./mac/install-dock-shortcut.sh
```

也可以在网页控制台的 `Pairing` 页面点击 `安装/刷新 Dock 快捷方式`。

You can also click `Install/Refresh Dock Shortcut` on the dashboard `Pairing` page.

## 网页访问地址 / Web Dashboard URL

控制台网页由 Mac 控制端提供。Mac 本机可以打开 `http://127.0.0.1:8765`。Windows companion installer 会安装 `OpenDashboard.ps1` 智能启动器，并创建桌面/开始菜单入口；启动器会依次测试 `red-lan-sync.local`、Mac 局域网 IP 和配置里的 fallback，找到可用地址后用 companion token 建立浏览器会话。

The dashboard is served by the Mac controller. The Mac itself can open `http://127.0.0.1:8765`. The Windows companion installer installs the `OpenDashboard.ps1` smart launcher and creates desktop/Start Menu entries; the launcher tests `red-lan-sync.local`, the Mac LAN IP, and configured fallbacks, then opens the reachable dashboard with the companion token.

如果 hosts 别名不可用，启动器会自动退回 Pairing 页面列出的 Mac 局域网地址，例如 `http://192.168.0.243:8765`。不要在 Windows 上使用 `http://127.0.0.1:8765`，因为它指向 Windows 自己。

If the hosts alias is unavailable, the launcher automatically falls back to the Mac LAN URL listed on the Pairing page, such as `http://192.168.0.243:8765`. Do not use `http://127.0.0.1:8765` on Windows because it points back to Windows itself.

如果 Windows 无法打开，请检查：

If Windows cannot open it, check:

- Mac 控制端正在运行，并且 `listen_host` 是 `0.0.0.0` 或 Mac 的局域网 IP。
- The Mac controller is running and `listen_host` is `0.0.0.0` or the Mac LAN IP.
- Mac 防火墙允许 TCP 8765 入站。
- The Mac firewall allows inbound TCP 8765.
- Windows 与 Mac 在同一个局域网内。
- Windows and Mac are on the same LAN.
- `C:\Windows\System32\drivers\etc\hosts` 中存在 `red-lan-sync.local` 到 Mac IP 的映射；如果 Mac IP 变化，重新运行 `python3 generate_windows_config.py` 并重跑 Windows installer。
- `C:\Windows\System32\drivers\etc\hosts` contains the `red-lan-sync.local` to Mac IP mapping; if the Mac IP changes, rerun `python3 generate_windows_config.py` and then rerun the Windows installer.

## Windows 节点 / Windows Node

1. 安装 Syncthing，并确认本地 GUI 可以打开。 / Install Syncthing and confirm the local GUI works.
2. 在 Mac 上运行。 / Run this on the Mac:

```sh
python3 generate_windows_config.py
```

3. 把 `windows` 文件夹复制到 Windows 机器。 / Copy the `windows` folder to the Windows machine.
4. 在该文件夹内打开管理员 PowerShell。 / Open Administrator PowerShell in that folder:

```powershell
powershell -ExecutionPolicy Bypass -File .\install-agent.ps1
```

5. 确认 Windows 防火墙允许 TCP 8766 和 Syncthing 端口。 / Confirm Windows firewall allows TCP 8766 and Syncthing ports.

安装脚本会创建两个入口：`Red LAN Sync Dashboard.lnk` 运行智能启动器并打开可操作的 Mac 控制台，`Wake RedM3Max.url` 打开本机 companion 页面；本机 companion 页面也提供一个跳转按钮，可根据当前配置打开网页管理端。

The installer creates two entries: `Red LAN Sync Dashboard.lnk` runs the smart launcher and opens the authenticated Mac dashboard, and `Wake RedM3Max.url` opens the local companion page; that local page also includes a button that redirects to the configured dashboard.

## 旧同步续传到 D 盘 / Resume Old Sync on the D Drive

如果旧 `lan-sync` 因 Windows 非法文件名卡住，请先在 Mac 控制台创建规范化副本，然后在 Windows 上用 `windows/seed-normalized-project.ps1` 把已有副本种到 `D:\LanSyncProjects`，再注册为独立 Syncthing 文件夹。

If the old `lan-sync` folder is stalled by Windows-invalid filenames, first create a normalized copy from the Mac dashboard, then use `windows/seed-normalized-project.ps1` on Windows to seed the existing copy into `D:\LanSyncProjects` and register it as an independent Syncthing folder.

完整流程见 / Full workflow: [Windows D 盘迁移与续传 / Windows D-drive migration and resume](WINDOWS_D_DRIVE_MIGRATION.md)。

命名检查页提供单独的源路径改名确认按钮，可在预览清单后把 Mac 源工程内部文件名同步为规范名。

The naming page provides a separate confirmed source-rename action, allowing the Mac source project internals to be aligned to safe names after reviewing the list.

## 工程依赖检查 / Project Dependency Check

在 `Naming` 页面填入源工程路径后，可以点击 `检查依赖` 查看 Adobe 文件、字体、插件和外部路径线索。点击 `打包依赖清单` 会在工程内创建 `_DependencyBundle`，其中包含 `dependency_manifest.json`、说明文件和可同步的项目本地字体/Adobe 辅助资产。

After entering a source project path on the `Naming` page, click `Check Dependencies` to review Adobe files, fonts, plugins, and external path signals. Clicking `Bundle Dependency Manifest` creates `_DependencyBundle` inside the project with `dependency_manifest.json`, a README, and syncable project-local fonts/Adobe helper assets.

Windows 独立检查脚本：

Standalone Windows check script:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\windows\check-dependencies.ps1
```

## 目标磁盘选择 / Storage Target Selection

在控制台打开 `Storage`：

In the dashboard, open `Storage`:

- 保存默认 Windows 工程根目录，例如 `D:\LanSyncProjects`。
- Save the default Windows project root, such as `D:\LanSyncProjects`.
- 如果希望大型工程落在指定磁盘上，把每个大型工程注册为单独 Syncthing 文件夹。
- Register each large project as its own Syncthing folder when you want it on a specific disk.
- 使用绝对 Windows 路径。Companion agent 会拒绝相对路径。
- Use absolute Windows paths. Relative paths are rejected by the companion agent.

## 局域网唤醒 / Wake-on-LAN

Wake-on-LAN 需要：

Wake-on-LAN requires:

- BIOS/UEFI 支持唤醒。
- BIOS/UEFI wake support.
- Windows 网卡开启 magic packet 唤醒。
- Windows network adapter magic packet support.
- 至少一台在线设备发送唤醒包。
- One online device to send the wake packet.
- 路由器允许局域网广播流量。
- LAN broadcast traffic allowed by the router.

如果远端电脑完全断电，且网卡没有保持可唤醒状态，软件无法唤醒它。

If the remote computer is fully powered off and the adapter does not stay armed, software cannot wake it.
