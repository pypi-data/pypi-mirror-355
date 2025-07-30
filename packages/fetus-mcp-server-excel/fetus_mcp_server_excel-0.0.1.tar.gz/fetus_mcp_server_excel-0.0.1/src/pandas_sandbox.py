import hashlib
import io
import json
import os
import sys
import tempfile
import traceback
import warnings
from pathlib import Path
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import seaborn as sns

# 忽略警告
warnings.filterwarnings('ignore')


class PandasSandbox:
    """
    Pandas沙盒环境 - 安全执行pandas代码并处理Excel文件
    """

    def __init__(self):
        self.data_frames = {}  # 存储所有DataFrame
        self.execution_history = []  # 执行历史
        self.current_df = None  # 当前活动的DataFrame
        self.output_buffer = io.StringIO()
        self.plot_buffer = io.BytesIO()

        # 设置matplotlib后端
        plt.switch_backend('Agg')

        # 安全的内置函数白名单
        self.safe_builtins = {
            'abs', 'all', 'any', 'bool', 'dict', 'enumerate', 'filter',
            'float', 'int', 'len', 'list', 'map', 'max', 'min', 'range',
            'round', 'set', 'sorted', 'str', 'sum', 'tuple', 'type', 'zip',
            'print', 'isinstance', 'hasattr', 'getattr', 'setattr'
        }

        # 允许的模块和函数
        self.safe_globals = {
            'pd': pd,
            'pandas': pd,
            'np': np,
            'numpy': np,
            'plt': plt,
            'matplotlib': plt,
            'sns': sns,
            'seaborn': sns,
            'io': io,
            'os': os,
            'Path': Path,
            'json': json,
            'print': print,
            '__builtins__': {name: getattr(__builtins__, name)
                             for name in self.safe_builtins if hasattr(__builtins__, name)}
        }

    def _is_valid_url(self, url: str) -> bool:
        """验证URL是否有效"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    def _generate_cache_key(self, url: str) -> str:
        """生成缓存键"""
        return hashlib.md5(url.encode()).hexdigest()

    def _get_file_extension_from_url(self, url: str) -> str:
        """从URL中提取文件扩展名"""
        parsed_url = urlparse(url)
        path = parsed_url.path
        if path:
            return Path(path).suffix.lower()
        return ''

    def _download_file(self, url: str, force_download: bool = False) -> Dict[str, Any]:
        """
        下载在线文件

        Args:
            url: 文件URL
            force_download: 是否强制重新下载

        Returns:
            下载结果字典
        """
        try:
            # 生成缓存键
            cache_key = self._generate_cache_key(url)

            # 检查缓存（如果已有下载文件缓存系统）
            if hasattr(self, 'downloaded_files') and not force_download:
                if cache_key in self.downloaded_files:
                    cached_info = self.downloaded_files[cache_key]
                    if Path(cached_info['local_path']).exists():
                        return {
                            "success": True,
                            "local_path": cached_info['local_path'],
                            "original_url": url,
                            "from_cache": True
                        }

            # 获取文件扩展名
            file_ext = self._get_file_extension_from_url(url)
            if not file_ext:
                # 尝试从HTTP头部获取文件类型
                try:
                    response = requests.head(url, timeout=10)
                    content_type = response.headers.get('content-type', '').lower()
                    if 'excel' in content_type or 'spreadsheet' in content_type:
                        file_ext = '.xlsx'
                    elif 'csv' in content_type:
                        file_ext = '.csv'
                    elif 'json' in content_type:
                        file_ext = '.json'
                    else:
                        file_ext = '.xlsx'  # 默认为Excel
                except:
                    file_ext = '.xlsx'  # 默认为Excel

            # 支持的文件类型检查
            supported_extensions = {'.xlsx', '.xls', '.csv', '.json', '.parquet', '.tsv', '.txt'}
            if file_ext not in supported_extensions:
                return {
                    "success": False,
                    "error": f"不支持的文件类型: {file_ext}"
                }

            # 下载文件
            print(f"正在下载文件: {url}")

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            response = requests.get(url, headers=headers, timeout=60, stream=True)
            response.raise_for_status()

            # 创建临时目录（如果不存在）
            if not hasattr(self, 'temp_directory'):
                self.temp_directory = Path(tempfile.gettempdir()) / "pandas_cache"
                self.temp_directory.mkdir(exist_ok=True)

            # 保存到临时文件
            temp_filename = f"{cache_key}{file_ext}"
            local_path = self.temp_directory / temp_filename

            total_size = 0
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        total_size += len(chunk)

            # 缓存文件信息
            if not hasattr(self, 'downloaded_files'):
                self.downloaded_files = {}

            file_info = {
                'local_path': str(local_path),
                'original_url': url,
                'file_size': total_size,
                'download_time': pd.Timestamp.now().isoformat()
            }
            self.downloaded_files[cache_key] = file_info

            print(f"文件下载完成: {url} -> {local_path} ({total_size} bytes)")

            return {
                "success": True,
                "local_path": str(local_path),
                "original_url": url,
                "file_size": total_size,
                "from_cache": False
            }

        except requests.exceptions.RequestException as e:
            error_msg = f"下载文件失败: {str(e)}"
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"处理文件失败: {str(e)}"
            return {"success": False, "error": error_msg}

    def load_excel_file(self, file_path: str, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """
        加载Excel文件（支持本地文件和在线链接）

        Args:
            file_path: Excel文件路径或在线链接URL
            sheet_name: 工作表名称，None表示加载所有表

        Returns:
            包含加载结果的字典
        """
        try:
            local_file_path = None
            is_url = self._is_valid_url(file_path)

            if is_url:
                # 处理在线文件
                download_result = self._download_file(file_path)
                if not download_result["success"]:
                    return download_result

                local_file_path = download_result["local_path"]
                source_info = f"在线文件: {file_path}"
                if download_result.get("from_cache"):
                    source_info += " (来自缓存)"
            else:
                # 处理本地文件
                local_file_path = file_path
                if not os.path.exists(local_file_path):
                    return {"success": False, "error": f"文件不存在: {local_file_path}"}
                source_info = f"本地文件: {local_file_path}"

            # 检查文件扩展名
            file_ext = Path(local_file_path).suffix.lower()

            if file_ext == '.xlsx' or file_ext == '.xls':
                # 读取Excel文件
                if sheet_name:
                    df = pd.read_excel(local_file_path, sheet_name=sheet_name)
                    df_name = f"df_{sheet_name.replace(' ', '_').replace('-', '_')}"
                    self.data_frames[df_name] = df
                    self.current_df = df
                    sheets_loaded = [sheet_name]
                else:
                    # 读取所有工作表
                    excel_file = pd.ExcelFile(local_file_path)
                    sheets_loaded = []
                    for sheet in excel_file.sheet_names:
                        try:
                            df = pd.read_excel(local_file_path, sheet_name=sheet)
                            df_name = f"df_{sheet.replace(' ', '_').replace('-', '_')}"
                            self.data_frames[df_name] = df
                            sheets_loaded.append(sheet)
                        except Exception as e:
                            print(f"警告: 跳过工作表 {sheet}: {str(e)}")

                    # 设置第一个成功加载的工作表为当前DataFrame
                    if sheets_loaded:
                        first_sheet = sheets_loaded[0]
                        self.current_df = self.data_frames[f"df_{first_sheet.replace(' ', '_').replace('-', '_')}"]

            elif file_ext == '.csv':
                # 读取CSV文件，支持多种编码
                try:
                    df = pd.read_csv(local_file_path, encoding='utf-8-sig')
                except UnicodeDecodeError:
                    # 尝试其他常见编码
                    for encoding in ['gbk', 'gb2312', 'utf-8', 'latin1']:
                        try:
                            df = pd.read_csv(local_file_path, encoding=encoding)
                            print(f"成功使用编码: {encoding}")
                            break
                        except:
                            continue
                    else:
                        return {"success": False, "error": "无法识别CSV文件编码"}

                df_name = "df_csv"
                self.data_frames[df_name] = df
                self.current_df = df
                sheets_loaded = ["csv"]

            elif file_ext == '.json':
                # 读取JSON文件
                df = pd.read_json(local_file_path)
                df_name = "df_json"
                self.data_frames[df_name] = df
                self.current_df = df
                sheets_loaded = ["json"]

            elif file_ext == '.parquet':
                # 读取Parquet文件
                df = pd.read_parquet(local_file_path)
                df_name = "df_parquet"
                self.data_frames[df_name] = df
                self.current_df = df
                sheets_loaded = ["parquet"]

            elif file_ext in ['.tsv', '.txt']:
                # 读取TSV/TXT文件
                try:
                    df = pd.read_csv(local_file_path, sep='\t', encoding='utf-8-sig')
                except UnicodeDecodeError:
                    for encoding in ['gbk', 'gb2312', 'utf-8', 'latin1']:
                        try:
                            df = pd.read_csv(local_file_path, sep='\t', encoding=encoding)
                            break
                        except:
                            continue
                    else:
                        return {"success": False, "error": "无法识别TSV文件编码"}

                df_name = "df_tsv"
                self.data_frames[df_name] = df
                self.current_df = df
                sheets_loaded = ["tsv"]

            else:
                return {"success": False, "error": f"不支持的文件格式: {file_ext}"}

            # 更新全局命名空间
            self.safe_globals.update(self.data_frames)
            if self.current_df is not None:
                self.safe_globals['df'] = self.current_df

            # 生成详细的返回信息
            result = {
                "success": True,
                "message": f"成功加载文件: {source_info}",
                "source": file_path,
                "file_type": file_ext,
                "sheets": list(self.data_frames.keys()),
                "sheets_loaded": sheets_loaded,
                "shape": self.current_df.shape if self.current_df is not None else None,
                "columns": self.current_df.columns.tolist() if self.current_df is not None else None,
                "dtypes": {str(k): str(v) for k, v in
                           self.current_df.dtypes.to_dict().items()} if self.current_df is not None else None,
                "memory_usage": int(
                    self.current_df.memory_usage(deep=True).sum()) if self.current_df is not None else None,
                "null_counts": self.current_df.isnull().sum().to_dict() if self.current_df is not None else None
            }

            # 如果是在线文件，添加下载信息
            if is_url:
                result["download_info"] = {
                    "original_url": file_path,
                    "local_cache_path": local_file_path,
                    "file_size": Path(local_file_path).stat().st_size,
                    "cached": download_result.get("from_cache", False)
                }

            return result

        except Exception as e:
            return {"success": False, "error": f"加载文件失败: {str(e)}"}

    def execute_code(self, code: str) -> Dict[str, Any]:
        """
        安全执行pandas代码

        Args:
            code: 要执行的Python代码

        Returns:
            执行结果字典
        """
        try:
            # 重定向输出
            old_stdout = sys.stdout
            old_stderr = sys.stderr

            output_capture = io.StringIO()
            error_capture = io.StringIO()

            sys.stdout = output_capture
            sys.stderr = error_capture

            # 清空plot buffer
            self.plot_buffer = io.BytesIO()
            plt.clf()

            # 执行代码
            local_vars = {}
            exec(code, self.safe_globals, local_vars)

            # 检查是否有新的DataFrame被创建
            for var_name, var_value in local_vars.items():
                if isinstance(var_value, pd.DataFrame):
                    self.data_frames[var_name] = var_value
                    self.safe_globals[var_name] = var_value

            # 捕获输出
            output = output_capture.getvalue()
            error = error_capture.getvalue()

            # # 检查是否有图形输出
            # plot_data = None
            # if plt.get_fignums():  # 检查是否有活动的图形
            #     plt.savefig(self.plot_buffer, format='png', bbox_inches='tight', dpi=150)
            #     self.plot_buffer.seek(0)
            #     plot_data = base64.b64encode(self.plot_buffer.getvalue()).decode()
            #     plt.clf()  # 清除图形

            # 恢复标准输出
            sys.stdout = old_stdout
            sys.stderr = old_stderr

            # # 记录执行历史
            # self.execution_history.append({
            #     "code": code,
            #     "output": output,
            #     "error": error,
            #     "success": True
            # })

            return {
                "success": True,
                "output": output,
                "error": error,
                # "plot": plot_data,
                "dataframes": {name: {
                    "shape": df.shape,
                    "columns": df.columns.tolist(),
                    "dtypes": df.dtypes.to_dict(),
                    "head": df.head().to_dict('records') if len(df) > 0 else []
                } for name, df in self.data_frames.items()}
            }

        except Exception as e:
            # 恢复标准输出
            sys.stdout = old_stdout
            sys.stderr = old_stderr

            error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"

            # self.execution_history.append({
            #     "code": code,
            #     "output": "",
            #     "error": error_msg,
            #     "success": False
            # })

            return {
                "success": False,
                "output": "",
                "error": error_msg,
                # "plot": None
            }

    def get_dataframe_info(self, df_name: str = None) -> Dict[str, Any]:
        """
        获取DataFrame的详细信息

        Args:
            df_name: DataFrame名称，None表示当前DataFrame

        Returns:
            DataFrame信息字典
        """
        try:
            if df_name:
                if df_name not in self.data_frames:
                    return {"success": False, "error": f"DataFrame '{df_name}' 不存在"}
                df = self.data_frames[df_name]
            else:
                if self.current_df is None:
                    return {"success": False, "error": "没有活动的DataFrame"}
                df = self.current_df

            # 生成统计信息
            info_buffer = io.StringIO()
            df.info(buf=info_buffer)
            info_str = info_buffer.getvalue()

            return {
                "success": True,
                "name": df_name or "current_df",
                "shape": df.shape,
                "columns": df.columns.tolist(),
                "dtypes": df.dtypes.to_dict(),
                "info": info_str,
                "describe": df.describe().to_dict() if len(df) > 0 else {},
                "head": df.head(10).to_dict('records') if len(df) > 0 else [],
                "tail": df.tail(5).to_dict('records') if len(df) > 0 else [],
                "null_counts": df.isnull().sum().to_dict(),
                "memory_usage": df.memory_usage(deep=True).sum()
            }

        except Exception as e:
            return {"success": False, "error": f"获取DataFrame信息失败: {str(e)}"}

    def export_dataframe(self, df_name: str, output_path: str, format_type: str = 'xlsx') -> Dict[str, Any]:
        """
        导出DataFrame到文件

        Args:
            df_name: DataFrame名称
            output_path: 输出文件路径
            format_type: 导出格式 ('xlsx', 'csv', 'json')

        Returns:
            导出结果字典
        """
        try:
            if df_name not in self.data_frames:
                return {"success": False, "error": f"DataFrame '{df_name}' 不存在"}

            df = self.data_frames[df_name]

            if format_type.lower() == 'xlsx':
                df.to_excel(output_path, index=False)
            elif format_type.lower() == 'csv':
                df.to_csv(output_path, index=False, encoding='utf-8-sig')
            elif format_type.lower() == 'json':
                df.to_json(output_path, orient='records', force_ascii=False, indent=2)
            else:
                return {"success": False, "error": f"不支持的导出格式: {format_type}"}

            return {
                "success": True,
                "message": f"成功导出到: {output_path}",
                "format": format_type,
                "records": len(df)
            }

        except Exception as e:
            return {"success": False, "error": f"导出失败: {str(e)}"}

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """获取代码执行历史"""
        return self.execution_history

    def clear_history(self):
        """清空执行历史"""
        self.execution_history.clear()

    def reset_sandbox(self):
        """重置沙盒环境"""
        self.data_frames.clear()
        self.execution_history.clear()
        self.current_df = None
        plt.clf()

        # 重新初始化安全全局变量
        self.safe_globals = {
            'pd': pd,
            'pandas': pd,
            'np': np,
            'numpy': np,
            'plt': plt,
            'matplotlib': plt,
            'sns': sns,
            'seaborn': sns,
            'io': io,
            'os': os,
            'Path': Path,
            'json': json,
            '__builtins__': {name: getattr(__builtins__, name)
                             for name in self.safe_builtins if hasattr(__builtins__, name)}
        }


def demo_usage():
    """演示沙盒环境的使用方法"""

    # 创建沙盒实例
    sandbox = PandasSandbox()

    print("=== Pandas沙盒环境演示 ===\n")

    # 创建示例数据
    print("1. 创建示例数据...")
    sample_data = {
        'Name': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'],
        'Age': [25, 30, 35, 28, 32],
        'Salary': [50000, 60000, 70000, 55000, 65000],
        'Department': ['IT', 'HR', 'IT', 'Finance', 'IT']
    }

    df = pd.DataFrame(sample_data)
    df.to_excel('sample_data.xlsx', index=False)
    print("✓ 示例Excel文件已创建")

    # 加载Excel文件
    print("\n2. 加载Excel文件...")
    result = sandbox.load_excel_file('sample_data.xlsx')
    print(f"✓ 加载结果: {result}")

    # 执行数据分析代码
    print("\n3. 执行pandas代码...")

    codes = [
        "print('数据基本信息:')\nprint(df.info())",
        "print('\\n数据统计描述:')\nprint(df.describe())",
        "print('\\nIT部门员工:')\nit_employees = df[df['Department'] == 'IT']\nprint(it_employees)",
        "print('\\n各部门平均薪资:')\navg_salary = df.groupby('Department')['Salary'].mean()\nprint(avg_salary)",
        """
# 创建可视化图表
plt.figure(figsize=(10, 6))
plt.subplot(1, 2, 1)
df['Department'].value_counts().plot(kind='pie', autopct='%1.1f%%')
plt.title('部门人员分布')

plt.subplot(1, 2, 2)
df.groupby('Department')['Salary'].mean().plot(kind='bar')
plt.title('各部门平均薪资')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
"""
    ]

    for i, code in enumerate(codes, 1):
        print(f"\n--- 执行代码 {i} ---")
        print(f"代码:\n{code}")

        result = sandbox.execute_code(code)

        if result['success']:
            print("✓ 执行成功")
            if result['output']:
                print(f"输出:\n{result['output']}")
            if result['plot']:
                print("✓ 生成了图表")
        else:
            print("✗ 执行失败")
            print(f"错误: {result['error']}")

    # 获取DataFrame信息
    print("\n4. 获取DataFrame详细信息...")
    info_result = sandbox.get_dataframe_info('df')
    if info_result['success']:
        print(f"✓ DataFrame形状: {info_result['shape']}")
        print(f"✓ 列名: {info_result['columns']}")
        print(f"✓ 内存使用: {info_result['memory_usage']} bytes")

    # 导出数据
    print("\n5. 导出处理后的数据...")
    export_result = sandbox.export_dataframe('df', 'output_data.csv', 'csv')
    print(f"✓ 导出结果: {export_result}")

    print("\n=== 演示完成 ===")

    # 清理临时文件
    if os.path.exists('sample_data.xlsx'):
        os.remove('sample_data.xlsx')
    if os.path.exists('output_data.csv'):
        os.remove('output_data.csv')


if __name__ == "__main__":
    # 运行演示
    demo_usage()

    print("\n" + "=" * 50)
    print("使用方法:")
    print("1. 实例化: sandbox = PandasSandbox()")
    print("2. 加载文件: sandbox.load_excel_file('your_file.xlsx')")
    print("3. 执行代码: sandbox.execute_code('your_pandas_code')")
    print("4. 获取信息: sandbox.get_dataframe_info()")
    print("5. 导出数据: sandbox.export_dataframe('df_name', 'output.xlsx')")
    print("=" * 50)
