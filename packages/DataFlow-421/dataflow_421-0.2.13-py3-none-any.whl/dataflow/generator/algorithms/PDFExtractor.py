import os
from typing import Optional, List, Dict
import PyPDF2
import pdfplumber
import json
from dataflow.utils.registry import GENERATOR_REGISTRY

@GENERATOR_REGISTRY.register()
class PDFExtractor:
    def __init__(self, args_dict:Dict):
        pdf_path=args_dict.get("pdf_path")
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")
        self.pdf_path = pdf_path
        self.extract_target=args_dict.get("extract_target","text")
        self.output_dir=args_dict.get("output_dir")
        os.makedirs(self.output_dir, exist_ok=True)

    def get_desc(self):
        return """
PDFExtractor: A Python class for extracting text, tables, and metadata from PDF files. 
Supports both layout-preserving and fast raw text extraction. 
Configured via dictionary input for PDF path and extraction target (text/table/metadata). 
Includes methods for single-target extraction and batch extraction of all content types. 
Requires PyPDF2 and pdfplumber libraries.
"""

    def run(self,preserve_layout:bool=False) -> str:
        if self.extract_target=="text":
            return self.extract_text(preserve_layout)
        elif self.extract_target=="table":
            return self.extract_table()
        elif self.extract_target=="metadata":
            return self.extract_metadata()
        else:
            raise ValueError(f"不支持的提取目标: {self.extract_target}")
        
    def extract_text(self, preserve_layout: bool = False) -> str:
        try:
            text = ""
            if preserve_layout:
                with pdfplumber.open(self.pdf_path) as pdf:
                    for page in pdf.pages:
                        text += page.extract_text() + "\n"
            else:
                with open(self.pdf_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
            
            output_path = os.path.join(self.output_dir, "extracted_text.txt")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text.strip())
                
            return f"Text extracted successfully. Saved to {output_path}"
            
        except Exception as e:
            return f"Text extraction failed: {str(e)}"

    def extract_tables(self) -> str:
        try:
            tables = []
            with pdfplumber.open(self.pdf_path) as pdf:
                for page in pdf.pages:
                    tables.extend(page.extract_tables())
            
            output_path = os.path.join(self.output_dir, "extracted_tables.json")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(tables, f, ensure_ascii=False, indent=2)
                
            return f"Tables extracted successfully. Saved to {output_path}"
            
        except Exception as e:
            return f"Table extraction failed: {str(e)}"

    def extract_metadata(self) -> str:
        try:
            with open(self.pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                metadata = reader.metadata or {}
            
            output_path = os.path.join(self.output_dir, "extracted_metadata.json")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
                
            return f"Metadata extracted successfully. Saved to {output_path}"
            
        except Exception as e:
            return f"Metadata extraction failed: {str(e)}"

    def extract_all(self) -> str:
        try:
            results = {
                "metadata": self.extract_metadata(),
                "text": self.extract_text(preserve_layout=True),
                "tables": self.extract_tables()
            }
            
            output_path = os.path.join(self.output_dir, "all_extracted_data.json")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
                
            return f"All data extracted successfully. Saved to {output_path}"
            
        except Exception as e:
            return f"Complete extraction failed: {str(e)}"