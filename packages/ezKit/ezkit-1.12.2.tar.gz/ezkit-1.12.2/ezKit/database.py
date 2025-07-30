"""Database Library"""

# Column, Table, MetaData API
#     https://docs.sqlalchemy.org/en/14/core/metadata.html#column-table-metadata-api
# CursorResult
#     https://docs.sqlalchemy.org/en/20/core/connections.html#sqlalchemy.engine.CursorResult
# PostgreSQL 14 Data Types
#     https://www.postgresql.org/docs/14/datatype.html
import csv
import json
from typing import Any

import pandas as pd
from loguru import logger
from sqlalchemy import CursorResult, Index, create_engine, text
from sqlalchemy.orm import DeclarativeBase

from . import utils


class Database:
    """Database"""

    engine = create_engine("sqlite://")

    def __init__(self, target: str | None = None, **options):
        """Initiation"""
        if isinstance(target, str) and utils.isTrue(target, str):
            if utils.isTrue(options, dict):
                self.engine = create_engine(target, **options)
            else:
                self.engine = create_engine(target)
        else:
            pass

    # ----------------------------------------------------------------------------------------------

    def initializer(self):
        """ensure the parent proc's database connections are not touched in the new connection pool"""
        self.engine.dispose(close=False)

    # ----------------------------------------------------------------------------------------------

    def connect_test(self) -> bool:
        info = "Database connect test"
        try:
            logger.info(f"{info} ......")
            with self.engine.connect() as _:
                logger.success(f"{info} [success]")
                return True
        except Exception as e:
            logger.error(f"{info} [failed]")
            logger.exception(e)
            return False

    # ----------------------------------------------------------------------------------------------

    def metadata_init(self, base: DeclarativeBase, **kwargs) -> bool:
        # https://stackoverflow.com/questions/19175311/how-to-create-only-one-table-with-sqlalchemy
        info = "Database init table"
        try:
            logger.info(f"{info} ......")
            base.metadata.drop_all(self.engine, **kwargs)
            base.metadata.create_all(self.engine, **kwargs)
            logger.success(f"{info} [success]")
            return True
        except Exception as e:
            logger.error(f"{info} [failed]")
            logger.exception(e)
            return False

    # ----------------------------------------------------------------------------------------------

    def create_index(self, index_name, table_field) -> bool:
        # 创建索引
        #   https://stackoverflow.com/a/41254430
        # 示例:
        #   index_name: a_share_list_code_idx1
        #   table_field: Table_a_share_list.code
        info = "Database create index"
        try:
            logger.info(f"{info} ......")
            idx = Index(index_name, table_field)
            try:
                idx.drop(bind=self.engine)
            except Exception as e:
                logger.exception(e)
            idx.create(bind=self.engine)
            logger.success(f"{info} [success]")
            return True
        except Exception as e:
            logger.error(f"{info} [failed]")
            logger.error(e)
            return False

    # ----------------------------------------------------------------------------------------------

    # 私有函数, 保存 execute 的结果到 CSV 文件
    def _result_save(self, file, data) -> bool:
        try:
            outcsv = csv.writer(file)
            outcsv.writerow(data.keys())
            outcsv.writerows(data)
            logger.success("save to csv success")
            return True
        except Exception as e:
            logger.error("save to csv failed")
            logger.exception(e)
            return False

    # ----------------------------------------------------------------------------------------------

    # def execute(
    #     self,
    #     sql: str | None = None,
    #     sql_file: str | None = None,
    #     sql_file_kwargs: dict | None = None,
    #     csv_file: str | None = None,
    #     csv_file_kwargs: dict | None = None
    # ) -> CursorResult[Any] | bool:
    #     """"运行"""

    #     # ------------------------------------------------------------

    #     # 提取 SQL
    #     # 如果 sql 和 sql_file 同时存在, 优先执行 sql

    #     sql_object = None

    #     info: str = f"""Extract SQL: {sql}"""

    #     try:

    #         logger.info(f"{info} ......")

    #         if utils.isTrue(sql, str):

    #             sql_object = sql

    #         elif sql_file is not None and utils.isTrue(sql_file, str):

    #             # 判断文件是否存在
    #             if isinstance(sql_file, str) and utils.check_file_type(sql_file, "file") is False:

    #                 logger.error(f"No such file: {sql_file}")
    #                 return False

    #             if isinstance(sql_file, str) and utils.isTrue(sql_file, str):

    #                 # 读取文件内容
    #                 if sql_file_kwargs is not None and utils.isTrue(sql_file_kwargs, dict):
    #                     with open(sql_file, "r", encoding="utf-8", **sql_file_kwargs) as _file:
    #                         sql_object = _file.read()
    #                 else:
    #                     with open(sql_file, "r", encoding="utf-8") as _file:
    #                         sql_object = _file.read()

    #         else:

    #             logger.error("SQL or SQL file error")
    #             logger.error(f"{info} [failed]")
    #             return False

    #         logger.success(f'{info} [success]')

    #     except Exception as e:

    #         logger.error(f"{info} [failed]")
    #         logger.exception(e)
    #         return False

    #     # ------------------------------------------------------------

    #     # 执行 SQL

    #     info = f"""Execute SQL: {sql_object}"""

    #     try:

    #         logger.info(f"{info} ......")

    #         with self.engine.connect() as connect:

    #             # 执行SQL
    #             if sql_object is None:
    #                 return False

    #             result = connect.execute(text(sql_object))

    #             connect.commit()

    #             if csv_file is None:
    #                 # 如果 csv_file 没有定义, 则直接返回结果
    #                 logger.success(f'{info} [success]')
    #                 return result

    #             # 如果 csv_file 有定义, 则保存结果到 csv_file
    #             info_of_save = f"Save result to file: {csv_file}"
    #             logger.info(f"{info_of_save} .......")

    #             # 保存结果
    #             if isinstance(csv_file_kwargs, dict) and utils.isTrue(csv_file_kwargs, dict):
    #                 with open(csv_file, "w", encoding="utf-8", **csv_file_kwargs) as _file:
    #                     result_of_save = self._result_save(_file, result)
    #             else:
    #                 with open(csv_file, "w", encoding="utf-8") as _file:
    #                     result_of_save = self._result_save(_file, result)

    #             # 检查保存结果
    #             if result_of_save is True:
    #                 logger.success(f'{info_of_save} [success]')
    #                 logger.success(f'{info} [success]')
    #                 return True

    #             logger.error(f"{info_of_save} [failed]")
    #             logger.error(f"{info} [failed]")
    #             return False

    #     except Exception as e:

    #         logger.error(f'{info} [failed]')
    #         logger.exception(e)
    #         return False

    # ----------------------------------------------------------------------------------------------

    def connect_execute(
        self,
        sql: str | None = None,
        read_sql_file: dict | None = None,
        save_to_csv: dict | None = None,
    ) -> CursorResult[Any] | bool | None:

        info: str = "Database connect execute"

        logger.info(f"{info} ......")

        sql_statement: str = ""

        # ------------------------------------------------------------------------------------------

        try:
            # SQL文件优先
            if isinstance(read_sql_file, dict) and utils.isTrue(read_sql_file, dict):
                read_sql_file.pop("encoding")
                read_sql_file_kwargs: dict = {
                    "mode": "r",
                    "encoding": "utf-8",
                    **read_sql_file,
                }
                with open(encoding="utf-8", **read_sql_file_kwargs) as _file:
                    sql_statement = _file.read()
            else:
                if not isinstance(sql, str):
                    return None
                sql_statement = sql
        except Exception as e:
            logger.exception(e)
            return None

        # ------------------------------------------------------------------------------------------

        # 创建一个连接
        with self.engine.connect() as connection:

            # 开始一个事务
            with connection.begin():  # 事务会自动提交或回滚

                try:

                    # 执行 SQL 查询
                    result = connection.execute(text(sql_statement))

                    # 执行成功
                    logger.success(f"{info} [success]")

                    # 返回查询结果
                    if isinstance(save_to_csv, dict) and utils.isTrue(save_to_csv, dict):
                        save_to_csv_kwargs: dict = {
                            "mode": "w",
                            "encoding": "utf-8",
                            **save_to_csv,
                        }
                        with open(encoding="utf-8", **save_to_csv_kwargs) as _file:
                            return self._result_save(_file, result)

                    return result

                except Exception as e:
                    # 发生异常时回滚事务
                    logger.info(f"{info} [failed]")
                    logger.exception(e)
                    return None

    # ----------------------------------------------------------------------------------------------

    def read_with_pandas(self, method: str = "read_sql", result_type: str = "df", **kwargs) -> pd.DataFrame | list | dict:
        """读取数据"""

        # 使用SQL查询数据: 使用 pd.read_sql 的参数
        # read_data_with_pandas(by="sql", result_type="df", sql="SELECT * FROM table ORDER BY date DESC LIMIT 1")

        # 读取表中的数据: 使用 pd.read_sql_table 的参数
        # read_data_with_pandas(by="table", result_type="df", table_name="ashare")

        data: pd.DataFrame = pd.DataFrame()

        info: str = "read data"

        try:

            logger.info(f"{info} ......")

            # 从 kwargs 中删除 con 键
            kwargs.pop("con", None)

            match method:
                case "read_sql":
                    data = pd.read_sql(con=self.engine, **kwargs)
                case "read_sql_query":
                    data = pd.read_sql_query(con=self.engine, **kwargs)
                case "read_sql_table":
                    data = pd.read_sql_table(con=self.engine, **kwargs)
                case _:
                    logger.error(f"{info} [incorrect method: {method}]")
                    return data

            if data.empty:
                logger.error(f"{info} [failed]")
                return data

            logger.success(f"{info} [success]")

            match result_type:
                case "json":
                    return json.loads(data.to_json(orient="records"))
                case "dict":
                    return data.to_dict()
                case "list":
                    # https://stackoverflow.com/a/26716774
                    return data.to_dict("list")
                case _:
                    return data

        except Exception as e:
            logger.error(f"{info} [failed]")
            logger.exception(e)
            return data
