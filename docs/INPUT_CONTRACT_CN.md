# 一次性本地源数据适配合同

**由原工作区中的Codex完成，作者不需要手动转换。** 标准化不是重新发明数据；必须按原事件、通道与数组键对应，不按数据相似度猜配。

## 1. 运行配置

参考`configs/config_template.json`。所有相对路径以该配置文件所在目录为基准；可使用本地绝对路径，但只能保存在被忽略的`local/`中。公共代码不硬编码作者的Mac路径。

每患者当前支持一份稳定通道集合的记录；同患者多记录不能改名伪装为独立患者。多记录设计需明确增加记录层，不能自动拼接。当前数据为每轮5动作×2条件，各1事件；不完整轮次不会被静默补齐或剔除。

## 2. 每记录NPZ：所有数组都有明确轴

|键|形状|含义|
|---|---|---|
|`beta_db`|E,C,T|源13–30 Hz频率均值dB逐事件时程，尚未跨事件/时间聚合|
|`times_s`|T|单调递增的相对时间轴|
|`pac_task_mi`|E,C,Wt,A,P|已按每窗/相位频率计算的未作task−baseline的MI|
|`pac_baseline_mi`|E,C,Wb,A,P|对应基线MI，不能拿已经相减的数据当此字段|
|`event_ids`|E，Unicode|确切事件键，与元数据逐行对应|
|`channel_ids`|C，Unicode|确切通道键，与元数据逐行对应|
|`amplitude_power_db`（可选）|E,C|既有同窗70–90 Hz事件级功率摘要；计算定义须在元数据声明|
|`bootstrap_indices`（可选）|B,R，整数|按元数据rounds次序编码的既有共同轮次抽样索引；尽量复用V02实际索引|

E=事件数，C=通道数，T=时间点，Wt/Wb=任务/基线窗，A/P=幅度/相位格点，R=完整轮次数，B=重抽样次数。

不要把4770行单事件PAC95表作为上述PAC数组输入。不要由旧散点图反推数值。确有源数组维度不同，适配器显式转置，并保存原轴含义与转换说明。

若原MI已存为`task_window_median_minus_baseline`，不能把它补成虚构的task/base窗数组；应从源窗数组找回，或对本包接口增加明确的“已相减格点数组”分支并测试等价性。禁止为通过输入检测而伪造窗口。

## 3. 元数据JSON

```json
{
  "schema": "ncs-arrays-1",
  "dataset_kind": "clinical",
  "subject": "P04",
  "record": "REC_P04",
  "event_channel_alignment_reviewed": true,
  "source_array_provenance_reviewed": true,
  "mi_normalization": "per_window_per_phase_bin_means",
  "beta_unit": "dB",
  "mi_unit": "dimensionless",
  "task_windows": 6,
  "baseline_windows": 1,
  "conditions": ["Move", "Imagine"],
  "actions": ["left_finger", "right_finger", "left_fist", "right_fist", "lip"],
  "channels": ["C1", "C2"],
  "rounds": ["R01", "R02"],
  "phase_bands_hz": [[13,17],[15,19],[17,21],[19,23],[21,25],[23,27],[25,29],[27,31]],
  "amplitude_bands_hz": [[70,80],[80,90],[90,98],[102,110],[110,120],[120,130],[130,140],[140,148]],
  "events": []
}
```

上述只是字段示例，**不是可冒用的真实患者配置**。必须填完整事件表和真实通道列表。每个事件包含`event_id, round_id, action, condition`。布尔声明只能在查过实际来源后填写，不等于伦理或定位认证。

可选功率字段对应：
```json
{"amplitude_power_unit":"dB", "amplitude_power_aggregation":"event_scalar_median_within_action_condition"}
```

记录采样率、预处理、硬件限制、事件时基及source token保留在本地数据字典；当前核心不会仅因元数据填了“已校正”就断言硬件/生理有效。

## 4. 结构NPZ

必须包含`fa, mask_left, mask_right, fa_affine, left_affine, right_affine, spatial_unit`。每幅原始图像/掩膜的仿射单独读取，**不能把FA仿射复制给其他文件以便通过检测**。可选`md,rd,ad`各自配有同名`*_affine`。空间单位明确为mm，MD/RD/AD输入单位为mm²/s。

掩膜为实际二值掩膜，不通过新阈值改变束大小；保留左右交叠。代码核对数值网格和采样口径，不从头信息宣称解剖配准成功。

## 5. 可选真实空间配对CSV

列名：
```text
subject,record,action,contrast,location_id,space_id,task_evidence_id,location_evidence_id,pairing_status,image_effect,beta_delta,pac_delta
```

`pairing_status=source_verified`必须对应实际证据。不同位置/动作的image_effect必须采用可比的明确对比定义。CSV不得混入未完成候选、不得将缺失填0。没有资料时在配置保留`spatial_pairs:null`，其他数值分析仍可运行。

这里只作同患者、同动作、同对比、同空间下的描述性关联，不把位置当独立患者，不执行忽略空间自相关的显著性检验，也不因为两项rho符号不同就宣称二者显著不同。

## 6. v1.0显式源窗中位接口

当上游实际缓存已按每事件的观察窗取中位数，元数据设置：

```json
{"pac_input_form":"source_window_medians", "source_window_aggregation":"median_over_windows_before_event_aggregation", "task_windows":6, "baseline_windows":1}
```

NPZ提供 `pac_task_window_median` 与 `pac_baseline_window_median`，均为E,C,A,P，尚未相减。窗数声明是源处理信息，不是假造的W轴；来源代码与窗口起点必须核实。程序检查形状、频率、单位、有限值及MI范围[0,1]，再直接相减。不得把已相减的格点当未相减MI。原 `window_arrays` 接口保留，人工测试确认两个接口对真实等价表示给出相同事件对比及统计量。
