import pymysql
from time import ctime


# 数据库返回结果对象
class DBResult:
    suc = False  # 执行成功与否
    result = None  # 执行结果，通常是查询结果集，一个 list 嵌套 dict 的结构
    error = None  # 异常信息
    rows = None  # 结果条目数量

    # 返回结果集合中指定位置的一条数据
    def index_of(self, index):
        # 判断是否执行成功，是的话接着判断 index 是否为整型，是的话最后再判断 index 是否在有效范围内
        if self.suc and isinstance(index, int) and self.rows > index >= -self.rows:
            # 条件都成立，返回对应下标的结果
            return self.result[index]

        return None

    # 返回结果集合中的第一条数据
    def get_first(self):
        return self.index_of(0)

    # 返回结果集合中的最后一条数据
    def get_last(self):
        return self.index_of(-1)

    @staticmethod
    def capture(func):
        def decorator(*args, **options):
            # 实例化
            ret = DBResult()

            # 捕获异常
            try:
                # 为 DBResult 对象的 rows 和 result 成员赋值
                ret.rows, ret.result = func(*args, **options)
                # 修改执行状态为 True 表示成功
                ret.suc = True
            except Exception as e:
                print(e)
                # 如果捕获到异常，将异常放进 DBResult 对象的 error 属性中
                ret.error = e
            # 返回 DBResult 对象

            if args[0].debug:
                print('\033[00;37m/ \033[01;35mSql Statement', args[1])
                print('\033[00;37m/ \033[01;31mError:', ret.error) if ret.error is not None else print(
                    '\033[00;37m/ \033[01;32mError:', ret.error)
                print('\033[00;37m/ \033[01;33mRows:', ret.rows)
                print('\033[00;37m/ \033[01;36mResult:', ret.result, '\033[00;37m\n')

            return ret

        # 返回 decorator 方法，其实就相当于返回 DBResult 对象
        return decorator

    def to_dict(self):
        return {
            'suc': self.suc,
            'result': self.result,
            'error': self.error,
            'rows': self.rows
        }


# 数据库模块
class BaseDB:
    # 实例对象初始化方法
    def __init__(self, user, password, database='', host='127.0.0.1', port=3306, charset='utf8',
                 cursor_class=pymysql.cursors.DictCursor, debug=False):
        self.user = user  # 连接用户
        self.password = password  # 连接用户密码
        self.database = database  # 选择的数据库
        self.host = host  # 主机名，默认 127.0.0.1
        self.port = port  # 端口号，默认 3306
        self.charset = charset  # 数据库编码，默认 UTF-8
        self.cursor_class = cursor_class  # 数据库游标类型，默认为 DictCursor，返回的每一行数据集都是个字典
        self.conn = self.connect()  # 数据库连接对象
        self.debug = debug  # 是否开启调试模式

    # 建立连接
    def connect(self):
        # 返回一个数据库连接对象
        return pymysql.connect(host=self.host, user=self.user, port=self.port,
                               passwd=self.password, db=self.database,
                               charset=self.charset, connect_timeout=10,
                               cursorclass=self.cursor_class)

    # 断开连接
    def close(self):
        # 关闭数据库连接
        self.conn.close()

    # 数据操作，增，删，改，查
    @DBResult.capture
    def execute(self, sql, params=None):

        sql = sql.replace('None', 'NULL')

        # 超时重连 MySQL
        try:
            self.conn.ping()

            if self.debug:
                print('/\033[00;37m *********** Database Debug ***********/')
                print('\033[00;37m/ \033[01;34mTime:', ctime())
                print('\033[00;37m/ \033[01;32mPing: Success')
        except:
            if self.debug:
                print('/\033[00;37m *********** Database Debug ***********/')
                print('\033[00;37m/ \033[01;34mTime:', ctime())
                print('\033[00;37m/ \033[01;31mPing: Failure')

            self.conn = self.connect()

        # 获取数据库连接对象上下文
        with self.conn as cursor:
            # 如果参数不为空并且时 Dict 类型时，把 SQL 语句与参数一起传入 execute 中调用，反之直接调用 exevute

            # 执行语句并获取影响条目数量
            rows = cursor.execute(sql, params) if params and isinstance(params, dict) else cursor.execute(sql)

            # 获取执行结果
            result = cursor.fetchall()

        ######################
        # 关闭数据重连，不要问我为什么要关闭，都是血与泪的教训，防止上一个连接中有未清空读完的数据导致下次复用这个连接会发生一些不可描述的事情
        ######################
        self.close()

        # 返回影响条目数量和执行结果
        return rows, result

    # 插入数据并获取最新插入的数据标识，也就是主键索引 ID 字段
    def insert(self, sql, params=None):
        ret = self.execute(sql, params)
        ret.result = self.conn.insert_id()

        return ret

    # 存储过程调用
    @DBResult.capture
    def process(self, func, params=None):
        # 获取数据库连接对象上下文
        with self.conn as cursor:
            # 如果参数不为空并且时 Dict 类型时，把存储过程名与参数一起传入 callproc 中调用，反之直接调用 callproc
            rows = cursor.callproc(func, params) if params and isinstance(params, dict) else cursor.callproc(func)

            # 获取存储过程执行结果
            result = cursor.fetchall()

        return rows, result

    # 创建数据库
    def create_db(self, db_name, db_charset='utf8'):
        return self.execute('CREATE DATABASE %s DEFAULT CHARACTER SET %s' % (db_name, db_charset))

    # 删除数据库
    def drop_db(self, db_name):
        return self.execute('DROP DATABASE %s' % db_name)

    # 选择数据库
    @DBResult.capture
    def choose_db(self, db_name):
        self.conn.select_db(db_name)
        return None, None
