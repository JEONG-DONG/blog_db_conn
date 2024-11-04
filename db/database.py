from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool, NullPool
from fastapi import status
from fastapi.exceptions import HTTPException
from datetime import datetime
from dotenv import load_dotenv
import os


# database connection URL
# DATABASE_CONN = "mysql+mysqlconnector://root:1234@localhost:3306/blog_db"

# .env 파일에서 환경변수를 가져옴
load_dotenv()
DATABASE_CONN = os.getenv("DATABASE_CONN")

# create engine
engine = create_engine(DATABASE_CONN, 
                       poolclass=QueuePool,   # QueuePool, NullPool
                       pool_size=20,
                       max_overflow=5,
                       pool_recycle=300)

# create connection : direct
def direct_get_conn():
    conn = None
    try:
        conn = engine.connect()
        return conn
    except SQLAlchemyError as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
                            detail="요청 서비스가 DB 문제로 제공할 수 없습니다.")
    
    
def context_get_conn():
    conn = None
    try:
        conn = engine.connect()
        yield conn  # 호출한 곳으로 conn 객체를 전달후 대기
    except SQLAlchemyError as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
                            detail="요청 서비스가 DB 문제로 제공할 수 없습니다.")
    finally:
        if conn:
            conn.close()



