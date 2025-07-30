import json
import re
import sys
from io import StringIO
from typing import Union, Pattern

import pandas as pd

# 兼容 __builtins__ 为模块或字典的情况
if isinstance(__builtins__, dict):
    original_open = __builtins__['open']
else:
    original_open = __builtins__.open

def restricted_open(name, mode='r', *args, **kwargs):
    if 'w' in mode or 'a' in mode or 'x' in mode:
        raise PermissionError("写入操作被禁止")
    return original_open(name, mode, *args, **kwargs)

# 根据 __builtins__ 的类型设置受限的 open 函数
if isinstance(__builtins__, dict):
    __builtins__['open'] = restricted_open
else:
    __builtins__.open = restricted_open

# 禁用 os 模块中的危险函数
import os

os.remove = lambda *args: _raise_error("remove")
os.rmdir = lambda *args: _raise_error("rmdir")
os.rename = lambda *args: _raise_error("rename")


def _raise_error(func_name):
    raise PermissionError(f"{func_name} 操作被禁止")


def read_gls(gls):
    """
    读取gls文件
    :param gls:
    :return:
    """
    with open(gls, 'r') as f:
        content = f.readlines()
    dfs = (pd.read_csv(StringIO(''.join(content[:2]))),
            pd.read_csv(StringIO(''.join(content[2:4]))),
            pd.read_csv(StringIO(''.join(content[4:]))))
    if len(sys.argv) > 2:
        return print(json.dumps([df.to_dict(orient='records') for df in dfs]))
    return dfs


def check_empty(df: pd.DataFrame, column_name: str):
    """
    检验空
    :param df:
    :param column_name:
    :return:
    """
    # 检查列是否存在
    if column_name not in df.columns:
        raise ValueError(f"列 '{column_name}' 不存在于DataFrame中")
    return (not df[column_name].isnull().any()) and (not (df[column_name] == '').any())


def check_range(df: pd.DataFrame, column_name: str, low=None, high=None, return_invalid=False):
    """
    校验指定列的值是否在给定范围内

    参数:
        df: 要检查的DataFrame
        column_name: 要检查的列名
        low: 最小值(包含), None表示不检查下限
        high: 最大值(包含), None表示不检查上限

    返回:
        tuple: (是否全部有效, 无效记录DataFrame)
    """
    # 检查列是否存在
    if column_name not in df.columns:
        raise ValueError(f"列 '{column_name}' 不存在于DataFrame中")
    # 初始化条件为全部True
    invalid_mask = pd.Series(False, index=df.index)

    # 检查下限
    if low is not None:
        invalid_mask = invalid_mask | (df[column_name] < low)

    # 检查上限
    if high is not None:
        invalid_mask = invalid_mask | (df[column_name] > high)

    invalid_records = df[invalid_mask]

    return (invalid_records.empty, invalid_records) if return_invalid else invalid_records.empty


def check_pattern(
        df: pd.DataFrame,
        column_name: str,
        pattern: Union[str, Pattern],
        case_sensitive: bool = False,
        allow_empty: bool = False,
        return_invalid=False
) -> tuple[bool, pd.DataFrame]:
    """
    校验DataFrame指定列是否符合正则表达式模式

    参数:
        df: 要检查的DataFrame
        column_name: 要检查的列名
        pattern: 正则表达式模式(字符串或编译后的正则表达式对象)
        case_sensitive: 是否区分大小写(默认False)
        allow_empty: 是否允许空字符串/NaN(默认False)

    返回:
        tuple: (是否全部有效, 无效记录DataFrame)
    """
    # 检查列是否存在
    if column_name not in df.columns:
        raise ValueError(f"列 '{column_name}' 不存在于DataFrame中")

    # 如果传入的是字符串模式，编译为正则表达式对象
    if isinstance(pattern, str):
        flags = 0 if case_sensitive else re.IGNORECASE
        pattern = re.compile(pattern, flags=flags)

    # 创建校验函数
    def is_valid(value):
        # 处理空值
        if pd.isna(value) or value == "":
            return allow_empty
        # 检查正则匹配
        return bool(pattern.fullmatch(str(value)))

    # 应用校验函数
    valid_mask = df[column_name].apply(is_valid)
    invalid_records = df[~valid_mask]

    return (invalid_records.empty, invalid_records) if return_invalid else invalid_records.empty


def check_length(df, column_name, expected_length, return_invalid=False) -> tuple[bool, pd.DataFrame]:
    """
    校验DataFrame指定列的所有行的字符串长度是否等于预期长度

    参数:
    df: pandas DataFrame - 要检查的数据框
    column_name: str - 要检查的列名
    expected_length: int - 预期的字符串长度

    返回:
    tuple: (bool, pd.DataFrame) -
        bool: 是否所有行都符合长度要求
        DataFrame: 不符合长度要求的行(如果全部符合则为空DataFrame)

    异常:
    ValueError: 如果raise_error=True且发现不符合长度的行
    """
    # 检查列是否存在
    if column_name not in df.columns:
        raise ValueError(f"列 '{column_name}' 不存在于DataFrame中")

    # 将列转换为字符串并计算长度
    str_series = df[column_name].astype(str)
    length_series = str_series.str.len()

    # 找出不符合长度的行
    invalid_rows = df[length_series != expected_length]

    # 返回检查结果和不符合的行
    all_valid = invalid_rows.empty
    return (all_valid, invalid_rows) if return_invalid else all_valid


def check_in(df: pd.DataFrame,
             column_name: str,
             *valid_values: Union[str, int, float],
             ignore_case: bool = False,
             return_invalid=False) -> tuple[bool, pd.DataFrame]:
    """
    校验DataFrame指定列的所有行的值是否都在指定的值集合中

    参数:
    df: pd.DataFrame - 要检查的数据框
    column_name: str - 要检查的列名
    *valid_values: Union[str, int, float] - 允许的有效值(可变参数形式)
    ignore_case: bool - 如果为True，字符串比较时忽略大小写；默认为False

    返回:
    tuple: (bool, pd.DataFrame) -
        bool: 是否所有行都符合要求
        DataFrame: 不符合要求的行(如果全部符合则为空DataFrame)
    """
    # 检查列是否存在
    if column_name not in df.columns:
        raise ValueError(f"列 '{column_name}' 不存在于DataFrame中")

    # 获取要检查的列
    column = df[column_name]

    # 处理忽略大小写的情况
    if ignore_case and pd.api.types.is_string_dtype(column.dtype):
        # 将列值和有效值都转换为小写进行比较
        column = column.str.lower()
        valid_values = [str(v).lower() for v in valid_values if v is not None]

    # 找出不符合要求的行
    invalid_mask = ~column.isin(valid_values)
    invalid_rows = df[invalid_mask]

    # 返回检查结果和不符合的行
    all_valid = invalid_rows.empty
    return (all_valid, invalid_rows) if return_invalid else all_valid




