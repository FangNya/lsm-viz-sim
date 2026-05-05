# 读放大与写放大统计口径规范

## 1. 目的

本文档用于固定当前项目中读放大与写放大的统计口径，作为后续代码修改、实验解释和论文写作的统一依据。

本规范遵循以下原则：

- 面向教学型 LSM-Tree 模拟系统，而非工业级数据库精确测量工具
- 指标定义必须清晰、可复现、可解释
- 指标口径要服务于论文和答辩的叙述，而不是被当前 JSONL 模拟实现细节绑死

## 2. 总体选择

当前读放大与写放大的统计采用以下路线：

- 写放大：采用“磁盘实际写入字节 / 用户逻辑写入字节”
- 读放大：当前阶段只统计“用户查询读放大”
- 用户查询读放大采用“教学型逻辑 IO 估算模型”
- 使用 `PAGE_SIZE = 4096` 字节作为一次逻辑页读取大小

说明：

- 当前不统计“系统总读 IO”对应的放大系数
- 当前不将 Compaction 背景读混入“用户查询读放大”
- 当前读放大中的 `Index Block` 和 `Data Block` 属于教学型逻辑抽象，不要求当前 JSONL 文件真实实现独立块结构

## 3. 写放大定义

## 3.1 公式

\[
\text{Write Amplification} =
\frac{\text{实际磁盘写入总字节数}}{\text{用户逻辑写入字节数}}
\]

该值应满足：

- 理想情况接近 `1`
- 系统发生额外落盘、重写、Compaction 越多，值越大

## 3.2 分母：用户逻辑写入字节数

用户逻辑写入字节数定义为所有 `put(key, value)` 的逻辑输入总字节数之和。

单条写入的逻辑字节数定义为：

\[
\text{logical\_write\_bytes(record)} =
\text{len(key.encode('utf-8'))} +
\text{len(value.encode('utf-8'))}
\]

说明：

- 不包含 `seq`
- 不包含 `timestamp`
- 不包含 `op`
- 不包含 Python 对象额外内存开销

原因：

- 分母应描述“用户本来想写入的数据量”
- 系统内部元数据不应进入逻辑写入量

## 3.3 分子：实际磁盘写入总字节数

实际磁盘写入总字节数定义为所有持久化文件写入字节的累计和。

应计入以下部分：

- `WAL` 追加写字节数
- Flush 生成的 `SSTable data file` 字节数
- Flush 生成的 `SSTable meta file` 字节数
- Flush 生成的 `Bloom file` 字节数
- Compaction 生成的新 `SSTable data file` 字节数
- Compaction 生成的新 `SSTable meta file` 字节数
- Compaction 生成的新 `Bloom file` 字节数

不计入以下部分：

- MemTable 内存写入
- Python 对象分配
- Trace/metrics 导出文件

## 3.4 推荐统计字段

建议后续内部或导出层使用以下字段：

- `logical_write_bytes_total`
- `wal_write_bytes_total`
- `flush_data_write_bytes_total`
- `flush_meta_write_bytes_total`
- `flush_bloom_write_bytes_total`
- `compaction_data_write_bytes_total`
- `compaction_meta_write_bytes_total`
- `compaction_bloom_write_bytes_total`
- `actual_disk_write_bytes_total`
- `write_amplification`

其中：

\[
\text{actual\_disk\_write\_bytes\_total}
=
\text{wal}
+ \text{flush data}
+ \text{flush meta}
+ \text{flush bloom}
+ \text{compaction data}
+ \text{compaction meta}
+ \text{compaction bloom}
\]

## 4. 用户查询读放大定义

## 4.1 公式

单次查询读放大定义为：

\[
\text{User Query Read Amplification (per query)}
=
\frac{\text{本次查询触发的总逻辑 IO 次数}}{1}
\]

由于理想情况设定为“1 次 IO 就拿到数据”，因此该值等于：

\[
\text{User Query Read Amplification (per query)}
=
\text{本次查询触发的总逻辑 IO 次数}
\]

系统运行期的聚合读放大定义为：

\[
\text{User Query Read Amplification}
=
\frac{\text{所有 get 查询触发的总逻辑 IO 次数}}{\text{get 总次数}}
\]

## 4.2 PAGE_SIZE

定义：

- `PAGE_SIZE = 4096` 字节

用途：

- 表示一次逻辑磁盘读取可加载的页大小
- 用于将 Bloom 文件大小换算为逻辑 IO 次数

## 4.3 当前采用的教学型查询模型

本项目当前采用路线 B，即采用更接近标准 SSTable 查询流程的教学型逻辑模型：

1. 先检查 Bloom Filter
2. 若 Bloom 判定可能存在，再读取 Index Block
3. 再读取 Data Block

说明：

- 当前代码中的 JSONL 文件并未真实实现独立 `Index Block`
- 当前代码中的 `find_key()` 也不是基于块索引 seek，而是顺序扫描
- 但为了使指标更符合 SSTable 教学模型，读放大统计中仍引入逻辑上的 `Index Block` 与 `Data Block`

这意味着：

- 当前读放大是“教学型逻辑 IO 估算”
- 不是底层物理文件访问的精确统计

## 4.4 单个 SSTable 的逻辑 IO 计算规则

### 情况一：MemTable 命中

若 `get(key)` 在 MemTable 命中：

\[
\text{query\_io} = 0
\]

原因：

- 不发生磁盘读取

### 情况二：访问某个 SSTable，Bloom Filter 判定不存在

设 Bloom 文件大小为 `bloom_size_bytes`，则：

\[
\text{bloom\_io} =
\left\lceil \frac{\text{bloom\_size\_bytes}}{\text{PAGE\_SIZE}} \right\rceil
\]

由于 Bloom 已判定该表中一定不存在该 key，因此：

- `index_io = 0`
- `data_io = 0`

总 IO 为：

\[
\text{sstable\_query\_io} =
\left\lceil \frac{\text{bloom\_size\_bytes}}{\text{PAGE\_SIZE}} \right\rceil
\]

### 情况三：访问某个 SSTable，Bloom Filter 判定可能存在

Bloom 仍需先加载：

\[
\text{bloom\_io} =
\left\lceil \frac{\text{bloom\_size\_bytes}}{\text{PAGE\_SIZE}} \right\rceil
\]

之后按教学型逻辑模型增加：

- `index_io = 1`
- `data_io = 1`

因此：

\[
\text{sstable\_query\_io} =
\left\lceil \frac{\text{bloom\_size\_bytes}}{\text{PAGE\_SIZE}} \right\rceil
+ 1
+ 1
\]

### 情况四：某个 SSTable 没有 Bloom 文件

若后续保留“无 Bloom 也能查”的兼容逻辑，则该表查询代价可定义为：

- `bloom_io = 0`
- `index_io = 1`
- `data_io = 1`

即：

\[
\text{sstable\_query\_io} = 2
\]

## 4.5 单次查询总 IO

设本次查询访问了多个 SSTable，则单次查询总逻辑 IO 为所有被检查表的逻辑 IO 累加：

\[
\text{query\_io\_total}
=
\sum \text{sstable\_query\_io}
\]

最终单次查询读放大：

\[
\text{User Query Read Amplification (per query)}
=
\text{query\_io\_total}
\]

## 5. Index Block 与 Data Block 的解释口径

## 5.1 为什么要算 Index Block

虽然当前 JSONL 文件没有独立实现索引块，但在教学型 LSM-Tree 中，引入 `Index Block` 有三点价值：

- 更接近标准 SSTable 查询过程
- 更容易解释“Bloom 过滤后为什么不需要整表扫描”
- 更适合作为答辩与论文中的机制说明

因此，本项目中 `Index Block = 1 IO` 应被视为：

- 教学型逻辑抽象
- 非当前文件格式的物理真实结构

## 5.2 为什么 Data Block 记为 1 IO

在标准 SSTable 模型下：

- Index Block 会帮助定位目标 key 所在的数据块
- 读取该数据块通常可视为一次逻辑页读取

因此，在本项目的教学型口径中：

- 若 Bloom 判定可能存在，则将 `Data Block` 记为 `1 IO`

这并不表示当前 JSONL 文件真实只读了一页，而表示：

- 从教学型抽象上，最终为取到目标数据而需要访问一个目标数据块

## 5.3 需要在论文和文档中明确的说明

后续论文、README 和实验说明中应明确写出：

- 当前 `Bloom IO` 与真实文件存在对应关系
- 当前 `Index Block` 与 `Data Block` 属于逻辑抽象
- 当前读放大用于教学型比较，不用于替代真实块存储引擎的物理测量

## 6. 暂不实现的指标

以下指标当前阶段暂不纳入放大公式：

- `System Total Read IO`
- `Compaction Read Amplification`
- `Background Read Pressure`

这些指标后续如需补充，应单独统计，不混入“用户查询读放大”。

## 7. 对当前代码改造的含义

若后续按本规范改造，意味着：

### 写放大

- 不再沿用当前的 `simulated_io_writes / total_puts`
- 改为真正按持久化文件新增字节累计

### 读放大

- 不再沿用当前的 `simulated_io_reads / total_gets`
- 改为只统计 `get()` 过程中的查询逻辑 IO
- `Compaction` 读不再进入该指标

### 指标解释

- 写放大更贴近“磁盘写放大”
- 读放大更贴近“教学型 SSTable 查询路径的逻辑 IO 开销”

## 8. 最终推荐采用的字段

建议最终在聚合指标中使用以下字段：

- `logical_write_bytes_total`
- `actual_disk_write_bytes_total`
- `write_amplification`
- `user_query_read_io_total`
- `user_query_read_amplification`

如需保留兼容或做更完整的观测，可继续增加：

- `wal_write_bytes_total`
- `flush_write_bytes_total`
- `compaction_write_bytes_total`
- `bloom_read_io_total`
- `index_read_io_total`
- `data_block_read_io_total`

## 9. 推荐论文表述

可直接采用如下表达：

“本系统中的写放大定义为实际磁盘写入总字节数与用户逻辑写入字节数之比，其中实际磁盘写入包括 WAL、Flush 产生的 SSTable 文件及其元数据与 Bloom 文件，以及 Compaction 过程中生成的新文件。该定义用于刻画教学型 LSM-Tree 模拟系统中因持久化与归并所带来的额外写入成本。”

“本系统中的用户查询读放大定义为单次 `get` 查询触发的总逻辑 IO 次数。为增强可解释性，系统采用基于 `PAGE_SIZE = 4KB` 的教学型逻辑估算模型：Bloom Filter 按文件页数估算读取代价，而 Index Block 与 Data Block 分别按 1 次逻辑 IO 计入。需要说明的是，后两者属于教学型抽象，并不要求当前 JSONL 模拟实现物理具备独立块结构。”

## 10. 结论

本规范确定了后续实现的统一方向：

- 写放大走“磁盘字节口径”
- 读放大走“用户查询逻辑 IO 口径”
- Bloom 与当前代码真实行为对齐
- Index/Data Block 采用教学型逻辑抽象

后续代码修改、实验重跑和论文写作应统一遵循本规范。
