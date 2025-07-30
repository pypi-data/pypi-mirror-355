from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv(filename="env.txt"))

from openai import OpenAI

global client 
client = None

# 基于 prompt 生成文本
# gpt-3.5-turbo 
def get_completion(prompt, response_format="text", model="gpt-4o-mini"):
    
    global client 
    if not client:
        # 初始化 OpenAI 客户端
        client = OpenAI()  # 默认使用环境变量中的 OPENAI_API_KEY 和 OPENAI_BASE_URL

    messages = [{"role": "user", "content": prompt}]    # 将 prompt 作为用户输入
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,                                  # 模型输出的随机性，0 表示随机性最小
        # 返回消息的格式，text 或 json_object
        response_format={"type": response_format},
    )

    if response.choices is None:
        err_msg = response.error["message"]
        raise Exception(f"{err_msg}")

    return response.choices[0].message.content          # 返回模型生成的文本


def chat(prompt, response_format="text", model="gpt-4o-mini"):
    """对话
    - prompt:输入文本
    - response_format:text,json_object
    
    """
    return get_completion(prompt, response_format, model)




def chat_stream(msg,model="gpt-4o-mini"):
    global client 
    if not client:
        # 初始化 OpenAI 客户端
        client = OpenAI()  # 默认使用环境变量中的 OPENAI_API_KEY 和 OPENAI_BASE_URL

    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": msg}],
        stream=True,
    )
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="")