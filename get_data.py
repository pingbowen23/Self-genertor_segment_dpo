import json

input_file = './data/output.jsonl'
output_file = './data/output_formated.jsonl'

with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
    for index, line in enumerate(infile):
        data = json.loads(line.strip())
        
        # 根据索引位置选择合适的 instruction
        if index < 2000:
            input_text = data.get("precise_instruction", "")
        elif 2000 <= index < 3500:
            input_text = data.get("medium_instruction", "")
        else:
            input_text = data.get("long_instruction", "")
        
        # 构建新的 JSON 对象
        new_data = {
            "input": input_text,
            "output": data.get("response", "")
        }
        
        # 将新的 JSON 对象写入输出文件
        json.dump(new_data, outfile, ensure_ascii=False)
        outfile.write('\n')
