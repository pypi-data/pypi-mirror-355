# -*- coding: utf-8 -*-
"""
---------------------------------------------
Created on 2024/12/10 下午2:44
@author: ZhangYundi
@email: yundi.xxii@outlook.com
---------------------------------------------
"""

import inspect
import os.path

import polars as pl
from jinja2 import Environment, FileSystemLoader
from pyecharts.charts.chart import RectChart


def get_dir():
    file_path = inspect.getfile(get_dir)
    return os.path.dirname(file_path)


def inject_data(table_df: pl.DataFrame,
                summary_table_data: pl.DataFrame,
                quantile_ret_bar_chart: RectChart,
                quantile_ret_box_chart: RectChart,
                cum_ic_chart: RectChart,
                cap_box_chart: RectChart,
                cum_ret_chart: RectChart,
                output_path: str):
    """注入表格数据到模板文件中"""
    dir_path = get_dir()
    template_html = os.path.join(dir_path, "template.html")

    # 初始化 Jinja2 环境
    env = Environment(loader=FileSystemLoader(dir_path))
    template = env.get_template(os.path.basename(template_html))
    # 注入alpha 报告表格
    # 使用 Polars 的高效方法转换 DataFrame
    columns = table_df.columns  # 获取列名
    rows = table_df.to_numpy().tolist()

    summary_columns = summary_table_data.columns
    summary_rows = summary_table_data.to_numpy().tolist()

    # ic_dist_chart_json = pio.to_json(ic_dist_fig)
    # ic_dist_chart_data = json.loads(ic_dist_chart_json)['data']
    # ic_dist_chart_layout = json.loads(ic_dist_chart_json)['layout']

    # q_ret_bar_chart_options = quantile_ret_bar_chart.dump_options_with_quotes()
    # q_ret_box_chart_options = quantile_ret_box_chart.dump_options_with_quotes()
    # cap_box_chart_options = cap_box_chart.dump_options_with_quotes()

    # 将数据和布局转为 JSON
    # ic_dist_chart_data_json = json.dumps(ic_dist_chart_data)
    # ic_dist_chart_layout_json = json.dumps(ic_dist_chart_layout)

    # 渲染模板
    html_content = template.render(columns=columns,
                                   rows=rows,
                                   summary_columns=summary_columns,
                                   summary_rows=summary_rows,
                                   # ic_dist_chart_data=ic_dist_chart_data_json,
                                   # ic_dist_chart_layout=ic_dist_chart_layout_json,
                                   q_bar_chart=quantile_ret_bar_chart.dump_options_with_quotes(),
                                   q_ret_box_chart=quantile_ret_box_chart.dump_options_with_quotes(),
                                   cap_box_chart=cap_box_chart.dump_options_with_quotes(),
                                   cum_ic_chart=cum_ic_chart.dump_options_with_quotes(),
                                   cum_ret_tab=cum_ret_chart.render_embed(),
                                   )
    # # 将生成的 HTML 写入文件
    try:
        os.makedirs(os.path.dirname(output_path))
    except FileExistsError as e:
        pass
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)


def render(table_data: pl.DataFrame,
           summary_table_data: pl.DataFrame,
           quantile_ret_bar_chart: RectChart,
           quantile_ret_box_chart: RectChart,
           cum_ic_lines_chart: RectChart,
           cap_box_chart: RectChart,
           cum_ret_chart: RectChart,
           output_path: str,
           ):
    inject_data(table_data,
                summary_table_data,
                quantile_ret_bar_chart,
                quantile_ret_box_chart,
                cum_ic_lines_chart,
                cap_box_chart,
                cum_ret_chart,
                output_path)
    # webbrowser.open(f"file://{os.path.realpath(output_path)}")
    abspath = f"{os.path.abspath(output_path)}"
    # display(IFrame(f"file://{abspath}", width="100%", height=800))
    # print(abspath)
    # webbrowser.open(abspath)
    # display(IFrame(abspath, width="100%", height=800))
    # with open(abspath, "r") as f:
    #     html_content = f.read()
    # display(HTML(html_content))
    return abspath
