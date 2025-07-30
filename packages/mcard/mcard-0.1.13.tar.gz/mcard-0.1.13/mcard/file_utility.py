"""
File utility functions for handling file operations in MCard.
"""
from pathlib import Path
from typing import Dict, Any, List, Union, Optional

from mcard.model.interpreter import ContentTypeInterpreter
from mcard.model.card_collection import CardCollection

class FileUtility:
    """
    Internal utility class for file operations in MCard.
    This class is not meant to be used directly. Use the standalone functions instead.
    """
    
    def __init__(self, collection: CardCollection):
        """Initialize with a CardCollection for storing MCards."""
        self.collection = collection
    
    @staticmethod
    def _load_files(directory: Union[str, Path], recursive: bool = False) -> List[Path]:
        """
        Load all files from the specified directory.
        
        Args:
            directory: The directory to load files from (can be str or Path)
            recursive: If True, recursively load files from subdirectories
            
        Returns:
            A list of Path objects for all files in the directory
        """
        dir_path = Path(directory) if isinstance(directory, str) else directory
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory '{dir_path}' does not exist.")
            
        if recursive:
            return [f for f in dir_path.rglob("*") if f.is_file()]
        return [f for f in dir_path.glob("*") if f.is_file()]
    
    @staticmethod
    def _analyze_content(content: bytes) -> Dict[str, Any]:
        """Analyze content using ContentTypeInterpreter and return metadata."""
        mime_type, extension = ContentTypeInterpreter.detect_content_type(content)
        is_binary = ContentTypeInterpreter.is_binary_content(content)
        
        return {
            "mime_type": mime_type,
            "extension": extension,
            "is_binary": is_binary,
            "size": len(content)
        }
    
    @staticmethod
    def _read_file(file_path: Union[str, Path]) -> bytes:
        """Read the contents of a file and return as bytes."""
        path = Path(file_path) if isinstance(file_path, str) else file_path
        if not path.exists():
            raise FileNotFoundError(f"File '{path}' does not exist.")
            
        with open(path, 'rb') as f:
            return f.read()
    
    @classmethod
    def _process_file(cls, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Process a single file and return its metadata."""
        content = cls._read_file(file_path)
        analysis = cls._analyze_content(content)
        
        return {
            "content": content,
            "filename": Path(file_path).name,
            "mime_type": analysis["mime_type"],
            "extension": analysis["extension"],
            "is_binary": analysis["is_binary"],
            "size": analysis["size"]
        }
        
    def _process_and_store_file(self, file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """Process a file, create an MCard, and store it in the collection."""
        from mcard import MCard
            
        try:
            # Process the file
            file_info = self._process_file(file_path)
            if not file_info:
                return None
                
            # Create MCard
            mcard = MCard(content=file_info["content"])
            
            # Add to collection
            self.collection.add(mcard)
            
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

def load_file_to_collection(path: Union[str, Path], 
                         collection: CardCollection, 
                         recursive: bool = False) -> List[Dict[str, Any]]:
    """
    Load a file or directory of files into the specified collection.
    
    This function handles the entire process of:
    1. If path is a file: Process that single file
    2. If path is a directory: Process all files in the directory (optionally recursively)
    3. Store the processed files in the collection
    4. Return processing information
    
    Args:
        path: Path to a file or directory to process
        collection: CardCollection to store the MCards in
        recursive: If True and path is a directory, recursively process files in subdirectories (default: False)
        
    Returns:
        List of dictionaries with processing information for each processed file
        
    Example:
        ```python
        from mcard import CardCollection
        from mcard.file_utility import load_file_to_collection
        
        # Create or load a collection
        collection = CardCollection()
        
        # Load a single file
        results = load_file_to_collection('/path/to/file.txt', collection)
        
        # Load files from a directory (non-recursive)
        results = load_file_to_collection('/path/to/files', collection)
        
        # Load files recursively from a directory
        results = load_file_to_collection('/path/to/files', collection, recursive=True)
        ```
    """
    path = Path(path) if isinstance(path, str) else path
    utility = FileUtility(collection)
    results = []
    
    if path.is_file():
        # Process a single file
        result = utility._process_and_store_file(path)
        if result:
            results.append(result)
    elif path.is_dir():
        # Process all files in the directory
        file_paths = utility._load_files(path, recursive=recursive)
        for file_path in file_paths:
            result = utility._process_and_store_file(file_path)
            if result:
                results.append(result)
    else:
        raise FileNotFoundError(f"Path '{path}' does not exist or is not accessible")
            
    return results
