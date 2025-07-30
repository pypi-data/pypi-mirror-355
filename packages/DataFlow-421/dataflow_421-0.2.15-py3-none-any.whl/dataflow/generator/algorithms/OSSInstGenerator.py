import os
import json
# from dataflow.generator.utils.LocalModelGenerator import LocalModelGenerator
# from dataflow.generator.utils.APIGenerator_aisuite import APIGenerator_aisuite
from dataflow.generator.utils.APIGenerator_request import APIGenerator_request
from dataflow.generator.utils.Prompts import OssInstGeneratorPrompt as OIP
import pandas as pd
from dataflow.utils.utils import get_logger
from dataflow.utils.registry import GENERATOR_REGISTRY
from dataflow.data import MyScaleStorage, DatabaseConfig

@GENERATOR_REGISTRY.register()
class OSSInstGenerator:
    def __init__(self, config :dict):
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
            self.stage = config.get('stage', 4)
            self.eval_stage = config.get('eval_stage', 0)
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

        # self.input_file = config.get("input_file")
        # self.output_file = config.get("output_file")
        self.input_key = config.get("input_key")
        self.output_key = config.get("output_key")
        self.logger = get_logger()
        self.logger.info(f"Initializing OSSInstGenerator...")
        self.model = self.__init_model__()

    @staticmethod
    def get_desc(lang):
        return "进行编写代码任务合成" if lang == "zh" else "Perform code generation task synthesis"
    
    def __init_model__(self):
        """
        Initialize the model generator based on the configuration.
        """
        generator_type = self.config.get("generator_type", "local").lower()

        if generator_type == "local":
            return LocalModelGenerator(self.config)
        elif generator_type == "aisuite":
            return APIGenerator_aisuite(self.config)
        elif generator_type == "request":
            return APIGenerator_request(self.config)
        else:
            raise ValueError(f"Invalid generator type: {generator_type}")
        
    def parse_llm_output(self, llm_output, key_list = ["Problem", "Analysis", "Solution"]):
        """
        Parses an LLM output string by identifying lines containing 'Problem', 'Analysis', and 'Solution'
        as pivots, then extracts and formats the content into a dictionary.
        """
        lines = llm_output.splitlines()
        
        # Initialize an empty dictionary to hold the results
        parsed_data = {}
        
        # Create a list to store the start index for each key section
        section_start = {key: None for key in key_list}
        
        # Iterate over lines to find the start indices of each section
        for i, line in enumerate(lines):
            for key in key_list:
                if key in line and section_start[key] is None:
                    section_start[key] = i
        
        # If any key has not been found, return None
        if any(start is None for start in section_start.values()):
            return None

        # Now, extract the content for each key from the lines
        for i, key in enumerate(key_list):
            start_index = section_start[key] + 1
            if i + 1 < len(key_list):
                end_index = section_start[key_list[i + 1]]
            else:
                end_index = len(lines)
            
            # Join the lines for the section and strip unnecessary whitespace
            parsed_data[key] = "\n".join(lines[start_index:end_index]).strip()

        return parsed_data
    
    def reformat_prompt(self, dataframe : pd.DataFrame):
        """
        Reformat the prompt for the oss inst generator.
        """
        if self.input_key not in dataframe.columns:
            raise ValueError(f"Input key {self.input_key} not found in dataframe columns: {dataframe.columns}")
        
        # get self.input_key from dataframe to list
        input_list = dataframe[self.input_key].to_list()
        # use prompt
        oip = OIP()
        inputs = [oip.oss_inst_generator_prompt(code) for code in input_list]
        self.logger.info(inputs[0])

        return inputs

    def _load_input(self):
        if hasattr(self, 'storage'):
            value_list = self.storage.read_str(['data'], category='code', format='PT', syn='syn', pipeline_id=self.pipeline_id, stage=self.stage, eval_stage=self.eval_stage, maxmin_scores=[dict(zip(['min_score', 'max_score'], list(_))) for _ in list(zip(self.read_min_score, self.read_max_score))])
            return pd.DataFrame(value_list)
        else:
            return pd.read_json(self.input_file, lines=True)
    
    def _write_output(self, save_path, data):
        if hasattr(self, 'storage'):
            self.storage.write_json(data, category='code', pipeline_id=self.pipeline_id, format=self.write_format, syn=self.write_syn, stage=self.stage+1)
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
        Main method to execute the OssInstGenerator.
        """
        # dataframe = pd.read_json(self.input_file,lines=True)
        # code_snippets = self.storage.read([self.input_key], where_str=f"WHERE {self.input_key} != ''")
        
        code_snippets = self._load_input()
        inputs = self.reformat_prompt(code_snippets[self.input_key])
        outputs = self.model.generate_text_from_input(inputs)
        parsed_outputs = [self.parse_llm_output(_) for _ in outputs]
        output_data = []
        if hasattr(self, 'storage'):
            for id, item in zip(code_snippets['id'], parsed_outputs):
                if item is not None:
                    output_data.append({'id': id, 'data': item})
        else:
            for item in parsed_outputs:
                if item is not None:
                    output_data.append({self.output_key: item})
        self._write_output(self.output_file, output_data)
        # dataframe[self.output_key] = outputs
        # # parse the output
        # dataframe[self.output_key] = dataframe[self.output_key].apply(self.parse_llm_output)
        # # save the output
        # dataframe.to_json(self.output_file,orient="records",lines=True)
