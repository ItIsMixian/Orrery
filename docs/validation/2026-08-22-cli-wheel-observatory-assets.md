# Validation：CLI Wheel Observatory Assets 与 DeepSeek Runtime 复验

Date: 2026-08-22
Scope: 修复普通 wheel CLI 对源码仓库 Observatory assets 的依赖，并以隔离 wheel 安装和真实 DeepSeek Harness turn 复验 Adapter → preflight → CLI validate；不处理 ADR 编号或 main 集成
Result: PASS — 普通非 editable wheel 可从 `site-packages` 加载 managed assets，scaffold／validate 与真实 DeepSeek Adapter 路由均通过
Source: branch `codex/claude-deepseek-adapters`，parent `b72daeb0322076782dcee453f518054f69fbcd16`

## 权威链与问题

- [ADR-0004](../decisions/0004-platform-neutral-core-and-adapter-boundaries.md)
- [Approved Design](../design/platform-neutral-core-and-adapter-architecture.md)
- [Implementation Plan](../implementation/plans/2026-08-19-platform-neutral-core-and-adapters.md)
- [触发问题的 DeepSeek Runtime Validation](2026-08-22-deepseek-harness-adapter-stage-b-runtime.md)

修复前，`project_orrery_cli.context.repository_context()` 无条件向上查找同时含
`packages/component-versions.json` 与 `scripts/docsite` 的源码仓库。CLI 0.1.1 wheel 的 distribution／entrypoint
预检能通过，但 `validate` 在读取 target 前抛出
`cannot locate Project Orrery source repository for Observatory assets`。这使版本兼容的普通 wheel 仍不可用。

## 实现

- `project-orrery-observatory/setup.py` 的自定义 `build_py` 从版本化 `component.json` 读取固定 managed-tool
  清单，并在 wheel build 阶段把九个 canonical 根工具复制进
  `project_orrery_observatory/assets/`。构建只读取白名单路径，不复制凭据、缓存、生成站点或作者文档。
- `observatory_asset_root()` 优先使用安装包内完整 assets；editable／source checkout 没有该目录时，才回退
  到持有完整 managed-tool 清单的 monorepo 根。两条路径都逐项检查九个文件存在。
- CLI `repository_context()` 改为向 Observatory package 请求资产根，不再自行猜测源码仓库。
- `tests/test_cli_wheel_installation.py` 在临时 monorepo 副本中构建三个 wheel，检查 Observatory wheel 的
  九个 asset entry，再安装进全新 venv；asset root 必须位于 `site-packages` 且不指向 staging source，
  随后真实执行 scaffold 和 validate。

该修复没有复制第二份受版本控制的 managed tools；wheel snapshot 只存在于构建输出。当前未发布 pipeline
仍必须从 monorepo 构建 Observatory wheel；独立 sdist 发布不在本次范围。

## 隔离 Wheel 证据

证据根：`D:\orrery-stage-b-dsh-wheel-fix-20260822-001`。pip cache、TEMP、staging repo、wheelhouse 和
runtime venv 全部位于该 D 盘根。

| Wheel | SHA-256 |
|---|---|
| `project_orrery_core-0.1.0-py3-none-any.whl` | `3387f6f02ba0ee2e3d86831f6a021c8e3671e16c0abff491bf08a8393ff3b31d` |
| `project_orrery_observatory-0.1.0-py3-none-any.whl` | `21aed57e52892f836ace822cfb6e88276b814559879d73da65fcd96436f04798` |
| `project_orrery_cli-0.1.1-py3-none-any.whl` | `f9e26124e4817fbec560050de0b4551283f7e5951b600b45bc993d66beb7dc19` |

安装后的资产根为
`D:\orrery-stage-b-dsh-wheel-fix-20260822-001\runtime\Lib\site-packages\project_orrery_observatory\assets`。
直接运行 `project-orrery validate` 对既有 424-file 作者 fixture exit 0，输出 `integrated candidate`。

## 真实 DeepSeek 复验

使用同一真实 `@deepseek-ai/dsh 0.1.0-rc.8`、`deepseek-official`／`deepseek-v4-flash` 和用户明确授权的
credential。Key 只进入该子进程内存；Adapter 仍安装在隔离 `DSH_HOME`，PATH 只新增上述普通 wheel venv。

显式 `/project-orrery` turn 的独立 session 是第 11 个 session、337 个事件：

- `request/context` 精确记录 provider、model 与 1,000,000 context window；
- Adapter preflight 只执行一次，exit 0，entrypoint 指向 wheel venv；
- `project-orrery validate --target .` 只执行一次，exit 0；
- 模型另以 `pip show`、freeze list 和 wheel `direct_url.json` 确认没有 editable location／`-e` entry；
- usage 为 input 6,472、output 7,164、cache-read 85,760、reasoning 4,942 tokens；`turn/end` 存在。

测试后第一次 remove 因漏带隔离 pnpm store／home 环境而 exit 1，probe 正确显示 Adapter 仍为 1；该结果不
冒充成功。使用与安装相同的完整隔离 pnpm 环境重试后 remove exit 0，最终 runtime probe 为 skills 0、
loaded false、profile dependency false、Bundle false。

作者 fixture 再次与原 archive 比较为 expected 424、actual 424、missing 0、unexpected 0、changed 0；真实
credential hash 不变，没有写 GUI profile 或真实 Agent Skill 根。

## 验证与结论

- `python -X utf8 -m unittest tests.test_cli_wheel_installation -v`：1/1 passed；
- Project Orrery + wheel + DeepSeek Adapter 定向组合：18 passed + 2 expected skips；
- 默认全仓：75 项中 73 passed、2 expected skips；integrated structure：PASS；
- 静态 docsite 构建到 `D:\orrery-docsite-cli-wheel-fix-20260822-001\index.html`：PASS；
- 258 份 Markdown／568 个本地链接／0 missing；secret scan 与 `git diff --check`：PASS；
- `docs/_site/index.html` 未创建或修改；
- 修复后的普通 wheel direct validate 与真实 DeepSeek model route：PASS；
- 当前功能缺口不再是 wheel assets。支持状态仍保留 `experimental`／`unreleased`，由另一集成工作负责
  同步当前 main、解决 Candidate ADR 编号并决定是否写入最终 `verified` compatibility entry。
