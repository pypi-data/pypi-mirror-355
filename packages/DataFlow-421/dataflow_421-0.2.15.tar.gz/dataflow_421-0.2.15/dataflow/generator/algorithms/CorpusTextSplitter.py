import os
import json
from typing import Dict, List, Optional
from chonkie import (
    TokenChunker,
    SentenceChunker,
    SemanticChunker,
    RecursiveChunker
)
from tokenizers import Tokenizer
from transformers import AutoTokenizer
from dataflow.utils.registry import GENERATOR_REGISTRY
from dataflow.data import MyScaleStorage, DatabaseConfig
import uuid

@GENERATOR_REGISTRY.register()
class CorpusTextSplitter:
    def __init__(self, args_dict: Dict):
        # 必需参数检查
        input_path = args_dict.get("input_path")
        if not input_path or not os.path.exists(input_path):
            raise ValueError(f"无效的输入文件路径: {input_path}")
        self.input_path = input_path
        use_db = args_dict.get("use_db", False) or os.environ.get("USE_DB", "").lower() == "true"
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
            self.output_file = None
            self.stage = args_dict.get("stage",0)
            self.pipeline_id = args_dict.get("pipeline_id","")
        else:
            self.output_file= args_dict.get("output_file")

        # 设置成员变量
        # self.input_path = input_path
        # self.output_dir = args_dict.get("output_dir", "output")
        self.chunk_size = args_dict.get("chunk_size", 512)
        self.chunk_overlap = args_dict.get("chunk_overlap", 50)
        self.split_method = args_dict.get("split_method", "token")
        self.min_tokens_per_chunk = args_dict.get("min_tokens_per_chunk", 128)

        tokenizer_name = args_dict.get("tokenizer_name", "bert-base-uncased")
        
        # 初始化tokenizer和chunker
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
        self.chunker = self._initialize_chunker()
        
        # 创建输出目录
        # os.makedirs(self.output_dir, exist_ok=True)

    def get_desc(self):
        return """
"ChonkieTextSplitter is a lightweight text segmentation tool that supports multiple chunking methods (token/sentence/semantic/recursive) with configurable size and overlap, optimized for RAG applications."
"""

    def _initialize_chunker(self):
        """Initialize the appropriate chunker based on method"""
        if self.split_method == "token":
            return TokenChunker(
                tokenizer=self.tokenizer,
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
        elif self.split_method == "sentence":
            return SentenceChunker(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
        elif self.split_method == "semantic":
            return SemanticChunker(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
        elif self.split_method == "recursive":
            return RecursiveChunker(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
        else:
            raise ValueError(f"Unsupported split method: {self.split_method}")

    def _load_text(self) -> str:
        """Load text from input file"""
        if not os.path.exists(self.input_path):
            raise FileNotFoundError(f"Input file not found: {self.input_path}")
        
        if self.input_path.endswith('.txt') or self.input_path.endswith('.md') or self.input_path.endswith('.xml'):
            with open(self.input_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        elif self.input_path.endswith(('.json', '.jsonl')):
            with open(self.input_path, 'r', encoding='utf-8') as f:
                data = json.load(f) if self.input_path.endswith('.json') else [json.loads(line) for line in f]
            
            # Extract text from common fields
            text_fields = ['text', 'content', 'body']
            for field in text_fields:
                if isinstance(data, list) and len(data) > 0 and field in data[0]:
                    return "\n".join([item[field] for item in data])
                elif isinstance(data, dict) and field in data:
                    return data[field]
            
            raise ValueError("No text field found in JSON input")
        else:
            raise ValueError("Unsupported file format")

    def run(self) -> str:
        """Perform text splitting and save results"""
        # try:
        text = self._load_text()

        # 计算总token数和最大限制
        tokens = self.tokenizer.encode(text)
        total_tokens = len(tokens)
        max_tokens = self.tokenizer.model_max_length  # 假设这是tokenizer的最大token限制
        print("max_tokens: ", self.tokenizer.model_max_length)

        if total_tokens <= max_tokens:
            chunks = self.chunker(text)
        else:
            # 计算需要分割的份数x（向上取整）
            x = (total_tokens + max_tokens - 1) // max_tokens
            
            # 按词数等分文本（近似分割）
            words = text.split()  # 按空格分词
            words_per_chunk = (len(words) + x - 1) // x  # 每份的词数
            
            chunks = []
            for i in range(0, len(words), words_per_chunk):
                chunk_text = ' '.join(words[i:i+words_per_chunk])
                
                # 验证分割后的token数（防止因分词不精确导致超限）
                chunk_tokens = self.tokenizer.encode(chunk_text)
                if len(chunk_tokens) > max_tokens:
                    # 若仍超限，则按token精确分割
                    chunk_text = self.tokenizer.decode(chunk_tokens[:max_tokens])
                
                # 处理子块并合并结果
                chunks.extend(self.chunker(chunk_text))

            # # 可选：合并过小的末尾块（根据实际需求调整）
            # if len(chunks) >= 2 and len(self.tokenizer.encode(chunks[-1])) < max_tokens // 4:
            #     last_chunk = chunks.pop()
            #     chunks[-1] += " " + last_chunk
            #         # print("chunk num: ", len(chunks)) 43

        if hasattr(self, 'storage'):
            # 准备存储数据（转换为字典列表）
            print("save to db...")
            output_rows = []
            for i, chunk in enumerate(chunks):
                if chunk.token_count < self.min_tokens_per_chunk:
                    continue
                output_rows.append({
                    "id": str(uuid.uuid4()),
                    "data": chunk.text,
                    # "method": self.split_method,
                })
            
            # 调用 storage.write_data 写入数据库
            self.storage.write_data(
                output_rows,
                # format="SFT_Single",      # 假设这是存储要求的格式
                Synthetic="non_syn",       # 可能是数据类型标记
                stage=self.stage + 1      # 当前阶段 +1（假设 self.stage 已定义）
            )
        else:
            # Prepare output file path
            output_file = self.output_file
            
            # Save chunks with metadata
            with open(output_file, 'w', encoding='utf-8') as f:
                for i, chunk in enumerate(chunks):
                    if(chunk.token_count < self.min_tokens_per_chunk):
                        continue
                    result = {
                        "chunk_id": i+1,
                        "raw_content": chunk.text,
                        "method": self.split_method,
                    }
                    f.write(json.dumps(result, ensure_ascii=False) + "\n")
            # print(f"Successfully split text into {len(chunks)} chunks. Saved to {output_file}")
            return f"Successfully split text into {len(chunks)} chunks. Saved to {output_file}"
        
        # except Exception as e:
        #     print("Error occurred during text splitting: ", str(e))
        #     return f"Text splitting failed: {str(e)}"

