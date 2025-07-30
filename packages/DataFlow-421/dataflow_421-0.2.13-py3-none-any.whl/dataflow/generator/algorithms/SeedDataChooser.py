import os
os.environ['CUDA_VISIBLE_DEVICES'] = '0,1,2,3,4,5,6,7'  # Set the visible GPUs
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'  # Use a mirror if needed
from sentence_transformers import SentenceTransformer, models, util
from transformers import AutoModel, AutoTokenizer
import json
import random
import matplotlib.pyplot as plt

from typing import List, Optional

import torch
import torch.nn.functional as F
from torch import Tensor

# from anomalib.models.components.dimensionality_reduction import SparseRandomProjection


class KCenterGreedy:
    """Implements k-center-greedy method.

    Args:
        embedding (Tensor): Embedding vector extracted from a CNN
        sampling_ratio (float): Ratio to choose coreset size from the embedding size.

    Example:
        >>> embedding.shape
        torch.Size([219520, 1536])
        >>> sampler = KCenterGreedy(embedding=embedding)
        >>> sampled_idxs = sampler.select_coreset_idxs()
        >>> coreset = embedding[sampled_idxs]
        >>> coreset.shape
        torch.Size([219, 1536])
    """

    def __init__(self, embedding: Tensor, sampling_ratio: float) -> None:
        self.embedding = embedding
        self.coreset_size = int(embedding.shape[0] * sampling_ratio)
        # self.model = SparseRandomProjection(eps=0.9)

        self.features: Tensor
        self.min_distances: Tensor = None
        self.n_observations = self.embedding.shape[0]

    def reset_distances(self) -> None:
        """Reset minimum distances."""
        self.min_distances = None

    def update_distances(self, cluster_centers: List[int]) -> None:
        """Update min distances given cluster centers.

        Args:
            cluster_centers (List[int]): indices of cluster centers
        """

        if cluster_centers:
            centers = self.features[cluster_centers]

            distance = F.pairwise_distance(self.features, centers, p=2).reshape(-1, 1)

            if self.min_distances is None:
                self.min_distances = distance
            else:
                self.min_distances = torch.minimum(self.min_distances, distance)

    def get_new_idx(self) -> int:
        """Get index value of a sample.

        Based on minimum distance of the cluster

        Returns:
            int: Sample index
        """

        if isinstance(self.min_distances, Tensor):
            idx = int(torch.argmax(self.min_distances).item())
        else:
            raise ValueError(f"self.min_distances must be of type Tensor. Got {type(self.min_distances)}")

        return idx

    def select_coreset_idxs(self, selected_idxs: Optional[List[int]] = None) -> List[int]:
        """Greedily form a coreset to minimize the maximum distance of a cluster.

        Args:
            selected_idxs: index of samples already selected. Defaults to an empty set.

        Returns:
          indices of samples selected to minimize distance to cluster centers
        """

        if selected_idxs is None:
            selected_idxs = []

        if self.embedding.ndim == 2:
            # self.model.fit(self.embedding)
            # self.features = self.model.transform(self.embedding)
            
            self.features = self.embedding
            self.reset_distances()
        else:
            self.features = self.embedding.reshape(self.embedding.shape[0], -1)
            self.update_distances(cluster_centers=selected_idxs)

        selected_coreset_idxs: List[int] = []
        idx = int(torch.randint(high=self.n_observations, size=(1,)).item())
        cnt = 0
        for _ in range(self.coreset_size):
            cnt += 1
            if(cnt % 1000 == 0):
                print(cnt)
            self.update_distances(cluster_centers=[idx])
            idx = self.get_new_idx()
            if idx in selected_idxs:
                raise ValueError("New indices should not be in selected indices.")
            self.min_distances[idx] = 0
            selected_coreset_idxs.append(idx)

        return selected_coreset_idxs

    def sample_coreset(self, selected_idxs: Optional[List[int]] = None) -> Tensor:
        """Select coreset from the embedding.

        Args:
            selected_idxs: index of samples already selected. Defaults to an empty set.

        Returns:
            Tensor: Output coreset

        Example:
            >>> embedding.shape
            torch.Size([219520, 1536])
            >>> sampler = KCenterGreedy(...)
            >>> coreset = sampler.sample_coreset()
            >>> coreset.shape
            torch.Size([219, 1536])
        """

        idxs = self.select_coreset_idxs(selected_idxs)
        coreset = self.embedding[idxs]

        return coreset
    
from dataflow.utils.registry import GENERATOR_REGISTRY
from dataflow.data import MyScaleStorage, DatabaseConfig
from dataflow.utils.utils import get_logger
from dataflow.generator.utils.APIGenerator_aisuite import APIGenerator_aisuite
from dataflow.generator.utils.APIGenerator_request import APIGenerator_request
import pandas as pd

@GENERATOR_REGISTRY.register()
class SeedDataChooser:
    '''
    SeedDataChooser is a generator that selects a subset of data from a larger dataset using K-Center Greedy sampling.
    '''

    def __init__(self, config: dict):
        self.config = config
        self.logger = get_logger()
        self.generator = self.__init_model__()

        self.input_key = config.get("input_key", "text")
        self.output_question_key = config.get("question_key", "question")
        self.output_answer_key = config.get("answer_key", "answer")
        self.num_samples = config.get("num_samples", 10)
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
            self.stage = config.get("stage", 0)
            self.eval_stage = self.config.get('eval_stage', 0)
            self.pipeline_id = config.get("pipeline_id", "")
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
                "SeedDataChooser 是一个生成器，它使用 K-Center Greedy 采样方法从更大的数据集中选择一个子集的数据。"
            )
        elif lang == "en":
            return (
                "SeedDataChooser is a generator that selects a subset of data from a larger dataset using K-Center Greedy sampling."
            )
        else:
            return (
                "SeedDataChooser is a generator that selects a subset of data from a larger dataset using K-Center Greedy sampling."
            )

    def _load_input(self):
        if hasattr(self, 'storage'):
            value_list = self.storage.read_json(
                ["data"], eval_stage=self.eval_stage, syn='', format='PT', stage=self.stage, pipeline_id=self.pipeline_id, category="RAG"
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
            self.storage.write_eval(output_rows, stage=self.stage+1, algo_name=self.__class__.__name__, score_key="ifchoose")
        else:
            dataframe.to_json(save_path, orient="records", lines=True, force_ascii=False)

    def run(self):
        input_df = self._load_input()
        texts = input_df[self.input_key].tolist()
        model_name = "/mnt/public/data/lh/models/hub/gte-Qwen2-7B-instruct"
        model = SentenceTransformer(model_name, trust_remote_code=True)
        model.max_seq_length = 8196
        input_embeddings = model.encode(texts, prompt_name="query", batch_size=8)
        embeddings = torch.tensor(input_embeddings)
        sampler = KCenterGreedy(embedding=embeddings, sampling_ratio=self.num_samples / len(texts))
        sampled_idxs = sampler.select_coreset_idxs()
        # sampled_idxs = list(range(len(texts)))
        selected_df = input_df.iloc[sampled_idxs].copy()
        input_df["ifchoose"] = 0
        input_df.loc[sampled_idxs, "ifchoose"] = 1
        input_df["original_id"] = list(range(len(texts)))
        
        self._write_output(self.output_file, input_df)
        self.logger.info(f"Sampled {len(sampled_idxs)} data points from {len(texts)} total data points.")