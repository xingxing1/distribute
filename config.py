DIALECT ='mysql'
DRIVER = 'mysqldb'
USERNAME = 'root'
PASSWORD = '123456' # 此处填写你的数据库密码
HOST = '192.168.137.161' # 部署到服务器不能用127.0.0.1 得用localhost
PORT = '3306'
DATABSE = 'distribute' # 此处为你建的数据库的名称
SQLALCHEMY_DATABASE_URI ="{}+{}://{}:{}@{}:{}/{}?charset=utf8".format(DIALECT,DRIVER,USERNAME,PASSWORD,HOST,PORT,DATABSE)
# SQLALCHEMY_DATABASE_URI ="{}://{}:{}@{}:{}/{}?charset=utf8".format(DIALECT,USERNAME,PASSWORD,HOST,PORT,DATABSE)


SQLALCHEMY_TRACK_MODIFICATIONS = False
