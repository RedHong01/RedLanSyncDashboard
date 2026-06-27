# Windows D 盘落地与续传 / Windows D-Drive Migration and Resume

这份流程用于把旧 `lan-sync` 中已经生成的规范化副本迁移到 Windows 的 D 盘，并在新控制台架构里注册为独立 Syncthing 文件夹。

Use this workflow to move an already generated normalized copy from the old `lan-sync` area to the Windows D drive, then register it as an independent Syncthing folder in the new dashboard architecture.

## 适用场景 / When To Use This

- 旧同步在 Windows 上因为非法文件名停住。
- The old sync stalled on Windows because of invalid filenames.
- Mac 已经创建了类似 `Motion_1_cross_platform` 的规范化副本。
- The Mac has created a normalized copy such as `Motion_1_cross_platform`.
- Windows 需要把大型工程落到 `D:\LanSyncProjects`，而不是 C 盘用户目录。
- Windows should store large projects under `D:\LanSyncProjects` instead of the C-drive user profile.

## 先安装 Windows Companion / Install the Windows Companion First

在 Mac 控制端生成 Windows 配置：

Generate the Windows config on the Mac controller:

```sh
python3 generate_windows_config.py
```

把 `windows` 文件夹复制到 Windows 后，以管理员 PowerShell 运行：

Copy the `windows` folder to Windows, then run from Administrator PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\install-agent.ps1
```

安装器会：

The installer will:

- 安装 companion agent 到 `C:\ProgramData\SystemSyncAgent`。
- Install the companion agent to `C:\ProgramData\SystemSyncAgent`.
- 开放 TCP 8766 防火墙规则。
- Open the TCP 8766 firewall rule.
- 创建登录启动计划任务。
- Create a logon scheduled task.
- 创建当前用户 Startup 兜底启动项。
- Create a current-user Startup fallback launcher.

## 用旧副本做种子 / Seed from the Existing Copy

如果旧同步目录中已有规范化副本，例如：

If the old sync directory already contains a normalized copy, for example:

```text
C:\Users\Red15\Sync\Motion_1_cross_platform
```

可以先把它复制到 D 盘，避免重新下载完整工程：

Seed it to the D drive first to avoid downloading the whole project again:

```powershell
.\windows\seed-normalized-project.ps1 `
  -Source "C:\Users\Red15\Sync\Motion_1_cross_platform" `
  -Destination "D:\LanSyncProjects\Motion_1_cross_platform"
```

脚本使用 `robocopy`，成功码 `0` 到 `7` 都视为成功。

The script uses `robocopy`; exit codes `0` through `7` are treated as success.

## 自动注册到控制台 / Register Through the Dashboard

如果你有 companion token，可以让脚本复制完成后自动调用 Mac 控制台注册：

If you have the companion token, the script can register the project through the Mac dashboard after seeding:

```powershell
$token = (Get-Content "C:\ProgramData\SystemSyncAgent\agent-config.json" -Raw | ConvertFrom-Json).Token

.\windows\seed-normalized-project.ps1 `
  -Source "C:\Users\Red15\Sync\Motion_1_cross_platform" `
  -Destination "D:\LanSyncProjects\Motion_1_cross_platform" `
  -DashboardUrl "http://192.168.0.243:8765" `
  -Token $token `
  -MacProjectPath "/Users/redwang/Sync/Motion_1_cross_platform" `
  -FolderId "motion-1-cross-platform" `
  -Label "Motion 1 Cross Platform" `
  -RemotePath "D:\LanSyncProjects\Motion_1_cross_platform"
```

注册成功后，Windows Syncthing 中会出现新的文件夹：

After registration, Windows Syncthing will show a new folder:

```text
motion-1-cross-platform -> D:\LanSyncProjects\Motion_1_cross_platform
```


## 同步源路径命名 / Align Source Path Names

如果 Windows 端已经使用规范化副本继续开发，而 Mac 源工程仍保留旧的非法或不一致命名，可以在控制台 `Naming` 页面执行单独确认流程：

If Windows continues from the normalized copy but the Mac source project still has old unsafe or mismatched names, use the separate confirmed flow on the dashboard `Naming` page:

1. 填入 Mac 源工程路径和规范化副本路径，点击 `扫描命名`。
   Enter the Mac source project path and normalized copy path, then click `Scan Names`.
2. 点击 `列出源路径改名`，检查每一条 `原路径 -> 规范路径`。
   Click `List Source Renames` and review each `original path -> safe path` row.
3. 确认清单正确后，点击 `确认改名源路径`。
   After the list looks correct, click `Apply Source Renames`.

这个动作不会自动执行；每次都会重新计算 plan hash，避免用户确认前文件树已经变化。源工程根目录本身不会被改名，改名范围是该工程目录内部的文件和子文件夹。

This action is never automatic. The dashboard recalculates a plan hash each time so changes are not applied to a stale file tree. The source project root itself is not renamed; the operation applies to files and subfolders inside that project folder.
## 验证 / Verify

在 Windows 上检查新文件夹状态：

Check the new folder on Windows:

```powershell
$api = ([xml](Get-Content "$env:LOCALAPPDATA\Syncthing\config.xml")).configuration.gui.apikey
$headers = @{ "X-API-Key" = $api }
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8384/rest/db/status?folder=motion-1-cross-platform" `
  -Headers $headers
```

期待结果：

Expected result:

- `state = idle`
- `needTotalItems = 0`
- `needBytes = 0`
- `errors = 0`
- `pullErrors = 0`

旧 `lan-sync` 仍可能显示 stalled，因为它包含原始非法路径。新的规范化独立文件夹才是后续开发和同步的目标。

The old `lan-sync` folder may still show stalled because it contains the original invalid paths. The new normalized independent folder is the target for future work and sync.
