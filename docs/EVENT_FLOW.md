# 事件流 / Event Flow

本页描述从 clone repo 到双端同步、命名修复、依赖审计和更新检测的完整事件流。

This page describes the full event flow from cloning the repo to two-end sync, name repair, dependency audit, and update checks.

## 1. Clone 到 Mac 控制端 / Clone to the Mac Controller

1. 用户 clone GitHub repo。 / The user clones the GitHub repo.
2. 运行 `./setup.sh` 初始化配置、安装 LaunchAgent、刷新 Dock 入口并生成 Windows 工具包。 / Run `./setup.sh` to initialize config, install the LaunchAgent, refresh the Dock entry, and generate the Windows package.
3. 填写或确认 `config.json` 后再次运行 `./setup.sh`。 / Fill in or confirm `config.json`, then run `./setup.sh` again.

## 2. Windows Companion 配对 / Windows Companion Pairing

1. Mac 运行 `python3 generate_windows_config.py` 生成 `windows/agent-config.generated.json`。 / The Mac runs `python3 generate_windows_config.py` to generate `windows/agent-config.generated.json`.
2. 用户把 `windows/` 文件夹复制到 Windows。 / The user copies `windows/` to Windows.
3. Windows 运行 `windows/setup.ps1`；脚本会在需要时请求管理员权限。 / Windows runs `windows/setup.ps1`; the script requests administrator permission when needed.
4. Installer 创建计划任务、防火墙规则、hosts alias、Startup 兜底、桌面/开始菜单智能启动器。 / The installer creates the scheduled task, firewall rule, hosts alias, Startup fallback, and desktop/Start Menu smart launcher.

## 3. 控制台同步事件 / Dashboard Sync Events

1. 浏览器请求 `/api/overview`。 / The browser requests `/api/overview`.
2. Mac server 查询本机 Syncthing REST API、磁盘、空闲状态。 / The Mac server queries local Syncthing REST, disks, and idle state.
3. Mac server 尝试查询 Windows companion `/api/agent/status`。 / The Mac server attempts Windows companion `/api/agent/status`.
4. Server 为每个 Syncthing 文件夹采样 completion、need bytes、folder state、need list 和 folder errors，并记录最近一次进度变化时间。 / The server samples completion, need bytes, folder state, need list, and folder errors for each Syncthing folder, and records the last progress-change time.
5. UI 按 `healthy/syncing/waiting/stalled/paused/error/unavailable` 显示状态，并在诊断面板显示当前项目、疑似卡住项目、无进度时间、相关路径/文件和建议动作。 / The UI displays health as `healthy/syncing/waiting/stalled/paused/error/unavailable`, and the diagnosis panel shows the current project, suspected blocked project, no-progress time, related paths/files, and suggested actions.
6. `继续当前同步` 调用 `/api/sync/resume`，同时恢复/扫描本机 Syncthing，并尽力请求 Windows companion 恢复。 / `Resume Current Sync` calls `/api/sync/resume`, resumes/scans local Syncthing, and best-effort requests Windows companion resume.

## 4. 命名与依赖事件 / Naming and Dependency Events

1. `扫描命名` 调用 `/api/audit`，返回非法命名和冲突预览。 / `Scan Names` calls `/api/audit` and returns unsafe naming/collision preview.
2. `创建安全副本` 调用 `/api/normalize`，生成规范化副本和 `_CrossPlatformReport`。 / `Create Safe Copy` calls `/api/normalize`, creating the normalized copy and `_CrossPlatformReport`.
3. 可选源路径改名先调用 `/api/source-renames/preview`，确认后才调用 `/api/source-renames/apply`。 / Optional source renaming first calls `/api/source-renames/preview`; only after confirmation does it call `/api/source-renames/apply`.
4. `规范化副本管理` 调用 `/api/normalizations` 和 `/api/normalizations/report`，集中查看历史安全副本、重命名映射、冲突、跳过项和风险提醒。 / `Normalized Copy Manager` calls `/api/normalizations` and `/api/normalizations/report` to review historical safe copies, rename mappings, collisions, skipped items, and risk notes in one place.
5. `检查依赖` 调用 `/api/dependencies/audit`，自动检测 Adobe、Unity、字体、插件、外部路径和 Windows 端缺失项。 / `Check Dependencies` calls `/api/dependencies/audit`, automatically detecting Adobe, Unity, fonts, plugins, external paths, and Windows-side gaps.
6. `打包依赖清单` 会创建 `_DependencyBundle`，作为可同步的依赖说明和项目本地资产包。 / `Bundle Dependency Manifest` creates `_DependencyBundle` as a syncable manifest and project-local asset bundle.

## 5. 更新事件 / Update Events

1. 控制台定期调用 `/api/update/check`。 / The dashboard periodically calls `/api/update/check`.
2. Server 查询配置的 GitHub release。 / The server checks the configured GitHub release.
3. 当 release 版本大于服务内置 `APP_VERSION` 时，UI 显示更新预览气泡。 / When the release version is newer than the service's built-in `APP_VERSION`, the UI shows an update preview bubble.

## 6. 失败边界 / Failure Boundaries

- Windows companion 离线时，Syncthing 仍可同步，但磁盘、电源、Windows resume 和远端依赖清单不可用。 / If Windows companion is offline, Syncthing can still sync, but disk, power, Windows resume, and remote dependency inventory are unavailable.
- Adobe 二进制文件不会被盲目重写；深度 relink 需要宿主应用脚本。 / Adobe binary files are not blindly rewritten; deep relink requires host-app scripts.
- 源工程默认不改名；原地改名必须二次确认。 / Source projects are not renamed by default; in-place rename requires a second confirmation.
