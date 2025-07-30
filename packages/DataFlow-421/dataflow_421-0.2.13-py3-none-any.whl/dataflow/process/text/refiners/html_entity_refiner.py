from dataflow.core import TextRefiner
from dataflow.data import TextDataset
import re
from dataflow.utils.registry import PROCESSOR_REGISTRY
from tqdm import tqdm
from dataflow.utils.utils import get_logger

"""
This refiner class, HTMLEntityRefiner, is designed to clean text data by removing HTML entities. 
It iterates over specified fields in a dataset, detects and removes any HTML entities (e.g., &nbsp;, &lt;, etc.) 
from the text. After cleaning, it returns the refined dataset and counts how many items were modified.
"""

@PROCESSOR_REGISTRY.register()
class HTMLEntityRefiner(TextRefiner):
    def __init__(self, args_dict: dict):
        super().__init__(args_dict)
        self.logger = get_logger()
        self.refiner_name = 'HTMLEntityRefiner'
        self.logger.info(f"Initializing {self.refiner_name}...")

        # 从参数中获取自定义 HTML 实体列表，如果未提供则使用默认列表
        self.html_entities = args_dict.get('html_entities', [
            "nbsp", "lt", "gt", "amp", "quot", "apos", "hellip", "ndash", "mdash", 
            "lsquo", "rsquo", "ldquo", "rdquo"
        ])

        # 构建正则表达式模式，匹配所有定义的 HTML 实体
        # 包括以下几种形式：
        # 1. &实体名;
        # 2. ＆实体名; （全角 &）
        # 3. &实体名； （中文分号）
        # 4. ＆实体名； （全角 & + 中文分号）
        entity_patterns = []
        for entity in self.html_entities:
            # &实体名;
            entity_patterns.append(fr'&{entity};')
            # ＆实体名; （全角 &）
            entity_patterns.append(fr'＆{entity};')
            # &实体名； （中文分号）
            entity_patterns.append(fr'&{entity}；')
            # ＆实体名； （全角 & + 中文分号）
            entity_patterns.append(fr'＆{entity}；')

        # 编译正则表达式
        self.html_entity_regex = re.compile('|'.join(entity_patterns))

    @staticmethod
    def get_desc(self, lang):
        return "去除文本中的HTML实体" if lang == "zh" else "Remove HTML entities from the text."

    def refine_func(self, dataset: TextDataset):
        """
        遍历数据集中的每一项，检测并移除文本中的HTML实体。

        Args:
            dataset (TextDataset): 包含文本数据的TextDataset对象。

        Returns:
            TextDataset: 经过HTML实体移除后的TextDataset对象。
            int: 被修改的数据项数量。
        """
        self.logger.info(f"Start running {self.refiner_name}...")

        # 初始化被修改的数据项计数
        numbers = 0

        # 确定要处理的字段键
        # 假设dataset.keys是一个列表，包含需要处理的字段名
        # 如果dataset.keys不是列表，则将其转换为列表
        keys = dataset.keys if isinstance(dataset.keys, list) else [dataset.keys]

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

                        # 使用正则表达式替换所有匹配的HTML实体为空字符串
                        refined_text = self.html_entity_regex.sub('', refined_text)

                        # 检查文本是否被修改
                        if original_text != refined_text:
                            item[key] = refined_text
                            modified = True
                            self.logger.debug(f"Modified text for key '{key}': Original: {original_text[:30]}... -> Refined: {refined_text[:30]}...")

                # 将处理后的项添加到新的数据集中
                refined_data.append(item)
                if modified:
                    numbers += 1
                    self.logger.debug(f"Item modified, total modified so far: {numbers}")
            else:
                # 如果item不是字典，直接添加到新的数据集中，不做修改
                refined_data.append(item)
                self.logger.warning(f"Item is not a dictionary, skipping: {item}")

        # 更新dataset的数据为经过refine后的数据
        dataset.dataset = refined_data

        self.logger.info(f"Refining completed. Total items modified: {numbers}")
        return dataset, numbers