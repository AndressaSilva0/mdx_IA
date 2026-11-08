# MySQL driver setup via PyMySQL (garante compatibilidade no PythonAnywhere e servidores Linux sem necessidade de compilar mysqlclient)
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

