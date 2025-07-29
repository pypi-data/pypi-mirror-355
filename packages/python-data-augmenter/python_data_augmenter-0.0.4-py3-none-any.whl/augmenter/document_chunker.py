from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
import os
import pandas as pd
import fitz 


class DocumentChunker:
    """
    A utility class for loading and chunking text from various document formats,
    such as Markdown, plain text, PDF, and JSONL, using the LangChain framework.
    """
    def __init__(self, chunk_size=240, chunk_overlap=128, separator="\n"):
        """
        Initializes the DocumentChunker instance with custom chunking parameters.

        Args:
            chunk_size (int): Maximum size of each chunk.
            chunk_overlap (int): Number of overlapping characters between chunks.
            separator (str): Text separator used for splitting.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator
        
    @staticmethod
    def process_md_file(file_path, chunk_size, chunk_overlap, separator):
        """
        Loads and chunks a Markdown (.md) file.

        Args:
            file_path (str): Path to the Markdown file.
            chunk_size (int): Size of each chunk.
            chunk_overlap (int): Overlap between chunks.
            separator (str): Text separator for splitting.

        Returns:
            DataFrame: A DataFrame containing chunked text in a 'document' column.
        """
        loader = UnstructuredMarkdownLoader(file_path) 
        document = loader.load()
        splitter = CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap, separator=separator)
        documents = splitter.split_documents(document)
        docs = [doc.page_content for doc in documents]
        return pd.DataFrame({"document": docs})

    @staticmethod
    def process_text_file(file_path, chunk_size, chunk_overlap, separator):
        """
        Loads and chunks a plain text (.txt) file.

        Args:
            file_path (str): Path to the text file.
            chunk_size (int): Size of each chunk.
            chunk_overlap (int): Overlap between chunks.
            separator (str): Text separator for splitting.

        Returns:
            DataFrame: A DataFrame with text chunks in a 'document' column.
        """
        loader = TextLoader(file_path)
        document = loader.load()
        splitter = CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap, separator=separator)
        documents = splitter.split_documents(document)
        docs = [doc.page_content for doc in documents]
        return pd.DataFrame({'document': docs})
    
    @staticmethod
    def process_PDF_file(file_path, chunk_size, chunk_overlap, separator):
        """
        Extracts and chunks text from a PDF file using PyMuPDF.

        Args:
            file_path (str): Path to the PDF file.
            chunk_size (int): Size of each chunk.
            chunk_overlap (int): Overlap between chunks.
            separator (str): Text separator for splitting.

        Returns:
            DataFrame: A DataFrame containing chunked text.
        """
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        splitter = CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap, separator=separator)
        documents = splitter.split_text(text)
        return pd.DataFrame({"document": documents})

    @staticmethod
    def process_jsonl_file(jsonl_path):
        """
        Loads a JSONL file and stores each line as a separate document.

        Args:
            jsonl_path (str): Path to the JSONL file.

        Returns:
            DataFrame: A DataFrame where each row is a line from the file.
        """
        with open(jsonl_path) as f:
            lines = [line.strip() for line in f]
        return pd.DataFrame({"document": lines})
    
    def process_file(self, file_path):
        """
        Automatically detects file type based on extension and delegates processing.

        Args:
            file_path (str): Path to the input file.

        Returns:
            DataFrame: A DataFrame with processed text chunks.

        Raises:
            ValueError: If the file type is not supported.
        """
        _, file_extension = os.path.splitext(file_path)
        file_extension = file_extension.lower() 
        print(f"Processing file with extension: {file_extension}")
        
        if file_extension == '.txt':
            return self.process_text_file(file_path, chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap, separator=self.separator)
        elif file_extension == '.jsonl':
            print("test")
            return self.process_jsonl_file(file_path)
        elif file_extension == '.md':
            return self.process_md_file(file_path, chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap, separator=self.separator)
        elif file_extension == '.pdf':
            return self.process_PDF_file(file_path, chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap, separator=self.separator)
        else:
            raise ValueError(f"Unsupported file extension: {file_extension}")