from dataflow.utils.registry import GENERATOR_REGISTRY
from dataflow.data import MyScaleStorage, DatabaseConfig
from dataflow.utils.utils import get_logger
from dataflow.generator.utils.APIGenerator_aisuite import APIGenerator_aisuite
from dataflow.generator.utils.APIGenerator_request import APIGenerator_request
from dataflow.generator.utils.Prompts import AutoPromptGeneratorPrompt as APGP
import pandas as pd
import os

@GENERATOR_REGISTRY.register()
class AutoPromptGenerator:
    '''
    AutoPromptGenerator is a class that uses LLMs to generate prompts for QA pairs generating based on seed input.
    '''
    def __init__(self, config: dict):
        self.config = config
        self.logger = get_logger()
        self.generator = self.__init_model__()

        self.input_key = config.get("input_key", "text")
        self.output_key = config.get("output_key", "prompt")
        use_db = self.config.get("use_db", False) or os.environ.get("USE_DB", "").lower() == "true"
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
            self.stage = self.config.get("stage", 1)
            self.eval_stage = self.config.get('eval_stage', 1)
            self.pipeline_id = self.config.get("pipeline_id", "")
            self.read_min_score: list = self.config.get('read_min_score', [])
            self.read_max_score: list = self.config.get('read_max_score', [])
        else:
            self.input_file = self.config["input_file"]
            self.output_file = self.config["output_file"]

        if not hasattr(self, "storage") and (not self.input_file or not self.output_file):
            raise ValueError("Both input_file and output_file must be specified in the config.")

    def __init_model__(self):
        generator_type = self.config.get("generator_type", "aisuite").lower()
        if generator_type == "aisuite":
            return APIGenerator_aisuite(self.config)
        elif generator_type == "request":
            return APIGenerator_request(self.config)
        else:
            raise ValueError(f"Unsupported generator_type: {generator_type}")

    def get_desc(self, lang):
        if lang == "zh":
            return (
                "AutoPromptGenerator 是一个使用 LLMs 生成基于种子输入生成 QA 对的提示的类。"
            )
        elif lang == "en":
            return (
                "AutoPromptGenerator is a class that uses LLMs to generate prompts for QA pairs generating based on seed input."
            )
        else:
            return (
                "AutoPromptGenerator is a class that uses LLMs to generate prompts for QA pairs generating based on seed input."
            )

    def _load_input(self):
        if hasattr(self, 'storage'):
            value_list = self.storage.read_json(
                ["data"], eval_stage=self.eval_stage, syn='', format='PT', stage=self.stage, pipeline_id=self.pipeline_id, category="RAG", maxmin_scores=[dict(zip(['min_score', 'max_score'], list(_))) for _ in list(zip(self.read_min_score, self.read_max_score))]
            )
            return pd.DataFrame([
                {**item['data'], 'id': str(item['id'])}
                for item in value_list
            ])
        else:
            return pd.read_json(self.input_file, lines=True)

    def _write_output(self, save_path, dataframe):
        if hasattr(self, 'storage'):
            output_rows = dataframe.where(pd.notnull(dataframe), None).to_dict(orient="records")
            self.storage.write_data(output_rows, format="PT", Synthetic="", stage=self.stage+1)
        else:
            dataframe.to_json(save_path, orient="records", lines=True, force_ascii=False)

    def _build_prompt(self, seed_text: str) -> str:
        return APGP.auto_prompt_generator_prompt(self, seed_data=seed_text)

    def run(self):
        df = self._load_input()

        if self.input_key not in df.columns:
            raise ValueError(f"input_key: {self.input_key} not found in the dataframe.")

        prompts = df[self.input_key].apply(self._build_prompt).tolist()
        responses = self.generator.generate_text_from_input(prompts)
        df[self.output_key] = responses
        self._write_output(self.output_file, df)
