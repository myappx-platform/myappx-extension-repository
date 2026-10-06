# MyAppx Extension Repository

**语言 / Language:** 中文 | [English](README.en.md)

MyAppx / iDempiere **14** 的扩展目录（catalog）。本目录本身是 OSGi Web bundle `org.idempiere.myappx.extension.repository`，经 HTTP 提供给 **Extension Management**。

规范：[extension-spec.md](extension-spec.md) · Schema：[metadata-schema.json](metadata-schema.json)  
上游布局：[iDempiere Extension Repository](https://github.com/idempiere/idempiere-extension-repository)

| 项目 | 说明 |
|------|------|
| iDempiere | 14 |
| Bundle | `org.idempiere.myappx.extension.repository` |
| Web-ContextPath | `/myappx-extension-repository` |
| 默认基址 | `http://127.0.0.1:18080/myappx-extension-repository` |
| 清单 / 安装顺序 | [`extensions.list`](extensions.list) |
| 源 metadata | `extensions/<Bundle-SymbolicName>/`（与 list 1:1） |
| 生成物 | `main/`（`index.json`、extensions、bundles），打进本 bundle |
| 部署 | 将本 bundle 放入服务器 `plugins/` |
| JVM 属性 | `-DIDEMPIERE_EXTENSION_REPOSITORY=...` |
| Web UI | **System Admin → Extension Management** |

---

## 目录

1. [作用](#1-作用)
2. [目录结构](#2-目录结构)
3. [HTTP 布局与 URL](#3-http-布局与-url)
4. [源与发布](#4-源与发布)
5. [extensions.list](#5-extensionslist)
6. [发布流程](#6-发布流程)
7. [脚本与选项](#7-脚本与选项)
8. [新增 / 下架扩展](#8-新增--下架扩展)
9. [metadata.json](#9-metadatajson)
10. [仅重建 index](#10-仅重建-index)
11. [故障排查](#11-故障排查)
12. [相关文档](#12-相关文档)

---

## 1. 作用

Extension Management 从 catalog 读取可安装扩展：列出名称、版本、依赖，并按 `downloadUrl` 拉取 JAR。

catalog 由本 bundle 的 `Web-ContextPath` 提供，不打进 `org.adempiere.server`。[`extensions.list`](extensions.list) 是唯一真相：只发布其中列出的扩展，行顺序即安装顺序（依赖在前）。`extensions/` 与清单必须 **1:1**。下架时从清单和 `extensions/` 一起删除。

本 bundle 是平台组件，不要写进 `extensions.list`。目录由它自己提供，不能再靠 Extension Management 安装自己。

---

## 2. 目录结构

```text
myappx-extension-repository/
├── META-INF/MANIFEST.MF          # Web-ContextPath: /myappx-extension-repository
├── WEB-INF/web.xml               # DefaultServlet，dirAllowed=false
├── extensions.list               # 清单 + 安装顺序（唯一真相）
├── extensions/                   # 源 metadata；必须与 list 1:1；不打进 bundle
│   └── <Bundle-SymbolicName>/
│       ├── info.md
│       ├── CHANGELOG.md          # 可选
│       ├── assets/               # 可选
│       └── <version>/
│           └── metadata.json
├── scripts/
│   ├── publish.py                # 生成 main/
│   └── generate_index.py         # 生成 index.json
├── publish.bat                   # 生成本地 catalog
├── main/                         # 生成的 HTTP catalog（打进 bundle）
│   ├── index.json
│   ├── extensions/
│   └── bundles/*.jar             # gitignore，发布时从 Maven target 复制
├── extension-spec.md
└── metadata-schema.json
```

`build.properties` 把 `META-INF/`、`WEB-INF/web.xml`、`main/` 和 `.`（编译后的类，含 catalog URL 过滤器）打进 bundle。README、脚本和 `extensions/` 不在 `bin.includes` 里，不会被这个 Web 路径直接下载。

---

## 3. HTTP 布局与 URL

Bundle 安装并启动后，`main/` 对应：

```text
/myappx-extension-repository/main/
├── index.json
├── extensions/<Bundle-SymbolicName>/...
└── bundles/*.jar
```

| URL | 用途 |
|-----|------|
| `http://127.0.0.1:18080/myappx-extension-repository/main/index.json` | 目录（Extension Manager） |
| `http://127.0.0.1:18080/myappx-extension-repository/main/extensions/<id>/...` | `info.md`、`CHANGELOG.md`、`metadata.json` |
| `http://127.0.0.1:18080/myappx-extension-repository/main/bundles/*.jar` | 扩展 JAR 下载 |

JVM：

```text
-DIDEMPIERE_EXTENSION_REPOSITORY=http://127.0.0.1:18080/myappx-extension-repository
```

`index.json` 和 `metadata.json` 里的地址默认写成占位符 `__MYAPPX_CATALOG_BASE__`。本 bundle 的过滤器按**这一次请求**的主机改写成绝对 URL。Extension Management 用上面的 JVM 属性来拉 `main/index.json`，所以下载地址跟这个属性的主机一致。换主机或端口时改 JVM 属性即可，不必重跑发布。只有需要把地址写死（例如脱离本 bundle、放到静态网站）时，才用 `publish.bat --base-url`。

---

## 4. 源与发布

| 路径 | 角色 |
|------|------|
| `extensions/` | Git 源：与 `extensions.list` **1:1** |
| `extensions.list` | 发布清单 + 安装顺序 |
| `scripts/publish.py` | 校验后按清单生成 `main/` |
| `main/` | HTTP catalog 生成物，随后打进本 bundle |

`index.json` 的扩展顺序来自 `extensions.list`，不硬编码。`publish.py` 在改写 `main/` 之前校验：目录与清单 1:1、`metadata.id` 等于目录名、`version` 等于版本目录名、依赖出现在清单更前面。校验失败时原来的 `main/` 保持不动。

---

## 5. extensions.list

格式：

```text
<模块目录>|<Bundle-SymbolicName>
```

- 空行与 `#` 开头行忽略。
- 顺序 = 发布顺序 = Extension Management 建议安装顺序（依赖在前）。
- 模块目录相对 `myappx-plugins/`，用于定位 `target/*.jar`。

示例：

```text
example-plugin|com.example.plugin
```

`publish.py` 按精确文件名查找 JAR（先正式包，再 `-SNAPSHOT`；不会选用 `tests` / `sources` / `javadoc`）：

1. `<模块>/<symbolicName>/target/<symbolicName>-<version>.jar` 或 `...-<version>-SNAPSHOT.jar`
2. `<模块>/target/` 下的同名文件

每个扩展只保留一个当前版本目录，目录名必须等于 `version`。多一个版本目录时发布失败。

当前清单以 [`extensions.list`](extensions.list) 为准，改后须重新发布。

---

## 6. 发布流程

清单里的插件模块排在本模块之前。`mvn clean verify` 构建那些 JAR 之后，本模块在 `prepare-package` 运行 `publish.py`（缺少 JAR 即失败），再把 `main/` 打进 bundle。`myappx-plugins/build.bat` 就是这一条命令。

```bat
cd myappx-plugins
mvn -Drevision=14.0.0-SNAPSHOT clean verify
```

只刷新 catalog、JAR 已经在各模块 `target/` 时：

```bat
cd myappx-extension-repository
publish.bat
cd ..
mvn -Drevision=14.0.0-SNAPSHOT -pl myappx-extension-repository package
```

上面的 `package` 会再发布一次。若 `main/` 刚刚由 `publish.bat` 写好，加上 `-Dmyappx.skip.catalog.publish=true` 可跳过第二次。

把 `myappx-extension-repository/target/org.idempiere.myappx.extension.repository-*.jar` 放进新服务器实例的 `plugins/`，设置 `IDEMPIERE_EXTENSION_REPOSITORY`，然后启动。

发布先在 `main.staging/` 写完整棵目录，成功后再替换 `main/`。JAR 的 SHA-256 来自本次复制的文件。

---

## 7. 脚本与选项

```bat
publish.bat                              生成 main/；缺少 JAR 或多个版本目录则失败，且不改已有 main/
publish.bat --base-url http://host:18080/myappx-extension-repository
python scripts\publish.py --check-inventory   校验清单、metadata 与依赖顺序
```

等价 Python：

```bat
python scripts\publish.py
python scripts\publish.py --check-inventory
```

| 选项 | 说明 |
|------|------|
| `--base-url` | 把绝对基址写入 `index.json` / `downloadUrl`，过滤器不再改写。未指定时用占位符；若设置了环境变量 `MYAPPX_EXTENSION_REPOSITORY_URL`，则用该值 |
| `--check-inventory` | 校验 `extensions/` 与 `extensions.list` 1:1、每个扩展只有一个版本目录、metadata 字段、版本目录名、依赖顺序，然后退出 |

---

## 8. 新增 / 下架扩展

**新增**

1. 创建 `extensions/<symbolic.name>/`：`info.md`、可选 `CHANGELOG.md` 与 `assets/`、`<version>/metadata.json`。`version` 必须与目录名相同。
2. 在 `extensions.list` 增加一行（依赖在前）——必须与源目录同时存在，保持 1:1。
3. 构建该模块 JAR。文件名须为 `<symbolicName>-<version>.jar` 或 `<symbolicName>-<version>-SNAPSHOT.jar`。
4. 运行 `publish.bat`，再打包本 bundle 并替换 `plugins/` 中的 jar。

**下架**

1. 从 `extensions.list` 删除该行。
2. 删除 `extensions/<id>/`。
3. 重新发布并重新打包。生成物中不再出现该扩展。

`info.md` 建议章节见 [extension-spec.md](extension-spec.md)：Summary、Features、Compatibility、Database Changes、Usage & Configuration、Author/Support。

---

## 9. metadata.json

源文件中的 `downloadUrl` / `sha256` 会被 `publish.py` 在 `main/` 中覆盖。源文件可写相对 Maven 产物路径，便于本地对照。

必填字段：`id`（等于目录名）、`name`、`version`（等于版本目录名）、`idempiereVersion`、`bundles`（至少一项，含 `symbolicName`）。`dependencies[].id` 必须出现在 `extensions.list` 更前面。完整约束见 [metadata-schema.json](metadata-schema.json)。

`idempiereVersion` 与 `dependencies.version` 使用 [OSGi 语义版本范围](https://docs.osgi.org/whitepaper/semantic-versioning/040-semantic-versions.html)。

---

## 10. 仅重建 index

在 `main/extensions/` 已存在时：

```bat
python scripts/generate_index.py main
python scripts/generate_index.py --base-url http://host:18080/myappx-extension-repository main
```

`generate_index.py` 按 `extensions.list` 过滤并排序。目录与清单不一致、或 `version` 与目录名不一致时失败。它不复制 JAR，也不重算 `sha256`。

---

## 11. 故障排查

| 现象 | 处理 |
|------|------|
| Extension Management 看不到某扩展 | 确认已在 `extensions.list`，已 `publish.bat`，已打包本 bundle 并放入服务器 `plugins/`，且 bundle 已启动 |
| 安装失败 / 无法下载 JAR | 重新构建对应模块后再发布。JAR 名必须是 `<symbolicName>-<version>.jar` 或带 `-SNAPSHOT` |
| URL 404 | 确认本 bundle 已安装并已启动，且 `IDEMPIERE_EXTENSION_REPOSITORY` 指向它的 Web-ContextPath |
| `index.json` 顺序不对 | 调整 `extensions.list` 顺序后重新发布 |
| 发布报依赖顺序错误 | 把被依赖的扩展移到 `extensions.list` 更前面 |
| SHA 校验失败 | `main/` 的 `sha256` 必须来自本次复制的 JAR；改过 JAR 后须再发布并重新打包 |
| 下载地址主机不对 | 让 `IDEMPIERE_EXTENSION_REPOSITORY` 指向客户端能访问的 catalog。默认 JSON 会按该请求改写。要写死地址时用 `publish.bat --base-url` |

---

## 12. 相关文档

| 文档 | 说明 |
|------|------|
| [extension-spec.md](extension-spec.md) | 扩展目录约定、`info.md` 与 metadata 示例 |
| [metadata-schema.json](metadata-schema.json) | metadata JSON Schema |
| [extensions/extension.md](extensions/extension.md) | 源目录结构说明 |
| [`extensions.list`](extensions.list) | 发布清单与安装顺序 |
