import os
import sys
import subprocess
import tempfile
from pathlib import Path
import shutil

def run_motec_converter(log_path, log_type, dbc_path=None, output_path=None, 
                       frequency=10, metadata=None, timeout=60):
    """
    Запускает оригинальный motec_log_generator.py через subprocess
    с обработкой ошибок.
    """
    # Проверка существования входных файлов
    if not os.path.exists(log_path):
        raise FileNotFoundError(f"Input log file not found: {log_path}")
    
    if dbc_path and not os.path.exists(dbc_path):
        raise FileNotFoundError(f"DBC file not found: {dbc_path}")
    
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
    
    try:
        # Запуск с таймаутом
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,  # ← ТАЙМАУТ 60 секунд
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        return result
        
    except subprocess.TimeoutExpired:
        raise Exception(f"Conversion timeout after {timeout} seconds")
    except FileNotFoundError as e:
        raise Exception(f"Required file not found: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to start conversion process: {str(e)}")

def process_log_file(log_path, log_type, dbc_path=None, output_folder='output',
                    frequency=10, output_filename=None, metadata=None):
    """
    Обертка для веб-интерфейса с полной обработкой ошибок
    """
    # Создаем папку для выходных файлов
    os.makedirs(output_folder, exist_ok=True)
    
    # Определяем выходной путь
    if output_filename:
        if not output_filename.endswith('.ld'):
            output_filename += '.ld'
        output_path = os.path.join(output_folder, output_filename)
    else:
        output_path = os.path.join(output_folder, 
                                 Path(log_path).stem + '.ld')
    
    try:
        # Запускаем конвертацию
        result = run_motec_converter(
            log_path=log_path,
            log_type=log_type,
            dbc_path=dbc_path,
            output_path=output_path,
            frequency=frequency,
            metadata=metadata,
            timeout=120  # 2 минуты на конвертацию
        )
        
        # Проверяем результат
        if result.returncode != 0:
            error_msg = result.stderr.strip()
            if not error_msg:
                error_msg = result.stdout.strip()
            
            # Извлекаем последнюю строку ошибки
            if "Traceback" in error_msg:
                lines = error_msg.split('\n')
                for line in reversed(lines):
                    if line.strip() and not line.startswith('  File'):
                        error_msg = line.strip()
                        break
            
            raise Exception(f"Conversion failed: {error_msg}")
        
        # Проверяем создание файла
        if not os.path.exists(output_path):
            # Ищем файл по умолчанию (рядом с исходным)
            default_output = Path(log_path).with_suffix('.ld')
            if os.path.exists(default_output):
                # Переносим его в нужную папку
                shutil.move(str(default_output), output_path)
            else:
                raise Exception(f"Output file was not created: {output_path}")
        
        # Проверяем, что файл не пустой
        if os.path.getsize(output_path) < 1024:  # Меньше 1 КБ
            print(f"Warning: Output file is very small: {output_path}")
            # Можно проверить содержимое
        
        return output_path
        
    except Exception as e:
        # Очистка: удаляем частично созданный файл
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except:
                pass  # Игнорируем ошибки удаления
        raise e  # Пробрасываем исключение дальше в app.py