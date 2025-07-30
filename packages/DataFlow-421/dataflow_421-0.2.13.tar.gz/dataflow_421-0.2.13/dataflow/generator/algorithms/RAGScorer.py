import os
import re
from dataflow.generator.utils.LocalModelGenerator import LocalModelGenerator
from dataflow.generator.utils.APIGenerator_aisuite import APIGenerator_aisuite
from dataflow.generator.utils.APIGenerator_request import APIGenerator_request
from dataflow.generator.utils.Prompts import RAGScorerPrompt as RSP
import pandas as pd
from dataflow.utils.utils import get_logger
from dataflow.utils.registry import GENERATOR_REGISTRY
from dataflow.data import MyScaleStorage, DatabaseConfig

@GENERATOR_REGISTRY.register()
class RAGScorer:
    def __init__(self, config :dict):
        self.config = config
        self.logger = get_logger()
        self.generator = self.__init_model__()

        self.input_key = config.get("input_key", "text")
        self.input_question_key = config.get("input_question_key", "question")
        self.input_answer_key = config.get("input_answer_key", "answer")
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
            self.stage = config.get("stage", 3)
            self.eval_stage = self.config.get('eval_stage', 1)
            self.pipeline_id = config.get("pipeline_id", "")
            self.read_min_score: list = self.config.get('read_min_score', [])
            self.read_max_score: list = self.config.get('read_max_score', [])
        else:
            self.input_file = config["input_file"]
            self.output_file = config["output_file"]

        if not hasattr(self, "storage") and (not self.input_file or not self.output_file):
            raise ValueError("Both input_file and output_file must be specified in the config.")
        
    def get_desc(self, lang):
        return "对RAG QA数据进行打分" if lang == "zh" else "Score the RAG QA data"

    def __init_model__(self):
        """
        Initialize the model generator based on the configuration.
        """
        generator_type = self.config.get("generator_type", "request").lower()
        if generator_type == "aisuite":
            return APIGenerator_aisuite(self.config)
        elif generator_type == "request":
            return APIGenerator_request(self.config)
        else:
            raise ValueError(f"Invalid generator type: {generator_type}")
        
    def process_prompt(self, dataframe :pd.DataFrame):
        """
        Process the prompt for the code scorer.
        """
        question_quality_inputs = []
        question_quality_prompt = RSP().question_quality_prompt()
        answer_alignment_inputs = []
        answer_alignment_prompt = RSP().answer_alignment_prompt()
        answer_verifiability_inputs = []
        answer_verifiability_prompt = RSP().answer_verifiability_prompt()
        downstream_value_inputs = []
        downstream_value_prompt = RSP().downstream_value_prompt()
        for index, row in dataframe.iterrows():
            # oss_inst = row[self.input_key]
            question_quality_content = question_quality_prompt + "Question: " + row[self.input_question_key] + "\n" + "Answer: " + row[self.input_answer_key]
            question_quality_inputs.append(question_quality_content)
            answer_alignment_content = answer_alignment_prompt + "Question: " + row[self.input_question_key] + "\n" + "Answer: " + row[self.input_answer_key]
            answer_alignment_inputs.append(answer_alignment_content)
            answer_verifiability_content = answer_verifiability_prompt + "Question: " + row[self.input_question_key] + "\n" + "Answer: " + row[self.input_answer_key]
            answer_verifiability_inputs.append(answer_verifiability_content)
            downstream_value_content = downstream_value_prompt + "Question: " + row[self.input_question_key] + "\n" + "Answer: " + row[self.input_answer_key]
            downstream_value_inputs.append(downstream_value_content)
        return question_quality_inputs, answer_alignment_inputs, answer_verifiability_inputs, downstream_value_inputs
    
    def _load_input(self):
        if hasattr(self, 'storage'):
            value_list = self.storage.read_json(
                ["data"], eval_stage=self.eval_stage, syn='syn_qa', format='RLHF', stage=self.stage, pipeline_id=self.pipeline_id, category="RAG", maxmin_scores=[dict(zip(['min_score', 'max_score'], list(_))) for _ in list(zip(self.read_min_score, self.read_max_score))]
            )
            return pd.DataFrame([
                {**item['data'], 'id': str(item['id'])}
                for item in value_list
            ])
        else:
            return pd.read_json(self.input_file, lines=True)

    def _write_output(self, save_path, dataframe):
        if hasattr(self, 'storage'):
            # print(dataframe.head())  # Debugging: print first few rows
            output_rows = dataframe.where(pd.notnull(dataframe), None).to_dict(orient="records")
            # print(output_rows[:5])  # Debugging: print first 5 rows
            self.storage.write_eval(output_rows, stage=self.stage+1, algo_name=self.__class__.__name__, score_keys=["question_quality_grades", "answer_alignment_grades", "answer_verifiability_grades", "downstream_value_grades"], info_keys=["question_quality_feedbacks", "answer_alignment_feedbacks", "answer_verifiability_feedbacks", "downstream_value_feedbacks"])
        else:
            dataframe.to_json(save_path, orient="records", lines=True, force_ascii=False)

    def extract_grading_feedback(self, text):
        grading_match = re.search(r"\*\*Grading\*\*:\s*(\d+)", text)
        feedback_match = re.search(r"\*\*Feedback\*\*:\s*(.+)", text, re.DOTALL)
        grading = float(grading_match.group(1)) if grading_match else 0
        feedback = feedback_match.group(1).strip() if feedback_match else ''

        return grading, feedback

    def run(self):
        """
        Run the code scorer.
        """
        self.logger.info(f"Reading code snippets from {self.input_file}")
        dataframe = self._load_input()
        question_quality_inputs, answer_alignment_inputs, answer_verifiability_inputs, downstream_value_inputs = self.process_prompt(dataframe)
        self.logger.info(f'Generating output...')
        question_quality_scores = self.generator.generate_text_from_input(question_quality_inputs)
        question_grades, question_feedbacks = zip(*[self.extract_grading_feedback(q) for q in question_quality_scores])
        answer_alignment_scores = self.generator.generate_text_from_input(answer_alignment_inputs)
        answer_alignment_grades, answer_alignment_feedbacks = zip(*[self.extract_grading_feedback(a) for a in answer_alignment_scores])
        answer_verifiability_scores = self.generator.generate_text_from_input(answer_verifiability_inputs)
        answer_verifiability_grades, answer_verifiability_feedbacks = zip(*[self.extract_grading_feedback(a) for a in answer_verifiability_scores])
        downstream_value_scores = self.generator.generate_text_from_input(downstream_value_inputs)
        downstream_value_grades, downstream_value_feedbacks = zip(*[self.extract_grading_feedback(d) for d in downstream_value_scores])
        self.logger.info(f'Output generated.')
        dataframe['question_quality_grades'] = question_grades
        dataframe['question_quality_feedbacks'] = question_feedbacks
        dataframe['answer_alignment_grades'] = answer_alignment_grades
        dataframe['answer_alignment_feedbacks'] = answer_alignment_feedbacks
        dataframe['answer_verifiability_grades'] = answer_verifiability_grades
        dataframe['answer_verifiability_feedbacks'] = answer_verifiability_feedbacks
        dataframe['downstream_value_grades'] = downstream_value_grades
        dataframe['downstream_value_feedbacks'] = downstream_value_feedbacks
        self.logger.info(f"Saving results into {self.output_file}")
        self._write_output(self.output_file, dataframe)