import random
import pandas as pd
import json
from dataflow.utils.registry import GENERATOR_REGISTRY, get_logger
from dataflow.data import MyScaleStorage, DatabaseConfig
import os

@GENERATOR_REGISTRY.register()
class ExtractLines:
    def __init__(self, config: dict):
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
            self.pipeline_id = config['pipeline_id']
            self.stage = config.get('stage', 3)
            self.eval_stage = config.get('eval_stage', 2)
            self.read_min_score = config.get('read_min_score', [])
            self.read_max_score = config.get('read_max_score', [])
            self.input_file = None
            self.output_file = None
            self.read_format = config.get('read_format')
            self.read_syn = config.get('read_syn')
            self.write_format = config.get('write_format')
            self.write_syn = config.get('write_syn')
        else:
            self.input_file = config.get("input_file")
            self.output_file = config.get("output_file")

        self.input_key = config.get("input_key")
        self.output_key = config.get("output_key")
        self.logger = get_logger()
    
    @staticmethod  
    def get_desc(lang):
        return "提取代码片段" if lang == "zh" else "Extract code snippets"

    def _load_inputs(self):
        """Load code strings from input JSONL file"""
        dataframe = pd.read_json(self.input_file,lines=True)
        return dataframe, dataframe[self.input_key].tolist()
    
    def _extract_continuous_lines(self, code_string):
        """Extract random continuous lines from a code string"""
        lines = code_string.splitlines()
        if not lines:
            return ""
            
        num_lines_to_extract = random.randint(4, 15)
        start_line = random.randint(0, max(0, len(lines) - num_lines_to_extract))
        return "\n".join(lines[start_line:start_line + num_lines_to_extract])
    
    def _load_input(self):
        if hasattr(self, 'storage'):
            value_list = self.storage.read_json(['data'], category='code', format='PT', syn='', pipeline_id=self.pipeline_id, stage=self.stage, eval_stage=self.eval_stage, maxmin_scores=[dict(zip(['min_score', 'max_score'], list(_))) for _ in list(zip(self.read_min_score, self.read_max_score))])
            return pd.DataFrame([{'id': _['id']} | _['data'] for _ in value_list])
        else:
            data = pd.read_json(self.input_file, lines=True)
            filtered_static_data = data[data['check_result'].isin([0, -1])]
            filtered_ast_data = filtered_static_data[filtered_static_data['ast_error'] == 0]
            return filtered_ast_data
    
    def _write_output(self, save_path, data):
        if hasattr(self, 'storage'):
            self.storage.write_str(data, category='code', pipeline_id=self.pipeline_id, format=self.write_format, syn=self.write_syn, stage=self.stage+1)
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
        Extract random continuous lines from code strings
        """
        # dataframe, code_strings = self._load_inputs()
        code_strings = self._load_input()
        self.logger.info(len(code_strings))
        extracted_lines = [self._extract_continuous_lines(code) for code in code_strings[self.input_key]]
        self.logger.info(len(extracted_lines))
        if hasattr(self, 'storage'):
            self._write_output(self.output_file, [{'id': item, 'data': code} for item, code in zip(code_strings['id'], extracted_lines)])
        else:
            self._write_output(self.output_file, [{self.output_key: code} for code in extracted_lines])
        # dataframe[self.output_key] = extracted_lines
        # dataframe.to_json(self.output_file,orient="records",lines=True)

        return

