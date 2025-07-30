import json
import logging
import re
import pandas as pd
from typing import Dict
from dataflow.utils.registry import GENERATOR_REGISTRY
from dataflow.generator.utils.LocalModelGenerator import LocalModelGenerator
from dataflow.generator.utils.APIGenerator_aisuite import APIGenerator_aisuite
from dataflow.generator.utils.APIGenerator_request import APIGenerator_request
from dataflow.utils.utils import get_logger
from dataflow.data import MyScaleStorage, DatabaseConfig
import os


def extract_json_object(model_output):
    """提取第一个包含 instruction 和 output 字段的 JSON 对象"""
    json_pattern = r'\{[^}]*\}'
    matches = re.findall(json_pattern, model_output)
    for match in matches:
        try:
            obj = json.loads(match)
            if 'instruction' in obj and 'output' in obj:
                return obj
        except json.JSONDecodeError:
            continue
    return None


@GENERATOR_REGISTRY.register()
class SupervisedFinetuneGenerator:
    def __init__(self, config: Dict):
        self.logger = get_logger()
        self.config = config
        use_db = config.get("use_db", False) or os.environ.get("USE_DB", "").lower() == "true"
        if use_db:
            db_config = DatabaseConfig(
                host=os.environ.get('MYSCALE_HOST', 'localhost'),
                port=int(os.environ.get('MYSCALE_PORT', '9000')),
                db_name=os.environ.get('MYSCALE_DATABASE', 'dataflow'),
                table_name=os.environ.get('MYSCALE_TABLE_NAME', ''),
                username=os.environ.get('MYSCALE_USER', ''),
                password=os.environ.get('MYSCALE_PASSWORD', '')
            )
            self.storage = MyScaleStorage(db_config)
            self.input_file = None
            self.output_file = None
        else:
            self.input_file = config['input_file']
            self.output_file = config['output_file']

        self.key = config['keys']
        self.model = self.__init_model__()
        self.stage = config['stage']
        self.pipeline_id = config['pipeline_id']
        self.eval_stage = config['eval_stage'] 
        self.read_format = config['read_format']
        self.read_syn = config['read_syn']
        self.read_min_score = config.get('read_min_score', [])
        self.read_max_score = config.get('read_max_score', [])
        self.write_format = config['write_format']
        self.write_syn = config['write_syn']

        self.logger.info(f"Initializing SupervisedFinetuneGenerator, keys={self.key}...")

    @staticmethod
    def get_desc(lang):
        return "基于给定文档内容，生成监督微调格式的问答数据。" if lang == "zh" else "Generate supervised fine-tuning format Q&A data based on the given document content."

    def __init_model__(self):
        generator_type = self.config.get("generator_type", "local").lower()
        if generator_type == "local":
            self.logger.info("Using LocalModelGenerator...")
            return LocalModelGenerator(self.config)
        elif generator_type == "aisuite":
            self.logger.info("Using APIGenerator_aisuite...")
            return APIGenerator_aisuite(self.config)
        elif generator_type == "request":
            self.logger.info("Using APIGenerator_request...")
            return APIGenerator_request(self.config)
        else:
            raise ValueError(f"Invalid generator type: {generator_type}")
    
    def _load_input(self):
        if hasattr(self, 'storage'):
            value_list = self.storage.read_str(['data'], category='text', pipeline_id=self.pipeline_id, stage=self.stage, eval_stage=self.eval_stage, format=self.read_format, syn=self.read_syn, maxmin_scores=[dict(zip(['min_score', 'max_score'], list(_))) for _ in list(zip(self.read_min_score, self.read_max_score))])
            return pd.DataFrame(value_list)
            # return pd.DataFrame([item['data'] for item in value_list])
        else:
            return pd.read_json(self.input_file, lines=True)

    def _write_output(self, save_path, dataframe, extractions):
        if hasattr(self, 'storage'):
            output_rows = dataframe.where(pd.notnull(dataframe), None).to_dict(orient="records")
            formatted_rows = [
                {
                    "id": row["id"],
                    "data": {k: v for k, v in row.items() if k != 'id'}
                }
                for row in output_rows
            ]
            self.storage.write_json(formatted_rows, format=self.write_format, syn=self.write_syn, category='text', pipeline_id=self.pipeline_id, stage=self.stage+1)
        else:
            dataframe.to_json(self.output_file, orient='records', lines=True)



    def run(self):
        self.logger.info("Running SupervisedFinetuneGenerator...")
        raw_dataframe = self._load_input()
        num_questions = 1
        prompt = f"""You are tasked with creating high-quality SFT data for LLM training. Please generate a batch of data where the only task is to create questions based on the provided context. Focus on diversity, relevance, and clarity when forming the questions. Please ensure each question is distinct and appropriately aligned with the context.
    Your Questions must meet the following requirements:
    1. You must strictly create exactly {num_questions} questions at a time.
    2. These {num_questions} questions must cover different aspects of the topic, ensuring diversity and comprehensiveness.
    3. Each question should be framed based on the provided context and should include sufficient background information. The questions should not be abrupt or vague.
    4. Please output the {num_questions} questions in the following JSON format:
    {{
        "instruction": "QUESTION",
        "output": "ANSWER"
    }}
    5. Here are some examples of high-quality SFT data questions with completed outputs:
    {{
        "instruction": "Can you provide a list of healthy habits to maintain a healthy lifestyle? Please format your response as an HTML page with bullet points.",
        "output": "Here's an HTML page with bullet points for healthy habits: <html><body><h3>Healthy Habits:</h3><ul><li>Eating a balanced diet with plenty of fruits and vegetables.</li><li>Engaging in regular physical activity, such as walking, running, or cycling.</li><li>Getting enough sleep each night, ideally 7-8 hours.</li><li>Staying hydrated by drinking plenty of water throughout the day.</li><li>Limiting alcohol consumption and avoiding smoking.</li><li>Managing stress through relaxation techniques like meditation or yoga.</li><li>Regularly visiting a healthcare provider for check-ups and preventative care.</li></ul></body></html>"
    }},
    {{
        "instruction": "How can we use Python to calculate the GCD (greatest common divisor) of five numbers and express each number in terms of the GCD?",
        "output": "Here's a Python function that calculates the GCD of five numbers: def find_gcd(a, b, c, d, e): smallest = min(a, b, c, d, e) while True: if all(x % smallest == 0 for x in [a, b, c, d, e]): return smallest else: smallest -= 1. This will compute the GCD and can express each number in terms of the GCD."
    }},
    {{
        "instruction": "Generate a list of ten essential items a person might need for a camping trip, considering the weather, terrain, and local wildlife. Provide a breakdown of weight, size, and functionality of each item.",
        "output": "Here's a list of ten essential items for a camping trip: 1. Tent - lightweight, easy to set up, weighs 3.5 pounds, $450. 2. Sleeping bag - keeps you warm at 20°F, weighs 2 pounds, $200. 3. Sleeping pad - insulates and cushions, weighs 1 pound, $100. 4. Backpack - 65L capacity, weighs 4.5 pounds, $250. 5. Water filter - lightweight, filters up to 100,000 gallons, $40. 6. Headlamp - bright, 300 lumens, $30. 7. Multi-tool - versatile, 18 tools, $80. 8. Stove - boils water in 2 minutes, $100. 9. Bear canister - stores food securely, $70. 10. First aid kit - essential medical supplies, $50."
    }}
    6. Now it's your turn. You can use your rich imagination, but note that you cannot copy the expression from the examples; you must have your own new expression:

    Please create {num_questions} distinct and well-formed questions based on the following context:"""

        # 构建模型输入
        llm_inputs = []
        for context in raw_dataframe[self.key]:
            message = f"<|im_start|>system\n{prompt}<|im_end|>\n<|im_start|>user\n{context}<|im_end|>\n<|im_start|>assistant"
            llm_inputs.append(message)

        # 生成结果
        outputs = self.model.generate_text_from_input(llm_inputs)

        # 处理输出并保存
        valid_records = []
        for idx, output in enumerate(outputs):
            result = extract_json_object(output)
            if result:
                result["raw_content"] = raw_dataframe[self.key].iloc[idx]  # 添加原文内容
                valid_records.append(result)

        if valid_records:
            pd.DataFrame(valid_records).to_json(self.output_file, orient='records', lines=True)
            self.logger.info(f"Saved {len(valid_records)} records to {self.output_file}")
        else:
            self.logger.warning("No valid records generated.")
