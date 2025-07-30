from datasets import Dataset
from dataflow.data import MyScaleStorage, TextDataset, DatabaseConfig
from dataflow.format import TextFormatter
from dataflow.utils.utils import get_logger
import os

class Deduplicator:

    def __init__(self, args):
        pass

    def dedup_func(self, dataset):
        raise NotImplementedError

    def __call__(self, dataset):
        init_len = len(dataset)
        deduped_dataset = self.dedup_func(dataset)
        print(f'Implemented {self.__class__.__name__}. Data Number: {init_len} -> {len(deduped_dataset)}')
        
        return deduped_dataset

class TextDeduplicator(Deduplicator):

    def __init__(self, args=None):
        self.data_type = "text"
        self.deduplicator_name = "TextDeduplicator"
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
            self.dataset = self._load_input()

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
        labels = self.dedup_func(dataset)
        if isinstance(dataset.dataset, Dataset):
            def filter_by_labels(example, index):
                return labels[index] == 1
            dataset.dataset = dataset.dataset.filter(filter_by_labels, with_indices=True)
            deduped_dataset = dataset
        else:
            deduped_dataset = dataset.filter(labels)
        self.logger.info(f'Implemented {self.dedupliactor_name}. Data Number: {init_len} -> {len(deduped_dataset)}')
        return labels, deduped_dataset
    
    def run(self):
        labels, deduplicated_dataset = self.__call__(self.dataset)
        if hasattr(self, 'storage'):
            self._write_output(labels, self.ids)
        else:
            deduplicated_dataset.dump(self.config['output_file'])

class ImageDeduplicator(Deduplicator):

    def __init__(self, args=None):
        self.data_type = "image"
