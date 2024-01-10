import json
from typing import List, Dict

import gradio as gr

from kwaiagents.agent_start import AgentService
from kwaiagents.config import CFG


def build_history_list(history: []) -> List[Dict]:
    chat_history = []
    for hist in history:
        question = hist[0] if hist[0] is not None else ""
        answer = hist[1] if hist[1] is not None else ""
        if len(question) > 0 and len(answer) > 0:
            chat_history.append({"query": question,"answer": answer})
    return chat_history


def get_pre_answer(query, history):
    yield history + [[query, None]], ""


def get_base_answer(query, history):
    if query == "" and history[-1][1] is None:
        query = history[-1][0]
        history = history[:-1]

    hist = build_history_list(history)
    args = {
        "id": "webui",
        "query": query,
        "history": hist,
        "use_local_llm": True,
        "llm_name": "kagentlms_qwen_7b_mat",
        "local_llm_host": "localhost",
        "local_llm_port": 8888,
        "lang": "zh",
        "max_iter_num": 5,
    }
    CFG.local_llm_host = args["local_llm_host"]
    CFG.local_llm_port = args["local_llm_port"]
    CFG.use_local_llm = args["use_local_llm"]
    agent_service = AgentService()
    result = agent_service.chat(args)
    history += [[query, result["response"]]]
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

webui_title = """
Inter Agent (大模型自动处理任务) 
"""


def start_ui():
    with gr.Blocks(css=block_css, theme=gr.themes.Default(**default_theme_args)) as demo:
        gr.Markdown(webui_title)
        with gr.Tab("自动代理"):
            with gr.Row():
                with gr.Column(scale=10):
                    # 聊天框模块
                    chatbot = gr.Chatbot([], height=800,
                                         elem_id="chat-box")

                    query = gr.Textbox(placeholder="请输入提问内容，按回车进行提交")
                    query.submit(fn=get_pre_answer,
                                 inputs=[query, chatbot],
                                 outputs=[chatbot, query]).then(fn=get_base_answer,
                                                                inputs=[query, chatbot],
                                                                outputs=[chatbot, query])

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
