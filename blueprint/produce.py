from . import produce_blue
from flask_restful import Resource, Api
from flask import request, Response, Flask
from models.database import Produce
import json
import time
from models.myRedis import myRedis, mySql
from models.exts import db
import traceback

api = Api(prefix='/shop')
myRedis = myRedis


class ProduceApi(Resource):
    def post(self):
        data = request.get_data().decode('utf-8')
        if not data:
            return {}
        data = json.loads(data)
        proId = data["id"]
        name = data["name"]
        keyRedis = myRedis.generate_redis_key(Produce.__tablename__, Produce.ID.key, proId, name)
        start_time = time.time()
        # identifier = myRedis.acquire_lock("numberDecr")
        if proId and name:
            number = myRedis.redis_conn.get(keyRedis)
            if not number:
                pro = db.session.query(Produce).filter(Produce.ID == proId).first()
                if pro:
                    number = pro.Number
                    myRedis.redis_conn.set(keyRedis, str(number))
                else:
                    return {}
            # number = int(number) - 1
            # if not ("pro" in locals().keys()):
            #     pro = db.session.query(Produce).filter(Produce.ID == proId).first()
            # pro.Number = number
            # db.session.commit()
            # myRedis.redis_conn.decr(keyRedis, 1)
            # myRedis.set_by_count(keyRedis)
            # myRedis.release_lock("numberDecr", identifier)
            print("number:", number)
            print("cost_time: ", time.time() - start_time)
        else:
            return ("查询参数有误！")
        return ("剩余数量: {}".format(number).encode("utf-8"))

    def get(self):
        data = request.get_data().decode('utf-8')
        if not data:
            return {}
        data = json.loads(data)
        proId = data["id"]
        name = data["name"]
        keyRedis = myRedis.generate_redis_key(Produce.__tablename__, Produce.ID.key, proId, name)
        if proId and name:
            start_time = time.time()
            number = myRedis.redis_conn.get(keyRedis)
            if not number:
                pro = Produce.query.filter(Produce.ID == proId).first()
                if pro:
                    number = pro.Number
                    # myRedis.bloomFilter.bfAdd("test", keyRedis)
                    myRedis.redis_conn.set(keyRedis, str(number))
                else:
                    return {}
            print("耗时: ", time.time() - start_time)
        else:
            return ("查询参数有误！")
        return ("剩余数量: {}".format(number))

    def patch(self):
        data = request.get_data().decode('utf-8')
        if not data:
            return {}
        data = json.loads(data)
        proId = data["id"]
        sql = "update produce set Number=Number-1 where ID={} and Number>0".format(int(proId))
        try:
            mySql.execute(sql)
            return "Buy Success!"
        except Exception as e:
            traceback.print_exc()
            return "Buy Fail!"

    def delete(self):
        pass

    def put(self):
        pass


api.add_resource(ProduceApi, '/produce')
