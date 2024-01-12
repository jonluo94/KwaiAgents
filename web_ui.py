import json
import os
import re
from typing import List, Dict

import gradio as gr

from kwaiagents.agent_start import AgentService


def build_history_list(history: []) -> List[Dict]:
    chat_history = []
    for hist in history:
        question = hist[0] if hist[0] is not None else ""
        answer = hist[1] if hist[1] is not None else ""
        if len(question) > 0 and len(answer) > 0:
            chat_history.append({"query": question, "answer": answer})
    return chat_history


def select_llm(use_local_llm):
    if use_local_llm == "是":
        yield gr.update(choices=["kagentlms_qwen_7b_mat"], value="kagentlms_qwen_7b_mat"), gr.update(
            visible=True), gr.update(visible=True), gr.update(visible=False)
    else:
        yield gr.update(choices=["gpt-3.5-turbo"], value="gpt-3.5-turbo"), gr.update(visible=False), gr.update(
            visible=False), gr.update(visible=True)


def clear_historys():
    yield None


def get_pre_answer(query, history):
    yield history + [[query, None]], ""


def have_image_to_md(text):
    pattern = r"(http[s]?:\/\/[^\s]+(?:jpe?g|png|gif))"
    # Find all matches in the text
    matches = re.findall(pattern, text)
    # Print the matched image links
    for match in matches:
        md_image_url = f"![image]({match})"
        text = text.replace(match, md_image_url)

    return text


def get_base_answer(query, history, use_local_llm, llm_name, local_llm_host, local_llm_port, openai_api_key, lang,
                    max_iter_num, tools):
    if len(tools) == 0:
        tools.append("auto")
    os.environ["OPENAI_API_KEY"] = openai_api_key
    if use_local_llm == "是":
        use_local_llm_b = True
    else:
        use_local_llm_b = False

    if query == "" and history[-1][1] is None:
        query = history[-1][0]
        history = history[:-1]

    hist = build_history_list(history)
    args = {
        "id": "webui",
        "query": query,
        "history": hist,
        "use_local_llm": use_local_llm_b,
        "llm_name": llm_name,
        "local_llm_host": local_llm_host,
        "local_llm_port": local_llm_port,
        "lang": lang,
        "max_iter_num": max_iter_num,
        "tool_names": tools,
    }
    agent_service = AgentService()
    result = agent_service.chat(args)

    chain_msg = result["chain_msg_str"] + have_image_to_md(result["response"])
    msg = ""
    history += [[query, ""]]
    for char in chain_msg:
        msg += char
        history[-1][1] = msg
        yield history, ""


block_css = """.importantButton {
    background: linear-gradient(45deg, #7e0570,#5d1c99, #6e00ff) !important;
    border: none !important;
}
.importantButton:hover {
    background: linear-gradient(45deg, #ff00e0,#8500ff, #6e00ff) !important;
    border: none !important;
}"""

default_theme_args = dict(
    font=["Source Sans Pro", 'ui-sans-serif', 'system-ui', 'sans-serif'],
    font_mono=['IBM Plex Mono', 'ui-monospace', 'Consolas', 'monospace'],
)


def start_ui():
    with gr.Blocks(css=block_css, theme=gr.themes.Default(**default_theme_args)) as demo:
        with gr.Tab("Inter Agent"):
            with gr.Row():
                with gr.Column(scale=15):
                    # 聊天框模块
                    chatbot = gr.Chatbot([], height=1000, label="对话",
                                         elem_id="chat-box")

                with gr.Column(scale=5):
                    with gr.Accordion("Agent配置"):
                        with gr.Accordion("模型配置"):
                            use_local_llm = gr.Radio(["是", "否"], label="使用本地模型", value="是")
                            llm_name = gr.Radio(["kagentlms_qwen_7b_mat"], label="模型名称",
                                                value="kagentlms_qwen_7b_mat")
                            local_llm_host = gr.Textbox(label="本地模型主机", placeholder="请输入本地模型主机",
                                                        value="127.0.0.1")
                            local_llm_port = gr.Number(label="本地模型端口", value=8888, precision=0)
                            openai_api_key = gr.Textbox(label="OPENAI_API_KEY", visible=False)
                        lang = gr.Radio(["zh", "en"], label="语言", value="zh")
                        max_iter_num = gr.Number(label="最大思考次数", value=5, precision=0)
                        tools = gr.CheckboxGroup(["web_search", "browse_website",
                                                  "get_weather_info", "get_calendar_info",
                                                  "time_delta", "get_solar_terms_info",
                                                  "image_gen", "code_interpreter", "math_calculater"],
                                                 label="工具", info="默认全部")
                        use_local_llm.change(fn=select_llm, inputs=[use_local_llm],
                                             outputs=[llm_name, local_llm_host, local_llm_port, openai_api_key])

            with gr.Row():
                with gr.Column(scale=15):
                    query = gr.Textbox(label="问题", placeholder="请输入提问内容，按回车进行提交")
                with gr.Column(scale=5):
                    clear = gr.Button("清空历史")

                query.submit(fn=get_pre_answer,
                             inputs=[query, chatbot],
                             outputs=[chatbot, query]).then(fn=get_base_answer,
                                                            inputs=[query, chatbot,
                                                                    use_local_llm, llm_name, local_llm_host,
                                                                    local_llm_port, openai_api_key,
                                                                    lang, max_iter_num, tools],
                                                            outputs=[chatbot, query])
                clear.click(fn=clear_historys,
                            inputs=[],
                            outputs=[chatbot])

        demo.load(
            queue=True,
            show_progress=False,
        )

    (demo
     .queue()
     .launch(server_name="0.0.0.0",
             server_port=7860,
             show_api=False,
             share=False,
             inbrowser=False))


if __name__ == '__main__':
    start_ui()
