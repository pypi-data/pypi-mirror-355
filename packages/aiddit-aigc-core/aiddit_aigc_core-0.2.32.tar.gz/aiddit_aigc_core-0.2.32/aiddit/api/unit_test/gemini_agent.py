from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import aiddit.model.google_genai as google_genai
import aiddit.api.unit_test.tools as tools_manager
from aiddit.exception.BizException import RetryIgnoreException

load_dotenv()
api_key = os.getenv("google_genai_api_key")
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_not_exception_type


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry=retry_if_not_exception_type(RetryIgnoreException))
def model_request(ask_contents, system_instruction, tools, model=google_genai.MODEL_GEMINI_2_5_PRO_EXPT_0325):
    client = genai.Client(api_key=api_key)
    config = types.GenerateContentConfig(tools=tools if tools else None,
                                         system_instruction=system_instruction,
                                         thinking_config=types.ThinkingConfig(thinking_budget=1024),
                                         automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)                                         )

    # Send request with function declarations
    response = client.models.generate_content(
        model=model,
        contents=ask_contents,
        config=config,
    )

    return response.candidates[0].content.parts


def run(user_input: str, system_instruction=None, tools=None, model=google_genai.MODEL_GEMINI_2_5_PRO_EXPT_0325):
    conversation_contents = []

    ask_content = types.Content(
        role="user",
        parts=[types.Part(text=user_input)]
    )
    conversation_contents.append(ask_content)

    while True:
        response_content = model_request(ask_contents=conversation_contents, system_instruction=system_instruction, tools=tools,
                                         model=model)
        print("response_content ---------->", response_content)
        conversation_contents.append(response_content)
        accept_tool_call_response = False
        if response_content:
            for part in response_content:
                if part.function_call is not None:
                    function_call = part.function_call
                    args = function_call.args
                    print(f"Function call: {function_call.name}")
                    print(f"Arguments: {args}")

                    tools_ans = None
                    try:
                        if function_call.name == tools_manager.get_weather.__name__:
                            tools_ans = tools_manager.get_weather(args.get("city", ""))
                        elif function_call.name == tools_manager.get_longitude_and_latitude.__name__:
                            tools_ans = tools_manager.get_longitude_and_latitude(args.get("city", ""))
                        elif function_call.name == tools_manager.comprehension_xhs_history_note_by_user_id.__name__:
                            tools_ans = tools_manager.comprehension_xhs_history_note_by_user_id(
                                args.get("xhs_user_id", ""), args.get("comprehension_requirements"))
                        elif function_call.name == tools_manager.persona_by_user_id.__name__:
                            tools_ans = tools_manager.persona_by_user_id(args.get("xhs_user_id", ""))
                        elif function_call.name == tools_manager.xhs_search_by_keyword.__name__:
                            tools_ans = tools_manager.xhs_search_by_keyword(args.get("keyword", ""))
                        else:
                            raise Exception(f"Unknown function call: {function_call.name}")

                        if tools_ans:
                            print(f"Function call {function_call.name} result: {tools_ans}")
                            function_response_part = types.Part.from_function_response(
                                name=function_call.name,
                                response={"result": tools_ans},
                            )

                            conversation_contents.append(
                                types.Content(role="user", parts=[function_response_part]))
                            accept_tool_call_response = True
                        else:
                            print(f"Function call {function_call.name} returned no result.")

                    except Exception as e:
                        print(f"Error processing function call: {function_call.nam} , {e}")

        if not accept_tool_call_response:
            break

    return conversation_contents
