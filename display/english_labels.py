"""English display labels only. No numerical operation or patient data."""
import re
import matplotlib.text as mt

EXACT={
'术前影像—术中任务—同通道比较':'Imaging, intraoperative tasks and matched-channel comparisons',
'影像描述运动通路；ECoG记录执行与想象中的局部变化':'Motor-pathway imaging and local ECoG responses during execution and imagery',
'术前影像':'Preoperative imaging','清醒术中任务与记录':'Awake tasks and recording',
'CST结构：3例':'CST structure: 3 patients','ECoG：4例 · 91通道 · 210事件':'ECoG: 4 patients · 91 channels · 210 events',
'脑表面来源布局':'Source brain-surface layout','五类动作 · 执行与想象':'Five actions · execution and imagery',
'三条来源条带：保留原图颜色与排列':'Three source strips: original colors and order',
'布局素材，不编码当前β或PAC数值':'Layout only; colors do not encode current β or PAC',
'执行动作':'Execute the action','想象同一动作':'Imagine the same action','同一动作，两种状态':'Same action, two states',
'任务内时间（秒）':'Within-task time (s)','基线':'Baseline','任务':'Task',
'单次任务时钟；与采集顺序分层':'Task clock, separate from acquisition order',
'同患者、同动作、同通道比较':'Match patient, action and channel',
'Δ = 想象 − 执行':'Δ = Imagery − Execution',
'人物与设备为示意；两子集仅共享P07。脑表面尚未绑定患者空间。':'People/equipment are schematic. Subsets share only P07; the surface is not bound to patient space.',
'原生FA与双侧CST':'Native FA and bilateral CST','左侧CST':'Left CST','右侧CST':'Right CST','体积（mm³）':'Volume (mm³)',
'时间（秒）':'Time (s)','时间（s）':'Time (s)','频率（Hz）':'Frequency (Hz)','功率（dB）':'Power (dB)',
'β功率（dB）':'β power (dB)','Δβ功率（dB）':'Δβ power (dB)','Δ校正PAC（10⁻⁴ MI）':'Δ corrected PAC (10⁻⁴ MI)',
'c–f：逐时点通道中位数及四分位范围；同批事件与基线，独立患者 n = 4。':'c–f: channel median and IQR; shared events and baseline; independent patients, n = 4.',
'小点：全部通道；大点：同通道差值的中位数；线段：95%条件范围。':'Small points: all channels; large points: paired medians; lines: 95% conditional ranges.',
'Δ = 想象 − 执行；每行21–24通道；20个患者–动作单元来自4名患者。':'Δ = Imagery − Execution; 21–24 channels per row; 20 patient–action units, 4 patients.',
'每患者五个动作特异Spearman ρ的中位数':'Median of five action-specific Spearman ρ values per patient',
'e  患者内的分层关联及95%条件范围':'e  Within-patient associations and 95% conditional ranges',
'a–d：坐标范围随患者变化；每通道重复参与5动作；患者为独立单位，n = 4。':'a–d: patient-specific axes; each channel recurs in 5 actions; independent patients, n = 4.',
'a  P07：已确认的条带与通道':'a  P07 strip map',
'右→左：触点1→8':'Right to left: contacts 1 to 8',
'□ 未记录；仅表示顺序，无毫米坐标':'□ Unrecorded; order only, no mm coordinates',
'b  β任务前后变化':'b  β task–baseline change','c  校正PAC':'c  Corrected PAC',
'每个色块对应一个原通道值；22个记录触点与2个空白触点完整保留。每动作每状态6事件，患者 n = 1。':'Each tile is one channel value; all 22 recorded contacts and 2 blanks retained. Six events per action/state; n = 1.',
'β变化（dB）':'β change (dB)','a  五个固定任务窗中的β阵列':'a  β arrays across five fixed task windows',
'五动作合并':'Actions pooled','每状态30事件':'30 events/state','细框：固定通道 C2':'Box: fixed channel C2',
'b  相同通道 C2 的完整时程':'b  C2 time course','任务前基线':'Baseline',
'上方窗图与下方时程共用时间分区；全部通道及五动作见图S9–S11。色标与原版一致。':'Arrays and curves share time divisions. All channels and actions: Figs. S9–S11. Original color scales retained.',
'同一通道顺序；两个未记录触点留空。五动作、状态与差值共享原色标；每状态6事件。':'Same contact order; 2 unrecorded contacts remain blank. Shared original scale across actions/states/differences; 6 events/state.',
'未记录':'No data','触点1':'Contact 1',
'横轴：时间（s）；纵轴：β变化（dB）。灰底为任务期，未记录触点留空；所有已保存时点完整显示。':'Axes: time (s) and β change (dB). Gray: task period. Unrecorded contacts blank; every saved time point shown.',
'任务期β功率（dB）':'Task β power (dB)',
'点为全部通道，灰线连接同通道条件，黑横线为通道中位数。':'Points: all channels; gray lines: within-channel pairs; black bars: channel medians.',
'原对数摘要的负值不等同于同尺度任务−基线下降；敏感性检查见图S5。':'Negative log summaries need not imply same-scale task–baseline decreases (Fig. S5).',
'相位中心（Hz）':'Phase center (Hz)','幅度中心（Hz）':'Amplitude center (Hz)',
'任务减基线PAC（10⁻⁴ MI）':'Task − baseline PAC (10⁻⁴ MI)','相对基线功率（dB）':'Baseline-relative power (dB)',
'固定来源通道；色标与图3a、b一致；每行是同一患者的两个条件。':'Fixed source channels; scale shared with Fig. 3a,b; paired conditions within each patient.',
'同一世界层面的并列对照；组织轮廓不吻合，未用于病灶或电极定位。':'Same world plane, discordant anatomy; not used for lesion or electrode localization.',
'任务−基线（dB）':'Task − baseline (dB)','a  合并动作后的同尺度β变化':'a  Same-scale β change, actions pooled',
'b  患者–动作中位数（dB）':'b  Patient–action medians (dB)','患者内动作ρ中位数':'Within-patient median action ρ',
'c  重定心β与PAC差值关联':'c  Recentered Δβ–ΔPAC','原PAC网格':'Original PAC grid','70–90 Hz网格':'70–90 Hz grid',
'同一事件、通道与PAC；仅增加同尺度基线扣除。范围为同步轮次重抽样。':'Same events, channels and PAC; baseline recentered. Ranges: synchronous complete-round resampling.',
'a  脑表面来源图':'a  Source brain surface','a′  同源局部放大':'a′  Detail from the same image',
'绿色、红色、蓝色保留来源条带含义；不是β或PAC数值。':'Green, red and blue retain source strip identities, not β or PAC values.',
'截图裁剪不构成当前患者的三维定位，也不增加空间分辨率。':'Cropping does not establish patient-space coordinates or improve spatial resolution.',
'横轴：时间（s）；纵轴：频率（Hz）。沿用原4–90 Hz数组；每状态30事件，原共享色标。':'Axes: time (s) and frequency (Hz). Original 4–90 Hz arrays; 30 events/state and original shared scale.',
'P07 · β阵列的五窗逐帧展示':'P07 · five-window β-array sequence',
'22个记录触点与2个空白；五动作共享固定色标。':'22 recorded contacts and 2 blanks; fixed scale across five actions.',
'仅播放原五个1秒窗；无插帧，无动态PAC。':'Original five 1 s windows only; no interpolation or dynamic PAC.'
}
PARTS=[('想象−执行','Imagery−Exec.'),('校正PAC','Corrected PAC'),('β功率','β power'),
('左指','L finger'),('右指','R finger'),('左拳','L fist'),('右拳','R fist'),('唇部','Lips'),
('执行','Execution'),('想象','Imagery'),('轴位','Axial'),('冠状位','Coronal'),('来源T1','Source T1'),
('：五个固定1秒窗中的β阵列',': β arrays across five fixed 1 s windows'),('：全部22通道时程',': all 22 channel time courses'),
('：全通道时频反应',': all-channel time–frequency responses'),('五动作合并','Actions pooled'),('当前任务窗：','Task window: '),
('条带','Strip '),('个配对',' pairs'),('全部','All '),('通道',' channels')]
def translate(s):
    s=str(s)
    if s in EXACT:return EXACT[s]
    for a,b in PARTS:s=s.replace(a,b)
    return s.replace('（',' (').replace('）',')').replace('：',': ')
_set_text=mt.Text.set_text
def install():
    def text(self,s): return _set_text(self,translate(s))
    mt.Text.set_text=text
def fit_labels(fig):
    """Only shrink long figure footnotes to fit the canvas, never numeric axes."""
    fig.canvas.draw();renderer=fig.canvas.get_renderer();W=fig.bbox.width
    for t in fig.texts:
        bb=t.get_window_extent(renderer)
        if bb.x1>W-8 and bb.width>0:
            size=max(7,t.get_fontsize()*(W-10-bb.x0)/bb.width)
            t.set_fontsize(size)
    fig.canvas.draw()
