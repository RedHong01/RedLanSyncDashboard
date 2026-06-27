# Clone 复刻部署 / Clone Setup

本流程面向第一次从 GitHub clone 的用户，目标是让一台 Mac 控制端和一台 Windows 节点复刻完整同步系统。

This flow is for first-time GitHub clone users. The goal is to recreate the full sync system with one Mac controller and one Windows node.

## 1. Mac 端准备 / Prepare the Mac

```sh
git clone https://github.com/RedHong01/SystemSync.git
cd SystemSync
./setup.sh
```

`setup.sh` 会在缺少 `config.json` 时从 `config.example.json` 创建一份配置，并安装/刷新 Mac 后台服务、Dock 图形入口和 Windows 配对工具包。

`setup.sh` creates `config.json` from `config.example.json` when needed, then installs/refreshes the Mac background service, Dock launcher, and Windows pairing package.

编辑或确认 `config.json`，至少填写：

Edit or confirm `config.json` and fill at least:

- `local_device_id`：Mac Syncthing device ID。 / Mac Syncthing device ID.
- `remote_device_id`：Windows Syncthing device ID。 / Windows Syncthing device ID.
- `mac_ip`：Mac 局域网 IP。 / Mac LAN IP.
- `remote_ip`：Windows 局域网 IP。 / Windows LAN IP.
- `mac_mac` / `remote_mac`：Wake-on-LAN 用 MAC 地址。 / MAC addresses for Wake-on-LAN.
- `sync_root`：Mac 同步根目录。 / Mac sync root.
- `remote_project_base`：Windows 工程根目录，例如 `D:\LanSyncProjects`。 / Windows project root, such as `D:\LanSyncProjects`.

再次运行一键安装，确保配置进入后台服务：

Run one-click setup again so the filled config is installed into the background service:

```sh
./setup.sh
```

打开方式：

Open:

```text
http://127.0.0.1:8765
```

Mac 重启后，Dock 里的 `SystemSync` 会继续作为一键图形入口。

After Mac restart, the Dock `SystemSync` app remains the one-click graphical entry.

## 2. Windows 节点准备 / Prepare Windows

`./setup.sh` 会自动在 Mac 上生成 Windows 配置。手动兜底命令是：

`./setup.sh` automatically generates the Windows config on the Mac. The manual fallback command is:

```sh
python3 generate_windows_config.py
```

如果 `sync_root` 已配置并存在，`./setup.sh` 会自动把整个 `windows/` 工具包复制到 `<sync_root>/_tools/SystemSyncWindows`。也可以手动把整个 `windows/` 文件夹复制到 Windows。然后在 Windows 上运行：

If `sync_root` is configured and exists, `./setup.sh` automatically copies the whole `windows/` package to `<sync_root>/_tools/SystemSyncWindows`. You can also copy the whole `windows/` folder to Windows manually. Then run on Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

`setup.ps1` 会在需要时请求管理员权限。安装后，Windows 桌面和开始菜单都会有 `SystemSync` 图形入口；重启后继续可用。

`setup.ps1` requests administrator permission when needed. After installation, Windows gets a `SystemSync` graphical entry on the desktop and Start Menu; it remains available after restart.

安装后 Windows 会得到：

After installation, Windows gets:

- `OpenSystemSyncDashboard.generated.url` 直接控制台兜底入口 / direct dashboard fallback
- companion agent on TCP `8766`
- firewall rule
- scheduled task and Startup fallback
- desktop/Start Menu dashboard launcher
- dependency inventory endpoint

## 3. Syncthing 配对 / Pair Syncthing

1. 在两端 Syncthing 中互相添加 device ID。 / Add each device ID in Syncthing on both endpoints.
2. 确认共享文件夹 ID，例如 `lan-sync`。 / Confirm the shared folder ID, such as `lan-sync`.
3. 在控制台 `Pairing` 页面检查已知设备和待确认设备。 / Check known and pending devices on the dashboard `Pairing` page.

## 4. 移动设备 / Mobile Devices

- iPhone/iPad：用 Safari 打开 Pairing 页面列出的 Mac 局域网控制台 URL，可监控、唤醒、继续同步和配对设备；可添加到主屏幕作为图形入口。 / iPhone/iPad: open the Mac LAN dashboard URL shown on the Pairing page in Safari to monitor, wake, resume sync, and pair devices; add it to the Home Screen for a graphical entry.
- Android：可以用浏览器打开同一控制台；如果需要作为同步节点，安装 Syncthing 兼容客户端，复制 Android 设备 ID，并在控制台 `Pairing` 页面添加。 / Android: open the same dashboard in a browser; to join as a sync node, install a Syncthing-compatible client, copy the Android device ID, and add it on the dashboard `Pairing` page.
- iOS/iPadOS 不作为默认常驻文件同步节点处理。 / iOS/iPadOS is not treated as a default always-on file sync node.
- HTTPS 或 localhost 部署会启用移动控制台壳缓存；普通局域网 HTTP 是实时浏览器入口，不承诺离线缓存。 / HTTPS or localhost deployments enable the mobile controller shell cache; plain LAN HTTP is a live browser entry and does not promise offline caching.

## 5. 工程同步 / Project Sync

- 先运行 `命名检查`，发现非法路径后创建安全副本。 / Run `Name Audit` first and create a safe copy when unsafe paths are found.
- 用 `检查依赖` 检测 Adobe、Unity、字体、插件和外部路径。 / Use `Check Dependencies` to detect Adobe, Unity, fonts, plugins, and external paths.
- 用 `新增同步文件夹` 把规范化副本注册到 Mac 和 Windows 目标路径。 / Use `Add Sync Folder` to register the normalized copy to Mac and Windows target paths.
- 在 `Overview` 的同步诊断面板查看当前项目、卡住项目、无进度时间、相关路径和建议动作。 / Use the sync diagnosis panel on `Overview` to inspect the current project, blocked project, no-progress time, related paths, and suggested actions.

## 6. 验证 / Verify

```sh
python3 scripts/preflight.py
curl -sS http://127.0.0.1:8765/api/overview
curl -sS http://127.0.0.1:8765/api/pairing
```

如果 Windows companion 不在线，Syncthing 仍可能同步，但磁盘、电源、Windows resume 和远端依赖比较会不可用。

If Windows companion is offline, Syncthing may still sync, but disk, power, Windows resume, and remote dependency comparison are unavailable.
