import os
import sys
import subprocess
import tempfile
from pathlib import Path

def run_motec_converter(log_path, log_type, dbc_path=None, output_path=None, 
                       frequency=10, metadata=None):
    """
    Запускает оригинальный motec_log_generator.py через subprocess
    """
    # Построение команды
    cmd = [
        sys.executable,
        'motec_log_generator.py',
        log_path,
        log_type,
        '--frequency', str(frequency)
    ]
    
    # Добавляем DBC если нужно
    if dbc_path and log_type == 'CAN':
        cmd.extend(['--dbc', dbc_path])
    
    # Добавляем выходной путь
    if output_path:
        cmd.extend(['--output', output_path])
    
    # Добавляем метаданные
    if metadata:
        for key, value in metadata.items():
            if value and value.strip():
                cmd.extend([f'--{key}', str(value)])
    
    # Запуск
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    
    return result

def process_log_file(log_path, log_type, dbc_path=None, output_folder='output',
                    frequency=10, output_filename=None, metadata=None):
    """
    Обертка для веб-интерфейса
    """
    # Определяем выходной путь
    if output_filename:
        if not output_filename.endswith('.ld'):
            output_filename += '.ld'
        output_path = os.path.join(output_folder, output_filename)
    else:
        output_path = os.path.join(output_folder, 
                                 Path(log_path).stem + '.ld')
    
    # Запускаем конвертацию
    result = run_motec_converter(
        log_path=log_path,
        log_type=log_type,
        dbc_path=dbc_path,
        output_path=output_path,
        frequency=frequency,
        metadata=metadata
    )
    
    # Проверяем результат
    if result.returncode != 0:
        error_msg = result.stderr.strip()
        if not error_msg:
            error_msg = result.stdout.strip()
        raise Exception(f"Conversion failed: {error_msg}")
    
    # Проверяем создание файла
    if not os.path.exists(output_path):
        # Ищем файл по умолчанию (рядом с исходным)
        default_output = Path(log_path).with_suffix('.ld')
        if os.path.exists(default_output):
            return str(default_output)
        else:
            raise Exception(f"Output file not found: {output_path}")
    
    return output_path