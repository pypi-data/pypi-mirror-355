import aiddit.model.google_genai as google_genai
from aiddit.api.xhs_api import _get_xhs_account_info, _get_xhs_account_note_list
import aiddit.utils as utils
import aiddit.api.history_note as history_note
import aiddit.api.persona.prompt as prompt
from aiddit.model.google_genai import GenaiConversationMessage


def comprehension_xhs_history_note_by_user_id(xhs_user_id: str, comprehension_requirements: str | None = None):
    account_info = _get_xhs_account_info(xhs_user_id)
    account_history_note_path = _get_xhs_account_note_list(xhs_user_id)

    model = google_genai.MODEL_GEMINI_2_5_FLASH

    history_notes = utils.load_from_json_dir(account_history_note_path)
    history_messages = []
    history_messages.extend(history_note.build_history_note_messages(history_notes))

    # 从小红书账号信息中获取`选题`人设信息
    persona_by_xhs_user_id_prompt = prompt.COMPREHENSION_XHS_HISTORY_NOTE_BY_USER_ID_PROMPT.format(
        account_name=account_info.get("account_name"),
        account_description=account_info.get("description"),
        requirements=comprehension_requirements)
    persona_conversation_user_message = GenaiConversationMessage.one("user", persona_by_xhs_user_id_prompt)

    persona_conversation_model_message = google_genai.google_genai_output_images_and_text(
        persona_conversation_user_message,
        model=model,
        history_messages=history_messages,
        system_instruction_prompt="")
    ans_content = persona_conversation_model_message.content[0].value

    return ans_content, [persona_conversation_model_message.usage_metadata]
