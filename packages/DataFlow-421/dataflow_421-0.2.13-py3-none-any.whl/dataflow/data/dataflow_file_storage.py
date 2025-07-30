import json
import uuid
import pandas as pd
from abc import ABC, abstractmethod
from typing import Any, Literal
from clickhouse_driver import Client
from dataflow.utils.utils import get_logger
from .storage import DataFlowStorage

class DataFlowFileStorage(DataFlowStorage):

    def __init__(self, **kwargs):
        if 'input_file' not in kwargs and 'output_file' not in kwargs:
            raise ValueError(f"Requires input/output file!")
        self.input_file = kwargs['input_file']
        self.output_file = kwargs['output_file']

    def read_df(self, lines: bool):
        return pd.read_json(self.input_file, lines=lines)

    def read_json(self, lines: bool):
        if lines:
            with open(self.input_file, 'r') as f:
                data = [json.loads(_) for _ in f]
            return data
        else:
            with open(self.input_file, 'r') as f:
                return json.load(f)
    
    def write_df(self, data: pd.DataFrame, lines=True):
        data.to_json(self.output_file, orient='records', lines=lines)

    def write_data(self, data: list, **kwargs) -> None:
        """Write data to file"""
        if not hasattr(self, 'output_file'):
            raise ValueError("output_file not set")
        with open(self.output_file, 'w') as f:
            for item in data:
                json.dump(item, f)
                f.write('\n')

    def write_eval(self, data: list, **kwargs) -> None:
        """Write evaluation results to file"""
        if not hasattr(self, 'output_file'):
            raise ValueError("output_file not set")
        with open(self.output_file, 'w') as f:
            for item in data:
                json.dump(item, f)
                f.write('\n')

    def write_json(self, data, lines=True):
        if lines:
            with open(self.output_file, 'w') as f:
                for item in data:
                    json.dump(item, f, ensure_ascii=True)
                    f.write('\n')
        else:
            with open(self.output_file, 'w') as f:
                json.dump(data, f)

    def read_str(self, key_list: list, **kwargs) -> list:
        """Read string data from file"""
        if not hasattr(self, 'input_file'):
            raise ValueError("input_file not set")
        data = pd.read_csv(self.input_file)
        return data.to_dict('records')

    def write_str(self, data: list, **kwargs) -> None:
        """Write string data to file"""
        if not hasattr(self, 'output_file'):
            raise ValueError("output_file not set")
        with open(self.output_file, 'w') as f:
            for item in data:
                f.write(item['data'] + '\n')
        
    def read_code(self, key_list: list, **kwargs) -> list:
        """Read code data from file"""
        if not hasattr(self, 'input_file'):
            raise ValueError("input_file not set")
        data = pd.read_json(self.input_file, lines=True)
        return data.to_dict('records')

    def write_code(self, data: list, **kwargs) -> None:
        """Write code data to file"""
        if not hasattr(self, 'output_file'):
            raise ValueError("output_file not set")
        with open(self.output_file, 'w') as f:
            for item in data:
                f.write(item['code'] + '\n')
