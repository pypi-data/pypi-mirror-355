import os
import re
import json
# from dataflow.generator.utils.LocalModelGenerator import LocalModelGenerator
# from dataflow.generator.utils.APIGenerator_aisuite import APIGenerator_aisuite
from dataflow.generator.utils.APIGenerator_request import APIGenerator_request
from dataflow.generator.utils.Prompts import CodeScorerPrompt as CSP
from dataflow.data import MyScaleStorage, DatabaseConfig
import pandas as pd
from dataflow.utils.registry import GENERATOR_REGISTRY, get_logger

@GENERATOR_REGISTRY.register()
class CodeScorer:
    def __init__(self, config :dict):
        self.config = config
        # self.input_file = config.get("input_file")
        # self.output_file = config.get("output_file")
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
            self.pipeline_id = config['pipeline_id']
            self.stage = config.get('stage', 5)
            self.eval_stage = config.get('eval_stage', 0)
            self.read_min_score = config.get('read_min_score', [])
            self.read_max_score = config.get('read_max_score', [])
            self.input_file = None
            self.output_file = None
            self.read_format = config.get('read_format')
            self.read_syn = config.get('read_syn')
        else:
            self.input_file = config.get("input_file")
            self.output_file = config.get("output_file")

        self.input_key_for_problem_description = config.get("input_key_for_problem_description")
        self.input_key_for_analysis = config.get("input_key_for_analysis")
        self.input_key_for_solution = config.get("input_key_for_solution")
        self.input_key = config.get("input_key")
        self.output_key = config.get("output_key")
        self.logger = get_logger()
        self.model = self.__init_model__()
        
    def get_desc(self, lang):
        return "对代码QA数据进行打分" if lang == "zh" else "Score the code QA data"

    def __init_model__(self):
        """
        Initialize the model generator based on the configuration.
        """
        generator_type = self.config.get("generator_type", "local").lower()

        # if generator_type == "local":
        #     return LocalModelGenerator(self.config)
        # elif generator_type == "aisuite":
        #     return APIGenerator_aisuite(self.config)
        if generator_type == "request":
            return APIGenerator_request(self.config)
        else:
            raise ValueError(f"Invalid generator type: {generator_type}")
        
    def process_prompt(self, input_list : list):
        """
        Process the prompt for the code scorer.
        """
        inputs = []
        sys_prompt = CSP().code_scorer_prompt()
        for item in input_list:
            # self.logger.info(data)
            # oss_inst = json.loads(data[self.input_key])
            # item = data[self.input_key]
            content = sys_prompt + "[Problem Description]\n" + item[self.input_key_for_problem_description] + "\n" + "[Analysis]\n" + item[self.input_key_for_analysis] + "\n" + "[Solution]\n" + item[self.input_key_for_solution]
            inputs.append(content)
        return inputs
    
    def extract_grading_feedback(self, text):
    # 使用正则表达式匹配Grading和Feedback，考虑可能的空格
        if text is None:
            return None
        grading_pattern_1 = r"\*\*Grading\*\*\s*:\s*(\d+)"

        # 第二种格式：Grading:** 和 Feedback:** 
        grading_pattern_2 = r"\*\*Grading:\*\*\s*(\d+)"

        # 查找第一种格式（**Grading**: 和 **Feedback**:）
        grading_match_1 = re.search(grading_pattern_1, text)
        result = {}

        if grading_match_1:
            result['Grading'] = int(grading_match_1.group(1))  # Grading 是一个整数
            return result
        # 查找第二种格式（Grading:** 和 Feedback:**）
        grading_match_2 = re.search(grading_pattern_2, text)

        if grading_match_2:
            result['Grading'] = int(grading_match_2.group(1))  # Grading 是一个整数
            return result
        print(text)
        return None
    
    def _load_input(self):
        if hasattr(self, 'storage'):
            value_list = self.storage.read_json(['data'], category='code', format=self.read_format, syn=self.read_syn, pipeline_id=self.pipeline_id, stage=self.stage, eval_stage=self.eval_stage, maxmin_scores=[dict(zip(['min_score', 'max_score'], list(_))) for _ in list(zip(self.read_min_score, self.read_max_score))])
            return pd.DataFrame(value_list)
        else:
            return pd.read_json(self.input_file, lines=True)
    
    def _write_output(self, save_path, data):
        if hasattr(self, 'storage'):
            self.storage.write_eval(data, stage=self.stage+1, score_key='Grading', algo_name=self.__class__.__name__)
        else:
            with open(save_path, 'w', encoding='utf-8') as f:
                for item in data:
                    for k,v in item.items():
                        if pd.isna(v):
                            item[k] = None
                    json.dump(item, f)
                    f.write('\n')
    def run(self):
        """
        Run the code scorer.
        """
        # dataframe = pd.read_json(self.input_file,lines=True)
        input_list = self._load_input()
        self.logger.info(len(input_list))
        inputs = self.process_prompt(input_list[self.input_key])
        scores = self.model.generate_text_from_input(inputs)
        processed_scores = [self.extract_grading_feedback(score) for score in scores]
        output_data = []
        if hasattr(self, 'storage'):
            for id, item in zip(input_list['id'], processed_scores):
                if item is not None:
                    output_data.append({'id': id} | item)
        else:
            for item in processed_scores:
                if item is not None:
                    output_data.append({self.output_key: item})
        self._write_output(self.output_file, output_data)
        # dataframe[self.output_key] = scores
        # dataframe.to_json(self.output_file,orient="records",lines=True)