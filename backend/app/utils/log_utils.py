"""
Utility functions for log filtering and pagination
"""
from datetime import datetime


def filter_logs_by_text(logs, search_text):
    """
    Filter logs by text content
    
    Args:
        logs: String or list of log lines
        search_text: Text to search for (case-insensitive)
        
    Returns:
        Filtered logs matching the search text
    """
    if not search_text:
        return logs
    
    search_text = search_text.lower()
    
    if isinstance(logs, str):
        lines = logs.split('\n')
    else:
        lines = logs
    
    filtered_lines = [
        line for line in lines
        if search_text in line.lower()
    ]
    
    return '\n'.join(filtered_lines) if isinstance(logs, str) else filtered_lines


def filter_logs_by_level(logs, level):
    """
    Filter logs by level (ERROR, WARN, INFO, DEBUG)
    
    Args:
        logs: String or list of log lines
        level: Log level to filter by
        
    Returns:
        Filtered logs matching the level
    """
    if not level:
        return logs
    
    level = level.upper()
    level_keywords = {
        'ERROR': ['error', 'err', 'exception', 'fatal', 'fail'],
        'WARN': ['warn', 'warning'],
        'INFO': ['info'],
        'DEBUG': ['debug', 'trace']
    }
    
    keywords = level_keywords.get(level, [level.lower()])
    
    if isinstance(logs, str):
        lines = logs.split('\n')
    else:
        lines = logs
    
    filtered_lines = [
        line for line in lines
        if any(keyword in line.lower() for keyword in keywords)
    ]
    
    return '\n'.join(filtered_lines) if isinstance(logs, str) else filtered_lines


def paginate_logs(logs, page=1, per_page=100):
    """
    Paginate logs for better performance
    
    Args:
        logs: String or list of log lines
        page: Page number (1-indexed)
        per_page: Number of lines per page
        
    Returns:
        Dictionary with paginated logs and metadata
    """
    if isinstance(logs, str):
        lines = logs.split('\n')
    else:
        lines = logs
    
    total_lines = len(lines)
    total_pages = (total_lines + per_page - 1) // per_page
    
    # Ensure page is within valid range
    page = max(1, min(page, total_pages if total_pages > 0 else 1))
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    paginated_lines = lines[start_idx:end_idx]
    
    return {
        'lines': '\n'.join(paginated_lines) if isinstance(logs, str) else paginated_lines,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total_lines': total_lines,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1,
            'start_line': start_idx + 1,
            'end_line': min(end_idx, total_lines)
        }
    }


def highlight_logs(logs, search_text=None, error_keywords=None):
    """
    Add highlighting markers to logs for frontend rendering
    
    Args:
        logs: String or list of log lines
        search_text: Text to highlight
        error_keywords: List of error keywords to highlight
        
    Returns:
        List of dicts with line content and highlighting info
    """
    if isinstance(logs, str):
        lines = logs.split('\n')
    else:
        lines = logs
    
    if error_keywords is None:
        error_keywords = ['error', 'err', 'exception', 'fatal', 'fail', 'failed']
    
    highlighted_lines = []
    
    for line in lines:
        line_lower = line.lower()
        line_info = {
            'content': line,
            'has_error': any(keyword in line_lower for keyword in error_keywords),
            'has_warning': any(keyword in line_lower for keyword in ['warn', 'warning']),
            'has_success': any(keyword in line_lower for keyword in ['success', 'completed', 'passed']),
            'matches_search': False
        }
        
        if search_text and search_text.lower() in line_lower:
            line_info['matches_search'] = True
        
        highlighted_lines.append(line_info)
    
    return highlighted_lines


def parse_execution_summary(logs):
    """
    Parse logs to extract execution summary
    
    Args:
        logs: String of complete logs
        
    Returns:
        Dictionary with summary information
    """
    if not logs:
        return {
            'total_steps': 0,
            'passed_steps': 0,
            'failed_steps': 0,
            'error_count': 0,
            'warning_count': 0
        }
    
    lines = logs.split('\n')
    
    summary = {
        'total_steps': 0,
        'passed_steps': 0,
        'failed_steps': 0,
        'error_count': 0,
        'warning_count': 0,
        'step_names': []
    }
    
    # Count steps (lines starting with ===)
    for line in lines:
        if line.strip().startswith('==='):
            summary['total_steps'] += 1
            # Extract step name
            step_name = line.strip().replace('===', '').strip()
            if step_name:
                summary['step_names'].append(step_name)
        
        line_lower = line.lower()
        
        # Count errors
        if any(keyword in line_lower for keyword in ['error', 'exception', 'fatal']):
            summary['error_count'] += 1
        
        # Count warnings
        if any(keyword in line_lower for keyword in ['warn', 'warning']):
            summary['warning_count'] += 1
        
        # Detect passed steps
        if 'completed' in line_lower or 'passed' in line_lower or 'success' in line_lower:
            summary['passed_steps'] += 1
        
        # Detect failed steps
        if 'failed' in line_lower or 'error' in line_lower:
            summary['failed_steps'] += 1
    
    return summary


def extract_timestamps_from_logs(logs):
    """
    Extract timestamps from logs
    
    Args:
        logs: String of logs
        
    Returns:
        List of tuples (timestamp, line)
    """
    import re
    
    if not logs:
        return []
    
    lines = logs.split('\n')
    
    # Common timestamp patterns
    timestamp_patterns = [
        r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}',  # ISO format
        r'\d{2}/\d{2}/\d{4}\s\d{2}:\d{2}:\d{2}',     # US format
        r'\d{2}-\d{2}-\d{4}\s\d{2}:\d{2}:\d{2}',     # EU format
    ]
    
    timestamped_lines = []
    
    for line in lines:
        timestamp = None
        for pattern in timestamp_patterns:
            match = re.search(pattern, line)
            if match:
                timestamp = match.group(0)
                break
        
        timestamped_lines.append((timestamp, line))
    
    return timestamped_lines


def get_log_statistics(logs):
    """
    Get comprehensive statistics about logs
    
    Args:
        logs: String of logs
        
    Returns:
        Dictionary with statistics
    """
    if not logs:
        return {
            'total_lines': 0,
            'total_characters': 0,
            'error_lines': 0,
            'warning_lines': 0,
            'info_lines': 0,
            'empty_lines': 0
        }
    
    lines = logs.split('\n')
    
    stats = {
        'total_lines': len(lines),
        'total_characters': len(logs),
        'error_lines': 0,
        'warning_lines': 0,
        'info_lines': 0,
        'empty_lines': 0,
        'average_line_length': 0
    }
    
    for line in lines:
        if not line.strip():
            stats['empty_lines'] += 1
            continue
        
        line_lower = line.lower()
        
        if any(keyword in line_lower for keyword in ['error', 'exception', 'fatal', 'fail']):
            stats['error_lines'] += 1
        elif any(keyword in line_lower for keyword in ['warn', 'warning']):
            stats['warning_lines'] += 1
        elif 'info' in line_lower:
            stats['info_lines'] += 1
    
    non_empty_lines = stats['total_lines'] - stats['empty_lines']
    if non_empty_lines > 0:
        stats['average_line_length'] = stats['total_characters'] / non_empty_lines
    
    return stats
