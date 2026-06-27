# Clone 复刻部署 / Clone Setup

本流程面向第一次从 GitHub clone 的用户，目标是让一台 Mac 控制端和一台 Windows 节点复刻完整同步系统。

This flow is for first-time GitHub clone users. The goal is to recreate the full sync system with one Mac controller and one Windows node.

## 1. Mac 端准备 / Prepare the Mac

```sh
git clone https://github.com/RedHong01/SystemSync.git
cd SystemSync
python3 scripts/preflight.py
cp config.example.json config.json
```

编辑 `config.json`，至少填写：

Edit `config.json` and fill at least:

- `local_device_id`：Mac Syncthing device ID。 / Mac Syncthing device ID.
- `remote_device_id`：Windows Syncthing device ID。 / Windows Syncthing device ID.
- `mac_ip`：Mac 局域网 IP。 / Mac LAN IP.
- `remote_ip`：Windows 局域网 IP。 / Windows LAN IP.
- `mac_mac` / `remote_mac`：Wake-on-LAN 用 MAC 地址。 / MAC addresses for Wake-on-LAN.
- `sync_root`：Mac 同步根目录。 / Mac sync root.
- `remote_project_base`：Windows 工程根目录，例如 `D:\LanSyncProjects`。 / Windows project root, such as `D:\LanSyncProjects`.

安装并启动控制台：

Install and start the dashboard:

```sh
./install-mac-service.sh
./mac/install-dock-shortcut.sh
```

打开：

Open:

```text
http://127.0.0.1:8765
```

## 2. Windows 节点准备 / Prepare Windows

在 Mac 上生成 Windows 配置：

Generate the Windows config on the Mac:

```sh
python3 generate_windows_config.py
```

把整个 `windows/` 文件夹复制到 Windows，然后以管理员 PowerShell 运行：

Copy the whole `windows/` folder to Windows, then run in Administrator PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\install-agent.ps1
```

安装后 Windows 会得到：

After installation, Windows gets:

- companion agent on TCP `8766`
- firewall rule
- scheduled task and Startup fallback
- desktop/Start Menu dashboard launcher
- dependency inventory endpoint

## 3. Syncthing 配对 / Pair Syncthing

1. 在两端 Syncthing 中互相添加 device ID。 / Add each device ID in Syncthing on both endpoints.
2. 确认共享文件夹 ID，例如 `lan-sync`。 / Confirm the shared folder ID, such as `lan-sync`.
3. 在控制台 `Pairing` 页面检查已知设备和待确认设备。 / Check known and pending devices on the dashboard `Pairing` page.

## 4. 工程同步 / Project Sync

- 先运行 `命名检查`，发现非法路径后创建安全副本。 / Run `Name Audit` first and create a safe copy when unsafe paths are found.
- 用 `检查依赖` 检测 Adobe、Unity、字体、插件和外部路径。 / Use `Check Dependencies` to detect Adobe, Unity, fonts, plugins, and external paths.
- 用 `新增同步文件夹` 把规范化副本注册到 Mac 和 Windows 目标路径。 / Use `Add Sync Folder` to register the normalized copy to Mac and Windows target paths.

## 5. 验证 / Verify

```sh
python3 scripts/preflight.py
curl -sS http://127.0.0.1:8765/api/overview
curl -sS http://127.0.0.1:8765/api/pairing
```

如果 Windows companion 不在线，Syncthing 仍可能同步，但磁盘、电源、Windows resume 和远端依赖比较会不可用。

If Windows companion is offline, Syncthing may still sync, but disk, power, Windows resume, and remote dependency comparison are unavailable.
