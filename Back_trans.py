from openai import OpenAI
import pandas as pd
import json
import os
import re
import argparse

def get_instruction(text):
    text = f'''
    You're an expert in creating instructions that closely align with the provided text. Assume the author of the provided text followed a detailed set of instructions to produce their work. Your task is to infer what those original instructions may have been by composing your own set of instructions that could recreate key aspects of the given text. You can follow these guiding principles: 
    1.**Comprehension**: ensure you fully grasp the content and purpose of the given text.     
    2.**Clarity and Precision**: make the instruction as specific as possible, avoiding ambiguity.
    3.**Creativity**: depending on the context, consider whether the instruction should allow for some creativity or personalization.\n\nYour task is to generate the following four types of instructions corresponding to the provided long document:
    1. **Precise Instruction**: Provide a writing instruction in fewer than 100 words.
    2. **Medium Instruction**: Offer a writing instruction of around 256 words, including more comprehensive details than the concise instruction.
    3. **Long Instruction**: Craft a writing instruction of approximately 500 words, incorporating additional details and context related to the document.
    4. **Extremely Long Instruction**: Develop a writing instruction of about 1000 words, thoroughly aligned with the document by including sufficient foundational elements and structural information.
    ### The document begins as follows:
    {text}
    ### The document ends here.\nPlease follow this format, do not include any other content:\n\nPrecise Instruction:\n\nMedium Instruction:\n\nLong Instruction:\n\nExtremely Long Instruction:\n\n"
  '''
    
    completion = client.chat.completions.create(
        model="gpt-4-1106-preview", # 
        messages=[
            {"role": "user", "content": text}
        ],
        temperature=1.0,
        # max_tokens=1000,
        top_p=1,
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
    

# 提取各部分内容
def extract_instruction(text, instruction_type):
    if instruction_type == "Precise Instruction":
        pattern = r"Precise Instruction:(.*?)(?=\n\nMedium Instruction:|$)"
    elif instruction_type == "Medium Instruction":
        pattern = r"Medium Instruction:(.*?)(?=\n\nLong Instruction:|$)"
    elif instruction_type == "Long Instruction":
        pattern = r"Long Instruction:(.*?)(?=\n\nExtremely Long Instruction:|$)"
    elif instruction_type == "Extremely Long Instruction":
        pattern = r"Extremely Long Instruction:(.*)"
    else:
        return None
    
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""

def extract_content(data_file,idx):
    df=pd.read_parquet(data_file)
    linejson=json.loads(df['clean_content'][idx])
    line={}
    line['context']=linejson['markdown']
            # line['question']='请总结这本书：'
            #line['question']='The summary of the book is:'
    return line["context"]


def retain_first_32k_words(text):
    # 将文本按空格分割为单词列表
    words = text.split()
    
    # 保留前32k个单词
    first_32k_words = words[:32000]
    
    # 将保留的单词重新组合为文本
    truncated_text = ' '.join(first_32k_words)
    
    return truncated_text

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--context_len_min', type=int)
    parser.add_argument('--context_len_max', type=int)
    parser.add_argument('--number', type=int, default=0)
    args = parser.parse_args()
        
    client = OpenAI(
        api_key='sk-TMDtm8NkAIaXwgS03a80CbAa21C940B793348993FbB288Ed',
        base_url='https://yeysai.com/v1/'
    )
    
    directory = '/data/public/wangshuo/LongContext/data/0722_mb_data/en.boke_kindle_mobi/version=2024-02-22-12/'
    files = os.listdir(directory)
    text = None
    records = []
    
    flag = False
    for filename in files:
        df = pd.read_parquet(os.path.join(directory, filename))
        df["clean_content"] = df["clean_content"].apply(json.loads)
        
        if flag == True:
            break
        
        for idx,content in enumerate(df["clean_content"]):
            length = content.get("n_words",-1)
            
            if length != -1 and length <= args.context_len_max and length >= args.context_len_min:
                response = content.get("markdown")
                response = retain_first_32k_words(response)
                instructions = ""
                # instructions = get_instruction(response)
                
                precise_instruction = extract_instruction(instructions, "Precise Instruction")
                medium_instruction = extract_instruction(instructions, "Medium Instruction")
                long_instruction = extract_instruction(instructions, "Long Instruction")
                extremely_long_instruction = extract_instruction(instructions, "Extremely Long Instruction")
                record = {
                    "response": response,
                    "precise_instruction": precise_instruction,
                    "medium_instruction": medium_instruction,
                    "long_instruction": long_instruction,
                    "extremely_long_instruction": extremely_long_instruction
                }
                records.append(record)
                
                if len(records) % args.number == 0: # 
                    flag = True
                    if flag == True:
                        break
                
                # score = get_score(instruction, "this is a test")
                # json_match = re.search(r'\{.*?\}',score , re.DOTALL)
                
                # if json_match:
                #     json_str = json_match.group(0)
                #     data = json.loads(json_str)
            elif length == -1:
                print(df.head())
                
    output_file = './data/output_32k+.jsonl'

    with open(output_file, 'w',encoding='utf-8') as f:
        for record in records:
            json.dump(record, f,ensure_ascii=False)
            f.write('\n')