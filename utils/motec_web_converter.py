import os
import sys
import tempfile
from pathlib import Path
import subprocess

def process_log_file(log_path, log_type, dbc_path=None, output_folder='output', 
                     frequency=10, output_filename=None, metadata=None):
    """
    Process log file using existing motec_log_generator functionality
    """
    # Prepare arguments for motec_log_generator
    args = [
        log_path,
        log_type
    ]
    
    # Set output path
    if output_filename:
        base_name = output_filename
        if not base_name.endswith('.ld'):
            base_name += '.ld'
    else:
        base_name = Path(log_path).stem + '.ld'
    
    output_path = os.path.join(output_folder, base_name)
    args.extend(['--output', output_path])
    
    # Add frequency
    args.extend(['--frequency', str(frequency)])
    
    # Add DBC path if provided
    if dbc_path and log_type == 'CAN':
        args.extend(['--dbc', dbc_path])
    
    # Add metadata if provided
    if metadata:
        for key, value in metadata.items():
            if value and value.strip():  # Skip empty values
                args.extend([f'--{key}', str(value)])
    
    try:
        # Call the original script via subprocess
        # First, find the path to motec_log_generator.py
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        generator_path = os.path.join(current_dir, 'motec_log_generator.py')
        
        # Build the command
        cmd = [sys.executable, generator_path] + args
        
        # Run the conversion
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=current_dir  # Run from project root
        )
        
        if result.returncode != 0:
            error_msg = result.stderr.strip()
            if not error_msg:
                error_msg = result.stdout.strip()
            raise Exception(f"Conversion failed: {error_msg}")
        
        # Verify output was created
        if os.path.exists(output_path):
            return output_path
        else:
            raise Exception("Output file was not created")
            
    except subprocess.CalledProcessError as e:
        raise Exception(f"Conversion process error: {e.stderr}")
    except Exception as e:
        # Clean up on error
        if os.path.exists(output_path):
            os.remove(output_path)
        raise e