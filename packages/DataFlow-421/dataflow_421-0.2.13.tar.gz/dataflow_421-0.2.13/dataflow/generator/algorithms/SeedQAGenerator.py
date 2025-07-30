from dataflow.utils.registry import GENERATOR_REGISTRY
from dataflow.data import MyScaleStorage, DatabaseConfig
from dataflow.utils.utils import get_logger
from dataflow.generator.utils.APIGenerator_aisuite import APIGenerator_aisuite
from dataflow.generator.utils.APIGenerator_request import APIGenerator_request
import pandas as pd
import os

@GENERATOR_REGISTRY.register()
class SeedQAGenerator:
    '''
    SeedQAGenerator is a class that uses LLMs to generate QA pairs based on seed input.
    '''

    def __init__(self, config: dict):
        self.config = config
        self.logger = get_logger()
        self.generator = self.__init_model__()

        self.input_key = config.get("input_key", "text")
        self.input_prompt_key = config.get("input_prompt_key", "prompt")
        self.output_question_key = config.get("question_key", "question")
        self.output_answer_key = config.get("answer_key", "answer")
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
            self.stage = config.get("stage", 2)
            self.eval_stage = self.config.get('eval_stage', 1)
            self.pipeline_id = config.get("pipeline_id", "")
            self.read_min_score: list = self.config.get('read_min_score', [])
            self.read_max_score: list = self.config.get('read_max_score', [])
        else:
            self.input_file = config["input_file"]
            self.output_file = config["output_file"]

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
                "该算子根据输入的种子文本调用大语言模型生成问答对（QA数据）。\n\n"
                "输入参数：\n"
                "- input_file：输入文件路径\n"
                "- output_file：输出文件路径\n"
                "- generator_type：生成器类型（aisuite/request）\n"
                "- max_worker：并发线程数\n\n"
                "输出参数：\n"
                "- question_key：生成的问题字段名\n"
                "- answer_key：生成的答案字段名"
            )
        elif lang == "en":
            return (
                "This operator uses LLMs to generate question-answer pairs from seed input text.\n\n"
                "Input Parameters:\n"
                "- input_file: Input file path\n"
                "- output_file: Output file path\n"
                "- generator_type: Generator type (aisuite/request)\n"
                "- max_worker: Number of threads\n\n"
                "Output Parameters:\n"
                "- question_key: Generated question field name\n"
                "- answer_key: Generated answer field name"
            )
        else:
            return "SeedQAGenerator creates QA pairs using LLMs based on seed data."

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
            self.storage.write_data(output_rows, format="RLHF", Synthetic="syn_qa", stage=self.stage+1)
        else:
            dataframe.to_json(save_path, orient="records", lines=True, force_ascii=False)

    def _build_prompt(self, df) -> str:
        prompts = []
        for index, row in df.iterrows():
            prompts.append(row[self.input_prompt_key] + "Format:\nQ: ...\nA: ..." + "\nSeed data:\n" + row[self.input_key])
        return pd.Series(prompts)

    def _parse_qa(self, response: str) -> tuple:
        lines = response.strip().split('\n')
        q = next((line[2:].strip() for line in lines if line.lower().startswith("q:")), "")
        a = next((line[2:].strip() for line in lines if line.lower().startswith("a:")), "")
        return q, a

    def run(self):
        df = self._load_input()

        if self.input_key not in df.columns or self.input_prompt_key not in df.columns:
            raise ValueError(f"input_key: {self.input_key} not found in the dataframe.")

        prompts = self._build_prompt(df).tolist()
        responses = self.generator.generate_text_from_input(prompts)

        questions, answers = zip(*[self._parse_qa(r) for r in responses])
        df[self.output_question_key] = questions
        df[self.output_answer_key] = answers

        self._write_output(self.output_file, df)
