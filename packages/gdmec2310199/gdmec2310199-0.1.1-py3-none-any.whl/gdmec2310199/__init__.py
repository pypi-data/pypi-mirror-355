from mcp.server.fastmcp import FastMCP
import json 
import httpx 
import requests

mcpserver = FastMCP('gdmec23120199')
@mcpserver.tool()
def sayHello(name):
    """
    打招呼，问候，寒暄
    :param name:对方的姓名
    :return:打招呼的回复
    """
    return f'{name}你好，很高兴认识您，我是23120199崔宇。'

@mcpserver.tool()
async def getweather(city):
    """
    获取天气信息
    :param city:城市或区县名称（需要使用中文，如北京市，广州市白云区)
    :return:当前实时天气信息,包含有天气情况，气温，体感温度，风向，风速。
    """

    async with httpx.AsyncClient() as client:
        try:
            apikey = '1495d6a02c3a42539e57ee1bde2c8924'
            apihost = 'https://m85huv826h.re.qweatherapi.com'
            geoapi = f'{apihost}/geo/v2/city/lookup'
            weatherapi = f'{apihost}/v7/weather/now'
            geopara = {'location': city, 'key': apikey}
            res = requests.get(geoapi, params=geopara)
            res = json.loads(res.content)
            print(res['location'][0]['name'],)
            id = res['location'][0]['id']
            weatherpara = {'location': id, 'key': apikey}
            res = requests.get(weatherapi, params=weatherpara)
            res = json.loads(res.content)
            res = f"""
            天气:{res['now']['text']},
            气温:{res['now']['temp']},
            体感温度:{res['now']['feelsLike']},
            风向:{res['now']['windDir']},
            风速:{res['now']['windSpeed']},
            """
            return res
        except httpx.HTTPStatusError as e:
            return {'error':f'HTTP 状态码错:{e.response.status_code}'}
        except Exception as e:
            return {'error':f'请求失败:{str(e)}'}


if __name__=='__main__':
    print('23120199崔宇的 mcp server.')
    mcpserver.run(transport='stdio')