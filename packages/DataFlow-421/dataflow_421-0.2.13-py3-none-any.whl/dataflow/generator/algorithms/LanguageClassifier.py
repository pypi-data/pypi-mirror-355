import json
import logging
from tqdm import tqdm
import torch
import os
# from transformers import AutoTokenizer, AutoModelForSequenceClassification
# from guesslang import Guess
from dataflow.data import MyScaleStorage
from dataflow.utils.utils import get_logger
from dataflow.utils.registry import GENERATOR_REGISTRY
from dataflow.generator.utils.APIGenerator_aisuite import APIGenerator_aisuite
from dataflow.generator.utils.APIGenerator_request import APIGenerator_request
from dataflow.generator.utils.Prompts import LanguageClassifierPrompt as LCP
import random
# guess = Guess()
# print(guess.supported_languages)
# def batch(iterable, size):
#     b = []
#     for item in iterable:
#         b.append(item)
#         if len(b) == size:
#             yield b
#             b = []
#     if b:
#         yield b

# class CodeBertClassifier:
#     def __init__(self, config):
#         self.config = config 
#         self.input_file = config.get("input_file")
#         self.output_file = config.get("output_file")
#         self.input_key = config.get('input_key', 'code')
#         self.output_key = config.get('output_key', 'label')
#         self.batch_size = 64
#         self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
#         self.model_name = 'philomath-1209/programming-language-identification'
#         self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
#         self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name).to(self.device)
#         self.logger = get_logger()
#         if 'db_name' in config.keys():
#             self.storage = MyScaleStorage(config['db_port'], config['db_name'], config['table_name'])
#             self.pipeline_id = config['pipeline_id']
#             self.stage = config.get('stage', 0)
#             self.eval_stage = config.get('eval_stage', 0)



#     def predict(self):
#         self.logger.info("Predicting language using CodeBERT model...")
#         all_results = []
#         # true_labels = []
#         data = self.storage.read_str(['data'], category='code', format='PT', syn='', pipeline_id=self.pipeline_id, stage=self.stage, eval_stage=self.eval_stage)
#         for line_batch in tqdm(batch(data, self.batch_size), desc="Predicting"):
#             # samples = [json.loads(line.strip()) for line in line_batch]
#             codes = [sample['data'] for sample in line_batch]
#             # true_langs = [sample["label"] for sample in samples]
#             inputs = self.tokenizer(codes, return_tensors="pt", truncation=True, padding=True, max_length=512)
#             inputs.to(self.device)
#             with torch.no_grad():
#                 logits = self.model(**inputs).logits
#                 pred_ids = torch.argmax(logits, dim=-1).tolist()
#             for pred_id in pred_ids:
#                 predicted_lang = self.model.config.id2label[pred_id].lower()
#                 all_results.append(predicted_lang)
#                 # for true_lang, pred_id in zip(true_langs, pred_ids):
#                 #     predicted_lang = self.model.config.id2label[pred_id]
#                 #     output_data = {
#                 #         "true_lang": true_lang.lower(),
#                 #         "predicted_lang": predicted_lang.lower()
#                 #     }
#                 #     all_results.append(output_data['predicted_lang'])
#                 #     true_labels.append(true_lang)
#                 #     fout.write(json.dumps(output_data, ensure_ascii=False) + "\n")
#         # print(self.calculate_accuracy(true_labels, all_results))
#         return all_results
    
#     # def calculate_accuracy(self, true, pred):
#     #     normal_dict = {
#     #         'csharp': 'c#',
#     #         'java': 'java',
#     #         'cpp': 'c++'
#     #     }
#     #     total = len(true)
#     #     correct = 0
#     #     for i in range(len(true)):
#     #         # print(normal_dict[true[i]], pred[i])
#     #         if normal_dict[true[i]] == pred[i]:
#     #             correct += 1
#     #     accuracy = correct / total
#     #     return accuracy

# class GuessLangClassifier:
#     def __init__(self, config):
#         self.config = config
#         self.input_file = config.get('input_file')
#         self.output_file = config.get('output_file')
#         self.input_key = config.get('input_key', 'code')
#         self.output_key = config.get('output_key', 'label')
#         self.classifier = Guess()
#         self.logger = get_logger()
#         if 'db_name' in config.keys():
#             self.storage = MyScaleStorage(config['db_port'], config['db_name'], config['table_name'])
#             self.pipeline_id = config['pipeline_id']
#             self.stage = config.get('stage', 0)
#             self.eval_stage = config.get('eval_stage', 0)


#     def predict(self):
#         self.logger.info("Predicting language using guesslang model...")
#         results = []
#         data = self.storage.read_str(['data'], category='code', format='PT', syn='', pipeline_id=self.pipeline_id, stage=self.stage, eval_stage=self.eval_stage)
#         # with open(self.input_file, 'r', encoding='utf-8') as f:
#         for item in tqdm(data, desc="Processing"):
#             # item = json.loads(line)
#             code = item['data']
#             language_id = self.classifier.language_name(code)
#             results.append(language_id.lower())
#         return results

@GENERATOR_REGISTRY.register()
class LanguageClassifier:
    def __init__(self, config, args=None):
        self.args = args
        self.config = config
        self.input_file = config.get('input_file')
        self.output_file = config.get('output_file')
        self.input_key = config.get('input_key', 'code')
        self.output_key = config.get('output_key', 'label')
        # self.codebert_classifier = CodeBertClassifier(self.config)
        # self.guesslang_calssifier = GuessLangClassifier(self.config)
        self.logger = get_logger()
        self.logger.info("Initializing LanguageClassifier...") 
        self.generator = self.__init_model__()
        # self.guesslang_classifier = 
        if 'db_name' in config.keys():
            self.storage = MyScaleStorage(config['db_port'], config['db_name'], config['table_name'])
            self.pipeline_id = config['pipeline_id']
            self.stage = config.get('stage', 0)
            self.eval_stage = config.get('eval_stage', 0)
        if (not self.input_file or not self.output_file) and not hasattr(self.storage):
            raise ValueError("Both input_file and output_file must be specified in the config.")

    def __init_model__(self):
        generator_type = self.config.get("generator_type", "request").lower()
        if generator_type == "aisuite":
            return APIGenerator_aisuite(self.config)
        elif generator_type == "request":
            return APIGenerator_request(self.config)
        else:
            raise ValueError(f"Unsupported generator_type: {generator_type}")

    @staticmethod
    def get_desc(lang):
        return "识别代码数据的语言" if lang == "zh" else "Identify the language of code data"

    def _load_input(self):
        if hasattr(self, 'storage'):
            data = self.storage.read_str(['data'], category='code', format='PT', syn='', pipeline_id=self.pipeline_id, stage=self.stage, eval_stage=self.eval_stage)
            return data
        else:
            with open(self.input_file, 'r') as f:
                return [json.loads(_) for _ in f]

    def _write_output(self, data):
        if hasattr(self, 'storage'):
            self.storage.write_data(data, category='code', stage=self.stage+1)
        else:
            with open(self.output_file, 'w') as f:
                for item in data:
                    json.dump(item, f)
                    f.write('\n')

    def run(self):
        self.logger.info("Start running LanguageClassifier...")
        self.logger.info(f"Reading input file: {self.input_file}...")
        data = self._load_input()
        prompts = []
        for item in tqdm(data, desc="Processing"):
            # item = json.loads(line)
            code = item[self.input_key]
            prompts.append(LCP.language_classifier_prompt(self, code=code))

        predictions = self.generator.generate_text_from_input(prompts)
        possible_languages = ['Assembly', 'Batchfile', 'C',	'C#', 'C++', 'Clojure', 'CMake', 'COBOL', 'CoffeeScript', 'CSS',
        'CSV', 'Dart', 'DM', 'Dockerfile', 'Elixir', 'Erlang', 'Fortran', 'Go', 'Groovy', 'Haskell', 'HTML', 'INI', 'Java', 'JavaScript', 'JSON',
        'Julia', 'Kotlin', 'Lisp', 'Lua', 'Makefile', 'Markdown', 'Matlab', 'Objective-C', 'OCaml', 'Pascal', 'Perl', 'PHP', 'PowerShell', 'Prolog', 'Python',
        'R', 'Ruby', 'Rust', 'Scala', 'Shell', 'SQL', 'Swift', 'TeX', 'TOML', 'TypeScript', 'Verilog', 'Visual Basic', 'XML', 'YAML']
        possible_languages = [lang.lower() for lang in possible_languages]
        final_predictions = []
        # count = 0
        for i in range(len(predictions)):
            final_prediction = predictions[i].lower().strip()
            if not final_prediction in possible_languages:
                # count += 1
                final_prediction = random.choice(possible_languages)
            if final_prediction == 'c' or final_prediction == 'objective-c':
                final_prediction = 'c++'
            if final_prediction == 'typescript':
                final_prediction = 'javascript'
            if final_prediction == "c++":
                final_prediction = "cpp"
            if final_prediction == "c#":
                final_prediction = "c_sharp"
            final_predictions.append({self.output_key: final_prediction})
        # data = self.storage.read_str(['data'], category='code', format='PT', syn='', pipeline_id=self.pipeline_id, stage=self.stage, eval_stage=self.eval_stage)
        # with open(self.output_file, 'w', encoding='utf-8') as f:
        #     with open(self.input_file, 'r', encoding='utf-8') as g:
        #         data = [json.loads(_) for _ in g]
        # print(f"Total {len(data)} data, {count} data not in the language list, replaced with random language.")
        new_data = []
        # for item, pred in zip(data, final_predictions):
        #     new_data.append({'id': item['id'], 'code': item['data'], 'lang': pred['lang']})
        # self.storage.write_data(new_data, category='code', stage=self.stage+1)
        if hasattr(self, 'storage'):
            for item, pred in zip(data, final_predictions):
                new_data.append({'id': item['id'], 'code': item['data'], 'lang': pred['lang']})
        else:
            for item, pred in zip(data, final_predictions):
                new_data.append({'content': item['content'], 'lang': pred['lang']})
        self._write_output(new_data)