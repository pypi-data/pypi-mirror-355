import aiddit.api.unit_test.gemini_agent as gemini_agent
import aiddit.api.unit_test.tools as tools
import aiddit.utils as utils
import aiddit.model.google_genai as google_genai

if __name__ == "__main__":
    ts = []

    system_prompt = utils.read_file_as_string(
        "/aiddit/api/unit_test/agent_application/prompt/creation_persona_requiremnts_comprehension_agent.md")
    user_input = """
我想做一个'减肥餐'的账号。可以参考一下"https://www.xiaohongshu.com/user/profile/62b5ad45000000001501d4f5?xsec_token=ABXm-4I81wUKqmAymUOZPe9716XL7XE5jAPHQLii2ReLs=&xsec_source=pc_feed，看看他们是怎么做脚本的，我希望最后内容形式跟他们一样，选题我自己找
"""

    ans = gemini_agent.run(user_input=user_input, tools=ts, system_instruction=system_prompt,model=google_genai.MODEL_GEMINI_2_5_PRO_EXPT_0605)

    for part in ans[-1]:
        print(part.text)
