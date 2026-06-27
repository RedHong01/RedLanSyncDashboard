# 工程依赖审计 / Project Dependency Audit

依赖审计用于在同步大型工程前识别 Adobe、字体、插件、预设和外部路径依赖，并把可安全同步的项目本地资产打包进 `_DependencyBundle`。

The dependency audit detects Adobe, font, plugin, preset, and external-path dependencies before syncing large projects, then packages safe project-local assets into `_DependencyBundle`.

## 会检测什么 / What It Detects

- Adobe 工程文件：After Effects、Premiere Pro、Photoshop、Illustrator、InDesign、Adobe XD、Animate。
- Adobe project files: After Effects, Premiere Pro, Photoshop, Illustrator, InDesign, Adobe XD, and Animate.
- Unity 工程根目录、Unity YAML 文件、`.meta` 文件和本机 Unity Editor 安装。
- Unity project roots, Unity YAML files, `.meta` files, and installed Unity Editors.
- 项目内携带的字体文件：`.ttf`、`.otf`、`.ttc`、`.dfont`、`.woff`、`.woff2`。
- Project-local font files: `.ttf`, `.otf`, `.ttc`, `.dfont`, `.woff`, `.woff2`.
- 可读文本文件中的字体名称和外部路径线索。
- Font names and external path references in text-readable project files.
- 项目内携带的 Adobe 资产：`.jsx`、`.jsxbin`、`.ffx`、`.mogrt`、`.aex`、`.plugin`、`.zxp`。
- Project-local Adobe assets: `.jsx`, `.jsxbin`, `.ffx`, `.mogrt`, `.aex`, `.plugin`, `.zxp`.
- 当前端点已安装的字体、Adobe 应用、Unity Editor 和常见 Adobe 插件目录。
- Installed fonts, Adobe applications, Unity Editors, and common Adobe plugin folders on the current endpoint.

## 打包策略 / Packaging Strategy

点击 `打包依赖清单` 后，控制台会在源工程内创建：

Clicking `Bundle Dependency Manifest` creates this inside the source project:

```text
_DependencyBundle/
  dependency_manifest.json
  README_DEPENDENCIES.md
  Fonts/
    Project/
    ReferencedInstalled/
  AdobeProjectAssets/
```

这个文件夹位于 Syncthing 工程内，因此会随工程同步到另一端。

This folder lives inside the Syncthing project, so it syncs with the project.

## 重要限制 / Important Limits

- 二进制 Adobe 文件可能隐藏字体和插件依赖；深度提取通常需要在 Adobe 应用内运行脚本或导出文本交换格式。
- Binary Adobe files can hide font and plugin dependencies; deep extraction often requires scripts inside the Adobe app or text interchange exports.
- 字体和插件可能有授权限制；工具会打包清单和项目本地资产，但不会自动安装到另一台电脑。
- Fonts and plugins may have licensing restrictions; the tool packages manifests and project-local assets, but does not auto-install them on another computer.
- Adobe 插件通常绑定平台、版本和安装器。工具会识别常见插件目录并报告缺失，不会盲目复制系统插件目录。
- Adobe plugins are often platform-, version-, and installer-specific. The tool identifies common plugin folders and reports gaps, but does not blindly copy system plugin directories.

## Windows 独立检查 / Standalone Windows Check

即使 companion agent 还未重装，也可以在 Windows 仓库目录运行：

Even before reinstalling the companion agent, run this from the Windows checkout:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\windows\check-dependencies.ps1
```

新版 companion agent 还会提供：

The updated companion agent also provides:

```text
GET /api/agent/dependencies
```
