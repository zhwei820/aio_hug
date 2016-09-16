from aiomysql.sa import create_engine
import sqlalchemy as sa

async def init_db(loop=None, host=None, db=None, user=None, password=None):
    engine = await create_engine(
        host=host,
        db=db,
        user=user,
        password=password,
        loop=loop,
        minsize=1,
        maxsize=5
        ) 
    return engine
