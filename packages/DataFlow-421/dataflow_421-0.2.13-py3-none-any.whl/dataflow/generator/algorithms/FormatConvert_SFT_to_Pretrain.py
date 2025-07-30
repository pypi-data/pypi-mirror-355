import random
import os
import pandas as pd
try:
    from utils import  APIGenerator_aisuite, APIGenerator_request
    from utils.Prompts import QuestionSynthesisPrompt
except ImportError:
    from dataflow.generator.utils import  APIGenerator_aisuite, APIGenerator_request
    from dataflow.generator.utils.Prompts import QuestionSynthesisPrompt
from dataflow.utils.registry import GENERATOR_REGISTRY
import logging
from dataflow.utils.utils import get_logger
from dataflow.data import MyScaleStorage, DatabaseConfig

@GENERATOR_REGISTRY.register()
class FormatConvert_SFT_to_Pretrain():
    def __init__(self, args):
        """
        Initialize the FormatConvert_SFT_to_Pretrain with the provided configuration.
        """
        self.config = args
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
            self.output_file= None
            self.stage = args.get("stage",0)
            self.pipeline_id = args.get("pipeline_id","")
        else:
            self.input_file = args.get("input_file")
            self.output_file= args.get("output_file")
        self.input_key = self.config.get("input_key", "data")
        self.read_key_question = self.config.get("read_key_question", "question")  # default key for question input
        self.read_key_answer = self.config.get("read_key_answer", "answer")  # default key for question input
        self.output_key = self.config.get("output_key", "text")  # default output key
        self.logger = get_logger()
        self.eval_stage = self.config.get('eval_stage', 3)
        # Ensure input_file and output_file are provided
        if not self.storage and (not self.input_file or not self.output_file):
            raise ValueError("Both input_file and output_file must be specified in the config.")

    def _load_input(self):
        if hasattr(self, 'storage'):
            value_list = self.storage.read_json(
                [self.input_key], eval_stage=self.eval_stage, syn='syn_qa', format='SFT_Single', stage=self.stage, pipeline_id=self.pipeline_id, category="reasoning"
            )
            return pd.DataFrame([
                {**item['data'], 'id': str(item['id'])}
                for item in value_list
            ])
        else:
            return pd.read_json(self.input_file, lines=True)

    def _write_output(self, save_path, dataframe, extractions):
        if hasattr(self, 'storage'):
            output_rows = dataframe.where(pd.notnull(dataframe), None).to_dict(orient="records")
            output_1 = []
            for row in output_rows:
                cur_q = row.get(self.read_key_question) if row.get(self.read_key_question) is not None else ""
                cur_a = row.get(self.read_key_answer) if row.get(self.read_key_answer) is not None else ""
                output_1.append({
                    "id": row.get("id"),
                    "text": cur_q + "\n" + cur_a,
                })
            self.storage.write_data(output_1, format="PT", Synthetic="syn_qa", stage=self.stage+1)
        else:
            dataframe.to_json(save_path, orient="records", lines=True)

    def run(self):
        """
        Run the pretrain data format convertion.
        """
        # Read the input
        dataframe = self._load_input()

        if self.output_key in dataframe.columns:
            key_list = dataframe.columns.tolist()
            raise ValueError(f"Found {self.output_key} in the dataframe, which leads to overwriting the existing column, please check the output_text_key: {key_list}")
        
        # Save DataFrame to the output
        self._write_output(self.output_file, dataframe, None)

        self.logger.info(f"SFT to PT convertion results saved to {self.output_file}")
        return

    @staticmethod
    def get_desc(self, lang):
        if lang == "zh":
            return (
                "该算子用于将SFT格式数据转换为预训练格式。\n\n"
                "输入参数：\n"
                "- input_file：输入文件路径\n"
                "- db_port/db_name：数据库连接配置\n"
                "- table_name：存储表名\n"
                "- eval_stage：数据处理阶段标识\n\n"
                "输出参数：\n"
                "- output_file：输出文件路径\n"
                "- 数据库存储：转换后的预训练格式数据"
            )
        elif lang == "en":
            return (
                "Converts SFT format data to pretraining format.\n\n"
                "Input Parameters:\n"
                "- input_file: Input file path\n"
                "- db_port/db_name: Database connection config\n"
                "- table_name: Storage table name\n"
                "- eval_stage: Data processing stage\n\n"
                "Output Parameters:\n"
                "- output_file: Output file path\n"
                "- Database storage: Converted pretraining data"
            )
        else:
            return "FormatConvert_SFT_to_Pretrain: SFT to Pretraining format converter"