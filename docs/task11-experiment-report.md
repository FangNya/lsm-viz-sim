# Task 11 实验设计与结果分析

## 1. 实验目的

为了验证教学型 LSM-Tree 模拟系统在不同 compaction 策略下的行为差异，本文围绕已经实现的两种策略，即 Size-Tiered Compaction（STC）和教学型简化 Leveled Compaction（LCS），设计可复现实验负载，对系统在写入、重叠键范围和热点更新场景下的运行结果进行对比分析。

本阶段实验重点不是追求工业级 benchmark 精度，而是通过可控制、可复现的 workload 与参数组合，观察以下指标在不同策略下的变化趋势：

- `flush_count`
- `compaction_count`
- `sstable_count_by_level`
- `read_amplification`
- `write_amplification`

通过这些指标，可以从教学演示角度解释两种 compaction 策略在文件组织方式、压缩频率和读写代价上的差异。

## 2. 实验设计

### 2.1 实验环境

实验基于本项目已实现的单机版 LSM-Tree 教学模拟器运行。系统已经支持以下核心流程：

- WAL 追加写
- MemTable 写入与阈值触发 flush
- Level 0 SSTable 落盘
- Bloom Filter
- STC 与教学型简化 LCS
- Metrics 与 Trace 导出

实验脚本位于 `experiments/run_workloads.py`，所有结果统一输出到 `experiments/output/summary.csv` 和对应目录下的 JSON/CSV 文件中。

### 2.2 实验变量

实验从两个维度构造对比：

1. workload 维度  
   通过不同访问模式模拟不同的系统压力。

2. profile 维度  
   通过不同参数组合调节 flush 与 compaction 的触发频率。

本次报告选取以下三组最有代表性的 workload：

- `write_heavy_long`：长序列写入负载，用于持续制造 flush 和多轮 compaction。
- `range_overlap_stress`：重叠 key range 写入负载，用于观察 LCS 对重叠范围合并的响应。
- `overwrite_hotspot`：热点 key 重复覆盖负载，用于观察重复更新场景下两种策略的差异。

本次报告重点选用以下两组 profile：

- `aggressive_compaction`：减小 memtable 容量并降低 compaction 触发阈值，使 compaction 被更频繁地触发。
- `overlap_pressure`：进一步增大重叠范围压力，突出 LCS 在重叠 SSTable 合并中的行为特征。

### 2.3 指标定义

- `flush_count`：MemTable 被刷写到磁盘生成 SSTable 的次数。
- `compaction_count`：compaction 实际执行次数。
- `sstable_count_by_level`：各层当前保留的 SSTable 数量分布。
- `read_amplification`：模拟统计意义上的读放大，用于反映查询过程中访问表与层的代价。
- `write_amplification`：模拟统计意义上的写放大，用于反映 compaction 带来的额外写入开销。

需要说明的是，本系统为教学型模拟器，读放大和写放大用于描述趋势和相对差异，不等价于工业级数据库中的精确物理统计值。

## 3. 实验结果与分析

### 3.1 实验一：长写入负载下的策略对比

该实验选择 `write_heavy_long + aggressive_compaction` 组合作为对比对象。该组合的特点是操作次数较多，且参数设置会频繁触发 flush 和 compaction，因此能够较好地放大两种策略在层级组织方式上的差异。

| Workload | Profile | Strategy | Operation Count | Flush Count | Compaction Count | SSTable Count By Level | Read Amplification | Write Amplification |
|---|---|---:|---:|---:|---:|---|---:|---:|
| write_heavy_long | aggressive_compaction | STC | 48 | 12 | 10 | `{"level_0": 0, "level_1": 0, "level_2": 1, "level_3": 1}` | 0.0000 | 6.5833 |
| write_heavy_long | aggressive_compaction | LCS | 48 | 12 | 6 | `{"level_0": 0, "level_1": 6}` | 0.0000 | 4.7500 |

分析如下：

- 在该长写入负载下，两种策略都发生了 `12` 次 flush，说明输入数据规模和内存阈值设置足以持续触发落盘。
- `STC` 产生了 `10` 次 compaction，而 `LCS` 仅产生了 `6` 次 compaction，表明在该教学实现下，`STC` 更倾向于不断对同层文件进行归并并向更高层推进。
- 从层级分布来看，`STC` 最终将数据推进到了 `level_2` 和 `level_3`，而 `LCS` 主要保留在 `level_1`。这说明两种策略在文件组织思路上存在明显区别：`STC` 更容易形成向高层持续滚动的层级结构，`LCS` 则更强调在较低层内进行受控整理。
- `STC` 的写放大达到 `6.5833`，明显高于 `LCS` 的 `4.7500`，说明在长写入负载下，`STC` 需要更多额外写入来完成文件归并。

因此，该实验可以说明：在持续写入场景下，`STC` compaction 更频繁、层级推进更深，但写放大也更高；`LCS` compaction 次数较少，写放大更低。

### 3.2 实验二：重叠范围负载下的策略对比

该实验选择 `range_overlap_stress + overlap_pressure` 组合作为对比对象。该 workload 会刻意生成多组具有重叠 key range 的 SSTable，从而更容易触发 LCS 对重叠范围的合并行为。

| Workload | Profile | Strategy | Operation Count | Flush Count | Compaction Count | SSTable Count By Level | Read Amplification | Write Amplification |
|---|---|---:|---:|---:|---:|---|---:|---:|
| range_overlap_stress | overlap_pressure | STC | 27 | 8 | 2 | `{"level_0": 2, "level_1": 2}` | 5.3333 | 4.5833 |
| range_overlap_stress | overlap_pressure | LCS | 27 | 8 | 4 | `{"level_0": 0, "level_1": 1}` | 5.3333 | 5.9167 |

分析如下：

- 两种策略在该实验中都发生了 `8` 次 flush，说明输入规模一致，基础写入压力相同。
- `LCS` 的 compaction 次数为 `4`，高于 `STC` 的 `2`，说明面对重叠 key range 时，`LCS` 会更积极地对相交范围的文件进行合并。
- 从最终层级状态来看，`STC` 仍保留了 `2` 个 `level_0` 文件和 `2` 个 `level_1` 文件，而 `LCS` 最终压缩为 `level_1` 中的 `1` 个文件，层级结构明显更紧凑。
- 该组实验中两者的读放大相同，均为 `5.3333`，但 `LCS` 的写放大更高，达到 `5.9167`。这说明为了减少层间重叠和收敛文件数量，`LCS` 在该场景下付出了更多额外写入代价。

因此，该实验可以说明：在 key range 重叠明显的场景中，`LCS` 更能体现“按重叠范围进行整理”的策略特征，虽然 compaction 更积极、最终层级更紧凑，但写放大也会随之上升。

### 3.3 实验三：热点覆盖负载下的补充对比

该实验选择 `overwrite_hotspot + aggressive_compaction` 组合作为补充说明，用于观察热点 key 被频繁覆盖时，两种策略在重复更新场景中的差异。

| Workload | Profile | Strategy | Operation Count | Flush Count | Compaction Count | SSTable Count By Level | Read Amplification | Write Amplification |
|---|---|---:|---:|---:|---:|---|---:|---:|
| overwrite_hotspot | aggressive_compaction | STC | 32 | 7 | 4 | `{"level_0": 1, "level_1": 1, "level_2": 1}` | 5.0000 | 4.9643 |
| overwrite_hotspot | aggressive_compaction | LCS | 32 | 7 | 3 | `{"level_0": 1, "level_1": 1}` | 4.7500 | 4.8929 |

分析如下：

- 两种策略均发生了 `7` 次 flush，说明工作负载规模一致。
- `STC` 的 compaction 次数略高于 `LCS`，并且最终数据推进到了 `level_2`。
- `LCS` 的读放大和写放大都略低于 `STC`，说明在热点覆盖场景下，`LCS` 仍然能够通过更受控的层级组织降低一部分额外代价。

该实验虽然不如前两组对比那样强烈，但可以作为补充证据，表明两种策略的差异不仅存在于纯写入场景，也会体现在热点更新场景中。

## 4. 实验结论

综合以上实验结果，可以得到以下结论：

1. 在温和负载下，`STC` 与 `LCS` 的差异并不明显；只有在较高写入压力、较小 memtable 阈值以及更积极的 compaction 参数下，两种策略的行为差异才会被充分放大。

2. 在长写入负载下，`STC` 往往触发更多 compaction，并将数据持续向更高层推进，因此更容易产生较高的写放大；相比之下，`LCS` 的 compaction 次数较少，写放大更低。

3. 在重叠 key range 场景下，`LCS` 更能体现其按范围合并的策略特点。它会更积极地整理重叠 SSTable，使最终层级状态更加紧凑，但通常需要付出更高的写放大代价。

4. 在热点 key 覆盖场景下，`LCS` 相比 `STC` 仍表现出一定的读写开销优势，但整体差异弱于重叠范围场景。

5. 从中期答辩展示的角度看，最适合用于说明两种策略差异的实验组合为：
   - `write_heavy_long + aggressive_compaction`
   - `range_overlap_stress + overlap_pressure`

这两组实验分别对应“持续写入压力”和“重叠范围整理”两类典型情形，能够较直观地展示教学型 LSM-Tree 系统中 STC 与 LCS 的行为差异。

## 5. 小结

本次实验基于教学型 LSM-Tree 模拟器完成，虽然没有实现工业级存储系统中的全部复杂机制，但已经能够通过可配置参数、可复现实验负载和稳定导出指标，对不同 compaction 策略的运行特征进行清晰展示。这为中期答辩中的系统演示、实验说明和后续功能扩展提供了较好的基础。
