import aiddit.api.unit_test.gemini_agent as gemini_agent
import aiddit.api.unit_test.tools as tools
import aiddit.utils as utils

if __name__ == "__main__":
    ts = [tools.comprehension_xhs_history_note_by_user_id, tools.persona_by_user_id, tools.xhs_search_by_keyword]


    system_prompt = utils.read_file_as_string("/aiddit/agent/agent_prompt_backup/creation_persona_topic_agent.md")
    user_input = """我想在旅行内容中融入更多本地美食元素。
    """

    ans = gemini_agent.run(user_input=user_input, tools=ts, system_instruction=system_prompt)

    for part in ans[-1]:
        print(part.text)