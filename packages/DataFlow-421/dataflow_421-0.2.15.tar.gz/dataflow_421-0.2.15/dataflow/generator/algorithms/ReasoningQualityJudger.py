import pandas as pd
from dataflow.data import MyScaleStorage, DatabaseConfig
from dataflow.utils.utils import get_logger
from dataflow.utils.registry import GENERATOR_REGISTRY
from dataflow.generator.utils.CategoryFuzzer import category_hasher_reverse
from transformers import AutoTokenizer
import os

logger = get_logger()

@GENERATOR_REGISTRY.register()
class ReasoningQualityJudger:
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
        self.input_key = self.config.get("input_key", "data")
        #self.question_key = self.config.get("question_key", "question")
        #self.answer_key = self.config.get("answer_key", "answer")
        #self.primary_category_key = self.config.get("primary_category_key", "primary_category")
        # self.secondary_category_key = self.config.get("secondary_category_key", "secondary_category")
        #self.difficulty_key = self.config.get("difficulty_key", "difficulty")

        self.read_min_score = self.config.get("read_min_score", 0.9)
        self.read_max_score = self.config.get("read_max_score", 2.0)
        self.eval_stage = self.config.get("eval_stage", 7)

        self.tokenizer_name_or_path = self.config.get("tokenizer_name_or_path", "Qwen/Qwen2.5-7B-Instruct")
        
        # Ensure input_file and output_file are provided
        if not hasattr(self, "storage") and (not self.input_file or not self.output_file):
            raise ValueError("Both input_file and output_file must be specified in the config.")
        
    def _load_input(self):
        if hasattr(self, 'storage'):
            value_list = self.storage.read_json(
                ['data'] + [f'eval_score_{i}' for i in range(1, self.eval_stage)] + [f'eval_algorithm_{i}' for i in range(1, self.eval_stage)], eval_stage=self.eval_stage, maxmin_scores=[dict(zip(['min_score', 'max_score'], list(_))) for _ in list(zip(self.read_min_score, self.read_max_score))], stage=self.stage, pipeline_id=self.pipeline_id, category="reasoning"
            )
            expanded_value_list = []
            for item in value_list:
                data_json = item['data']
                item['id'] = str(item['id'])
                del item['data']
                expanded_value_list.append(data_json | item)
            dataframe = pd.DataFrame(expanded_value_list)
            # print(dataframe.keys())
            return dataframe

        else:
            return pd.read_json(self.input_file, lines=True)

    def category_judger(self,dataframe, stage_name):
        
        # 输出每个类别的数量
        dataframe["category"] = dataframe[stage_name].apply(category_hasher_reverse)
        dict = {}
        for index, row in dataframe.iterrows():
            category = row["category"]
            if category in dict.keys():
                dict[category].append(row["id"])
            else:
                dict[category] = [row["id"]]
        # lst = dataframe["category"].value_counts().to_dict()
        #for key, value in lst.items():
        #    print(f"{key}: {value}")
        
        return dict
    
    def difficulty_judger(self,dataframe, stage_name):
        # 输出每个难度的数量
        dict = {}
        for index, row in dataframe.iterrows():
            difficulty = row[stage_name]
            if difficulty in dict.keys():
                dict[difficulty].append(row["id"])
            else:
                dict[difficulty] = [row["id"]]
        #for key, value in lst.items():
        #    print(f"{key}: {value}")
        return dict
    
    def token_calculator(self,dataframe):
        questions = []
        answers = []
        empty_question = 0
        empty_answer = 0
        for index, row in dataframe.iterrows():
            try:
                question = row['instruction']
                if question == "" or question == "None":
                    empty_question += 1
                    question = ""
                questions.append(question)
            except:
                empty_question += 1
            try:
                answer = row['generated_cot']
                if answer == "" or answer == "None":
                    empty_answer += 1
                    answer = ""
                answers.append(answer)
            except:
                empty_answer += 1
                answer = ""
                answers.append(answer)
        tokenizer = AutoTokenizer.from_pretrained(self.tokenizer_name_or_path)
        question_length = []
        answer_length = []
        for question in questions:
            # Add type checking and default value
            if not isinstance(question, str) or not question:
                question = ""  # or some default value
                empty_question += 1
            
            tokens = tokenizer.encode(question, add_special_tokens=True)
            question_length.append(len(tokens))
        
        for answer in answers:
            tokens = tokenizer.encode(answer, add_special_tokens=True)
            answer_length.append(len(tokens))
        
        # 报告平均长度、最大长度、最小长度
        # print(f"Question average length: {sum(question_length) / len(question_length)}")
        # print(f"Question max length: {max(question_length)}")
        # print(f"Question min length: {min(question_length)}")
        # print(f"Answer average length: {sum(answer_length) / len(answer_length)}")
        # print(f"Answer max length: {max(answer_length)}")
        # print(f"Answer min length: {min(answer_length)}")
        # 两位小数
        output = {
            "empty_question_number": empty_question,
            "empty_answer_number": empty_answer,
            "question_average_length": round(sum(question_length) / len(question_length), 2),
            "question_max_length": max(question_length),
            "question_min_length": min(question_length),
            "answer_average_length": round(sum(answer_length) / len(answer_length), 2),
            "answer_max_length": max(answer_length),
            "answer_min_length": min(answer_length)
        }
        return output
    
    def run(self):
        dataframe = self._load_input()
        keys = dataframe.keys()
        if dataframe.shape[0] == 0:
            logger.warning("No data found in the input file.")
            return

        if not hasattr(self, "storage"):
            QuestionCategoryKey = self.config.get("primary_category_key",None)
            QuestionDifficultyKey = self.config.get("difficulty_key",None)
        else:
            row = dataframe.iloc[0]
            QuestionCategoryKey = None
            QuestionDifficultyKey = None
            for key in keys:
                if row[key] == "QuestionCategoryClassifier":
                    logger.info(f"Question Category Classifier: {key}")
                    id = key.split("_")[-1]
                    QuestionCategoryKey = f"eval_score_{id}"
                if row[key] == "QuestionDifficultyClassifier":
                    logger.info(f"Question Difficulty Classifier: {key}")
                    id = key.split("_")[-1]
                    QuestionDifficultyKey = f"eval_score_{id}"
        if QuestionCategoryKey:
            category_lst = self.category_judger(dataframe, QuestionCategoryKey)
            logger.info(f"Question Category Information: {category_lst}")
        else:
            logger.warning("No Question Category Information")
        if QuestionDifficultyKey:
            difficulty_lst = self.difficulty_judger(dataframe, QuestionDifficultyKey)
            logger.info(f"Question Difficulty Information: {difficulty_lst}")
        else:
            logger.warning("No Question Difficulty Information")
        token_info = self.token_calculator(dataframe)
        logger.info(f"Token Information: {token_info}")
        # save category_lst, difficulty_lst, token_info to txt
        return category_lst, difficulty_lst, token_info