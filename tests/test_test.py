import os
import sys
par_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
sys.path.append(par_dir)

import pytest, json
import hug
from aiohttp import web

api = hug.API(__name__)


@hug.post("/async_test", versions = '1')
async def async_test(request, response, aa):
    return {"code": 0, "message": "test ok!"}


@hug.get("/async_test", versions = '2')
async def async_test1(request, response, aa:hug.types.number, bb):
    ''' doc for this end point
    '''
    return 'test'


@pytest.fixture
def cli(loop, test_client):
    app = api.http.aio_server(loop)
    return loop.run_until_complete(test_client(app))

async def test_post(cli):
    resp = await cli.post('/v1/async_test', data={'aa': 'foo'})
    assert resp.status == 200
    assert json.loads(await resp.text()) == {"code": 0, "message": "test ok!"}

async def test_get(cli):
    resp = await cli.get('/v2/async_test?aa=1&bb=kkk')
    assert resp.status == 200
    assert await resp.text() == '"test"'
