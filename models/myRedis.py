import redis
import json
from collections import OrderedDict
import time
import uuid
from redisbloom.client import Client
import pymysql
import traceback


class MySql(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.mysql = pymysql.connect("192.168.137.161", "root", "123456", "distribute")
        self.cursor = self.mysql.cursor()
    def _reCon(self):
        while True:
            try:
                self.mysql.ping()
                break
            except pymysql.err.OperationalError:
                self.mysql.ping(reconnect=True)
    def execute(self, sql):
        self._reCon()
        try:
            # with self.mysql:
            self.cursor.execute(sql)
            self.mysql.commit()
        except Exception:
            traceback.print_exc()
            # self.mysql.rollback()

    def __call__(self, sql):
        try:
            self.mysql.ping(reconnect=True)
            self.cursor.execute(sql)
            self.mysql.commit()
        except Exception as e:
            traceback.print_exc()
            print(e)
            self.mysql = pymysql.connections.Connection("192.168.137.161", "root", "123456", "distribute")


class MyRedis(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.pool = redis.ConnectionPool(host='192.168.137.160', port=6379, decode_responses=True)
        self.redis_conn = redis.Redis(connection_pool=self.pool)
        self.bloomFilter = Client(connection_pool=self.pool)
        self.setCount = 0

    def set_by_count(self, key):
        if self.setCount < 30:
            self.setCount += 1
            return
        else:
            identifier = self.acquire_lock("produce")
            value = self.redis_conn.get(key)
            self.redis_conn.set(key, (int(value) - 30))
            self.setCount = 0
            self.release_lock("produce", identifier)

    def generate_redis_key(self, tableName, primary, value, field):
        return tableName + ":" + primary + ":" + value + ":" + field

    def get_key_by_kwargs(self, **kwargs):
        dic = OrderedDict()
        dic.update(**kwargs)
        dicStr = json.dumps(dic)
        return dicStr

    def query(self, table, primary, value, *args):
        res = []
        for arg in args:
            res = self.redis_conn.get(table.__tablename__ + ":" + primary + ":" + value + arg)
            if not res:
                table.query.filter(eval("table." + primary) == value).first()

    def query_by_index(self, table, index):
        key = str(index)
        res = self.redis_conn.get(key)
        if res == None:
            res = table.query.filter(key).first()
            if res:
                self.redis_conn.set(key, res)
            else:
                return None
        return self.redis_conn.get(key)

    def update(self, db, data, key):
        # 先更新数据库再删除redis
        # dbRes = table.query(id=key).first()
        db.session.add(data)  # 修改成员数据
        db.session.commit()  # 提交
        self.redis_conn.delete(key)
        # key = self.get_key_by_kwargs(table=table, **kwargs)

    def acquire_lock(self, lock_name, acquire_time=10, time_out=10):
        identifier = str(uuid.uuid4())
        stop = time.time() + acquire_time
        lock = "string:lock:" + lock_name
        while time.time() < stop:
            if self.redis_conn.setnx(lock, identifier):
                self.redis_conn.expire(lock, time_out)
                return identifier
            elif not self.redis_conn.ttl(lock):
                self.redis_conn.expire(lock_name, time_out)
            time.sleep(0.001)
        return False

    def release_lock(self, lock_name, identifier):
        lock = "string:lock:" + lock_name
        pip = self.redis_conn.pipeline(True)
        while True:
            try:
                pip.watch(lock)
                lock_value = self.redis_conn.get(lock)
                if lock_value == None:
                    return True
                if lock_value == identifier:
                    pip.multi()
                    pip.delete(lock)
                    pip.execute()
                    return True
                pip.unwatch()
                break
            except redis.exceptions.WatchError:
                pass
        return False

    def insert_in_bloom(self, bloom, key):
        self.bloomFilter.bfAdd(bloom, key)

    def query_in_bloom(self, bloom, key):
        self.bloomFilter.bfExists(bloom, key)


global myRedis
myRedis = MyRedis()
global mySql
mySql = MySql()
# myRedis.acquire_lock("test")
#
# myRedis.query("user", name='xing', age='26')
if __name__ == '__main__':
    mySql.cursor.execute("select * from produce where Number > 1")
    result = mySql.cursor.fetchall()
    print(result)
