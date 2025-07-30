import os 
import cx_Oracle as ora
import pymysql
import pandas as pd 
import sqlite3
from tpf import read

class DbConnect():
    def __init__(self) -> None:
        """数据库连接初始化,
        每次生产一个新的游标,游标是复用还是关闭由使用者决定
        """
        # 读取配置并加载完成连接初始化，外定方法返回句柄 
        # self.oradb = self.oracle()

        local_file_path=os.path.abspath(__file__)
        father_path=os.path.abspath(os.path.dirname(local_file_path)+os.path.sep+".")
        file_path = os.path.join(father_path,"db.db")
        self.db_file = file_path
        # self.db_file = "db.db"
        self._db_dict = {}
        if os.path.exists(self.db_file):
            with open(self.db_file,'r',encoding="utf-8") as f:
                db_dict = eval(f.read())
                self._db_dict = db_dict
        if len(self._db_dict)==0:
            print("没有配置数据库连接信息")
            
    def __enter__(self):
        # self.openedFile = open(self.filename, self.mode)
        # return self.openedFile
        pass 

    def __exit__(self, *unused):
        # self.openedFile.close()
        pass 
    
    def is_ora_open(self,conn):
        try:
            # 尝试执行一个轻量级操作
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 FROM dual")
                return True
        except ora.DatabaseError:
            return False
            
    def oradb(self, name="ora3"):
        """每次创建一个新游标,但若有已打开的连接会优先使用已有连接
        """
        db_dict = self._db_dict
        conn_name = "{}.username.connect".format(name) 
        _dbconnect = db_dict.get(conn_name,None)
        is_conn_open = True   
        if _dbconnect is None:
            is_conn_open = False
        # else:
        #     print(_dbconnect)  
            
        #and self.is_ora_open(_dbconnect)
        # if is_conn_open:
        #     return _dbconnect
                
        _dbconnect = None
        if len(db_dict) > 0 :
            if db_dict["{}.username".format(name)]:

                try:
                    _dbconnect = ora.connect(db_dict["{}.username".format(name)],db_dict["{}.password".format(name)],db_dict["{}.url".format(name)])
                except:
                    error_msg = "{} db connect error".format(db_dict["{}.url".format(name)])
                    print(error_msg)
                    
            else:
                print("{} 连接信息不存在".format(name))

        self._db_dict[conn_name] = _dbconnect
        return _dbconnect 

    def casedb(self):
        """每次创建一个新游标,是复用还是关闭请自行判断 
        """
        db_dict = self._db_dict
        _casedb = None
        if len(db_dict) > 0 :
            if db_dict["case.username"]:
                try:
                    _casedb = ora.connect(db_dict["case.username"],db_dict["case.password"],db_dict["case.url"])
                except:
               
               
                    error_msg = "{} case db connect error".format(db_dict["case.url"])
                    print(error_msg)
                    
            else:
                print("case 连接信息不存在")

        return _casedb 

    def reportdb(self):
        """每次创建一个新游标,是复用还是关闭请自行判断 
        """
        db_dict = self._db_dict
        _reportdb = None
        if len(db_dict) > 0 :
            if db_dict["report.username"]:
                try:
                    _reportdb = ora.connect(db_dict["report.username"],db_dict["report.password"],db_dict["report.url"])
                except:
                    error_msg = "{} report db connect error".format(db_dict["report.url"])
                    print(error_msg)
            else:
                print("report 连接信息不存在")
        

        return _reportdb 

    def mysql(self,name=None):
        """每次创建一个新游标,是复用还是关闭请自行判断 
        """
        db_dict = self._db_dict
        _mysql = None 
        if len(db_dict) > 0 :
            if name:
                if db_dict["{}.host".format(name)]:
                    try:
                        _mysql = pymysql.connect(host=db_dict["{}.host".format(name)],
                                    port=db_dict["{}.port".format(name)],
                                    user=db_dict["{}.username".format(name)],
                                    password=db_dict["{}.password".format(name)],
                                    database=db_dict["{}.database".format(name)],
                                    charset=db_dict["{}.charset".format(name)])

                    except  Exception as e:
                        error_msg = "{} {} mysql db connect error".format(db_dict["{}.host".format(name)],db_dict["{}.port".format(name)])
                        print(error_msg)
                        print(e)
                        
                else:
                    print("mysql {} 连接信息不存在".format(name))
                    
            else:
                if db_dict["db1.host"]:
                    try:
                        _mysql = pymysql.connect(host=db_dict["db1.host"],
                                    port=db_dict["db1.port"],
                                    user=db_dict["db1.username"],
                                    password=db_dict["db1.password"],
                                    database=db_dict["db1.database"],
                                    charset=db_dict["db1.charset"])

                    except:
                        error_msg = "{} mysql db connect error".format(db_dict["db1.host"])
                        print(error_msg)
                        
                else:
                    print("mysql 连接信息不存在")
                
        return _mysql
        
    def write(self,obj):
        ss = str(obj)
        with open(self.db_file,"w",encoding="utf-8") as f:
            f.write(ss)

class DbTools(DbConnect):
    def __init__(self,db_dict=None) -> None:
        super().__init__()
        # if db_dict:
        #     self.resetPwd(db_dict=db_dict)
        #     super().__init__() # 重置密码后再初始化一次 

    def get_dbfile(self):
        return self.db_file

    def getPwd(self):
        """读取文件中的内容"""
        with open(self.db_file, 'r', encoding='utf-8') as file:
            content = file.read()
        return content

    def resetPwd(self, db_dict=None):
        """每次写入都会覆盖之前的字典
        """
        if db_dict :
            self.write(db_dict)
        else:
            db_dict = {
                "report.username":"case",
                "report.password":"rootroot",
                "report.url":"192.168.111.220:1521/case",
                "case.username":"case",
                "case.password":"rootroot",
                "case.url":"192.168.111.220:1521/case",
                "ora3.username":"case",
                "ora3.password":"rootroot",
                "ora3.url":"192.168.111.220:1521/case",
                "db1.username":"automng",
                "db1.password":"Automng_123",
                "db1.host":"127.0.0.1",
                "db1.port":13301,
                "db1.database":"db1",
                "db1.charset":"utf8",
            }
            self.write(db_dict)
    
    def ora_table_stuct(self,table_name):
        sql = """
        select column_name,data_type,DATA_LENGTH From all_tab_columns  
        where table_name=upper('{}')
        """.format(table_name)
        print(sql)
        res = ""
        col = []
        with self.reportdb() as connection:
            cursor = connection.cursor()
            query = cursor.execute(sql)
            col = [c[0] for c in cursor.description]
            res = query.fetchall()
            data = pd.DataFrame(res,columns=col) 
            cursor.close()
            # connection.commit()
        return data

    def ora_select(self,sql,name='report',show_sql=False,lob=False):
        if show_sql:
            print(sql)
        res = ""
        col = []
        with self.oradb(name=name) as connection:
            cursor = connection.cursor()
            query = cursor.execute(sql)
            col = [c[0] for c in cursor.description]
            if lob:
                # 一次性读取所有结果中的 LOB 数据
                res = [(lob.read() if lob is not None else None,) for lob, in query.fetchall()]
            else:
                res = query.fetchall()
            data = pd.DataFrame(res,columns=col) 
            cursor.close()
            # connection.commit()
        return data
    
    def ora_exec(self,sql, name='report'):
        """批量插入请参考
        https://www.cnblogs.com/cszcoder/p/16248561.html
        """
        print(sql)
        res = ""
        col = []
        with self.oradb(name=name) as connection:
            cursor = connection.cursor()
            cursor.execute(sql)
            connection.commit()
            cursor.close()
            
    
    def select(self, sql,name='db1',show_sql=False):
        """mysql select 
        """
        if show_sql:
            print(sql)
        res = ""
        col = []
        with self.mysql(name=name) as connection:
            cursor = connection.cursor()
            cursor.execute(sql)
            col = [c[0] for c in cursor.description]
            
            # res type list
            # res[0] type tuple 
            res = cursor.fetchall()   
            data = pd.DataFrame(res,columns=col) 
            cursor.close()
            # connection.commit()
        return data 

    def show_mysql_version(self,name='db1'):
        sql = """
        SELECT VERSION()
        """
        print(sql)
        res = ""
        col = []
        with self.mysql(name=name) as connection:
            cursor = connection.cursor()
            cursor.execute(sql)
             # 使用 fetchone() 方法获取单条数据.
            data = cursor.fetchone()
            print ("数据库连接成功,version =",data[0])
            cursor.close()
            # connection.commit()
        return data 


    def exec(self,sql,name='db1'):
        """创建记录表
        """
        res=-1
        with self.mysql(name=name) as connection:
            cursor = connection.cursor()
            res=cursor.execute(sql)
            connection.commit()
            cursor.close()
        return res


    def insert_many(self,col_list,value_list,table_name, name='db1', insert_type="ignore"):
        """
        参数列表
        --------------------------
        - col_list:[]
        - value_list:[(),()]
        - insert_type:replace/ignore


        return
        ---------------------------------
        - res:影响数据库行数


        举例
        -------------------------------------

        mock_data = [
            (1, 1001, 'aaa', 70.00, 0, '2024-03-12 10:00:00', None),
            (2, 1001, 'bbb', 65.50, 1, '2025-05-16 12:00:00', '2025-05-16 12:00:00')
        ]

        col_list=['id', 'customer_id', 'product_id', 'price', 'status', 'create_time', 'pay_time']
        
        ms.insert_many(col_list,mock_data,table_name='orders')

        
        """
        if insert_type=="replace":
            sql_insert = "replace into {}({}) values({})"
        else:
            sql_insert = "insert ignore into {}({}) values({})"
            
        cols = ','. join(col_list)
        col_num = len(col_list)-1
        place_flag = '%s'
        for i in range(col_num):
            place_flag = place_flag+','+'%s'

        #要以可插入mysql的类型查询出来
        sql_to_mysql= sql_insert.format(table_name, cols, place_flag)
        print(sql_to_mysql)
        print(value_list[0])
        res = 0
        with self.mysql(name=name) as connection:
            cursor = connection.cursor()
            res=cursor.executemany(sql_to_mysql, value_list)
            connection.commit()
            print(f"{table_name} insert 插入行数: {res}\n")
            cursor.close()
        return res
    
    def pd2mysql(self,data_pd,table_name,dbname):
        """
        - insert_type:ignore/replace
        
        -- 用法
        ms.pd2mysql(data_pd,table_name="students",dbname="db1",insert_type="ignore")
        
        """
        res = 0
        col_list = data_pd.columns.tolist()
        values=[]
        for i in range(data_pd.shape[0]):
            row = data_pd.iloc[i]
            values.append(tuple(row.tolist()))

        if len(values)>0:
            res = self.insert_many(col_list=col_list,value_list=values,table_name=table_name,name=dbname,insert_type="ignore")
        return res 

def getPwd():
    """读取文件中的内容"""
    dt = DbTools()
    # content = dt.getPwd()
    db_file = dt.get_dbfile() 
    content = read(db_file)
    return content

def reset_passwd(db_dict):
    """重置密码，会抹去原来所有密码并写入新密码
    example
    -------------------------------------------
    from tpf.db import reset_passwd
    reset_passwd({"db1.username":"automng",
                "db1.password":"Automng_123",
                "db1.host":"11.11.11.11",
                "db1.port":3306,
                "db1.database":"db1",
                "db1.charset":"utf8",
                "report.username":"aaa",
                "report.password":"aaabbbcccddd",
                "report.url":"10.11.111.11:1521/orcl"})
    
    - report:oracle连接方式
    - db1:mysql连接方式
    """

    dt = DbTools()
    dt.resetPwd(db_dict=db_dict)
    
def update_passwd(db_dict):
    """更新密码，字典同key则更新，否则写入
    example
    -------------------------------------------
    from tpf.db import reset_passwd
    reset_passwd({"db1.username":"automng",
                "db1.password":"Automng_123",
                "db1.host":"11.11.11.11",
                "db1.port":3306,
                "db1.database":"db1",
                "db1.charset":"utf8",
                "report.username":"aaa",
                "report.password":"aaabbbcccddd",
                "report.url":"10.11.111.11:1521/orcl"})
    
    - report:oracle连接方式
    - db1:mysql连接方式
    """
    old_pwd = getPwd()
    old_pwd.update(db_dict)

    dt = DbTools()
    dt.resetPwd(db_dict=old_pwd)


class OracleDb():
    def __init__(self,name):
        self.name = name
        self.ms = DbTools()
        
    def select(self, sql, name=None,show_sql=False,lob=False):
        """
        - name:为None时使用初始化的name
        - lob:True表示查询lob字段，但仅限单列查询
        """
        if show_sql:
            print(sql)
        if name is None:
            name = self.name
        res = self.ms.ora_select(sql=sql,name=name,lob=lob)
        return res
    
    def exec(self, sql, name=None):
        """- name:为None时使用初始化的name"""
        if name is None:
            name = self.name
        self.ms.ora_exec(sql=sql,name=name)
        
    def insert_many(self, col_list, value_list, table_name, insert_type = None, name=None):
        """
        - name:为None时使用初始化的name
        
        批量插入数据
        参数列表
        --------------------------
        - col_list:[] 列英文名称
        - value_list:[(),()] 批量数据与列英文名称一致
        举例
        -------------------------------------
        col_list=['id', 'customer_id', 'product_id', 'price', 'status', 'create_time', 'pay_time']
        value_list = [
            (1, 1001, 'aaa', 70.00, 0, '2024-03-12 10:00:00', None),
            (2, 1001, 'bbb', 65.50, 1, '2025-05-16 12:00:00', '2025-05-16 12:00:00')
        ]
        ms.insert_many(col_list,value_list,table_name='orders')


        """
        if name is None:
            name = self.name
            
        if insert_type:
            if insert_type == "replace":
                #存在则替换，不存在则插入
                sql_insert = "replace into {}({}) values({})"
            else:
                #如果表中数据已存在则不再插入
                sql_insert = "insert ignore into {}({}) values({})"
        else:
            sql_insert = "insert into {}({}) values({})"

        # cols = ','.join(col_list)
        cols = ','.join(f'"{col}"' for col in col_list)
        col_num = len(col_list) - 1
        place_flag = '?'  # python为%s,java为?
        for i in range(col_num):
            place_flag = place_flag + ',' + '?'

        # 要以可插入mysql的类型查询出来
        sql_to_mysql = sql_insert.format(table_name, cols, place_flag)
    
        with self.oradb(name=name) as connection:
            cursor = None
            try:
                cursor = connection.cursor()
                cursor.executemany(sql_to_mysql, value_list)
                connection.commit()
            finally:
                if cursor is not None:
                    cursor.close()

    def insert_many_pd(self, data_pd, table_name, show_msg=False, name=None):
        """批量插入数据
        - name:为None时使用初始化的name
        - insert_type:ignore/replace

        -- 用法
        ms.pd2mysql(data_pd,table_name="students",insert_type="ignore")

        """
        col_list = data_pd.columns.tolist()
        values = []
        for i in range(data_pd.shape[0]):
            row = data_pd.iloc[i]
            values.append(tuple(row.tolist()))
        if show_msg:
            print("col_list:\n",col_list)
            print("values:\n",values)
        if len(values) > 0:
            self.insert_many(col_list=col_list, value_list=values, table_name=table_name,name=name)

   
class MyDb():
    def __init__(self,name="link_mysql") -> None:
        self.dbtool = DbTools()
        self.name = name
        
    def select(self,sql,show_sql=False):
        if show_sql:
            print(sql)
        return self.dbtool.select(sql,name=self.name)
    
    def exec(self,sql):
        self.dbtool.exec(sql=sql,name=self.name)
        
    def insert_many(self,col_list,value_list,table_name):
        res = self.dbtool.insert_many(col_list=col_list,value_list=value_list,table_name=table_name, name=self.name, insert_type="ignore")
        return res
    
    def pd2mysql(self,data_pd,table_name):
        res = self.dbtool.pd2mysql(data_pd=data_pd,table_name=table_name,dbname=self.name)
        return res     
 

class SqLite():
    def __init__(self,db="vo.db"):
        # 连接到数据库（如果数据库文件不存在，会自动创建）
        self.conn = sqlite3.connect('vo.db')

    def exec(self, sql):
        cursor = self.conn.cursor()
        cursor.execute(sql)
        self.conn.commit()
        cursor.close()

    def select(self, sql, columns=None):
        cursor = self.conn.cursor()
        # 查询数据
        cursor.execute(sql)
        rows = cursor.fetchall()
        if columns:
            df = pd.DataFrame(rows, columns=columns)
        else:
            df = pd.DataFrame(rows)
        cursor.close()
        return df 
        
    def close(self):
        self.conn.close()

    def init_order(self):
        database_schema_string = """
        CREATE TABLE orders (
            id INT PRIMARY KEY NOT NULL, -- 主键，不允许为空
            customer_id INT NOT NULL, -- 客户ID，不允许为空
            product_id STR NOT NULL, -- 产品ID，不允许为空
            price DECIMAL(10,2) NOT NULL, -- 价格，不允许为空
            status INT NOT NULL, -- 订单状态，整数类型，不允许为空。0代表待支付，1代表已支付，2代表已退款
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 创建时间，默认为当前时间
            pay_time TIMESTAMP -- 支付时间，可以为空
        );
        """ 
                
        cursor = self.conn.cursor()
        cursor.execute(database_schema_string)

        mock_data = [
            (1, 1001, 'TSHIRT_1', 50.00, 0, '2023-09-12 10:00:00', None),
            (2, 1001, 'TSHIRT_2', 75.50, 1, '2023-09-16 11:00:00', '2023-08-16 12:00:00'),
            (3, 1002, 'SHOES_X2', 25.25, 2, '2023-10-17 12:30:00', '2023-08-17 13:00:00'),
            (4, 1003, 'SHOES_X2', 25.25, 1, '2023-10-17 12:30:00', '2023-08-17 13:00:00'),
            (5, 1003, 'HAT_Z112', 60.75, 1, '2023-10-20 14:00:00', '2023-08-20 15:00:00'),
            (6, 1002, 'WATCH_X001', 90.00, 0, '2023-10-28 16:00:00', None)
        ]

        for record in mock_data:
            cursor.execute('''
            INSERT INTO orders (id, customer_id, product_id, price, status, create_time, pay_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', record)

        self.conn.commit()
        
    def select_order(self):
        sql = "select id, customer_id, product_id, price, status, create_time, pay_time from orders" 
        df = self.select(sql,columns=["id", "customer_id", "product_id", "price", "status", "create_time", "pay_time"])
        return df 

    def select_single(self, sql, columns=None):
        """单值查询"""
        res = self.select(sql)
        if res.shape[0]>0:
            value = res.iloc[0][0]
            return value 
        return None 
                
        
if __name__=="__main__":
    from tpf.db import MyDb,reset_passwd
    reset_passwd({"db1.username":"automng",
                    "db1.password":"Automng_123",
                    "db1.host":"11.11.11.11",
                    "db1.port":13301,
                    "db1.database":"db1",
                    "db1.charset":"utf8",
                    "report.username":"aaa",
                    "report.password":"aaabbbcccddd",
                    "report.url":"10.11.111.11:1521/orcl"})

    db = MyDb(name='db1')
    db.select("select version()")


    sdb = SqLite()
    sql= '''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER
    )
    '''
    sdb.exec(sql)
    #插入数据
    sdb.exec("INSERT INTO users (name, age) VALUES ('Alice', 25)")
    sdb.exec("INSERT INTO users (name, age) VALUES ('Bob', 30)")
    sql = "SELECT * FROM users"
    sdb.select(sql, columns=["id","name","age"])
    
    
    sdb.init_order()
    sdb.select_order()
    
    print("----------over -------")
