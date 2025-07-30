## 本地股票数据读取类
# 该类负责从本地文件系统读取股票数据
import pandas as pd
from pathlib import Path
import logging
from typing import Union
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('TableReader')


class DailyReader:
    """
    高效读取CSV/Excel表格数据的工具类，自动忽略最后一行注释
    
    特性：
    - 自动处理CSV和Excel格式
    - 高效读取大型文件
    - 智能数据类型推断
    - 详细的错误处理和日志记录
    - 忽略最后一行注释的功能
    - 内存优化
    """
    @staticmethod
    def read_daily_data(file_path: Union[str, Path]) -> pd.DataFrame:
        """
        从文件读取日线数据
        
        参数:
            file_path: 文件路径 (str 或 Path对象)

        返回:
            pd.DataFrame - 包含日线数据
            
        异常:
            如果文件读取失败会抛出RuntimeError                                                                                                                                                  
        """
        column_float=['流通市值Z','换手Z','今开','开盘%','涨幅%','开盘金额','开盘昨比%','昨成交额','总金额','竞价量比','开盘抢筹%','封单额','封成比',
                       '昨封单额','前封单额','主力净额','散户单增比','主力占比%','均价','现价','最低','最高','距5日线%','10日涨幅%','贝塔系数','每股净资',
                       '市盈(TTM)','流通市值','回头波%']
        column_int=['未匹配量','连板天','笔均量','年涨停天','连涨天','总量','安全分']
        column_str=['代码','名称','热点题材','几天几板','涨停原因分析','近日指标提示','地区','细分行业','策略选股']
        column_date=['上市日期']
        df= DailyReader.read_table(file_path)
        for col in column_float:
            if col in df.columns:
                if col in ['流通市值Z','流通市值']:
                    df[col] = df[col].str.replace('亿', '')
                df[col] = pd.to_numeric(df[col], errors='coerce')
        for col in column_int:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce', downcast='integer').astype('Int64')  # 使用pandas的Int64类型支持缺失值
        
        for col in column_str:
            if col in df.columns:
                df[col] = df[col].astype('string') #
        for col in column_date:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce', format='%Y%m%d')
        return df
    
    @staticmethod
    def read_table(file_path: Union[str, Path], ignore_last_line: bool = True, encoding: str = 'gbk') -> pd.DataFrame:
        """
        从文件读取表格数据
        
        参数:
            file_path: 文件路径 (str 或 Path对象)
            ignore_last_line: 是否忽略最后一行 (默认为True)
            encoding: 文件编码 (默认为'gbk')

        返回:
            pd.DataFrame - 包含表格数据
            
        异常:
            如果文件读取失败会抛出RuntimeError
        """
        path = Path(file_path)
        logger.info(f"开始读取表格文件: {path.name}")
        
        # 1. 验证文件是否存在并可读
        if not path.exists():
            error_msg = f"文件不存在: {path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
            
        if not path.is_file():
            error_msg = f"路径不是文件: {path}"
            logger.error(error_msg)
            raise IsADirectoryError(error_msg)
            
        if not os.access(path, os.R_OK):
            error_msg = f"无文件读取权限: {path}"
            logger.error(error_msg)
            raise PermissionError(error_msg)
        
        # 2. 根据扩展名选择读取器
        try:
            if path.suffix.lower() in ('.csv'):
                logger.info("检测到CSV格式")
                return DailyReader._read_csv(path, ignore_last_line, encoding)
                
            elif path.suffix.lower() in ('.xlsx', '.xls'):
                logger.info("检测到Excel格式")
                return DailyReader._read_excel(path, ignore_last_line)
                
            else:
                error_msg = f"不支持的文件格式: {path.suffix}"
                logger.error(error_msg)
                raise ValueError(error_msg)
                
        except Exception as e:
            logger.error(f"文件读取失败: {type(e).__name__} - {str(e)}")
            raise RuntimeError(f"无法读取文件 {path}") from e
            
    @staticmethod
    def _read_csv(path: Path, ignore_last_line: bool, encoding: str) -> pd.DataFrame:
        """读取CSV文件并处理最后一行注释"""
        try:
            # 第一步：只读取列名以优化内存
            columns = pd.read_csv(path, encoding=encoding, nrows=0, sep='\t').columns.tolist()
            logger.info(f"检测到列名: {columns}")
            
            # 第二步：确定要读取的行数
            row_count = 0
            with path.open(encoding=encoding) as f:
                # 第一行是表头
                next(f)  
                for line in f:
                    row_count += 1
            
            # 计算要读取的行数（减去最后一行注释）
            read_rows = row_count - 1 if ignore_last_line and row_count > 1 else row_count
            logger.info(f"文件总行数: {row_count+1} (将读取 {read_rows} 行)")

            # 第三步：高效读取数据
            df = pd.read_csv(
                path,
                encoding=encoding,
                header=0,  # 第一行作为表头
                sep='\t',  # 使用制表符分隔
                dtype={col: 'string' for col in columns},  # 将全部列转换为字符串以提高效率
                nrows=read_rows,  # 忽略最后一行
                skipfooter=0,  # 明确不使用skipfooter因为nrows已经处理
                memory_map=True,  # 内存映射提高大文件性能
                float_precision='high'  # 高精度浮点数处理
            )
            
            # 对于CSV，我们可能需要在读取后转换数据类型
            return DailyReader._optimize_dtypes(df)
            
        except pd.errors.EmptyDataError:
            logger.warning(f"CSV文件为空: {path}")
            return pd.DataFrame()
        except UnicodeDecodeError:
            logger.warning(f"编码检测失败，尝试备用编码: {path}")
            return DailyReader._read_with_fallback_encoding(path, ignore_last_line)
            
    @staticmethod
    def _read_with_fallback_encoding(path: Path, ignore_last_line: bool) -> pd.DataFrame:
        """尝试使用备选编码读取CSV文件"""
        encodings = ['gbk', 'latin1', 'big5', 'utf-16', 'cp1252']
        for encoding in encodings:
            try:
                logger.info(f"尝试编码: {encoding}")
                return DailyReader._read_csv(path, ignore_last_line, encoding)
            except UnicodeDecodeError:
                continue

        error_msg = f"无法识别的文件编码: {path}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    @staticmethod
    def _read_excel(path: Path, ignore_last_line: bool) -> pd.DataFrame:
        """读取Excel文件并处理最后一行注释"""
        try:
            # 使用openpyxl引擎以获得更多格式支持
            df = pd.read_excel(
                path,
                engine='openpyxl',
                dtype=str,  # 初始将所有列读取为字符串优化内存
                na_values=['', 'NA', 'N/A', 'NULL', 'NaN', 'nan'],  # 自定义NA值
                keep_default_na=False  # 防止自动转换
            )
            
            # 如果要求忽略最后一行且数据不为空
            if ignore_last_line and not df.empty:
                logger.info(f"删除最后一行注释 (原始行数: {len(df)})")
                df = df.iloc[:-1]  # 高效删除最后一行 
            
            # 优化数据类型
            return DailyReader._optimize_dtypes(df)  # type: ignore[assignment]  # 忽略类型警告
            
        except Exception as e:
            # 处理特定Excel错误
            if "File contains corrupted data" in str(e):
                logger.error(f"Excel文件损坏: {path}")
            elif "Unsupported format" in str(e):
                logger.error(f"不支持的Excel格式: {path}")
            raise
    
    @staticmethod
    def _optimize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
        """智能优化DataFrame数据类型以减少内存使用"""
        # 返回优化后的DataFrame
        return df


# 使用示例
def main():
    file=r"C:\data\日线\20250616.xlsx"  # 替换为实际文件路径
    df = DailyReader.read_daily_data(file)
    if df.empty:
        print(f"⚠️ 文件为空: {file}")
    else:
        print(f"✔️ 成功读取数据 - 行数: {len(df)}, 列数: {len(df.columns)}")
        print("数据预览:")
        print(df.head(30))
        print("数据类型:")
        print(df.dtypes)
if __name__ == "__main__":
    main()
