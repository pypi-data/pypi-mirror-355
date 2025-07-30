from dataflow.format import TextFormatter
from dataflow.data import MyScaleStorage, TextDataset, DatabaseConfig
from dataflow.utils.utils import get_logger
from datasets import Dataset
import os

class Refiner():

    def __init__(self, args):
        pass

    def __call__(self, dataset):
        pass

class TextRefiner(Refiner):

    def __init__(self, args=None):
        self.data_type = "text"
        self.logger = get_logger()
        use_db = args.get("use_db", False) or os.environ.get("USE_DB", "").lower() == "true"
        if "input_file" in args.keys():
            self.config = args
            self.formatter = TextFormatter(args)
            self.dataset = self.formatter.load_dataset()
        elif use_db:
            db_config = DatabaseConfig(
                host=os.environ.get('MYSCALE_HOST', 'localhost'),
                port=int(os.environ.get('MYSCALE_PORT', '9000')),
                db_name=os.environ.get('MYSCALE_DATABASE', 'dataflow'),
                table_name=os.environ.get('MYSCALE_TABLE_NAME', ''),
                username=os.environ.get('MYSCALE_USER', ''),
                password=os.environ.get('MYSCALE_PASSWORD', '')
            )
            self.storage = MyScaleStorage(db_config)
            self.stage = args['stage']
            self.pipeline_id = args['pipeline_id']
            self.eval_stage = args['eval_stage'] 
            self.read_format = args['read_format']
            self.read_syn = args['read_syn']
            self.read_min_score = args.get('read_min_score', [])
            self.read_max_score = args.get('read_max_score', [])
            self.write_format = args['write_format']
            self.write_syn = args['write_syn']
            self.ids = None
            self.dataset = self._load_input()
            # self.write_format = args['write_format']
            # self.write_syn = args['write_syn']

    def _load_input(self):
        if self.read_format == "PT": 
            value_list = self.storage.read_str(['data'], category='text', pipeline_id=self.pipeline_id, stage=self.stage, eval_stage=self.eval_stage, format=self.read_format, syn=self.read_syn, maxmin_scores=[dict(zip(['min_score', 'max_score'], list(_))) for _ in list(zip(self.read_min_score, self.read_max_score))])
            self.ids = [str(_['id']) for _ in value_list]
            dataset = Dataset.from_list([{'data': _['data']} for _ in value_list])
            return TextDataset(
                dataset=dataset,
                keys='data',
                metadata=None
            )
        else:
            value_list = self.storage.read_json(['data'], category='text', pipeline_id=self.pipeline_id, stage=self.stage, eval_stage=self.eval_stage, format=self.read_format, syn=self.read_syn, maxmin_scores=[dict(zip(['min_score', 'max_score'], list(_))) for _ in list(zip(self.read_min_score, self.read_max_score))])
            expanded_value_list = [
                item['data']
                for item in value_list
            ]
            self.ids = [str(_['id']) for _ in value_list]
            dataset = Dataset.from_list(expanded_value_list)
            return TextDataset(
                dataset=dataset,
                keys=value_list[0].keys(),
                metadata=None
            )
        
    def _write_output(self, refined_dataset, ids):
        if self.write_format == "PT":
            data = refined_dataset.to_list()
            id_data = [
                {'id': id, 'data': item['data']}
                for id, item in zip(self.ids, data)
            ]
            self.storage.write_str(id_data, format=self.write_format, syn=self.write_syn, category='text', pipeline_id=self.pipeline_id, stage=self.stage+1)
        else:
            data = refined_dataset.to_list()
            id_data = [
                {'id': id} | item
                for id, item in zip(self.ids, data)
            ]
            self.storage.write_json(id_data, format=self.write_format, syn=self.write_syn, category='text', pipeline_id=self.pipeline_id, stage=self.stage+1)
        
    def __call__(self, dataset):
        refined_dataset, numbers = self.refine_func(dataset)
        self.logger.info(f'Implemented {self.refiner_name}. {numbers} data refined.')
        
        return refined_dataset
    
    def run(self):
        refined_dataset = self.__call__(self.dataset)
        if hasattr(self, 'storage'):
            self._write_output(refined_dataset, self.ids)
        else:
            refined_dataset.dump(self.config['output_file'])
