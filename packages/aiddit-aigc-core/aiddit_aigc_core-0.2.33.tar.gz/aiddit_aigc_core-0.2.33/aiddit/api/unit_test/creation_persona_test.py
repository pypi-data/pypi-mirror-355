import aiddit.api.unit_test.gemini_agent as gemini_agent
import aiddit.api.unit_test.tools as tools

if __name__ == "__main__":
    ts = [tools.get_weather, tools.get_longitude_and_latitude]
    ans = gemini_agent.run("利用工具`get_weather`、 `get_longitude_and_latitude`获取北京的天气和经纬度", tools=ts)

    pass
