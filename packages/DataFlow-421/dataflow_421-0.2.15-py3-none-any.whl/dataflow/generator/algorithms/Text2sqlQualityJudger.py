import pandas as pd
from dataflow.data import MyScaleStorage, DatabaseConfig
from dataflow.utils.utils import get_logger
from dataflow.utils.registry import GENERATOR_REGISTRY
from transformers import AutoTokenizer
import os

@GENERATOR_REGISTRY.register()
class Text2sqlQualityJudger:
    def __init__(self, args):
        self.config = args
        self.logger = get_logger()
        use_db = args.get("use_db", False) or os.environ.get("USE_DB", "").lower() == "true"
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
            self.stage = args.get("stage", 0)
            self.pipeline_id = args.get("pipeline_id", "")
        else:
            self.input_file = args.get("input_file")
            self.output_file = args.get("output_file")
        self.eval_stage = args.get("eval_stage", 3)
        self.input_key = self.config.get("input_key", "data")
        self.tokenizer_name_or_path = self.config.get("tokenizer_name_or_path", "Qwen/Qwen2.5-7B-Instruct")
        self.read_max_score = args.get("read_max_score")
        self.read_min_score = args.get("read_min_score")
        
        self.sft_prompt_key = args.get("sft_prompt_key")
        self.rl_prompt_key = args.get("rl_prompt_key")
        self.sft_output_key = args.get("sft_output_key")
        self.whole_format_schema_key = args.get("whole_format_schema_key")

        if not hasattr(self, "storage") and (not self.input_file or not self.output_file):
            raise ValueError("Both input_file and output_file must be specified in the config.")

        
    def _load_input(self):
        if hasattr(self, 'storage'):
            value_list = self.storage.read_json(
                ['data'] + [f'eval_score_{i}' for i in range(1, self.eval_stage + 1)] + [f'eval_algorithm_{i}' for i in range(1, self.eval_stage + 1)], eval_stage=self.eval_stage, syn='syn_qa', format='SFT_Single', maxmin_scores=[dict(zip(['min_score', 'max_score'], list(_))) for _ in list(zip(self.read_min_score, self.read_max_score))], stage=self.stage, pipeline_id=self.pipeline_id, category="text2sql_data"
            )
            expanded_value_list = []
            for item in value_list:
                data_json = item['data']
                item['id'] = str(item['id'])
                del item['data']
                expanded_value_list.append(data_json | item)
            dataframe = pd.DataFrame(expanded_value_list)
            return dataframe
        else:
            return pd.read_json(self.input_file, lines=True)

    def filter_judger(self, dataframe):
        lst = dataframe["eval_score_1"].value_counts().to_dict()
        return lst
    
    def component_difficulty_judger(self, dataframe):
        lst = dataframe["eval_score_2"].value_counts().to_dict()
        return lst
    
    def execution_difficulty_judger(self, dataframe):
        lst = dataframe["eval_score_3"].value_counts().to_dict()
        return lst
    
    def token_calculator(self, dataframe):
        sft_prompts = []
        rl_prompts = []
        sft_outputs = []
        whole_format_schemas = []
        
        for index, row in dataframe.iterrows():
            sft_prompts.append(str(row.get(self.sft_prompt_key, "")))  
            rl_prompts.append(str(row.get(self.rl_prompt_key, "")))    
            sft_outputs.append(str(row.get(self.sft_output_key, "")))
            whole_format_schemas.append(str(row.get(self.whole_format_schema_key, "")))

        tokenizer = AutoTokenizer.from_pretrained(self.tokenizer_name_or_path)
        
        def calculate_lengths(texts):
            valid_texts = [text for text in texts if isinstance(text, str)]
            if not valid_texts:
                return []
            return [len(tokenizer.encode(text, add_special_tokens=True)) for text in valid_texts]

        sft_prompt_lengths = calculate_lengths(sft_prompts)
        rl_prompt_lengths = calculate_lengths(rl_prompts)
        sft_output_lengths = calculate_lengths(sft_outputs)
        schema_lengths = calculate_lengths(whole_format_schemas)

        def get_stats(lengths):
            if not lengths: 
                return {
                    "average": 0,
                    "max": 0,
                    "min": 0
                }
            return {
                "average": round(sum(lengths) / len(lengths), 2),
                "max": max(lengths),
                "min": min(lengths)
            }

        output = {
            "sft_prompt": get_stats(sft_prompt_lengths),
            "rl_prompt": get_stats(rl_prompt_lengths),
            "sft_output": get_stats(sft_output_lengths),
            "schema": get_stats(schema_lengths),
            "total_samples": len(dataframe)
        }
        
        return output
        
    def run(self):
        dataframe = self._load_input()
        filter_lst = self.filter_judger(dataframe)
        component_difficulty_lst = self.component_difficulty_judger(dataframe)
        execution_difficulty_lst = self.execution_difficulty_judger(dataframe)
        token_info = self.token_calculator(dataframe)

        self.logger.info(f"Filter Judger: {filter_lst}")
        self.logger.info(f"Component Difficulty Judger: {component_difficulty_lst}")
        self.logger.info(f"Execution Difficulty Judger: {execution_difficulty_lst}")
        self.logger.info(f"Token Info: {token_info}")
        
        return filter_lst, component_difficulty_lst, execution_difficulty_lst, token_info