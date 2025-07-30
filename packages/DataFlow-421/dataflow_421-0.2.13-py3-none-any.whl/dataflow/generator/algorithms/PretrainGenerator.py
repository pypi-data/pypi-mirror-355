import json
import logging
from typing import Dict, List
from tqdm import tqdm
import pandas as pd
from vllm import LLM, SamplingParams
from huggingface_hub import snapshot_download
import torch, os, itertools, string
from dataflow.utils.registry import GENERATOR_REGISTRY
from dataflow.generator.utils.LocalModelGenerator import LocalModelGenerator
from dataflow.generator.utils.APIGenerator_aisuite import APIGenerator_aisuite
from dataflow.generator.utils.APIGenerator_request import APIGenerator_request
from dataflow.generator.utils.Prompts import PretrainPrompt
from dataflow.utils.utils import get_logger
from dataflow.data import MyScaleStorage, DatabaseConfig


@GENERATOR_REGISTRY.register()
class PretrainGenerator:
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
            self.stage = config['stage']
            self.pipeline_id = config['pipeline_id']
            self.eval_stage = config['eval_stage'] 
            self.read_format = config['read_format']
            self.read_syn = config['read_syn']
            self.read_min_score = config.get('read_min_score', [])
            self.read_max_score = config.get('read_max_score', [])
            self.write_format = config['write_format']
            self.write_syn = config['write_syn']
        else:
            self.input_file = config['input_file']
            self.output_file = config['output_file']
        self.key = config['keys']
        self.logger.info(f"Initializing PretrainGenerator keys={self.key}...")
        self.model = self.__init_model__()

    @staticmethod
    def get_desc(lang):
        return "基于给定文档内容，生成预训练格式的多轮对话问答数据。" if lang == "zh" else "Generate pre-training format multi-turn dialogue Q&A data based on the given document content."

    def __init_model__(self):
        """
        Initialize the model generator based on the configuration.
        """
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
            print(value_list)
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
                    "data": row['generated_content']
                }
                for row in output_rows
            ]
            self.storage.write_str(formatted_rows, format=self.write_format, syn=self.write_syn, category='text', pipeline_id=self.pipeline_id, stage=self.stage+1)
        else:
            dataframe.to_json(self.output_file, orient='records', lines=True)



    def run(self):
        self.logger.info("Running PretrainGenerator...")

        # Load the raw dataframe from the input file
        try:
            raw_dataframe = self._load_input()
            self.logger.info(f"Loading, number of rows: {len(raw_dataframe)}")
        except Exception as e:
            self.logger.error(f"Error loading {e}")
            return

        # Create a list to hold all generated questions and answers
        llm_inputs = []

        # Prepare LLM inputs by formatting the prompt with raw content from the dataframe
        for index, row in raw_dataframe.iterrows():
            raw_content = row.get(self.key, '')
            if raw_content:
                llm_input = self._generate_llm_input(raw_content)
                llm_inputs.append(llm_input)
        
        # Generate the text using the model
        try:
            self.logger.info("Generating text using the model...")
            generated_outputs = self.model.generate_text_from_input(llm_inputs)
            self.logger.info("Text generation completed.")
        except Exception as e:
            self.logger.error(f"Error during text generation: {e}")
            return

        # Add the generated content back to the dataframe
        raw_dataframe['generated_content'] = generated_outputs

        # Save the updated dataframe to the output file
        try:
            self._write_output(self.output_file, raw_dataframe, None)
            self.logger.info(f"Saved the output")
        except Exception as e:
            self.logger.error(f"Error saving the output file{e}")

    def _generate_llm_input(self, raw_content: str) -> str:
        """
        Generate the LLM input prompt by inserting the raw content into the prompt template.
        """
        prompt = """
        A chat between a curious user and an artificial intelligence assistant. The assistant gives helpful, detailed, and polite answers to the questions. 
        Convert the following paragraph into a conversational format with multiple tags of "Question:" followed by "Answer:":

        You can only output as the given format:
        Question: xxx Answer: xxx
        Question: xxx Answer: xxx
        Now please covert the content below.
        {content}
        """
        return prompt.format(content=raw_content)