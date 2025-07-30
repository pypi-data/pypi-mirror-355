from dataflow.data import DataFlowDataset, MyScaleStorage, TextDataset, DatabaseConfig
from dataflow.core import ScoreRecord
from dataflow.format import TextFormatter
from datasets import Dataset
from dataflow.utils.utils import get_logger
import os

class Filter():

    def __init__(self, args=None):
        pass

    def filter_func(self):
        pass
    
    def __call__(self, dataset: DataFlowDataset):
        pass

class TextFilter(Filter):
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
            self.ids = None
            self.keys = args['keys']
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
                keys=self.keys,
                metadata=None
            )
        
    def _write_output(self, labels, ids):
        output_rows = []
        for id, label in zip(ids, labels):
            output_rows.append({
                'score': label,
                'id': id
            })
        self.storage.write_eval(output_rows, stage=self.stage+1, algo_name=self.__class__.__name__, score_key='score')
        
    def __call__(self, dataset):
        init_len = len(dataset)
        score_record = ScoreRecord()
        dataset.set_score_record(score_record)
        labels = self.filter_func(dataset)
        if isinstance(dataset.dataset, Dataset):
            def filter_by_labels(example, index):
                return labels[index] == 1
            dataset.dataset = dataset.dataset.filter(filter_by_labels, with_indices=True)
            filtered_dataset = dataset
        else:
            filtered_dataset = dataset.filter(labels)
        self.logger.info(f'Implemented {self.filter_name}. Data Number: {init_len} -> {len(filtered_dataset)}')
        return labels, filtered_dataset
    
    def run(self):
        labels, filtered_dataset = self.__call__(self.dataset)
        if hasattr(self, 'storage'):
            self._write_output(labels, self.ids)
        else:
            filtered_dataset.dump(save_path=self.config['output_file'])

class ImageFilter(Filter):
    
    def __init__(self, args=None):
        super().__init__()
        self.data_type = "image"
        
    def __call__(self, dataset: DataFlowDataset):
        init_len = len(dataset)
        score_record = ScoreRecord()
        dataset.set_score_record(score_record)
        filtered_dataset = dataset.filter(self.filter_func(dataset))
        print(f'Implemented {self.__class__.__name__}. Data Number: {init_len} -> {len(filtered_dataset)}')

        return filtered_dataset

class ImageTextFilter(Filter):
    
    def __init__(self, args=None):
        super().__init__()
        self.data_type = "image_caption"
        
    def __call__(self, dataset: DataFlowDataset):
        init_len = len(dataset)
        score_record = ScoreRecord()
        dataset.set_score_record(score_record)
        filtered_dataset = dataset.filter(self.filter_func(dataset))
        print(f'Implemented {self.__class__.__name__}. Data Number: {init_len} -> {len(filtered_dataset)}')

        return filtered_dataset

class VideoFilter(Filter):
    
    def __init__(self, args=None):
        self.data_type = "video"
        
    def __call__(self, dataset: DataFlowDataset):
        score_record = ScoreRecord()
        dataset.set_score_record(score_record)
        filtered_dataset = dataset.filter(self.filter_func(dataset))
        print(filtered_dataset.get_indices())
        return filtered_dataset

class VideoTextFilter(Filter):
    
    def __init__(self, args=None):
        self.data_type = "video_caption"
        
    def __call__(self, dataset: DataFlowDataset):
        score_record = ScoreRecord()
        dataset.set_score_record(score_record)
        filtered_dataset = dataset.filter(self.filter_func(dataset))
        print(filtered_dataset.get_indices())
        return filtered_dataset