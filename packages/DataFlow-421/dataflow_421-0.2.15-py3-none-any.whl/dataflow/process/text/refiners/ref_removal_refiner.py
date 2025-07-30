from dataflow.core import TextRefiner
from dataflow.data import TextDataset
import re
from dataflow.utils.registry import PROCESSOR_REGISTRY
from tqdm import tqdm
from dataflow.utils.utils import get_logger

"""
This refiner class, ReferenceRemoverRefiner, is designed to clean text data by removing unclosed or incomplete reference tags and citation links. 
It iterates over specified fields in a dataset, detects and removes any unclosed reference tags (e.g., <ref>, </ref>) 
and citation links (e.g., {{cite web}}) in the text. After removal, it returns the refined dataset and counts how many items were modified.
"""

@PROCESSOR_REGISTRY.register()
class ReferenceRemoverRefiner(TextRefiner):
    def __init__(self, args_dict: dict):
        super().__init__(args_dict)
        self.logger = get_logger()
        self.refiner_name = 'ReferenceRemoverRefiner'
        self.logger.info(f"Initializing {self.refiner_name}...")

    @staticmethod
    def get_desc(self, lang):
        return "删除文本中未闭合的引用标签和引用链接" if lang == "zh" else "Remove unclosed reference tags and citation links from the text."

    def refine_func(self, dataset: TextDataset):
        """
        遍历数据集中的每一项，检测并删除未闭合的引用标签和引用链接。

        Args:
            dataset (TextDataset): 包含文本数据的TextDataset对象。

        Returns:
            TextDataset: 经过引用标签和链接删除后的TextDataset对象。
            int: 被修改的数据项数量。
        """
        self.logger.info(f"Start running {self.refiner_name}...")

        # 初始化被修改的数据项计数
        numbers = 0

        # 确定要处理的字段键
        # 假设dataset.keys是一个列表，包含需要处理的字段名
        # 如果dataset.keys不是列表，则将其转换为列表
        keys = dataset.keys if isinstance(dataset.keys, list) else [dataset.keys]

        # 定义要删除的模式 - 更全面的版本
        # 1. 所有<ref>标签及其内容(包括各种不完整形式)
        ref_pattern = re.compile(
            r'<ref\b[^>]*>.*?</ref>|'  # 完整的ref标签
            r'<ref\b[^>]*>[^<]*$|'     # 不完整的ref标签(没有闭合)
            r'<ref\b[^>]*>.*?/br'      # ref标签后跟/br(如你示例中的情况)
        )
        
        # 2. 所有{{cite}}模板及其内容(包括各种不完整形式)
        cite_pattern = re.compile(
            r'\{\{cite\s+\w+\|[^}]*\}\}|'  # 完整的cite模板
            r'\{\{cite\s+\w+\|[^}]*$'      # 不完整的cite模板(没有闭合)
        )

        # 遍历数据集中的每一项
        refined_data = []
        for item in tqdm(dataset, desc=f"Implementing {self.refiner_name}"):
            if isinstance(item, dict):
                modified = False
                # 遍历所有指定的字段
                for key in keys:
                    if key in item and isinstance(item[key], str):
                        original_text = item[key]
                        refined_text = original_text

                        # 删除所有未闭合的ref标签
                        refined_text, ref_count = ref_pattern.subn('', refined_text)
                        
                        # 删除所有不完整的cite模板
                        refined_text, cite_count = cite_pattern.subn('', refined_text)

                        # 检查是否有任何修改
                        if ref_count > 0 or cite_count > 0:
                            modified = True
                            numbers += 1
                            self.logger.debug(f"Item modified, removed {ref_count} ref tags and {cite_count} cite templates")

                # 将处理后的项添加到新的数据集中
                refined_data.append(item)
                if modified:
                    self.logger.debug(f"Item modified, total modified so far: {numbers}")
            else:
                # 如果item不是字典，直接添加到新的数据集中，不做修改
                refined_data.append(item)
                self.logger.warning(f"Item is not a dictionary, skipping: {item}")

        # 更新dataset的数据为经过refine后的数据
        dataset.dataset = refined_data

        self.logger.info(f"Refining completed. Total items modified: {numbers}")
        return dataset, numbers