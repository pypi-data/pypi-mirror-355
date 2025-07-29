"""
coding:utf-8
@Software: PyCharm
@Time: 2024/6/4 下午5:48
@Author: xingyun
"""

import pymysql

from minimax_qa_mcp.utils.logger import logger


class MysqlOp(object):
    def __init__(self):
        self.password = "ngo0nZYnPvpoke7P"
        self.host = "10.11.24.40"
        self.database = "qa_tools"
        self.user = "qa_test"
        self.port = 3306

    def connect(self, sql_, data=None, op=None):
        # 连接到MySQL数据库
        conn = pymysql.connect(host=self.host,
                               user=self.user,
                               password=self.password,
                               db=self.database,
                               port=self.port)

        # 创建Cursor对象
        try:
            with conn.cursor() as cursor:
                if op == 'insert':
                    cursor.execute(sql_, data)
                    conn.commit()
                    # 插入成功后，可以获取插入数据的ID（如果表有自增主键）
                    last_id = cursor.lastrowid
                    logger.info(f"Last inserted record ID is {last_id}")
                    return last_id
                elif op == 'select':
                    cursor.execute(sql_, data)
                    # 获取查询结果
                    results = cursor.fetchall()
                    # 打印结果
                    for row in results:
                        logger.info(row)
                    return results
                elif op == 'delete':
                    cursor.execute(sql_, data)
                    # 提交到数据库执行
                    conn.commit()
                    logger.info("记录已成功删除。")
                elif op == 'update':
                    cursor.execute(sql_, data)
                    # 提交到数据库执行
                    conn.commit()
                    logger.info("数据更新成功！")
                    # 获取更新的行数
                    affected_rows = cursor.rowcount
                    logger.info(f"Number of rows affected: {affected_rows}")
                    return affected_rows

        except pymysql.MySQLError as e:
            # 如果发生错误，打印错误信息
            logger.info(f"Error: {e}")
        finally:
            # 关闭Cursor和Connection
            conn.close()

    def batch_insert(self, sql_, batch_data):
        """
        批量插入数据到MySQL数据库
        :param sql_: 带有占位符的SQL插入语句
        :param batch_data: 包含多组参数的列表，每组参数对应一条记录
        :return: 成功插入的记录数
        """
        if not batch_data:
            logger.info("批量插入数据为空，跳过")
            return 0
            
        # 连接到MySQL数据库
        conn = pymysql.connect(host=self.host,
                              user=self.user,
                              password=self.password,
                              db=self.database,
                              port=self.port)
                              
        success_count = 0
        try:
            with conn.cursor() as cursor:
                # 执行批量插入
                success_count = cursor.executemany(sql_, batch_data)
                conn.commit()
                logger.info(f"成功批量插入 {success_count} 条记录")
                return success_count
        except pymysql.MySQLError as e:
            # 如果发生错误，回滚事务并打印错误信息
            conn.rollback()
            logger.info(f"批量插入错误: {e}")
            return 0
        finally:
            # 关闭连接
            conn.close()
            
    def batch_update(self, sql_, batch_data):
        """
        批量更新MySQL数据库中的记录
        :param sql_: 带有占位符的SQL更新语句
        :param batch_data: 包含多组参数的列表，每组参数对应一条记录
        :return: 成功更新的记录数
        """
        if not batch_data:
            logger.info("批量更新数据为空，跳过")
            return 0
            
        # 连接到MySQL数据库
        conn = pymysql.connect(host=self.host,
                              user=self.user,
                              password=self.password,
                              db=self.database,
                              port=self.port)
                              
        success_count = 0
        try:
            with conn.cursor() as cursor:
                # 执行批量更新
                success_count = cursor.executemany(sql_, batch_data)
                conn.commit()
                logger.info(f"成功批量更新 {success_count} 条记录")
                return success_count
        except pymysql.MySQLError as e:
            # 如果发生错误，回滚事务并打印错误信息
            conn.rollback()
            logger.info(f"批量更新错误: {e}")
            return 0
        finally:
            # 关闭连接
            conn.close()


if __name__ == '__main__':
    # group_id = '112233445566'
    # bank_account_no = 'test_1234'
    # card_num = 'test_card_num'
    # redis_key = 'cred_group_id_data'
    # ping_an_resp = 'xxx'
    # time_stamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # mysql_op = MysqlOp('qa_db')
    # # sql_ = 'insert into pingan_un_bank_info (group_id, bank_account_no, card_num, redis_key, pingan_url_resp, creat_time, delete_time) values (%s, %s, %s, %s, %s, %s, %s)'
    # # mysql_op.connect(sql_=sql_, data=(group_id, bank_account_no, card_num, redis_key, ping_an_resp, time_stamp, time_stamp), op='insert')
    # update_sql = 'update pingan_un_bank_info set pingan_url_resp = %s where group_id = %s'
    # mysql_op.connect(sql_=update_sql, data=('test_resp sxxxxxxxxxxxxxx', '112233445566'), op='update')

    # operator_ = 'xingyun1'
    # psm_ = 'open_platform'
    # task_name_ = '开放平台线上环境巡检'
    # job_id = '20240612124204'
    # report_url_ = ''
    # report_tos_key_ = 'qa-tool-1315599187/swingReport/20240604/swing_report_20240604_123456.zip'
    # status_ = True
    # create_time_ = str(datetime.now())
    # env_ = 'prod'
    # sql = 'insert into swing_report (operator, psm, task_name, task_id, report_tos_key, status, create_time, env, job_id) values (%s, %s, %s, %s, %s, %s, %s, %s, %s)'
    # MysqlOp().connect(sql, data=(operator_, psm_, task_name_, task_id_, report_tos_key_, status_, create_time_, env_, job_id), op='insert')
    # sql = 'select * from swing_report limit 10'
    # sql = 'select * from user_group limit 10'
    # # # sql = 'delete from swing_report where operator = %s'
    # # mys = MysqlOp('kaiping_usercore_online_db')
    # mys.connect(sql_=sql, data=None, op='select')
    # sql = 'update swing_report set status = %s where id = %s'
    # mys.connect(sql_=sql, data=('2', 1), op='update')
    sql = "select * from qa_tools.api_meta where psm_name = %s"
    mysql_op = MysqlOp()
    result = mysql_op.connect(sql, data=('weaver.conversation.biz',), op='select')
    print(result)

