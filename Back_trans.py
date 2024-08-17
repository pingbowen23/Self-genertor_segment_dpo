from openai import OpenAI
import pandas as pd
import json
import os
import re
def get_instruction(text):
    text = f'''
    Assume the author of the provided text followed a detailed set of instructions to produce their work. Your task is to infer what those original instructions may have been by composing your own set of instructions that could recreate key aspects of the given text.\n\nYour response must include:\n\n  1. An overarching instruction under the "Main Instruction" section that summarizes the goal of the instructions.
    ### Document:
    {text}
    ### Your response:
    '''

    completion = client.chat.completions.create(
        model="gpt-4-1106-preview", # 
        messages=[
            {"role": "user", "content": text}
        ]
    )
    return completion.choices[0].message.content

def get_score(instruction,response):
    text = f'''
    You are an expert in evaluating text quality. Please evaluate the quality of an AI assistant’s response to a user’s writing request. Be as strict as possible.\nYou need to evaluate across the following six dimensions, with scores ranging from 1 to 5. The scoring criteria from 5 to 1 for each dimension are as follows:\n1. Relevance: From content highly relevant and fully applicable to the user’s request to completely irrelevant or inapplicable.\n2. Accuracy: From content completely accurate with no factual errors or misleading information to content with numerous errors and highly misleading.\n3. Coherence: From clear structure with smooth logical connections to disorganized structure with no coherence.\n4. Clarity: From clear language, rich in detail, and easy to understand to confusing expression with minimal details.\n5. Breadth and Depth: From both broad and deep content with a lot of information to seriously lacking breadth and depth with minimal information.\n6. Reading Experience: From excellent reading experience, engaging and easy to understand content to very poor reading experience, boring and hard to understand content.\nPlease evaluate the quality of the following response to a user’s request according to the above requirements.\n⟨User Request⟩\n{instruction}\n⟨/User Request⟩\n⟨Response⟩{response}⟨/Response⟩\nPlease evaluate the quality of the response. You must first provide a brief analysis of its quality, then give a comprehensive analysis with scores for each dimension. The output must strictly follow the JSON format: {{'Analysis': '...', 'Relevance': '...', 'Accuracy': '...', 'Coherence': '...','Clarity': '...', 'Breadth and Depth': '...', 'Reading Experience': '...'}}. You do not need to consider whether the response meets the user’s length requirements in your evaluation. Ensure that only one integer between 1 and 5 is output for each dimension score.
    '''

    completion = client.chat.completions.create(
        model="gpt-4-1106-preview", # 
        messages=[
            {"role": "user", "content": text}
        ]
    )
    
    return completion.choices[0].message.content
    

if __name__ == '__main__':
    client = OpenAI(
        api_key='sk-TMDtm8NkAIaXwgS03a80CbAa21C940B793348993FbB288Ed',
        base_url='https://yeysai.com/v1/'
    )
    
    directory = '/data/public/wangshuo/LongContext/data/0722_mb_data/en.boke_kindle_mobi/version=2024-02-22-12/'
    files = os.listdir(directory)
    # text = None
    # instruction = get_instruction("this is a test")
    # score = get_score(instruction, "this is a test")
    # json_match = re.search(r'\{.*?\}',score , re.DOTALL)
    # json_str = json_match.group(0)
    # data = json.loads(json_str)
    for filename in files:
        df = pd.read_parquet(os.path.join(directory, filename))
        df["clean_content"] = df["clean_content"].apply(json.loads)
        for content in df["clean_content"]:
            length = content.get("n_words",-1)
            
            if length != -1 and length <= 32000:
                text = content.get("markdown")
                instruction = get_instruction(text)
                main_instruction_match = re.search(r'### Main Instruction:\s*(.*?)(\n###|$)', instruction, re.DOTALL)
                
                if main_instruction_match:
                    main_instruction_content = main_instruction_match.group(1).strip()
                
                score = get_score(instruction, "this is a test")
                json_match = re.search(r'\{.*?\}',score , re.DOTALL)
                
                if json_match:
                    json_str = json_match.group(0)
                    data = json.loads(json_str)
            elif length == -1:
                print(df.head())