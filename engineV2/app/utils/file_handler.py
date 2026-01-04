"""
File handling utilities with comprehensive operations.
Applies: Error handling, Path management, File validation
"""

import os
import shutil
import hashlib
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class FileHandler:
    """
    Utility class for file operations.
    
    Design Pattern: Utility/Helper Pattern
    """
    
    @staticmethod
    def ensure_directory(directory: Union[str, Path]) -> bool:
        """
        Ensure directory exists, create if not.
        
        Args:
            directory: Directory path
            
        Returns:
            Success status
        """
        try:
            directory = Path(directory)
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Directory ensured: {directory}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create directory {directory}: {e}")
            return False
    
    @staticmethod
    def delete_file(filepath: Union[str, Path]) -> bool:
        """
        Safely delete a file.
        
        Args:
            filepath: File path
            
        Returns:
            Success status
        """
        try:
            filepath = Path(filepath)
            if filepath.exists() and filepath.is_file():
                filepath.unlink()
                logger.debug(f"File deleted: {filepath}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete file {filepath}: {e}")
            return False
    
    @staticmethod
    def delete_directory(directory: Union[str, Path], recursive: bool = False) -> bool:
        """
        Delete a directory.
        
        Args:
            directory: Directory path
            recursive: Delete recursively
            
        Returns:
            Success status
        """
        try:
            directory = Path(directory)
            if directory.exists() and directory.is_dir():
                if recursive:
                    shutil.rmtree(directory)
                else:
                    directory.rmdir()
                logger.debug(f"Directory deleted: {directory}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete directory {directory}: {e}")
            return False
    
    @staticmethod
    def copy_file(source: Union[str, Path], destination: Union[str, Path]) -> bool:
        """
        Copy a file.
        
        Args:
            source: Source file path
            destination: Destination file path
            
        Returns:
            Success status
        """
        try:
            source = Path(source)
            destination = Path(destination)
            
            if not source.exists():
                raise FileNotFoundError(f"Source file not found: {source}")
            
            # Ensure destination directory exists
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(source, destination)
            logger.debug(f"File copied: {source} -> {destination}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to copy file: {e}")
            return False
    
    @staticmethod
    def move_file(source: Union[str, Path], destination: Union[str, Path]) -> bool:
        """
        Move a file.
        
        Args:
            source: Source file path
            destination: Destination file path
            
        Returns:
            Success status
        """
        try:
            source = Path(source)
            destination = Path(destination)
            
            if not source.exists():
                raise FileNotFoundError(f"Source file not found: {source}")
            
            # Ensure destination directory exists
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(source), str(destination))
            logger.debug(f"File moved: {source} -> {destination}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to move file: {e}")
            return False
    
    @staticmethod
    def get_file_size(filepath: Union[str, Path]) -> int:
        """
        Get file size in bytes.
        
        Args:
            filepath: File path
            
        Returns:
            File size in bytes, -1 if error
        """
        try:
            filepath = Path(filepath)
            if filepath.exists() and filepath.is_file():
                return filepath.stat().st_size
            return -1
            
        except Exception as e:
            logger.error(f"Failed to get file size: {e}")
            return -1
    
    @staticmethod
    def get_file_hash(filepath: Union[str, Path], algorithm: str = 'sha256') -> Optional[str]:
        """
        Calculate file hash.
        
        Args:
            filepath: File path
            algorithm: Hash algorithm (md5, sha1, sha256, etc.)
            
        Returns:
            File hash or None if error
        """
        try:
            filepath = Path(filepath)
            
            if not filepath.exists():
                return None
            
            hash_func = hashlib.new(algorithm)
            
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    hash_func.update(chunk)
            
            return hash_func.hexdigest()
            
        except Exception as e:
            logger.error(f"Failed to calculate file hash: {e}")
            return None
    
    @staticmethod
    def read_json(filepath: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """
        Read JSON file.
        
        Args:
            filepath: JSON file path
            
        Returns:
            Parsed JSON data or None
        """
        try:
            filepath = Path(filepath)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to read JSON file: {e}")
            return None
    
    @staticmethod
    def write_json(
        data: Dict[str, Any],
        filepath: Union[str, Path],
        indent: int = 2
    ) -> bool:
        """
        Write JSON file.
        
        Args:
            data: Data to write
            filepath: Output file path
            indent: JSON indentation
            
        Returns:
            Success status
        """
        try:
            filepath = Path(filepath)
            
            # Ensure directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            
            logger.debug(f"JSON written to: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write JSON file: {e}")
            return False
    
    @staticmethod
    def list_files(
        directory: Union[str, Path],
        pattern: str = '*',
        recursive: bool = False
    ) -> List[Path]:
        """
        List files in directory.
        
        Args:
            directory: Directory path
            pattern: File pattern (e.g., '*.pdf')
            recursive: Search recursively
            
        Returns:
            List of file paths
        """
        try:
            directory = Path(directory)
            
            if not directory.exists() or not directory.is_dir():
                return []
            
            if recursive:
                files = list(directory.rglob(pattern))
            else:
                files = list(directory.glob(pattern))
            
            # Filter only files
            files = [f for f in files if f.is_file()]
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            return []
    
    @staticmethod
    def get_file_info(filepath: Union[str, Path]) -> Dict[str, Any]:
        """
        Get comprehensive file information.
        
        Args:
            filepath: File path
            
        Returns:
            Dictionary with file info
        """
        try:
            filepath = Path(filepath)
            
            if not filepath.exists():
                return {'error': 'File not found'}
            
            stat = filepath.stat()
            
            info = {
                'name': filepath.name,
                'path': str(filepath.absolute()),
                'size': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'extension': filepath.suffix,
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'is_file': filepath.is_file(),
                'is_dir': filepath.is_dir()
            }
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get file info: {e}")
            return {'error': str(e)}


class FileManager:
    """
    Advanced file manager with history tracking.
    
    Design Pattern: Manager Pattern
    DSA: Stack for operation history (LIFO)
    """
    
    def __init__(self, base_directory: Union[str, Path]):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.base_directory = Path(base_directory)
        self._operation_history: List[Dict[str, Any]] = []  # Stack
        self._max_history = 100
        
        # Ensure base directory exists
        FileHandler.ensure_directory(self.base_directory)
    
    def _log_operation(self, operation: str, details: Dict[str, Any]) -> None:
        """
        Log operation to history.
        
        Args:
            operation: Operation name
            details: Operation details
        """
        try:
            record = {
                'timestamp': datetime.now().isoformat(),
                'operation': operation,
                'details': details
            }
            
            self._operation_history.append(record)
            
            # Maintain max history size
            if len(self._operation_history) > self._max_history:
                self._operation_history.pop(0)
            
        except Exception as e:
            self.logger.error(f"Failed to log operation: {e}")
    
    def save_file(
        self,
        content: Union[str, bytes],
        filename: str,
        subdirectory: Optional[str] = None
    ) -> Optional[Path]:
        """
        Save content to file.
        
        Args:
            content: File content
            filename: Filename
            subdirectory: Optional subdirectory
            
        Returns:
            File path or None if error
        """
        try:
            if subdirectory:
                target_dir = self.base_directory / subdirectory
            else:
                target_dir = self.base_directory
            
            FileHandler.ensure_directory(target_dir)
            
            filepath = target_dir / filename
            
            mode = 'wb' if isinstance(content, bytes) else 'w'
            encoding = None if isinstance(content, bytes) else 'utf-8'
            
            with open(filepath, mode, encoding=encoding) as f:
                f.write(content)
            
            self._log_operation('save_file', {
                'filepath': str(filepath),
                'size': len(content)
            })
            
            self.logger.info(f"File saved: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Failed to save file: {e}", exc_info=True)
            return None
    
    def load_file(
        self,
        filename: str,
        subdirectory: Optional[str] = None,
        binary: bool = False
    ) -> Optional[Union[str, bytes]]:
        """
        Load file content.
        
        Args:
            filename: Filename
            subdirectory: Optional subdirectory
            binary: Read as binary
            
        Returns:
            File content or None
        """
        try:
            if subdirectory:
                filepath = self.base_directory / subdirectory / filename
            else:
                filepath = self.base_directory / filename
            
            if not filepath.exists():
                self.logger.warning(f"File not found: {filepath}")
                return None
            
            mode = 'rb' if binary else 'r'
            encoding = None if binary else 'utf-8'
            
            with open(filepath, mode, encoding=encoding) as f:
                content = f.read()
            
            self._log_operation('load_file', {
                'filepath': str(filepath),
                'size': len(content)
            })
            
            return content
            
        except Exception as e:
            self.logger.error(f"Failed to load file: {e}", exc_info=True)
            return None
    
    def cleanup_old_files(self, days: int = 7, pattern: str = '*') -> int:
        """
        Clean up files older than specified days.
        
        Args:
            days: Age threshold in days
            pattern: File pattern to match
            
        Returns:
            Number of files deleted
        """
        try:
            from datetime import timedelta
            
            cutoff_time = datetime.now() - timedelta(days=days)
            deleted_count = 0
            
            files = FileHandler.list_files(self.base_directory, pattern, recursive=True)
            
            for filepath in files:
                try:
                    modified_time = datetime.fromtimestamp(filepath.stat().st_mtime)
                    
                    if modified_time < cutoff_time:
                        if FileHandler.delete_file(filepath):
                            deleted_count += 1
                            
                except Exception as e:
                    self.logger.warning(f"Failed to process {filepath}: {e}")
            
            self._log_operation('cleanup', {
                'days': days,
                'deleted': deleted_count
            })
            
            self.logger.info(f"Cleaned up {deleted_count} old files")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}", exc_info=True)
            return 0
    
    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get operation history.
        
        Args:
            limit: Maximum number of records
            
        Returns:
            List of operation records
        """
        return self._operation_history[-limit:]
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.
        
        Returns:
            Dictionary with storage stats
        """
        try:
            total_size = 0
            file_count = 0
            
            files = FileHandler.list_files(self.base_directory, '*', recursive=True)
            
            for filepath in files:
                try:
                    total_size += filepath.stat().st_size
                    file_count += 1
                except Exception:
                    pass
            
            return {
                'base_directory': str(self.base_directory),
                'total_files': file_count,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'total_size_gb': round(total_size / (1024 * 1024 * 1024), 2)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get storage stats: {e}")
            return {}
