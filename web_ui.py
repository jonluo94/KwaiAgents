import json
import os
import re
import shutil
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


def get_knowledge_table_list(knowledge_txt):
    knowledge_table = list([])
    with open(os.path.join("knowledge", knowledge_txt), 'r') as file:
        for line in file:
            knowledge_table.append([line])
    return knowledge_table


def get_knowledge_list():
    lst_default = []
    kb_root_path = "knowledge"
    lst = os.listdir(kb_root_path)
    if not lst:
        return lst_default
    lst.sort()
    return lst_default + lst


def upload_knowledge(files):
    file_paths = [file.name for file in files]
    kb_root_path = "knowledge"
    for file_path in file_paths:
        # 复制文件到kb_root_path目录
        shutil.copy(file_path, kb_root_path)
    return gr.update(choices=get_knowledge_list())


PAGE_SIZE = 10


def prev_page(page_index: int) -> int:
    return page_index - 1 if page_index > 1 else page_index


def next_page(page_index: int, total_num: int) -> int:
    return page_index + 1 if page_index * PAGE_SIZE < total_num else page_index


def get_preview(kb, page):
    if kb is None or len(kb) == 0:
        return 0, [], gr.update(visible=False)
    knowledges = get_knowledge_table_list(kb)
    return len(knowledges), knowledges[PAGE_SIZE * (page - 1): PAGE_SIZE * page], gr.update(visible=True)


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
}
.modal-box {
  position: fixed !important;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%); /* center horizontally */
  max-width: 1000px;
  max-height: 750px;
  overflow-y: auto;
  background-color: var(--input-background-fill);
  flex-wrap: nowrap !important;
  border: 2px solid black !important;
  z-index: 1000;
  padding: 10px;
}
.dark .modal-box {
  border: 2px solid white !important;
}
"""

default_theme_args = dict(
    font=["Source Sans Pro", 'ui-sans-serif', 'system-ui', 'sans-serif'],
    font_mono=['IBM Plex Mono', 'ui-monospace', 'Consolas', 'monospace'],
)


def start_ui():
    with gr.Blocks(css=block_css, theme=gr.themes.Default(**default_theme_args)) as demo:
        with gr.Tab("Inter Agent"):
            with gr.Row():
                with gr.Column(scale=20):
                    # 聊天框模块
                    chatbot = gr.Chatbot([], height=1000, label="对话",
                                         elem_id="chat-box")
                    with gr.Row():
                        with gr.Column(scale=18):
                            query = gr.Textbox(label="问题", placeholder="请输入提问内容，按回车进行提交")
                        with gr.Column(scale=2):
                            clear = gr.Button("清空历史")
                with gr.Column(scale=8):
                    with gr.Accordion("Agent配置"):
                        with gr.Accordion("模型配置"):
                            use_local_llm = gr.Radio(["是", "否"], label="使用本地模型", value="是")
                            llm_name = gr.Radio(["kagentlms_qwen_7b_mat"], label="模型名称",
                                                value="kagentlms_qwen_7b_mat")
                            local_llm_host = gr.Textbox(label="本地模型主机", placeholder="请输入本地模型主机",
                                                        value="127.0.0.1")
                            local_llm_port = gr.Number(label="本地模型端口", value=8888, precision=0)
                            openai_api_key = gr.Textbox(label="OPENAI_API_KEY", visible=False)
                        with gr.Accordion("知识库"):
                            kbt = gr.Dropdown(choices=get_knowledge_list(), label="知识库文件")

                            with gr.Row():
                                upload_button = gr.UploadButton("上传", file_types=["text"],
                                                                file_count="multiple")
                                data_preview_btn = gr.Button("预览")
                                upload_button.upload(upload_knowledge, upload_button, kbt)

                            with gr.Column(visible=False, elem_classes="modal-box") as preview_box:
                                kdf = gr.List(
                                    headers=["知识"],
                                    datatype=["str"],
                                    type="array"
                                )
                                with gr.Row():
                                    preview_count = gr.Number(label="总数量", value=0, interactive=False, precision=0)
                                    page_index = gr.Number(label="页数", value=1, minimum=1, interactive=False,
                                                           precision=0)
                                with gr.Row():
                                    prev_btn = gr.Button("上一页")
                                    next_btn = gr.Button("下一页")
                                    close_btn = gr.Button("关闭")

                            data_preview_btn.click(
                                get_preview,
                                [kbt, page_index],
                                [preview_count, kdf, preview_box]
                            )
                            prev_btn.click(prev_page, [page_index], [page_index]).then(
                                get_preview, [kbt, page_index], [preview_count, kdf, preview_box]
                            )
                            next_btn.click(next_page, [page_index, preview_count], [page_index]).then(
                                get_preview, [kbt, page_index], [preview_count, kdf, preview_box]
                            )
                            close_btn.click(lambda: gr.update(visible=False), outputs=[preview_box])
                        with gr.Accordion("工具"):
                            tools = gr.CheckboxGroup(["web_search", "browse_website",
                                                      "get_weather_info", "get_calendar_info",
                                                      "time_delta", "get_solar_terms_info",
                                                      "image_gen", "code_interpreter", "math_calculater",
                                                      "bilibili_crawler"],
                                                     label="工具集", info="默认全部")
                        with gr.Accordion("其他", open=False):
                            with gr.Row():
                                max_iter_num = gr.Number(label="最大思考次数", value=3, precision=0)
                                lang = gr.Radio(["zh", "en"], label="语言", value="zh")

                        use_local_llm.change(fn=select_llm, inputs=[use_local_llm],
                                             outputs=[llm_name, local_llm_host, local_llm_port, openai_api_key])

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
