#!/usr/bin/env python3
"""Generate the PDF algorithm design document (Chinese) summarizing the
full skew pre-compensation development: rounds 1-5."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                PageBreak, Table, TableStyle, Image)

pdfmetrics.registerFont(TTFont(
    "WQY", "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", subfontIndex=0))

INK = colors.HexColor("#1a2733")
ACC = colors.HexColor("#2b5aa0")
GRID = colors.HexColor("#b8c4d0")
HDRBG = colors.HexColor("#e8eef6")
ALT = colors.HexColor("#f4f7fb")

S = {}
S["title"] = ParagraphStyle("title", fontName="WQY", fontSize=20, leading=28,
                            alignment=TA_CENTER, textColor=INK)
S["subtitle"] = ParagraphStyle("subtitle", fontName="WQY", fontSize=12,
                               leading=18, alignment=TA_CENTER,
                               textColor=colors.HexColor("#51606e"))
S["h1"] = ParagraphStyle("h1", fontName="WQY", fontSize=14.5, leading=20,
                         spaceBefore=16, spaceAfter=8, textColor=ACC)
S["h2"] = ParagraphStyle("h2", fontName="WQY", fontSize=12, leading=17,
                         spaceBefore=10, spaceAfter=5, textColor=INK)
S["body"] = ParagraphStyle("body", fontName="WQY", fontSize=10.2,
                           leading=16.5, spaceAfter=6, alignment=TA_JUSTIFY,
                           textColor=INK, wordWrap="CJK")
S["formula"] = ParagraphStyle("formula", fontName="WQY", fontSize=10.2,
                              leading=16, spaceBefore=4, spaceAfter=8,
                              alignment=TA_CENTER, textColor=INK)
S["cap"] = ParagraphStyle("cap", fontName="WQY", fontSize=9, leading=13,
                          alignment=TA_CENTER, spaceBefore=3, spaceAfter=10,
                          textColor=colors.HexColor("#51606e"))
S["cell"] = ParagraphStyle("cell", fontName="WQY", fontSize=9, leading=12.5,
                           textColor=INK, wordWrap="CJK")
S["cellc"] = ParagraphStyle("cellc", fontName="WQY", fontSize=9,
                            leading=12.5, alignment=TA_CENTER, textColor=INK)
S["hdr"] = ParagraphStyle("hdr", fontName="WQY", fontSize=9, leading=12.5,
                          alignment=TA_CENTER, textColor=ACC)


def tbl(data, widths, header=True):
    rows = [[Paragraph(c, S["hdr"] if (header and i == 0) else
                       (S["cell"] if j == 0 else S["cellc"]))
             for j, c in enumerate(r)] for i, r in enumerate(data)]
    t = Table(rows, colWidths=widths, repeatRows=1 if header else 0)
    style = [("GRID", (0, 0), (-1, -1), 0.6, GRID),
             ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("TOPPADDING", (0, 0), (-1, -1), 4),
             ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
             ("LEFTPADDING", (0, 0), (-1, -1), 6),
             ("RIGHTPADDING", (0, 0), (-1, -1), 6)]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), HDRBG))
        for r in range(2, len(data), 2):
            style.append(("BACKGROUND", (0, r), (-1, r), ALT))
    t.setStyle(TableStyle(style))
    return t


def p(txt):
    return Paragraph(txt, S["body"])


def h1(txt):
    return Paragraph(txt, S["h1"])


def h2(txt):
    return Paragraph(txt, S["h2"])


def formula(txt):
    return Paragraph(txt, S["formula"])


def cap(txt):
    return Paragraph(txt, S["cap"])


def img(path, w):
    from PIL import Image as PILImage
    iw, ih = PILImage.open(path).size
    return Image(path, width=w, height=w * ih / iw)


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("WQY", 8)
    canvas.setFillColor(colors.HexColor("#8a97a5"))
    canvas.drawString(2 * cm, 1.2 * cm,
                      "236G PAM4 Skew 预补偿算法方案设计文档  v1.0")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"第 {doc.page} 页")
    canvas.restoreState()


doc = SimpleDocTemplate("skew_precomp_design_doc.pdf", pagesize=A4,
                        leftMargin=2 * cm, rightMargin=2 * cm,
                        topMargin=2 * cm, bottomMargin=2 * cm,
                        title="236G PAM4 Skew 预补偿算法方案设计文档",
                        author="DSP Algorithm Team")
E = []

# ================= cover =================
E.append(Spacer(1, 4.5 * cm))
E.append(Paragraph("236 GBaud PAM4 发射端 Skew 预补偿", S["title"]))
E.append(Paragraph("算法方案设计文档", S["title"]))
E.append(Spacer(1, 1.2 * cm))
E.append(Paragraph("低复杂度 / 低功耗 分数延时补偿算法的推导、优化与硬件实现方案",
                   S["subtitle"]))
E.append(Spacer(1, 5 * cm))
E.append(Paragraph("版本：v1.0　　日期：2026-08-06", S["subtitle"]))
E.append(Paragraph("仓库分支：claude/pam4-skew-precompensation-ljov42　"
                   "目录：skew-precomp/", S["subtitle"]))
E.append(PageBreak())

# ================= 1. problem =================
E.append(h1("1　问题定义与设计指标"))
E.append(p("发射端多通道（如 I/Q 或 X/Y 极化的各电学 lane）之间存在皮秒量级的时延失配"
           "（skew），需要在数字域对信号做分数延时预补偿。本项目在给定采样率与精度约束"
           "下，寻找实现复杂度最低的补偿算法，并随需求演进（在线可调、功耗优先、范围扩展）"
           "持续优化。系统参数如下："))
E.append(tbl([
    ["参数", "取值", "说明"],
    ["调制格式 / 波特率", "PAM4，236 GBaud", ""],
    ["采样率 F<sub>s</sub>", "236 × 1.125 = 265.5 GSa/s", "1.125 sps = 9/8"],
    ["采样周期 T<sub>s</sub>", "3.7665 ps", ""],
    ["成形滚降 β", "0.05 ~ 0.125", "1.125 sps 下 β 上限为 0.125"],
    ["skew 需求（演进）", "0.35 ps 固定 → 在线可调 → ±1 ps",
     "0.35 ps 对应 μ = 0.093 采样"],
    ["精度指标", "MSE &lt; -25 dB", "相对理想补偿（数百抽头 FIR）"],
], [4.2 * cm, 6.4 * cm, 6.4 * cm]))
E.append(Spacer(1, 6))
E.append(h2("1.1　指标定义"))
E.append(formula("MSE = E|y - y<sub>ideal</sub>|<super>2</super> / "
                 "E|y<sub>ideal</sub>|<super>2</super>，"
                 "y<sub>ideal</sub> 为频域相位斜坡 e<super>-j2πfτ</super> 的精确延时输出"))
E.append(p("参考基准合法性已验证：401 抽头 Kaiser 加窗 sinc FIR 与频域理想延时的互差为 "
           "-118 dB，故以频域相位斜坡作为“理想补偿”参考严谨可靠。"))
E.append(h2("1.2　技术难点"))
E.append(p("1.125 sps 的过采样率极低：信号带边缘 (1+β)×118 GHz 达到 Nyquist"
           "（132.75 GHz）的 89%~100%（β=0.1 时为 97.8%）。分数延时滤波器的误差天然"
           "集中在 Nyquist 附近，通用插值器（线性 / Lagrange / 加窗 sinc / Farrow "
           "教科书设计）优化的是全带平坦响应，在这种近 Nyquist 场景下效率很低。本项目"
           "的核心思路是：<b>只在信号 PSD 加权意义下达标</b>（LS 设计自动实现），并利用"
           "“μ 很小”与“μ 准静态”两个先验做结构化设计。"))

E.append(h1("2　仿真方法学"))
E.append(p("信号生成：PAM4 随机符号 → 9 倍上采样 → RRC(β) 频域成形 → 8 倍抽取，得到 "
           "9/8 sps 的发射信号；覆盖 β ∈ {0.05, 0.10, 0.125} 全部可行取值。"
           "所有滤波器设计在一组信号上做最小二乘拟合（自动按信号 PSD 加权），在<b>独立"
           "随机种子的另一组信号</b>上验证，避免过拟合。可调方案的指标一律取"
           "<b>μ 全范围 × 全部 β 的最坏 MSE</b>。定点方案另做 bit-exact 链路仿真。"))

# ================= 3. round1 =================
E.append(h1("3　第一轮：固定 0.35 ps 的最低复杂度设计"))
E.append(p("0.35 ps 对应 μ = 0.0929 采样。先扫描通用候选算法（β=0.1，独立验证集）："))
E.append(tbl([
    ["算法", "乘法器/样本", "MSE (dB)", "达标"],
    ["2 抽头线性插值", "2", "-17.9", "✗"],
    ["3 抽头 Lagrange", "3", "-20.6", "✗"],
    ["4 抽头 Lagrange", "4", "-21.2", "✗"],
    ["7 抽头加窗 sinc", "7", "-24.5", "✗"],
    ["1 阶 Thiran 全通 IIR", "1", "-13.9", "✗（且 IIR 无法高倍并行）"],
    ["4 抽头 LS FIR", "4", "-25.0", "临界"],
    ["5 抽头 LS FIR", "5", "-27.2", "✓"],
], [5.2 * cm, 3.2 * cm, 3.2 * cm, 5.4 * cm]))
E.append(Spacer(1, 6))
E.append(h2("3.1　结构化设计：单位中心 + 反对称修正对"))
E.append(p("利用 μ ≪ 1：e<super>-jωμ</super> = cos(ωμ) - j·sin(ωμ)，带内 cos(ωμ) ≈ 1"
           "（带边缘仅降至 0.96），误差几乎全部来自奇对称虚部。故将滤波器约束为："))
E.append(formula("y[n] = x[n] + c<sub>1</sub>·(x[n-1] - x[n+1]) + "
                 "c<sub>2</sub>·(x[n-2] - x[n+2])"))
E.append(p("每个修正对先预减后乘，天然只需 2 个乘法器（5 抽头跨度）。进一步做量化感知 "
           "CSD 搜索，系数取 c<sub>1</sub> = 3/32、c<sub>2</sub> = -5/128 后，两个乘法"
           "退化为移位相加：<b>0 个乘法器、约 8 个加法器</b>，MSE = -26.3 ~ -27.1 dB"
           "（覆盖全部 β），余量 ≥ 1.3 dB。"))
E.append(img("results.png", 16.5 * cm))
E.append(cap("图 1　第一轮：MSE-乘法器数 Pareto（左）与误差频响 vs 信号 PSD（右）。"
             "反对称结构把误差压到信号已滚降的带边缘，因而以 0~2 个乘法器胜过 7 抽头通用设计。"))

# ================= 4. round2 =================
E.append(h1("4　第二轮：skew 在线可调（奇偶约束 Farrow）"))
E.append(p("需求更新：不复用发射端成形 FIR、skew 在线可调。skew 是慢变校准量"
           "（温漂/老化时间尺度），<b>无需逐样本变化</b>，复杂度指标随之改为“每输出样本"
           "的可编程乘法器数”——固定系数子滤波器可 CSD 移位化（≈0 乘法器），只有系数会"
           "在线改写的乘法必须用真乘法器。结构为 μ = 0 严格恒等的奇偶约束 Farrow："))
E.append(formula("y[n] = x[n] + μ·(C<sub>1</sub>∗x) + μ<super>2</super>·"
                 "(C<sub>2</sub>∗x) + … + μ<super>P</super>·(C<sub>P</sub>∗x)"
                 "，奇数阶反对称、偶数阶对称"))
E.append(p("μ, μ<super>2</super>, … 由固件在校准时算好写入寄存器；整数样本部分用移位"
           "寄存器 + mux（零乘法器），分数部分只需覆盖 μ ∈ [-1/2, +1/2]。分档结果："))
E.append(tbl([
    ["校准范围", "最低结构", "可编程乘法器", "最坏 MSE", "可编程 FIR 基线"],
    ["±0.5 ps（μ≤0.133）", "P=1，K=4 对", "1", "-26.9 dB", "7 抽头 / 7 乘法器"],
    ["±1.0 ps（μ≤0.266）", "P=2，K=5 对", "2", "-26.3 dB", "11 抽头 / 11 乘法器"],
    ["±1.88 ps（μ≤0.5，任意）", "P=3，K=7 对", "3", "-26.9 dB", "13 抽头 / 13 乘法器"],
], [4.6 * cm, 3.4 * cm, 2.8 * cm, 2.6 * cm, 3.6 * cm]))
E.append(Spacer(1, 4))
E.append(img("results_tunable.png", 16.5 * cm))
E.append(cap("图 2　第二轮：Farrow（红）与可编程系数 FIR 基线（蓝）的最坏 MSE 对比。"
             "Farrow 把可编程乘法器从 7~13 个压缩到 1~3 个。"))

# ================= 5. round3 =================
E.append(h1("5　第三轮：范围收紧至 |skew| ≤ 0.35 ps 的冻结设计"))
E.append(p("需求最终确定为最大 0.35 ps、在线可调。μ ≤ 0.093 时一阶结构即可，K 进一步"
           "压缩，CSD 搜索后系数落在极简值上："))
E.append(formula("d<sub>k</sub>[n] = x[n-k] - x[n+k]，k = 1, 2, 3"))
E.append(formula("方案 A（最简）：y = x + μ·( d<sub>1</sub> - (7/16)·d<sub>2</sub> )"
                 "<br/>方案 B（推荐）：y = x + μ·( d<sub>1</sub> - (7/16)·d<sub>2</sub>"
                 " + (1/4)·d<sub>3</sub> )"))
E.append(tbl([
    ["方案", "可编程乘法器", "加法器", "最坏 MSE", "余量"],
    ["A：2 对（5 抽头跨度）", "1", "5", "-26.3 dB", "1.3 dB"],
    ["B：3 对（7 抽头跨度）", "1", "7", "-28.9 dB", "3.9 dB"],
    ["B + 6bit μ 寄存器", "1", "7", "-28.7 dB", "3.7 dB"],
], [5.4 * cm, 3.0 * cm, 2.2 * cm, 3.2 * cm, 3.2 * cm]))
E.append(Spacer(1, 4))
E.append(p("7/16 = 1/2 - 1/16（2 次移位相加），1/4 为纯移位，均为硬件常数；在线只改写 "
           "μ 寄存器（6 bit 即够，步进约 59 fs，符号覆盖两个方向）。任何在线可调结构至少"
           "需要 1 个乘法器，故该方案在乘法器维度已达下限。一阶结构的适用边界约为 "
           "±0.55 ps（设计到 ±0.6 ps 时最坏 -24.6 dB 开始不达标）。"))

# ================= 6. round4 =================
E.append(h1("6　第四轮：功耗优先的再优化"))
E.append(p("动态功耗 ∝ 翻转活动 × 有效位宽，与面积的权衡不同。μ 准静态这一先验在功耗维度"
           "可以榨得更彻底，三个定量结论如下。"))
E.append(h2("6.1　修正通路可大幅截位"))
E.append(p("修正项经 μ ≤ 0.093 缩放后才进入主通路，其量化噪声被压低约 21 dB："))
E.append(tbl([
    ["d<sub>k</sub> 位宽", "乘积位宽", "最坏 MSE"],
    ["全精度", "全精度", "-28.9 dB"],
    ["5 bit", "8 bit", "-28.4 dB"],
    ["4 bit", "6 bit", "-26.1 dB"],
], [5.6 * cm, 5.6 * cm, 5.8 * cm]))
E.append(Spacer(1, 4))
E.append(h2("6.2　消除乘法器：μ 折算为可编程移位（SPT）"))
E.append(p("乘法器每样本重复回答“乘以多少”，而 μ 几分钟才变一次。做法：保持 v = "
           "d<sub>1</sub> - (7/16)d<sub>2</sub> + (1/4)d<sub>3</sub> 硬连线不变，仅把"
           "“× μ”一级替换为共享的 2 项带符号 2 的幂（SPT）："))
E.append(formula("y[n] = x[n] + ( ±2<super>-a</super> ± 2<super>-b</super> )"
                 "·v[n]，固件按校准结果查 49 项小表写入 (符号, 移位) × 2"))
E.append(p("移位器为桶形 mux，<b>选择线静态不翻转</b>（功耗近似走线）；乘法器的部分积与 "
           "Booth 编码翻转彻底消失。移位挡位经穷举验证：{≫4, ≫5, ≫6, ≫7} 4 挡 + 置零挡"
           "（<b>5 选 1 mux × 2</b>）即可，-28.66 dB 与不限挡位完全一致；缺 2"
           "<super>-4</super> 挡则掉到 -24.7 dB 不达标。粗略能量核算（按加法器位宽单位）"
           "：乘法器版 ≈ 90 单位/样本，全移位版 ≈ 55~65 单位，<b>约省 30~40% 动态功耗</b>。"))
E.append(h2("6.3　功耗真正的下限：时钟域补偿"))
E.append(p("纯延时残差 δ 的容限：0.05 ps → -33.3 dB；0.10 ps → -27.3 dB；0.12 ps 为 "
           "-25 dB 临界。若 DAC 采样时钟路径具备每通道相位插值器（PI），LSB ≤ 0.2 ps"
           "（取整后残差 ≤ 0.1 ps）即可把 0.35 ps 完全在时钟域补偿：<b>每样本数字功耗"
           "严格为零</b>。约束：PI 附加抖动 ≪ 0.1 ps RMS，且需每通道独立时钟微调。"))
E.append(h2("6.4　功耗视角的方案排序"))
E.append(tbl([
    ["优先级", "方案", "每样本数字代价", "条件"],
    ["①", "DAC 时钟 PI（模拟）", "0", "硬件具备 ~0.2 ps 步进每通道时钟微调"],
    ["②", "全移位数字结构（6.2 + 6.1）", "0 乘法器，约 10 个窄加法器",
     "数字方案中功耗最优"],
    ["③", "第三轮方案 B + 截位", "1 个小乘法器", "不加移位网络时的最小改动"],
], [1.6 * cm, 5.4 * cm, 5.2 * cm, 4.8 * cm]))

# ================= 7. hardware =================
E.append(h1("7　最终硬件实现方案（|skew| ≤ 0.35 ps）"))
E.append(p("按 6.2 方案落地，主通路假设 s8（8 bit 有符号，LSB = FS/128）。整条定点链"
           "经逐节点 bit-exact 仿真：<b>最坏 MSE = -28.35 dB</b>（β=0.125，μ=-0.086），"
           "余量 3.3 dB。"))
E.append(img("blockdiagram.png", 17 * cm))
E.append(cap("图 3　最终方案框图（单条并行 lane）。黄色为固定硬件（纯移位加），绿色为"
             "静态可配置的 5:1 mux 选择，紫色虚线框为软件域（仅校准时运行）。"))
E.append(tbl([
    ["节点", "格式", "LSB 权重", "范围", "说明"],
    ["x[n] / 延时线", "s8 × 7", "FS/128", "±FS", "主通路，6 级寄存器"],
    ["截位 x<sub>t</sub>", "s5 × 6", "FS/16", "±FS", "外侧 6 抽头丢 3 个 LSB"],
    ["d<sub>1..3</sub>", "s6", "FS/16", "±2FS", "3 个窄减法器"],
    ["v", "s8", "FS/32", "±3.375FS", "硬连线移位加"],
    ["t<sub>A</sub>, t<sub>B</sub>", "s6", "FS/128", "±0.21FS",
     "5:1 mux 输出，对齐主通路"],
    ["c = μ̂·v", "s7", "FS/128", "±0.32FS", "静态加/减合并"],
    ["y[n]", "s8", "FS/128", "±FS", "s9 求和后舍入 + 饱和"],
    ["μ 寄存器 / 配置", "8 bit / 8 bit", "1/256 / -", "|码|≤24",
     "固件写入，双缓冲切换"],
], [3.4 * cm, 2.6 * cm, 2.4 * cm, 2.6 * cm, 6.0 * cm]))
E.append(Spacer(1, 4))
E.append(p("并行化说明：结构内只有 ±3 采样内的静态引用、无反馈，在 64/128 路并行 DSP 中"
           "逐路复制即可，延时线体现为跨 lane 静态布线，全部配置寄存器全局共享一份；"
           "静态选择线不翻转的功耗优势在并行化后同样成立。"))

# ================= 8. round5 =================
E.append(h1("8　第五轮：范围扩展到 |skew| ≤ 1 ps"))
E.append(h2("8.1　为什么必须升二阶"))
E.append(p("μ 最大 0.266 时，偶次误差项 cos(ωμ) - 1 ≈ -(ωμ)<super>2</super>/2 在带边缘"
           "达 -0.33，一阶结构仅 -18 dB。补一条对称的二阶支路后："))
E.append(formula("v<sub>1</sub> = Σ<sub>k</sub> a<sub>k</sub>·(x[n-k] - x[n+k])，"
                 "k = 1..6　（反对称）<br/>"
                 "v<sub>2</sub> = b<sub>0</sub>·x[n] + Σ<sub>k</sub> b<sub>k</sub>"
                 "·(x[n-k] + x[n+k])，k = 1..2　（对称）<br/>"
                 "y = x + s<sub>1</sub>·v<sub>1</sub> + s<sub>2</sub>·v<sub>2</sub>，"
                 "s<sub>1</sub> ≈ μ、s<sub>2</sub> ≈ μ<super>2</super>"))
E.append(p("二阶支路很便宜：K<sub>2</sub> = 2 即饱和（二阶项 ∝ μ<super>2</super> 本身小，"
           "其误差再被衰减约 11 dB）。s<sub>1</sub>、s<sub>2</sub> 仍为准静态标量，各用 "
           "≤2 项 SPT 移位实现——<b>零乘法器结构在 1 ps 下依然成立</b>。"))
E.append(tbl([
    ["配置（逐步叠加约束）", "最坏 MSE"],
    ["K1=6, K2=2，浮点标量", "-27.8 dB"],
    ["+ s1/s2 各 ≤2 项 SPT", "-27.8 dB（无损）"],
    ["+ 移位窗口收紧（s1 用 7:1、s2 用 6:1 mux）", "-27.2 dB"],
    ["+ d<sub>k</sub> 截到 6 bit（比 0.35 ps 版紧一位）", "-27.2 dB，余量 2.2 dB"],
], [11.4 * cm, 5.6 * cm]))
E.append(Spacer(1, 6))
E.append(h2("8.2　子滤波器系数（CSD 分解 = 精确分数，回环验证零损失）"))
E.append(tbl([
    ["系数", "CSD 分解", "精确值", "系数", "CSD 分解", "精确值"],
    ["a<sub>1</sub>", "1-2<super>-4</super>+2<super>-6</super>", "61/64",
     "a<sub>2</sub>", "-2<super>-1</super>+2<super>-4</super>", "-7/16"],
    ["a<sub>3</sub>", "2<super>-2</super>+2<super>-6</super>", "17/64",
     "a<sub>4</sub>", "-2<super>-2</super>+2<super>-4</super>+2<super>-7</super>",
     "-23/128"],
    ["a<sub>5</sub>", "2<super>-3</super>-2<super>-8</super>", "31/256",
     "a<sub>6</sub>", "-2<super>-4</super>-2<super>-6</super>-2<super>-9</super>",
     "-41/512"],
    ["b<sub>0</sub>", "-1-2<super>-1</super>-2<super>-5</super>", "-49/32",
     "b<sub>1</sub>", "1-2<super>-3</super>+2<super>-5</super>", "29/32"],
    ["b<sub>2</sub>", "-2<super>-2</super>+2<super>-4</super>+2<super>-6</super>",
     "-11/64", "", "", ""],
], [1.6 * cm, 3.6 * cm, 2.2 * cm, 1.6 * cm, 4.2 * cm, 2.2 * cm]))
E.append(Spacer(1, 6))
E.append(h2("8.3　两种实现的对照"))
E.append(tbl([
    ["", "传统二阶 Farrow（Horner）", "零乘法器 SPT 版"],
    ["可编程元素", "2 个真乘法器（同一 μ）", "4 个静态移位 mux（7:1×2 + 6:1×2）"],
    ["固件工作", "只写 μ（最简）", "算 μ<super>2</super> + 查 SPT 表 + 写 2 组码"],
    ["面积", "更省", "略大（多 4 套移位网络）"],
    ["功耗", "较高（部分积每样本翻转）", "更低（选择线静止）"],
    ["最坏 MSE", "-27.2 dB", "-27.2 dB"],
], [2.8 * cm, 6.8 * cm, 7.4 * cm]))
E.append(Spacer(1, 4))
E.append(p("两版子滤波器（a、b 系数）完全相同，可做成同一 RTL 的两个例化选项。"
           "传统 Farrow 的框图如下："))
E.append(img("blockdiagram_farrow_1ps.png", 17 * cm))
E.append(cap("图 4　传统二阶 Farrow（Horner 形式，2 个可编程乘法器），"
             "v<sub>1</sub>/v<sub>2</sub> 的 CSD 系数已展开为精确分数。"))

# ================= 9. selection =================
E.append(h1("9　方案选型总表"))
E.append(tbl([
    ["skew 范围", "优化目标", "推荐方案", "代价", "最坏 MSE"],
    ["0.35 ps 固定", "复杂度", "2 对反对称 + CSD（第 3 章）", "0 乘 / 8 加",
     "-26.3 dB"],
    ["±0.35 ps 可调", "面积", "方案 B：1 乘法器（第 5 章）", "1 乘 / 7 加",
     "-28.9 dB"],
    ["±0.35 ps 可调", "功耗", "SPT 移位版（第 6~7 章）", "0 乘 / ~10 加 / 2 mux",
     "-28.4 dB"],
    ["±1 ps 可调", "面积/固件最简", "传统二阶 Farrow（8.3）", "2 乘 / ~23 加",
     "-27.2 dB"],
    ["±1 ps 可调", "功耗", "二阶 SPT 版（8.1）", "0 乘 / ~30 加 / 4 mux",
     "-27.2 dB"],
    ["任意（含 >1 ps）", "-", "整数延时线 + 三阶 Farrow（第 4 章）", "3 乘",
     "-26.9 dB"],
    ["任意", "功耗极限", "DAC 时钟 PI（6.3）", "数字侧为 0",
     "受 PI 步进/抖动限制"],
], [3.0 * cm, 2.6 * cm, 5.6 * cm, 3.4 * cm, 2.4 * cm]))
E.append(Spacer(1, 4))
E.append(p("通用规律：范围每扩一档（0.35 ps → 1 ps → 1.88 ps），Farrow 阶数加一、"
           "一阶支路抽头对数约翻倍；而“标量准静态 → SPT 移位化”的零乘法器思路对每一档"
           "都成立。"))

# ================= 10. deliverables =================
E.append(h1("10　交付物与复现指南"))
E.append(tbl([
    ["文件", "内容"],
    ["REPORT.md", "五轮完整技术报告（本文档的底稿）"],
    ["sim_skew_precomp.py", "信号生成、理想延时基准、通用候选算法扫描、量化与鲁棒性"],
    ["sim_structured.py", "反对称结构化设计（第一轮核心）"],
    ["sim_csd.py", "量化感知 CSD 搜索（零乘法器固定方案）"],
    ["sim_farrow.py", "奇偶约束 Farrow 分档设计 + 可编程 FIR 基线（第二轮）"],
    ["sim_final.py", "±0.35 ps 冻结设计（系数硬编码）独立验证（第三轮）"],
    ["sim_power.py", "截位 / SPT 折算 / 时钟域容限三项功耗分析（第四轮）"],
    ["sim_mux.py", "因式分解结构与 mux 挡位窗口验证（第四轮 b）"],
    ["sim_fixedpoint.py", "最终方案 bit-exact 定点链验证（-28.35 dB）"],
    ["sim_1ps.py", "1 ps 二阶扩展设计与验证（第五轮）"],
    ["make_figures.py / make_fig_tunable.py", "图 1 / 图 2"],
    ["make_blockdiagram.py / make_blockdiagram_farrow.py", "图 3 / 图 4"],
], [6.4 * cm, 10.6 * cm]))
E.append(Spacer(1, 4))
E.append(p("环境：Python 3 + numpy / scipy / matplotlib。全部结论可由上述脚本独立复现；"
           "关键设计均在独立随机种子数据上验证，定点方案另有 bit-exact 仿真。"))

E.append(h1("11　后续工作建议"))
E.append(p("① 端到端验证：在完整发射链（DAC sinc、驱动器带宽、眼图/BER）中确认 -25 dB "
           "指标的充分性与余量分配；② 并行化实现：64/128 路展开的跨 lane 布线与时序收敛，"
           "配置双缓冲的换页时序；③ 与 DAC sinc 补偿/预加重的联合定点优化；④ 若采用时钟"
           "域方案，需评估 PI 的抖动传递与每通道独立性；⑤ 校准环路对接：μ 码的来源"
           "（片上误差检测或出厂标定）与更新协议。"))

doc.build(E, onFirstPage=footer, onLaterPages=footer)
print("saved skew_precomp_design_doc.pdf")
