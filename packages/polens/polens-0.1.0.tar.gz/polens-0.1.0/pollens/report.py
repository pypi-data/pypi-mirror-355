# -*- coding: utf-8 -*-
"""
---------------------------------------------
Created on 2024/12/15 下午3:09
@author: ZhangYundi
@email: yundi.xxii@outlook.com
---------------------------------------------
"""

import pandas as pd
import polars as pl
from pyecharts.charts import Tab

import finplot
from . import tears, performance, utils
from .board import render


def report(factor_data: pl.DataFrame,
           demeaned: bool = True,
           group_neutral: bool = True,
           by_time: bool = False,
           lag: int = 1,
           report_path: str = "alphalens.html") -> tuple[pl.DataFrame, str]:
    """
    生成 factor_data 的报告并输出为 HTML 文件。

    Parameters
    ----------
    factor_data : pl.DataFrame
    输入的因子数据框，包含因子值和其他相关数据。

    demeaned : bool
    是否进行去均值处理。如果为 True，则在计算收益时会去掉因子的均值影响。

    group_neutral : bool
    是否进行组中性处理。如果为 True，则收益会减去行业均值

    by_time : bool, 可选
    是否按时间分组计算。默认为 False。

    lag: int
            计算因子自回归以及换手时的滞后期数, 默认上一期:1

    report_path : str, 可选
    输出的 HTML 报告文件路径。默认为 "alphalens.html"。

    Returns
    -------
    该函数生成的报告包括：
    - 因子数据的汇总表。
    - 分组平均收益的柱状图。
    - 信息系数 (IC) 的分布图和累计曲线。
    - 分组累计收益的时间序列图。
    - 市值分布的箱线图。
    - 收益分布的箱线图。

    该函数会使用 finplot 库绘制图表，并将所有图表和汇总表渲染到指定的 HTML 文件中。

    Notes
    -----
    group_neutral 和 demeaned 控制是否对收益做调整, group_neutral优先级更高
        - group_neutral 为 True: 收益-行业均值
        - group_neutral 为 False: 如果demeaned 为 True，则收益 - 全市场均值

    """
    # 汇总表
    summary_tb = tears.get_summary_report(factor_data,
                                          long_short=demeaned,
                                          group_neutral=group_neutral,
                                          by_time=by_time)
    brief_tb = summary_tb.select("period", "ic", pl.col("top_bps").alias("top"), pl.col("bottom_bps").alias("bottom"),
                                 pl.col("spread_bps").alias("spread"))
    # 分组平均收益
    ret_data, _, _ = performance.mean_return_by_quantile(factor_data, by_time=False, by_group=False, demeaned=demeaned,
                                                         group_adjust=group_neutral)
    cols = utils.get_forward_returns_columns(ret_data.columns)
    ret_data = ret_data.with_columns(
        (pl.col(col) * 1e4).round(2) for col in cols
    )
    ret_chart = finplot.bar(ret_data.to_pandas().set_index("factor_quantile", drop=True), title="分组收益")
    # ic分布和ic累计曲线
    ic_data = performance.factor_information_coefficient(factor_data, group_adjust=group_neutral, by_time=False,
                                                         by_group=False)
    # ic_dist_chart = finplot.distplot(ic_data.to_pandas().set_index("date", drop=True).round(3), bin_size=0.02)
    cum_ic_data = ic_data.with_columns("date", *[(pl.col(col).cum_sum()).round(3) for col in cols])
    cum_ic_chart = finplot.lines(cum_ic_data.to_pandas().set_index("date", drop=True), title="累计IC")
    # 分组累计收益
    daily_ret, _, _ = performance.mean_return_by_quantile(factor_data, by_date=True, by_time=False, by_group=False,
                                                          demeaned=demeaned, group_adjust=group_neutral)
    tab = Tab()
    labels = factor_data["factor_quantile"].drop_nulls().unique()
    max_q = labels.max()
    min_q = labels.min()
    labels = [str(label) for label in labels.to_list()]
    hidden_labels = pd.Index(labels).difference([str(min_q), str(max_q), "ls"])
    for col in cols:
        data = daily_ret.select("factor_quantile", "date", col).pivot("factor_quantile", index="date", values=col).sort(
            by="date")
        # 多空收益
        data = data.with_columns((pl.col(str(max_q)) - pl.col(str(min_q))).alias("ls"))
        # 累计收益
        data = data.with_columns(((pl.col(label) + 1).cum_prod() - 1).round(4) for label in [*labels, "ls"])
        chart = finplot.lines(data.to_pandas().set_index("date", drop=True), hidden=hidden_labels)
        tab.add(chart, tab_name=col)
    # 分组换手曲线
    q_to_data = performance.quantile_turnover(factor_data, by_time=by_time, period=lag)
    mean_to_bytime = q_to_data.pivot("factor_quantile", index=["date", "time"], values="turnover").group_by(
        "date").mean().sort(by="date")
    mean_to_bytime = mean_to_bytime.slice(1, mean_to_bytime.height - 1).drop("time")
    q_to_chart = finplot.lines(mean_to_bytime.to_pandas().set_index("date", drop=True).round(4),
                               hidden=pd.Index(labels).difference([str(min_q), str(max_q), ]))
    tab.add(q_to_chart, tab_name="分组换手")
    # 市值分布
    cap_data = factor_data["date", "time", "asset", "factor_quantile", "cap"]
    cap_data = cap_data.with_columns(
        pl.col("cap").qcut(50, labels=[str(i) for i in range(1, 51)], allow_duplicates=True).over(["date", "time"])
    ).with_columns(pl.col(pl.Categorical).cast(pl.Int32))
    # # 转为50分组
    cap_box_chart = finplot.box(
        cap_data.select("factor_quantile", "cap").to_pandas().set_index("factor_quantile", drop=True), title="市值分布")
    # 收益分布
    ret_box_data = factor_data.select("date", "factor_quantile", *cols, ).group_by(["date", "factor_quantile"]).mean()
    ret_box_chart = finplot.box(
        ret_box_data.select("factor_quantile", *[pl.col(col).round(6) for col in cols]).to_pandas().set_index(
            "factor_quantile", drop=True), title="收益分布")

    # 渲染
    filePath = render(summary_tb, brief_tb, ret_chart, ret_box_chart, cum_ic_chart, cap_box_chart, tab, report_path)
    return brief_tb, filePath
