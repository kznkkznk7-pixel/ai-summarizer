import os
import streamlit as st
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# --- 导入 PDF 处理库 ---
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

# 加载 .env 文件中的配置
load_dotenv()

# 初始化 OpenAI 客户端
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
)

# 设置网页配置
st.set_page_config(page_title="智能文件总结助手", page_icon="📝", layout="centered")

def read_pdf_file(uploaded_file):
    """提取 PDF 文件中的文字 (支持 Streamlit 上传对象)"""
    if fitz is None:
        st.error("❌ 错误：尚未安装 PyMuPDF 库。请在终端运行: pip install pymupdf")
        return None
    
    try:
        # 将上传的文件流读入内存
        file_bytes = uploaded_file.read()
        text = ""
        # 使用 stream 参数打开 PDF
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        return text
    except Exception as e:
        st.error(f"❌ 读取 PDF 文件时发生错误: {e}")
        return None

def summarize_text(text):
    """调用 API 进行深度总结"""
    if not text or len(text.strip()) == 0:
        st.warning("⚠️ 警告：提取到的文本内容为空，无法生成总结。")
        return None

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "你是一个极具专业水平的文件总结专家。请对用户提供的文本进行深度总结。\n"
                        "要求：\n"
                        "1. 结构化输出：必须包含【核心观点提取】和【详细内容展开】两个部分。\n"
                        "2. 格式规范：使用清晰的分段、列表（Bullet Points）或数字编号。\n"
                        "3. 语气风格：保持专业、严谨、客观。\n"
                        "4. 语言：中文。"
                    )
                },
                {"role": "user", "content": f"请针对以下文本内容进行深度总结：\n\n{text}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"❌ 调用 API 时发生错误: {e}")
        return None

def main():
    # 界面标题和副标题
    st.title("🚀 智能文件总结助手")
    st.markdown("---")
    st.info("上传一个文件 (.txt, .md, .pdf)，我将为你生成精简且深度的总结报告。")

    # 检查 API KEY
    if not os.getenv("OPENAI_API_KEY"):
        st.error("💡 请先在根目录的 `.env` 文件中设置您的 `OPENAI_API_KEY` 以继续。")
        st.stop()

    # 文件上传组件
    uploaded_file = st.file_uploader("选择一个文件", type=["txt", "md", "pdf"])

    if uploaded_file is not None:
        file_details = {"文件名": uploaded_file.name, "文件大小": f"{uploaded_file.size / 1024:.2f} KB"}
        st.write("📁 文件已选择:", file_details)

        # 点击开始总结
        if st.button("✨ 开始总结", type="primary"):
            with st.spinner("🔍 正在深度解析并总结，请稍候..."):
                content = ""
                # 根据类型读取内容
                if uploaded_file.name.endswith(".pdf"):
                    content = read_pdf_file(uploaded_file)
                else:
                    # 读取文本文件
                    content = uploaded_file.read().decode("utf-8")

                if content:
                    summary = summarize_text(content)
                    
                    if summary:
                        st.success("✅ 总结完成！")
                        st.markdown("### 📝 总结结果：")
                        # 使用二级容器展示结果，看起来更精美
                        st.markdown(f"> **生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        st.markdown(summary)

                        # 准备下载内容
                        download_content = f"总结报告\n{'='*20}\n文件名：{uploaded_file.name}\n生成时间：{datetime.now()}\n\n{summary}"
                        
                        st.download_button(
                            label="📥 下载总结结果",
                            data=download_content,
                            file_name=f"{os.path.splitext(uploaded_file.name)[0]}_总结结果.txt",
                            mime="text/plain"
                        )

    # 侧边栏说明
    with st.sidebar:
        st.header("关于助手")
        st.write("本助手基于 DeepSeek API 开发，支持多种格式文档的一键总结。")
        st.divider()
        st.caption("版本: 4.0 (Web + Streamlit)")

if __name__ == "__main__":
    main()
