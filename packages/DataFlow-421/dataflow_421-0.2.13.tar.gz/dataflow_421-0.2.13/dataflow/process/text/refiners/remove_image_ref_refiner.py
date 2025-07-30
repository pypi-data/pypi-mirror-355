from dataflow.core import TextRefiner
from dataflow.utils.registry import PROCESSOR_REGISTRY
from tqdm import tqdm
from dataflow.utils.utils import get_logger
import re

@PROCESSOR_REGISTRY.register()
class RemoveImageRefsRefiner(TextRefiner):
    def __init__(self, args_dict: dict):
        super().__init__(args_dict)
        self.logger = get_logger()
        self.refiner_name = 'RemoveImageRefsRefiner'
        # 优化后的正则表达式模式（支持多种图片格式和大小写）[7,8](@ref)
        self.image_pattern = re.compile(
            r'!\[\]\(images\/[0-9a-fA-F]\.jpg\)|'
            r'[a-fA-F0-9]+\.[a-zA-Z]{3,4}\)|'
            r'!\[\]\(images\/[a-f0-9]|'
            r'图\s+\d+-\d+：[\u4e00-\u9fa5a-zA-Z0-9]+|'
            r'(?:[0-9a-zA-Z]+){7,}|'                # 正则5
            r'(?:[一二三四五六七八九十零壹贰叁肆伍陆柒捌玖拾佰仟万亿]+){5,}|'  # 正则6（汉字数字）
            r"u200e|"
            r"&#247;|\? :|"
            r"[�□]|\{\/U\}|"
            r"U\+26[0-F][0-D]|U\+273[3-4]|U\+1F[3-6][0-4][0-F]|U\+1F6[8-F][0-F]"
        )
        self.logger.info(f"Initializing {self.refiner_name}...")

    @staticmethod
    def get_desc(self, lang):
        return "去除文本中的图片引用" if lang == "zh" else "Remove image references in text."

    def refine_func(self, dataset):
        self.logger.info(f"Start running {self.refiner_name}...")
        refined_data = []
        numbers = 0
        keys = dataset.keys if isinstance(dataset.keys, list) else [dataset.keys]

        for item in tqdm(dataset, desc=f"Implementing {self.refiner_name}"):
            if isinstance(item, dict):
                modified = False
                for key in keys:
                    if key in item and isinstance(item[key], str):
                        original_text = item[key]
                        # 移除所有图片引用格式[1,2](@ref)
                        cleaned_text = self.image_pattern.sub('', original_text)
                        
                        if original_text != cleaned_text:
                            item[key] = cleaned_text
                            modified = True
                            # 调试日志：显示修改前后的对比
                            self.logger.debug(f"Modified text for key '{key}':")
                            self.logger.debug(f"Original: {original_text[:100]}...")
                            self.logger.debug(f"Refined : {cleaned_text[:100]}...")

                refined_data.append(item)
                if modified:
                    numbers += 1
                    self.logger.debug(f"Item modified, total modified so far: {numbers}")

        dataset.dataset = refined_data
        self.logger.info(f"Refining completed. Total items modified: {numbers}")
        return dataset, numbers