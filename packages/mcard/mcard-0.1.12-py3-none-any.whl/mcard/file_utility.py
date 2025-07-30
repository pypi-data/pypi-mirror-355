"""
File utility functions for handling file operations in MCard.
"""
from pathlib import Path
from typing import Dict, Any, List, Union, Optional

from mcard.model.interpreter import ContentTypeInterpreter
from mcard.model.card_collection import CardCollection

class FileUtility:
    """
    A utility class for file operations in MCard.
    """
    
    def __init__(self, collection=None):
        """
        Initialize the FileUtility with an optional CardCollection.
        
        Args:
            collection: Optional CardCollection instance for storing MCards.
        """
        self.collection = collection
    
    @staticmethod
    def load_files(directory: Union[str, Path]) -> List[Path]:
        """
        Load all files from the specified directory.
        
        Args:
            directory: The directory to load files from (can be str or Path)
            
        Returns:
            A list of Path objects for all files in the directory
        """
        dir_path = Path(directory) if isinstance(directory, str) else directory
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory '{dir_path}' does not exist.")
            
        return [file_path for file_path in dir_path.glob("*") if file_path.is_file()]
    
    @staticmethod
    def analyze_content(content: bytes) -> Dict[str, Any]:
        """
        Analyze content using ContentTypeInterpreter.
        
        Args:
            content: The content to analyze as bytes
            
        Returns:
            A dictionary with content information including:
            - mime_type: The detected MIME type
            - extension: The appropriate file extension
            - is_binary: Whether the content is binary or text
            - size: Size of the content in bytes
        """
        mime_type, extension = ContentTypeInterpreter.detect_content_type(content)
        is_binary = ContentTypeInterpreter.is_binary_content(content)
        
        return {
            "mime_type": mime_type,
            "extension": extension,
            "is_binary": is_binary,
            "size": len(content)
        }
    
    @staticmethod
    def read_file(file_path: Union[str, Path]) -> bytes:
        """
        Read the contents of a file.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            The file content as bytes
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            IOError: If there's an error reading the file
        """
        path = Path(file_path) if isinstance(file_path, str) else file_path
        if not path.exists():
            raise FileNotFoundError(f"File '{path}' does not exist.")
            
        with open(path, 'rb') as f:
            return f.read()
    
    @classmethod
    def process_file(cls, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Process a single file and return its metadata.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            A dictionary with file metadata:
            - content: The file content as bytes
            - filename: The original filename
            - mime_type: Detected MIME type
            - extension: Suggested file extension
            - is_binary: Whether the content is binary
            - size: File size in bytes
            
        Raises:
            Exception: If there's an error processing the file
        """
        content = cls.read_file(file_path)
        analysis = cls.analyze_content(content)
        
        return {
            "content": content,
            "filename": Path(file_path).name,
            "mime_type": analysis["mime_type"],
            "extension": analysis["extension"],
            "is_binary": analysis["is_binary"],
            "size": analysis["size"]
        }
        
    def process_and_store_file(self, file_path: Union[str, Path], collection: Optional[CardCollection] = None) -> Optional[Dict[str, Any]]:
        """
        Process a file, create an MCard, and store it in the specified collection.
        
        Args:
            file_path: Path to the file to process
            collection: Optional CardCollection to store the MCard in.
                      If not provided, uses the collection from initialization.
                      If neither is available, raises ValueError.
                      
        Returns:
            A dictionary with information about the processed file:
            - hash: The MCard hash
            - content_type: The detected content type
            - is_binary: Whether the content is binary
            - filename: The original filename
            - size: File size in bytes
            None if there was an error processing the file
            
        Raises:
            ValueError: If no CardCollection is provided and none was set during initialization
        """
        from mcard import MCard
        
        # Use provided collection or fall back to instance collection
        target_collection = collection or self.collection
        if target_collection is None:
            raise ValueError("No CardCollection provided and none set during initialization")
            
        try:
            # Process the file
            file_info = self.process_file(file_path)
            if not file_info:
                return None
                
            # Create MCard
            mcard = MCard(
                content=file_info["content"]
            )
            
            # Add to collection
            target_collection.add(mcard)
            
            # Return processing info
            return {
                "hash": mcard.get_hash(),
                "content_type": file_info["mime_type"],
                "is_binary": file_info["is_binary"],
                "filename": file_info["filename"],
                "size": file_info["size"]
            }
            
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
            return None
            
    @staticmethod
    def load_directory_to_collection(directory: Union[str, Path], collection: CardCollection) -> List[Dict[str, Any]]:
        """
        Load all files from a directory into the specified collection.
        
        This is a convenience static method that handles the entire process of:
        1. Finding all files in the directory
        2. Processing each file
        3. Storing them in the collection
        4. Returning processing information
        
        Args:
            directory: Directory containing files to process
            collection: CardCollection to store the MCards in
            
        Returns:
            List of dictionaries with processing information for each file
            
        Example:
            ```python
            from mcard import CardCollection
            from mcard.file_utility import FileUtility
            
            # Create or load a collection
            collection = CardCollection()
            
            # Load all files from a directory
            results = FileUtility.load_directory_to_collection("path/to/files", collection)
            print(f"Processed {len(results)} files")
            ```
        """
        file_util = FileUtility(collection=collection)
        files = file_util.load_files(directory)
        return file_util.process_and_store_files(files)
            
    def process_and_store_files(self, file_paths: List[Union[str, Path]], collection: Optional[CardCollection] = None) -> List[Dict[str, Any]]:
        """
        Process multiple files and store them as MCards.
        
        Args:
            file_paths: List of file paths to process
            collection: Optional CardCollection to store the MCards in.
                      If not provided, uses the collection from initialization.
                      
        Returns:
            A list of dictionaries with processing information for each file
        """
        results = []
        for file_path in file_paths:
            result = self.process_and_store_file(file_path, collection)
            if result:
                results.append(result)
        return results
