# -*- coding: utf-8 -*-
"""
---------------------------------------------
Created on 2024/11/21 下午2:05
@author: ZhangYundi
@email: yundi.xxii@outlook.com
---------------------------------------------
"""
import numpy as np
import pandas as pd
import polars as pl
import pyarrow as pa

def to_pl(df: pd.DataFrame) -> pl.DataFrame:
    """将pandas.DataFrame转为polars.DataFrame"""
    result = pl.from_arrow(pa.Table.from_pandas(df.reset_index()))
    cols = result.columns
    if "date" in cols:
        result = result.with_columns(pl.col("date").cast(pl.Date))
    return result.fill_nan(None)

def get_forward_returns_columns(columns: list[str]) -> list[str]:
    """
    从列名列表中筛选出代表时间差的列名。

    参数:
    - columns: 列名列表。

    返回:
    - 代表时间差的列名列表。
    """
    timedelta_columns = []
    for col in columns:
        try:
            # 尝试将列名解析为 Timedelta
            pd.Timedelta(col)
            timedelta_columns.append(col)
        except ValueError:
            # 如果解析失败，说明不是时间差
            pass
    return timedelta_columns

def demean_forward_returns(factor_data: pl.DataFrame, grouper=None):
    if grouper is None:
        grouper = pd.Index(["date", "time"]).intersection(factor_data.columns).tolist()
    # 提取需要计算的列
    cols = get_forward_returns_columns(factor_data.columns)

    # 按 grouper 分组，对 cols 列进行中心化 (x - x.mean())
    result = factor_data.with_columns([
        (pl.col(col) - pl.col(col).mean().over(grouper)).alias(col)
        for col in cols
    ])

    return result

def freq_adjust(period, trading_hours=4, target_period="252d"):
    """调整周期: 按照1天交易时间4h"""
    scaler = (pd.Timedelta(target_period).days * trading_hours * 60 * 60 + pd.Timedelta(target_period).seconds) / (pd.Timedelta(period).days * trading_hours * 60 * 60 + pd.Timedelta(period).seconds)
    return scaler

def add_factor_quantile(factor_data: pl.DataFrame, bins: int=10, by_group: bool=False)->pl.DataFrame:
    """添加分组列 `facotr_quantile` """
    grouper = pd.Index(["date", "time"]).intersection(factor_data.columns).tolist()
    if by_group:
        grouper.append("group")
    return factor_data.with_columns(
        pl.col("factor").qcut(bins,
                              labels=[str(i) for i in range(1, bins+1)],
                              allow_duplicates=True).over(grouper).alias("factor_quantile")
    ).with_columns(
        pl.col(pl.Categorical).cast(pl.Int32))

def add_factor_quantile_byval(factor_data: pl.DataFrame, min_value: float, max_value: float, bins: int=10):
    """根据因子值来分组"""
    # cols = ["date", "time", "asset", *get_forward_returns_columns(factor_data.columns)]
    # fac_cols = pd.Index(factor_data.columns).difference(cols).to_list()
    bin_num = max(bins-1, 2)
    over = pd.Index(["date", "time"]).intersection(factor_data.columns).to_list()
    bins = np.linspace(min_value, max_value, bin_num)
    return (
        factor_data
        # .drop_nulls()
        .with_columns(
            pl.col("factor")
            .cut(bins, labels=[str(i) for i in range(1, bin_num+2)])
            .over(over)
            .cast(pl.Int16)
            .alias(f"factor_quantile")
        )
        .sort(by=[*over, "asset"])
    )
