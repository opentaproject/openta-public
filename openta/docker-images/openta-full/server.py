from simple_http_server import route, server
import psycopg2
import memcache, redis
import os


@route("/")
def index():

    pgbouncer_ip = os.environ.get('PGBOUNCER_SERVICE_SERVICE_HOST','') 
    memcached_ip = os.environ.get('MEMCACHED_SERVICE_SERVICE_HOST','')
    redis_ip = os.environ.get('REDIS_SERVER_SERVICE_HOST','')
    mc = memcache.Client([f'{memcached_ip}:11211'], debug=0)
    mc.set("test_key", "Hello Memcached!")
    value = mc.get("test_key")
    #print("Retrieved value:", value)
    # Check if the retrieval was success
    res = ''
    try :
        if value is not None:
            res = "Connection success!"
        else:
            res = "Connection failed or key not found."
    except Exception as e:
        res = str(e)
    
    try:
        r = redis.Redis(host=f'{redis_ip}', port=6379, db=0)
        r.set('test', 'hello')
        value = r.get('test')
        if value == b'hello':
            res_redis = "Connection success"
        else :
            res_redis = f"Connection gave wrong value {value}"
        print(res_redis)
    
    except redis.ConnectionError:
        res_redis = "Could not connect to redis"
    
    
    try:
        pgbouncer_ip = os.environ.get('PGBOUNCER_SERVICE_SERVICE_HOST','') 
        pguser = os.environ.get('PGUSER','') 
        pgpassword = os.environ.get('PGPASSWORD','')
        pghost = os.environ.get('DB_SERVER_SERVICE_HOST','')
        dbname = 'postgres'
        conn = psycopg2.connect(
            dbname=dbname,
            user=pguser,
            password=pgpassword,
            host=pghost,
            port='5432',
            connect_timeout=4,
        )
        cur = conn.cursor()
        cur.execute('SELECT version();')
        version = cur.fetchone()
        res_db = version[0].split('on')[0]
        cur.close()
        conn.close()
    except psycopg2.Error as e:
        res_db = f"Error: {e}"
    print("RES_DB" , res_db)
    
    
    try:
        pgbouncer_ip = os.environ.get('PGBOUNCER_SERVICE_SERVICE_HOST','') 
        pguser = os.environ.get('PGUSER','') 
        pgpassword = os.environ.get('PGPASSWORD','')
        pghost = os.environ.get('DB_SERVER_SERVICE_HOST','')
        dbname = 'postgres'
        conn = psycopg2.connect(
            dbname=dbname,
            user=pguser,
            password=pgpassword,
            host=pgbouncer_ip,
            port='5432', 
            connect_timeout=4,
        )
        cur = conn.cursor()
        cur.execute('SELECT version();')
        version = cur.fetchone()
        res_pgbouncer= version[0].split('on')[0]
        print(res_pgbouncer)
        cur.close()
        conn.close()
    except psycopg2.Error as e:
        res_pgbouncer = f"Error: {e}"
        print(f"res_pgbouncer")
    print("RES_PGBOUNCER " , res_pgbouncer)
    return {"hello": "world","memcached" : res , "redis" : res_redis, "db" : res_db, "pgbouncer" : res_pgbouncer }   
    
server.start(port=8888)
