# LCS 语义重构规范

## 1. 目标

本次重构只调整教学型简化 LCS 的 **L1 及以上层触发条件**，不修改 STC 逻辑，不引入按字节大小建模，也不实现工业级 split / score / seek-based compaction。

目标是让 LCS 的层级容量语义更接近“层总容量按倍数扩大”的教学直觉，使其后续与 STC 的读放大、写放大比较更容易解释。

## 2. 本次保留的既有语义

1. `L0` 仍然按 `l0_compaction_trigger_tables` 触发 compaction。
2. `L0 -> L1` 仍然选择当前全部 `L0` SSTable 作为输入。
3. `L1+` 仍然采用“选择当前层一个源表 + 目标层重叠表”的简化部分 compaction。
4. 当前阶段仍然只按 **记录条数** 建模层容量，不按字节大小建模。
5. 当前阶段仍然不对 compaction 输出做 split，输出仍可能是一张较大的 SSTable。

## 3. 新的容量语义

### 3.1 基础 run 大小

教学语义中，`memtable_max_records` 作为基础 flush run 的目标记录数。

记：

- `R = memtable_max_records`
- `T0 = l0_compaction_trigger_tables`
- `M = level_size_multiplier`

### 3.2 L0 目标容量

`L0` 的目标容量定义为：

`capacity(L0) = R * T0`

解释：

- `L0` 仍按表数触发；
- 该值主要用于推导更高层的目标容量基线；
- 若每个 L0 SSTable 大致来自一次接近阈值的 flush，则 `T0` 张 L0 表合起来约为 `R * T0` 条记录。

### 3.3 L1 及以上层目标容量

对于 `level >= 1`：

`capacity(level) = R * T0 * (M ** level)`

例如：

- `memtable_max_records = 2`
- `l0_compaction_trigger_tables = 2`
- `level_size_multiplier = 2`

则：

- `capacity(L0) = 2 * 2 = 4`
- `capacity(L1) = 2 * 2 * 2^1 = 8`
- `capacity(L2) = 2 * 2 * 2^2 = 16`

## 4. 新的触发规则

### 4.1 L0

保持不变：

- 当 `len(L0_tables) >= l0_compaction_trigger_tables` 时触发 `L0 -> L1` compaction。

### 4.2 L1+

重构后改为：

- 当 `当前层总记录数 > 该层目标容量` 时触发向下一层 compaction。

即：

`sum(table.record_count for table in level_tables) > capacity(level)`

注意：

- 这里比较的是 **当前层总记录数**，不是 SSTable 数量；
- 这里比较的是 **该层目标容量**，不是下一层目标容量；
- 触发后仍然执行当前已有的简化部分 compaction 逻辑。

## 5. 本次不解决的问题

1. **不限制单个 SSTable 的最大记录数**。
   - 因此 LCS 的某个高层 SSTable 仍可能变得较大；
   - 这是当前教学简化模型允许的行为。

2. **不实现 LCS 输出 split**。
   - 即 compaction 输出不会按目标表大小切成多张 SSTable；
   - 这意味着“层总容量语义”已经统一，但“单表大小语义”仍未完全工业化。

3. **不修正字符串 key 的字典序问题**。
   - 后续实验统一使用 `k001` 这类定长 key，以避免字符串排序带来的歧义。

## 6. 对 STC / LCS 比较口径的影响

本次重构后：

1. STC 仍然体现“随着层级上升，单表大小变大”的特征；
2. LCS 仍然保留“按重叠范围做部分 compaction”的特征；
3. 但 LCS 不再仅按“表数上限”决定上层是否 compaction；
4. 因而 `level_size_multiplier` 在 LCS 中更接近“层总容量倍率”的教学语义；
5. 后续如果实验中令 `stc_trigger_tables = level_size_multiplier`，则两种策略在“层与层之间的容量增长倍率”上更容易对齐。

## 7. 预期效果

重构后，类似下面的配置：

- `memtable_max_records = 2`
- `l0_compaction_trigger_tables = 2`
- `level_size_multiplier = 2`

应满足教学预期：

- `L1` 目标容量为 `8` 条记录；
- 若 `L1` 累计记录数增长到 `12`，则应触发 `L1 -> L2` compaction；
- 不再出现“L1 总记录数远超预期容量，但因为 SSTable 数量未超限而完全不触发”的情况。
