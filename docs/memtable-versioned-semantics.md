# MemTable 多版本语义重构规范

## 1. 目标

本次重构将教学型模拟器中的 MemTable 从“同 key 直接覆盖”调整为“同 key 多版本共存”，使系统的写入、flush、查询与 compaction 语义更接近 LSM-Tree 的版本流动过程。

本次重构的目标不是实现工业级 skiplist 或内部键编码，而是在当前教学型框架下建立一致的多版本语义。

## 2. 重构后的核心语义

### 2.1 MemTable 保存多版本

对于相同 `user_key` 的多次 `put`：

- 不再在 MemTable 内直接覆盖旧值。
- 每次 `put` 都作为一个新的 `Record(key, value, seq)` 版本追加到 MemTable。
- MemTable 中允许同一个 `key` 对应多个版本。

示例：

1. `put(k, v1, seq=1)`
2. `put(k, v2, seq=2)`

重构后，MemTable 中同时存在：

- `(k, v1, seq=1)`
- `(k, v2, seq=2)`

### 2.2 MemTable 查询返回最新版本

`MemTable.get(key)` 必须返回该 `key` 在 MemTable 中 `seq` 最大的版本值。

即：

- 若存在多个版本，返回最新版本。
- 若不存在该 `key`，返回 `None`。

### 2.3 Flush 保留多版本

`flush_memtable()` 不再在 flush 前对同 key 做覆盖去重。

Flush 时应将 MemTable 中所有版本都落到 SSTable。

### 2.4 Flush 排序规则

为了保证同一 SSTable 中同 key 查询时能优先命中最新版本，flush 输出记录顺序定义为：

1. 先按 `key` 升序
2. 同一 `key` 内按 `seq` 降序

示例：

- `(a, old, seq=1)`
- `(a, new, seq=3)`
- `(b, x, seq=2)`

Flush 输出顺序应为：

1. `(a, new, seq=3)`
2. `(a, old, seq=1)`
3. `(b, x, seq=2)`

## 3. SSTable 查询语义

### 3.1 同一 SSTable 内的多版本

当前阶段允许 flush 生成的单个 SSTable 中包含同 key 的多个版本。

### 3.2 `find_key()` 返回最新版本

在同一 SSTable 内查找某个 key 时，应返回该表中该 key 的最新版本。

当前教学型最小实现允许依赖“flush 已按 `key asc + seq desc` 排序”的前提：

- `find_key()` 遇到该 key 的第一条记录即可返回。

## 4. Compaction 语义

Compaction 仍保持现有规则：

- 多个输入表合并时，对同 key 保留 `seq` 更大的版本。
- 旧版本在 compaction 阶段清理。

因此，版本生命周期变为：

1. WAL 追加全部版本
2. MemTable 保留全部版本
3. Flush 后 SSTable 保留全部版本
4. Compaction 再做跨表版本归并

## 5. 指标口径变化

### 5.1 `memtable_size_records`

重构后，`memtable_size_records` 表示：

- MemTable 中的版本条数
- 不再表示“唯一 key 数”

因此：

- 连续两次写同一个 key，会让 `memtable_size_records` 增加 2，而不是保持 1。

### 5.2 SSTable `record_count`

重构后，SSTable 的 `record_count` 表示：

- 落盘记录总条数
- 允许包含同 key 的多个版本

## 6. 本次不做的内容

1. 不实现 `user_key + seq` 的工业级内部键编码。
2. 不将 MemTable 改为 skiplist，仍保持教学型简化结构。
3. 不实现 tombstone / delete 语义。
4. 不修改 compaction 的基本去重规则。
5. 不重构查询 IO 指标口径。

## 7. 对外说明建议

本次重构后，应将系统定位表述为：

- MemTable 为教学型简化实现；
- 但版本语义已经从“覆盖式缓存”调整为“多版本暂存 + compaction 清理旧版本”；
- 因而更适合用于解释 LSM-Tree 中 overwrite、flush、compaction 的真实逻辑关系。
