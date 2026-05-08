# 结题阶段实验分析报告

## 1. 实验目标

本轮实验的目标不是追求工业级 benchmark 数值，而是验证当前教学型 LSM-Tree 模拟系统是否已经具备以下三项结题所需能力：

1. `put/get + WAL + MemTable + Flush + SSTable + STC/LCS` 主流程在大 workload 下仍然正确。
2. 系统能够稳定输出具有解释意义的读放大、写放大、flush 次数、compaction 次数与层级状态。
3. 不同 compaction 策略与不同参数配置会产生可复现、可解释、可用于论文论述的差异化结果。

本轮实验已在 LCS 语义重构和 MemTable 多版本语义重构之后重新运行。当前系统具有以下教学型特征：

- MemTable 不再对同 key 直接覆盖，而是保留多版本。
- flush 会把同 key 的多个版本一起落到 SSTable。
- 旧版本主要在 compaction 阶段按 `seq` 清理。
- `L0` 仍按表数触发 compaction。
- `L1+` 的触发改为按“当前层总记录数是否超过该层目标容量”判断。
- `L1+` 查询先做 key range 范围裁剪，再按有序 key range 做候选表定位。
- `L1+` 查询使用二分定位候选 SSTable，而不是全层遍历。

因此，本轮结果比旧版更能反映当前系统中 LCS 的真实读路径优势、版本保留行为与高层 pushdown 成本。

## 2. 实验环境与方法

### 2.1 系统对象

实验对象为当前仓库中的教学型 LSM-Tree 模拟系统，具有如下特点：

- 单机、单进程模拟。
- MemTable 使用 Python 容器维护“同 key 的多版本列表”。
- SSTable 使用 `JSONL + metadata JSON + Bloom JSON` 文件格式。
- STC 与 LCS 均为教学型简化实现。
- 读放大、写放大均为“教学型逻辑统计值”，用于解释系统行为，而不是替代真实数据库的物理测量。

### 2.2 指标口径

本轮实验沿用当前实现中的指标定义。

1. 用户查询读放大：

\[
\text{Read Amplification} =
\frac{\text{user\_query\_read\_io\_total}}{\text{total\_gets}}
\]

说明：

- 仅统计 `get()` 查询路径产生的逻辑 IO。
- 不混入 compaction 后台读取。
- Bloom Filter 文件读取计入逻辑 IO。
- `Index Block = 1 IO`、`Data Block = 1 IO` 属于教学型抽象。

2. 写放大：

\[
\text{Write Amplification} =
\frac{\text{actual\_disk\_write\_bytes\_total}}{\text{logical\_write\_bytes\_total}}
\]

说明：

- 分母为用户逻辑写入字节数，仅统计 `key + value`。
- 分子统计 WAL、flush 生成文件、compaction 生成文件的总字节数。
- 不计 MemTable 内存写入。

### 2.3 实验组织方式

本轮共使用：

- 4 组 workload
- 3 组参数 profile
- 2 种 compaction strategy

总运行数：

\[
4 \times 3 \times 2 = 24
\]

每组运行均会导出：

- `metrics.json / metrics.csv`
- `trace.json / trace.csv`
- `validation.json`
- `summary.csv / summary.json`
- `strategy_deltas.csv`

其中 `validation.json` 由实验脚本维护内存 oracle，对每次 `get` 的理论正确结果进行校验。

## 3. 参数配置设计

本轮结题实验主要使用以下 3 组 profile。

| Profile | 主要参数 | 设计意图 |
|---|---|---|
| `final_balanced` | `memtable_max_records=24`, `stc_trigger_tables=4`, `l0_compaction_trigger_tables=4`, `level_size_multiplier=6.0` | 平衡配置，用于观察系统在中等 compaction 压力下的常规行为。 |
| `final_dense_compaction` | `memtable_max_records=12`, `stc_trigger_tables=3`, `l0_compaction_trigger_tables=3`, `level_size_multiplier=3.0` | 通过更小的 MemTable 和更紧的触发阈值，提高 flush/compaction 频率。 |
| `final_overlap_sensitive` | `memtable_max_records=8`, `stc_trigger_tables=4`, `l0_compaction_trigger_tables=2`, `level_size_multiplier=2.5` | 放大 overlap 与高层 compaction 压力，突出 STC/LCS 差异。 |

这三组 profile 的设计目的不是覆盖所有真实数据库调优情况，而是构造三种教学上容易解释的压力场景：

- 平衡场景
- 密集 compaction 场景
- overlap 敏感场景

## 4. Workload 设计

### 4.1 `final_sequential_ingest`

- 操作总数：`825`
- `put` 数量：`768`
- `get` 数量：`57`

设计方式：

- 连续顺序写入 `seq_0001 ~ seq_0768`
- 每写入 64 条插入若干命中查询与缺失查询
- 尾部再追加一组全局验证查询

设计目的：

- 强制产生多轮 flush
- 观察顺序写场景下 STC 与 LCS 的层级演化
- 验证旧 key、新 key 和不存在 key 在多轮 compaction 后仍能正确查询

### 4.2 `final_hotspot_overwrite`

- 操作总数：`656`
- `put` 数量：`576`
- `get` 数量：`80`

设计方式：

- 固定一组 `hot_01 ~ hot_08` 热点 key
- 跨 36 个周期重复覆盖写
- 每个周期同时写入若干一次性冷数据
- 周期性插入热点 key、冷数据 key 和缺失 key 查询

设计目的：

- 验证重复 key 的最新值是否始终正确
- 放大 duplicate-heavy workload 下的 compaction 差异
- 观察 LCS 是否因更多重叠合并而承担更高写代价

### 4.3 `final_overlap_waves`

- 操作总数：`688`
- `put` 数量：`640`
- `get` 数量：`48`

设计方式：

- 共 40 个滑动写入波次
- 相邻波次存在 12 个 key 的重叠区间
- 周期性插入命中查询与缺失查询

设计目的：

- 主动制造多批次 key range overlap
- 验证 LCS 在 overlap 感知 compaction 下的行为
- 观察“读放大下降、写放大上升”的典型读写权衡

### 4.4 `final_mixed_read_validation`

- 操作总数：`680`
- `put` 数量：`480`
- `get` 数量：`200`

设计方式：

- 24 个 batch
- 每个 batch 同时包含：
  - 热点 key 覆盖写
  - 普通顺序追加写
  - 边缘 key 写入
  - 多个命中 / 缺失查询

设计目的：

- 验证在更接近“持续读写交错”的场景中，系统是否仍能正确运行
- 检查读放大与写放大是否随 compaction 策略发生可解释变化
- 用于展示系统的“可模拟性”而非只支持单一写入演示

## 5. 正确性验证结果

本轮实验最重要的第一结论是：系统在所有大 workload 下都保持了正确性。

全局结果如下：

- 总运行数：`24`
- 总 `get` 校验次数：`2310`
- 总错误数：`0`
- 全部运行的 `validation_accuracy = 1.0`

这说明当前系统至少已经具备以下结题所需的基础正确性：

1. `put` 写入后能够被后续 `get` 正确读取。
2. MemTable flush 到 SSTable 后，原始数据不会丢失。
3. STC 与 LCS compaction 后，重复 key 仍保持“较大 seq 覆盖较小 seq”的语义。
4. 不存在的 key 不会误返回错误值。
5. 多轮 flush 与多轮 compaction 之后，查询路径仍然可用。

从“系统正确性”角度看，这批实验数据已经能够支持如下表述：

> 当前教学型 LSM-Tree 模拟系统并非仅能完成小样本演示，而是可以在数百条写入、数十到数百次查询、并伴随多轮 flush/compaction 的场景下稳定运行，并保持查询结果正确。

## 6. 总体实验结论

将 12 组 `workload × profile` 配对后，可得到以下总体趋势：

- 在 `12 / 12` 组对比中，LCS 的读放大均低于 STC。
- 在 `10 / 12` 组对比中，LCS 的写放大高于 STC。
- 在 `2 / 12` 组对比中，LCS 的写放大低于 STC。
- 在 `6 / 12` 组对比中，LCS 的 compaction 次数低于 STC。

这里尤其要强调两点：

1. LCS 的读优势在本轮所有实验组中都已经稳定体现，说明“范围裁剪 + 有序维护 + 二分定位候选表”的查询优化是有效的。
2. LCS 并不是在所有情况下都更高写放大。当前模型中存在 2 组顺序写场景，LCS 既降低了读放大，也降低了写放大。这是当前教学型高层触发与向下 pushdown 逻辑共同作用的结果，必须作为“当前模拟器行为”而非“工业级普遍规律”进行解释。
3. MemTable 改为多版本保留后，overwrite workload 的版本流动过程更接近真实 LSM，因而当前实验中的写放大结果比“MemTable 直接覆盖旧值”的旧实现更具解释力。

因此，当前系统已经能够稳定模拟出“不同 compaction 策略在读写代价上的差异化行为”，并且能够暴露模型语义对实验结果的影响。

## 7. 代表性结果分析

下面选择 4 组最适合写入结题报告正文的结果进行分析。

### 7.1 顺序写入场景：`final_sequential_ingest + final_balanced`

| Strategy | Flush | Compaction | Level State | Read Amp | Write Amp |
|---|---:|---:|---|---:|---:|
| STC | 32 | 10 | `L2=2` | 3.070 | 28.082 |
| LCS | 32 | 10 | `L1=6, L2=2` | 2.298 | 23.207 |

这一组结果有两个重要意义：

1. LCS 读放大已经稳定低于 STC。
2. 在当前顺序写教学场景下，LCS 写放大也低于 STC。

#### 合理之处

在 LCS 读路径优化之前，顺序写场景下的 LCS 会因为保留多个高层 SSTable 而在查询时逐表扫描，导致读放大偏高。优化后，LCS `L1+` 查询改为：

- 先做范围裁剪
- 再做按 key range 的候选表定位
- 最后只访问极少量候选 SSTable

因此，即使 LCS 最终保留了多张 `L1/L2` 表，也不再需要对整层做线性扫描，读放大显著下降。

#### 为什么这里 LCS 写放大反而更低

这不是经典教材中的普遍结论，而是当前教学模型下的可解释结果：

1. 当前写放大按“实际落盘总字节 / 逻辑写入字节”计算。
2. 该 workload 近乎纯顺序写，重复 key 很少，写放大主要由“数据被整体重写多少轮”决定。
3. 在 `final_balanced` 配置下，STC 把 run 更积极地向深层推进，导致相同数据被更多次重写。STC每层容量相当于*4，LCS每层容量*6，导致STC层会更深
我改过配置后：
memtable_max_records=24
memtable_max_bytes=4096
max_levels=6
stc_trigger_tables=4
l0_compaction_trigger_tables=4
level_size_multiplier=4.0
bloom_bits_per_key=12

测试 workload：

final_sequential_ingest
实验结果：

STC
flush_count = 32
compaction_count = 10
read_amplification = 3.070
write_amplification = 27.949
level state = L2=2
LCS
flush_count = 32
compaction_count = 12
read_amplification = 2.298
write_amplification = 24.802
level state = L1=4, L2=4
结果仍然是STC写放大更大。
当前实现里，STC 写放大更大的根本原因，不只是“LCS 层容量更大”，而是“STC 的同步整批下推 + 顺序写无去重收益 + 写放大按总落盘字节统计”这三件事叠加在一起。
4. 当前 LCS 虽然保留了更多有序高层表，但减少了进一步下推重写，因此总落盘字节更低。

这个结论应写成：**当前模拟器中，顺序写场景下的 LCS 在读放大和写放大上都可能优于 STC；这是当前简化语义的实验现象，不宜直接外推为工业级 LCS 的通用规律。**

### 7.2 热点覆盖写场景：`final_hotspot_overwrite + final_dense_compaction`

| Strategy | Flush | Compaction | Level State | Read Amp | Write Amp |
|---|---:|---:|---|---:|---:|
| STC | 48 | 22 | `L1=1, L2=2, L3=1` | 3.550 | 20.391 |
| LCS | 48 | 18 | `L1=1, L2=1` | 3.013 | 24.394 |

这一组结果说明：

1. LCS 保持了较低读放大。
2. LCS 的写放大高于 STC。
3. LCS 的 compaction 次数反而更少。

这是一个很有论文价值的组合，因为它说明：

- LCS 的写代价不一定来自“compaction 次数更多”；
- 即使 compaction 次数更少，只要每次 overlap 合并牵涉的旧数据更多，总重写字节仍可能更高。

对热点覆盖写 workload 而言，热点 key 被反复更新，LCS 为了维持更整洁的高层读路径，会更频繁地把重叠范围内的旧数据一起卷入重写，因此写放大上升是合理的。

### 7.3 重叠波次场景：`final_overlap_waves + final_dense_compaction`

| Strategy | Flush | Compaction | Level State | Read Amp | Write Amp |
|---|---:|---:|---|---:|---:|
| STC | 54 | 26 | `L3=2` | 3.729 | 19.352 |
| LCS | 54 | 19 | `L1=1, L2=1` | 2.562 | 22.742 |

这一组是最能体现 LCS 设计目标的典型结果：

- LCS 通过处理 overlap，让高层查询代价下降。
- 代价是写放大增加。
- 即使 compaction 次数少于 STC，LCS 的每次合并仍可能重写更多重叠旧数据。

该组结果非常适合在结题报告中支撑如下表述：

> 当 workload 中存在大量重叠 key range 时，LCS 更容易表现出“降低读代价、增加写代价”的典型特征，而 STC 则更接近“减少 overlap 感知处理、保留较低写放大”的行为。

### 7.4 混合读写验证场景：`final_mixed_read_validation + final_overlap_sensitive`

| Strategy | Flush | Compaction | Level State | Read Amp | Write Amp |
|---|---:|---:|---|---:|---:|
| STC | 60 | 18 | `L1=3, L2=3` | 3.855 | 20.822 |
| LCS | 60 | 43 | `L3=1, L4=1` | 2.645 | 39.328 |

这是本轮最“激进”的一组结果。

它说明：

1. LCS 的确能显著压低读放大。
2. 在 overlap-sensitive 参数下，LCS 会触发更多高层 pushdown。
3. 更多高层 pushdown 进一步带来了更高写放大。

这组结果对结题很重要，因为它说明系统并没有把 LCS “美化”为单方面更优策略，而是真实反映了参数与策略组合可能带来的高写代价。尤其是在当前“按层总记录数触发高层 compaction”的教学语义下，激进参数会把 LCS 推向更强的整理行为，从而放大写代价。

## 8. 结果的合理性与系统可模拟性说明

本轮实验可以证明系统具备较强的“可模拟性”，主要体现在以下几个方面。

### 8.1 策略差异是可复现的

同一 workload 在 STC 与 LCS 下，能够稳定产生：

- 不同的 compaction 次数
- 不同的层级分布
- 不同的读放大
- 不同的写放大

这说明系统不是“随便输出几个数字”，而是能够把策略逻辑映射为稳定的实验现象。

### 8.2 参数变化会引起可解释的行为变化

同一 workload 在 `final_balanced`、`final_dense_compaction`、`final_overlap_sensitive` 下，其 flush 与 compaction 频率、层级结构和放大指标均发生了明显变化。

例如：

- 减小 MemTable 阈值，会增加 flush 次数。
- 减小 compaction 触发阈值，会提高 compaction 频率。
- 增强 overlap 压力，会进一步放大 LCS 的高层 pushdown 与写代价。

这些变化都符合当前模拟器的参数语义，说明系统已经具备参数敏感性分析能力。

### 8.3 查询正确性与结构演化可以同时验证

本轮实验不是“只看指标，不管结果对不对”，而是把逻辑正确性与结构行为绑定在一起验证：

- 一方面，导出层级状态、compaction 次数、放大指标。
- 另一方面，所有 `get` 都用 oracle 验证。

这使得实验同时支持：

- 功能正确性论证
- 存储结构演化论证
- 指标分析论证

这也是本系统相较于纯 UI 演示原型更接近“结题可论证系统”的关键标志。

## 9. 局限性与后续改进方向

尽管本轮实验已经足以支撑结题阶段的正确性与可模拟性展示，但仍需明确以下局限性。

### 9.1 LCS 仍是教学型简化实现

当前 LCS 已经补上了高层查询优化和按层总记录数触发的高层 pushdown，但它仍不等于工业级 LCS：

- 高层触发逻辑仍是简化版
- 层容量控制仍未按真实总字节严格建模
- 选表策略仍远不如真实系统复杂
- compaction 输出仍不做 split

因此，实验结果应解释为“当前教学型模拟器中的 LCS 行为”，而不是对工业级数据库策略的直接复现。

### 9.2 写放大结果带有实现口径特征

尤其是 `final_sequential_ingest` 中 LCS 写放大低于 STC 的现象，虽然在当前系统内有清晰解释，但仍然说明：

- 当前高层触发与向下 pushdown 逻辑，会显著影响写放大结果。
- 写放大不是只由“策略名称”决定，还受模型语义和参数配置共同影响。
- 该结果既是系统现象，也是模型边界。

因此，在结题报告中应同时强调：

- 结果是有效的、可复现的。
- 结果也体现了当前简化模型与标准理论之间的偏差。

### 9.3 读放大已经更接近预期，但仍是教学型逻辑 IO

当前读放大经过修正后已能体现 LCS 读优势，但仍然采用：

- Bloom 文件页读取
- `Index Block = 1 IO`
- `Data Block = 1 IO`

这一定义非常适合教学解释，但不应误写成真实磁盘物理测试。

## 10. 结论

本轮实验表明，当前教学型 LSM-Tree 可视化与交互式模拟系统已经从“能演示的中期原型”提升为“具备结题论证价值的可验证系统”。

主要依据如下：

1. 系统在 24 组大 workload 运行中保持了 `2310 / 2310` 次查询正确。
2. STC 与 LCS 在不同 workload 与参数配置下表现出稳定且可解释的差异。
3. LCS 高层读路径优化后，读优势能够在所有实验组中稳定体现。
4. 系统不仅能展示“正确结果”，还能展示“为何会得到这样的结构与指标结果”。
5. 系统同样能够暴露简化模型与经典理论之间的偏差，这使其更适合作为教学与论文论证工具。

因此，从结题视角看，本系统已经能够支持如下两类论证：

- **正确性论证**：主流程在多轮 flush 与 compaction 后仍能保持查询正确。
- **可模拟性论证**：系统能复现不同 compaction 策略与参数配置下的读写权衡差异，并生成稳定实验数据。

如果后续继续完善前端解释面板、实验展示材料以及论文中的“模型边界说明”，则这套系统已经足以支撑结题答辩的核心技术论证。
