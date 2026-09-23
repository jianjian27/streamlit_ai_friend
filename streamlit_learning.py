import streamlit as st

# 设置页面的配置项
st.set_page_config(
    page_title="Streamlit Learning",
    page_icon=":guardsman:",
    layout="wide",
    
    # 设置初始侧边栏状态
    initial_sidebar_state="expanded",

    menu_items={
        'Get Help': 'https://www.streamlit.io/help',
        'Report a bug': "https://github.com/streamlit/streamlit/issues",
        'About': "# This is a header. This is an *markdown* section."
    }
)

# 标题
st.title("Streamlit learning")
st.header("Streamlit level 1")
st.header("Streamlit level 2")

# 段落文字
st.write("Streamlit is an open-source app framework for Machine Learning and Data Science teams. It helps you create beautiful web apps in a short time.")
st.write("""
This is a multi-line paragraph.
You can write as much text as you want here.
""")

# 显示图片
st.image("./image/神.jpg", width = 300 ,caption="hello")

# logo
st.logo("image/神.jpg")

# 显示音频
st.audio("audio/Muriel-Nguyen-Xuan-Chopin-valse-opus64-1.ogg", format="audio/ogg")

# 显示视频
st.video("video/star.mp4", format="video/mp4")

# 显示表格
product_data = {
    "Product": ["Apple", "Banana", "Orange"],
    "Price": [1.2, 0.5, 0.8],
    "Quantity": [10, 20, 15]
}
st.table(product_data,border=True)

# 输入框
name = st.text_input("Enter your name:")
st.write(f"Hello, {name}!")

password = st.text_input("Enter your password:", type="password")
st.write(f"password: {password}")

# 单选按钮
fruit = st.radio("Choose your favorite fruit:", ["Apple", "Banana", "Orange"])
st.write(f"Your favorite fruit is: {fruit}")