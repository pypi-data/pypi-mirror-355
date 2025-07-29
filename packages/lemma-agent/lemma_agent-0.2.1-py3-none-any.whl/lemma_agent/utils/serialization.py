"""
Serialization utilities for AgentDebugger SDK.

Handles serialization and deserialization of execution data, trace results,
and other complex objects for storage and transmission.
"""

import json
import pickle
import gzip
import base64
from typing import Any, Dict, Optional, Union, List
from datetime import datetime
from dataclasses import asdict, is_dataclass
import sys


class AgentDebuggerEncoder(json.JSONEncoder):
    """Custom JSON encoder for AgentDebugger objects."""
    
    def default(self, obj):
        """Convert objects to JSON-serializable format."""
        
        # Handle dataclass objects
        if is_dataclass(obj):
            result = asdict(obj)
            result['__dataclass__'] = obj.__class__.__name__
            return result
        
        # Handle datetime objects
        if isinstance(obj, datetime):
            return {
                '__datetime__': obj.isoformat(),
                '__timezone__': str(obj.tzinfo) if obj.tzinfo else None
            }
        
        # Handle exceptions
        if isinstance(obj, Exception):
            return {
                '__exception__': {
                    'type': obj.__class__.__name__,
                    'message': str(obj),
                    'args': obj.args
                }
            }
        
        # Handle complex types that can't be serialized
        if hasattr(obj, '__dict__'):
            return {
                '__object__': obj.__class__.__name__,
                '__dict__': obj.__dict__
            }
        
        # Handle other types by converting to string
        try:
            return str(obj)
        except Exception:
            return f"<Unserializable {type(obj).__name__}>"


def serialize_execution_data(execution_data: Any, 
                           format: str = "json",
                           compress: bool = False) -> Union[str, bytes]:
    """
    Serialize execution data for storage or transmission.
    
    Args:
        execution_data: Data to serialize (can be any object)
        format: Serialization format ('json', 'pickle', 'msgpack')
        compress: Whether to compress the serialized data
        
    Returns:
        Serialized data as string or bytes
        
    Raises:
        ValueError: If format is not supported
        SerializationError: If serialization fails
    """
    try:
        if format.lower() == "json":
            serialized = json.dumps(
                execution_data, 
                cls=AgentDebuggerEncoder,
                indent=None,
                separators=(',', ':'),
                ensure_ascii=False
            ).encode('utf-8')
            
        elif format.lower() == "pickle":
            serialized = pickle.dumps(execution_data, protocol=pickle.HIGHEST_PROTOCOL)
            
        elif format.lower() == "msgpack":
            try:
                import msgpack
                serialized = msgpack.packb(
                    execution_data, 
                    default=_msgpack_encoder,
                    use_bin_type=True
                )
            except ImportError:
                raise ValueError("msgpack library not installed. Use 'pip install msgpack'")
                
        else:
            raise ValueError(f"Unsupported serialization format: {format}")
        
        # Apply compression if requested
        if compress:
            serialized = gzip.compress(serialized)
        
        # For JSON, return as string if not compressed
        if format.lower() == "json" and not compress:
            return serialized.decode('utf-8')
        else:
            return serialized
            
    except Exception as e:
        raise SerializationError(f"Failed to serialize data: {str(e)}") from e


def deserialize_execution_data(serialized_data: Union[str, bytes], 
                             format: str = "json",
                             compressed: bool = False) -> Any:
    """
    Deserialize execution data back to original objects.
    
    Args:
        serialized_data: Serialized data to deserialize
        format: Serialization format used ('json', 'pickle', 'msgpack')
        compressed: Whether the data is compressed
        
    Returns:
        Deserialized object
        
    Raises:
        ValueError: If format is not supported
        DeserializationError: If deserialization fails
    """
    try:
        # Handle compression
        if compressed:
            if isinstance(serialized_data, str):
                serialized_data = serialized_data.encode('utf-8')
            serialized_data = gzip.decompress(serialized_data)
        
        # Deserialize based on format
        if format.lower() == "json":
            if isinstance(serialized_data, bytes):
                serialized_data = serialized_data.decode('utf-8')
            
            data = json.loads(serialized_data)
            return _decode_json_objects(data)
            
        elif format.lower() == "pickle":
            if isinstance(serialized_data, str):
                serialized_data = serialized_data.encode('utf-8')
            return pickle.loads(serialized_data)
            
        elif format.lower() == "msgpack":
            try:
                import msgpack
                if isinstance(serialized_data, str):
                    serialized_data = serialized_data.encode('utf-8')
                return msgpack.unpackb(serialized_data, raw=False)
            except ImportError:
                raise ValueError("msgpack library not installed. Use 'pip install msgpack'")
                
        else:
            raise ValueError(f"Unsupported deserialization format: {format}")
            
    except Exception as e:
        raise DeserializationError(f"Failed to deserialize data: {str(e)}") from e


def serialize_for_transmission(data: Any, 
                             compress: bool = True,
                             encoding: str = "base64") -> str:
    """
    Serialize data optimized for network transmission.
    
    Args:
        data: Data to serialize
        compress: Whether to compress the data
        encoding: Encoding for the result ('base64', 'hex')
        
    Returns:
        Encoded string suitable for transmission
    """
    try:
        # Serialize using the most compact format
        serialized = serialize_execution_data(data, format="json", compress=compress)
        
        # Ensure we have bytes
        if isinstance(serialized, str):
            serialized = serialized.encode('utf-8')
        
        # Encode for transmission
        if encoding.lower() == "base64":
            return base64.b64encode(serialized).decode('ascii')
        elif encoding.lower() == "hex":
            return serialized.hex()
        else:
            raise ValueError(f"Unsupported encoding: {encoding}")
            
    except Exception as e:
        raise SerializationError(f"Failed to serialize for transmission: {str(e)}") from e


def deserialize_from_transmission(encoded_data: str,
                                compressed: bool = True,
                                encoding: str = "base64") -> Any:
    """
    Deserialize data received from network transmission.
    
    Args:
        encoded_data: Encoded data string
        compressed: Whether the data was compressed
        encoding: Encoding used ('base64', 'hex')
        
    Returns:
        Deserialized object
    """
    try:
        # Decode from transmission format
        if encoding.lower() == "base64":
            serialized = base64.b64decode(encoded_data.encode('ascii'))
        elif encoding.lower() == "hex":
            serialized = bytes.fromhex(encoded_data)
        else:
            raise ValueError(f"Unsupported encoding: {encoding}")
        
        # Deserialize
        return deserialize_execution_data(serialized, format="json", compressed=compressed)
        
    except Exception as e:
        raise DeserializationError(f"Failed to deserialize from transmission: {str(e)}") from e


def get_serialized_size(data: Any, format: str = "json", compress: bool = False) -> int:
    """
    Get the size of data when serialized.
    
    Args:
        data: Data to measure
        format: Serialization format
        compress: Whether to include compression
        
    Returns:
        Size in bytes
    """
    try:
        serialized = serialize_execution_data(data, format=format, compress=compress)
        if isinstance(serialized, str):
            return len(serialized.encode('utf-8'))
        else:
            return len(serialized)
    except Exception:
        return 0


def estimate_serialization_efficiency(data: Any) -> Dict[str, Any]:
    """
    Compare different serialization options and return efficiency metrics.
    
    Args:
        data: Data to analyze
        
    Returns:
        Dictionary with size comparisons and recommendations
    """
    results = {
        "original_size": sys.getsizeof(data),
        "formats": {},
        "recommendation": None
    }
    
    formats_to_test = ["json", "pickle"]
    
    # Test msgpack if available
    try:
        import msgpack
        formats_to_test.append("msgpack")
    except ImportError:
        pass
    
    for format_name in formats_to_test:
        try:
            # Test without compression
            uncompressed = serialize_execution_data(data, format=format_name, compress=False)
            uncompressed_size = get_serialized_size(data, format=format_name, compress=False)
            
            # Test with compression
            compressed_size = get_serialized_size(data, format=format_name, compress=True)
            
            results["formats"][format_name] = {
                "uncompressed_size": uncompressed_size,
                "compressed_size": compressed_size,
                "compression_ratio": uncompressed_size / max(compressed_size, 1),
                "efficiency_score": results["original_size"] / max(uncompressed_size, 1)
            }
            
        except Exception as e:
            results["formats"][format_name] = {
                "error": str(e)
            }
    
    # Generate recommendation
    valid_formats = {k: v for k, v in results["formats"].items() if "error" not in v}
    if valid_formats:
        # Find most efficient format (best compression + reliability)
        best_format = min(valid_formats.keys(), 
                         key=lambda f: valid_formats[f]["compressed_size"])
        
        results["recommendation"] = {
            "format": best_format,
            "compress": valid_formats[best_format]["compression_ratio"] > 1.2,
            "reasoning": f"Best size efficiency with {best_format} format"
        }
    
    return results


def _msgpack_encoder(obj):
    """Custom encoder for msgpack serialization."""
    if is_dataclass(obj):
        result = asdict(obj)
        result['__dataclass__'] = obj.__class__.__name__
        return result
    elif isinstance(obj, datetime):
        return {
            '__datetime__': obj.isoformat(),
            '__timezone__': str(obj.tzinfo) if obj.tzinfo else None
        }
    elif isinstance(obj, Exception):
        return {
            '__exception__': {
                'type': obj.__class__.__name__,
                'message': str(obj),
                'args': obj.args
            }
        }
    else:
        return str(obj)


def _decode_json_objects(data):
    """Recursively decode special JSON objects back to Python objects."""
    if isinstance(data, dict):
        # Handle datetime objects
        if '__datetime__' in data:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(data['__datetime__'])
                return dt
            except Exception:
                return data['__datetime__']  # Fallback to string
        
        # Handle exception objects
        elif '__exception__' in data:
            exc_data = data['__exception__']
            try:
                # Try to reconstruct the exception
                exc_type = getattr(__builtins__, exc_data['type'], Exception)
                return exc_type(exc_data['message'])
            except Exception:
                return exc_data  # Fallback to dict
        
        # Handle dataclass objects
        elif '__dataclass__' in data:
            # For now, return as dict since we'd need to import the actual class
            result = data.copy()
            del result['__dataclass__']
            return result
        
        # Handle generic objects
        elif '__object__' in data:
            return data['__dict__']
        
        # Recursively process dictionaries
        else:
            return {key: _decode_json_objects(value) for key, value in data.items()}
    
    elif isinstance(data, list):
        return [_decode_json_objects(item) for item in data]
    
    else:
        return data


class SerializationError(Exception):
    """Exception raised when serialization fails."""
    pass


class DeserializationError(Exception):
    """Exception raised when deserialization fails."""
    pass


# Convenience functions for common use cases
def to_json(data: Any, pretty: bool = False) -> str:
    """Serialize data to JSON string."""
    return json.dumps(
        data, 
        cls=AgentDebuggerEncoder,
        indent=2 if pretty else None,
        separators=(',', ': ') if pretty else (',', ':')
    )


def from_json(json_str: str) -> Any:
    """Deserialize data from JSON string."""
    data = json.loads(json_str)
    return _decode_json_objects(data)


def to_compressed_json(data: Any) -> bytes:
    """Serialize data to compressed JSON bytes."""
    return serialize_execution_data(data, format="json", compress=True)


def from_compressed_json(compressed_data: bytes) -> Any:
    """Deserialize data from compressed JSON bytes."""
    return deserialize_execution_data(compressed_data, format="json", compressed=True)