# Ring Protocol Lab · 环形电极协议实验台

![原创标志](assets/logo.svg)

一个只依赖 Python 标准库的 EIT 测量协议规划 CLI。用可复现的环形索引运算生成激励与相邻电压测量表，适合在嵌入式扫描固件开发前核对通道顺序、极性和编号。独立实现，不包含第三方源码、资源或数据。

## 快速开始

需要 Python 3.10 或更新版本。无需安装任何依赖，在仓库根目录运行：

```sh
python -m ring_protocol_lab generate -n 8 --drive-step 1 --index-base 0 -o protocol.json
python -m ring_protocol_lab validate -n 8 --drive-step 1 --index-base 0 protocol.json
python -m ring_protocol_lab generate -n 8 --drive-step 2 --index-base 1 --format csv -o protocol.csv
python -m ring_protocol_lab svg -n 8 --drive-step 2 --index-base 1 --excitation 1 -o ring.svg
python -m unittest discover -s tests -v
```

用浏览器打开 `ring.svg`。橙色表示激励端点和连线，绿色表示可用的相邻电压测量边。`examples/` 包含可直接查看的 4 电极 JSON/CSV 和 8 电极 SVG。

## 约定与数学定义

- `-n`：电极数，支持 4–512。此上限限制内存使用，不代表硬件能力。
- `--drive-step d`：顺时针距离；1 表示相邻激励，2 表示跳过一个电极。合法范围为 1 到 n−1。
- `--index-base` 必须显式指定 0 或 1。它同时影响电极标签和 excitation 标签。
- 对内部零基激励 i，电流正端为 i，负端为 `(i+d) mod n`。
- 遍历所有 j，电压正端为 j，负端为 `(j+1) mod n`。只保留两个测量电极都不属于当前激励对的测量。
- 先按激励 i，再按测量正端 j 升序输出；所有环绕边都保留。
- 每个电极作为电流正端一次。对径激励也保留反向激励，不自动执行互易性去重。
- 相邻或反向相邻驱动，每次有 n−3 个测量；其余驱动，每次有 n−4 个测量。4 电极对径激励没有合法相邻测量，因此报错。
- 电压极性定义为 V(measure_plus) − V(measure_minus)；实际电流源/采样电路必须单独确认极性。

## 输出与验证

CSV 列依次为 `excitation, drive_plus, drive_minus, measure_plus, measure_minus`。CSV 不携带配置元数据，请与实验配置一起保存。

JSON 使用 `schema: ring-protocol-lab/v1`，包含 `config` 和 `rows`。`validate` 接收 JSON，校验 schema、命令行配置、整型字段、行数、精确顺序与极性。它验证的是完整规范表，不接受手工删减的子协议。CSV 验证暂不支持。

不传 `-o` 时写到标准输出，可重定向或管道处理。`-o` 会覆盖已有文件，父目录必须存在。非法参数、文件错误或无效协议会向 stderr 输出简短说明并返回状态码 2；成功返回 0。

## 架构

- `protocol.py`：不可变配置、协议生成和规范表校验，均无外部状态。
- `svg.py`：确定性的 SVG 环示意图，不使用网络或绘图库。
- `__main__.py`：参数处理与 CSV/JSON/SVG 文件边界。
- `tests/test_protocol.py`：21 个单元/CLI 测试，覆盖环绕、索引基、排除规则、反向激励、错误输入和文件往返。

生成复杂度为 O(n²)，JSON/CSV 生成与校验在内存中完成。SVG 的高密度标签在电极数较大时可能重叠，推荐 8–32 电极用于人工检查。

## 限制与安全边界

本项目只规划协议，不提供有限元网格、FEM 正问题、雅可比、图像重建、接触阻抗建模、电流密度或人体安全判断。没有连接或控制任何硬件。示意图不是电流路径模拟。硬件使用前仍需核对多路复用器引脚映射、源/汇约定、电压量程、采样时序、隔离和电气安全；不能据此进行诊断或直接在人身上实验。

## 开发

零运行时和测试依赖，使用标准库 unittest。直接从仓库运行即可。新增输出格式应复用纯函数协议层，不更改既有表的极性或排序；有意变更格式时应提升 schema 版本并补充测试。
