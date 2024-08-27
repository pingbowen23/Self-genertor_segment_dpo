import json
import re
import argparse
from openai import OpenAI

# 定义正则表达式，用于检测http或https链接
url_pattern = re.compile(r'(https?://|www\.)[^\s]+')
ref_pattern = re.compile(r'REF\d+FIG')
special_str_pattern = '> > > > >'
dictionary_entry_pattern = re.compile(r'\n\n(.*?)\n\n', re.DOTALL)
exam_pattern = re.compile(r'\d+\.\s+[^\n]+\n(?:[a-d]\)\s+[^\n]+\n)+')

def count_chinese_english_matches(input_text):
    # 定义正则表达式，用于匹配相邻 \n\n 之间的内容
    pattern = re.compile(r'\n\n(.*?)\n\n', re.DOTALL)
    
    # 定义检查中文字符的正则表达式
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
    
    # 定义检查英文字符的正则表达式
    english_pattern = re.compile(r'[A-Za-z]')
    
    # 使用正则表达式匹配相邻 \n\n 之间的所有内容
    matches = pattern.findall(input_text)
    
    # 初始化统计变量
    count_both = 0
    total_chinese_count = 0
    total_english_count = 0
    
    for match in matches:
        contains_chinese = chinese_pattern.search(match)
        contains_english = english_pattern.search(match)
        
        # 如果同时包含中文和英文
        if contains_chinese and contains_english:
            count_both += 1
        
        # 统计每个match中中文和英文的总数
        total_chinese_count += len(chinese_pattern.findall(match))
        total_english_count += len(english_pattern.findall(match))
    
    # return count_both, total_chinese_count, total_english_count
    return  total_english_count - total_chinese_count, count_both


def contains_chinese_and_english(text):
    # 定义正则表达式，用于匹配中文字符
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
    
    # 定义正则表达式，用于匹配英文字符
    english_pattern = re.compile(r'[A-Za-z]')
    
    # 检查文本中是否包含中文和英文字符
    contains_chinese = chinese_pattern.search(text)
    contains_english = english_pattern.search(text)
    
    # 如果文本同时包含中文和英文字符，则返回True
    return bool(contains_chinese) and bool(contains_english)

# 打开输入文件进行读取


def count_chinese_and_english(text):
    # Count Chinese characters
    chinese_characters = re.findall(r'[\u4e00-\u9fff]', text)
    chinese_count = len(chinese_characters)
    
    # Count English words
    english_words = re.findall(r'\b[A-Za-z]+\b', text)
    english_count = len(english_words)
    
    return chinese_count, english_count

def clean_exam_bilingual_format(text):
    
    client = OpenAI(
        api_key='sk-TMDtm8NkAIaXwgS03a80CbAa21C940B793348993FbB288Ed',
        base_url='https://yeysai.com/v1/'
    )
    
    text = f"""
    You are given a text, and your task is to determine whether the main content of this text is a test question consisting of a question and several options, or whether it is a bilingual book with alternating English and Chinese sentences.\n\nYou should only output "yes" or "no" without providing any unrelated content.
    ### Input text
    {text[:4096]}
    ### The text ends here. Please, give your response.
    """
    
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo", # 
        messages=[
            {"role": "user", "content": text}
        ]
    )
    
    return completion.choices[0].message.content


def retain_text_from_special_word(text):
    # 正则表达式模式，匹配首字母大写且首字母两边带有双星号的单词
    pattern = r'\*\*[A-Z]\*\*[a-zA-Z]*'
    
    # 查找第一个符合条件的单词及其在文本中的位置
    match = re.search(pattern, text)
    
    if match:
        # 保留从第一个匹配开始的所有内容
        result_text = text[match.start():]
        return result_text
    else:
        return text


if __name__ == '__main__':
    # with open("/home/pingbowen/workspace/DDPO/Self-genertor_segment_dpo/Index_data/data.jsonl", 'r', encoding='utf-8') as file:
    #     for idx,line in enumerate(file):
    #         data = json.loads(line)
    #         words = data["output"]
    #         import pdb; pdb.set_trace()
    #         a = 1
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--language', type=str, default='data.jsonl')
    argparser.add_argument('--input_file', type=str, default="")
    argparser.add_argument('--output_file', type=str, default="")
    args = argparser.parse_args()
    
    input_file = args.input_file 
    output_file = args.output_file
    
    threshold = 0.06 if args.language == 'en' else 0.04
    
    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        for idx,line in enumerate(infile):
            # 解析JSON行
            data = json.loads(line)
            response = data.get('response', '') # response
            
            response = retain_text_from_special_word(response) # 出去版权声明、参考文献等特殊词汇
            
            ref_count = len(re.findall(ref_pattern, response)) # 清理refXfig
            special_count = response.count(special_str_pattern) # 清理">>>>>"
            chinese_count, english_count = count_chinese_and_english(response) # 统计中文和英文字符数
            if args.language == 'en':
                ratio = chinese_count / (chinese_count + english_count)
            else:
                ratio = english_count / (chinese_count + english_count)
            
            if not re.search(url_pattern, response) and ref_count < 3 and special_count < 3 and ratio < threshold : #and 
                outfile.write(line)

    print(f"过滤后的数据已保存到 {output_file}")
