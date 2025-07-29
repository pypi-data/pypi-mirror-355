import os
import shutil
import datetime
import hashlib
import shutil

#------------------------------------------
def copy_file_with_timestamp(original_file_path):
    """
    Copies a file adding a timestamp based on the modification date.

    Args:
        original_file_path (str): The full path to the original file.
    """

    try:
        # Get the modification timestamp of the original file
        modification_timestamp = os.path.getmtime(original_file_path)
        modification_date = datetime.datetime.fromtimestamp(modification_timestamp)

        # Format the timestamp for the new file name
        formatted_timestamp = modification_date.strftime("%Y%m%d_%H%M%S")

        # Create the new file name with the timestamp
        original_file_name = os.path.basename(original_file_path)
        new_file_name = f"{os.path.splitext(original_file_name)[0]}_{formatted_timestamp}{os.path.splitext(original_file_name)[1]}"

        # Get the directory of the original file to use as the destination
        destination_folder = os.path.dirname(original_file_path)
        new_file_path = os.path.join(destination_folder, new_file_name)

        # Copy the file
        shutil.copy2(original_file_path, new_file_path)

    except FileNotFoundError:
        print(f"Error: The original file was not found at: {original_file_path}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

#------------------------------------------
def calculate_md5(filepath):
    """
    Calculates the MD5 checksum of a file.

    Args:
        filepath (str): The path of the file.

    Returns:
        str: The MD5 checksum in hexadecimal format.
    """
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

#------------------------------------------
def verify_md5(yaml_filepath):
  """
  Verifies if the MD5 checksum of a YAML file matches the content of its corresponding .md5 file.

  Args:
      yaml_filepath (str): The path of the YAML file.

  Returns:
      bool: True if the checksum matches, False otherwise.
  """
  md5_filepath = yaml_filepath + ".md5"

  if not os.path.exists(md5_filepath):
      return False

  try:
      with open(md5_filepath, "r") as f:
          expected_md5 = f.read().strip()
  except FileNotFoundError:
      return False

  actual_md5 = calculate_md5(yaml_filepath)

  if actual_md5 == expected_md5:
      return True
  else:
      return False

#------------------------------------------
def get_uppercase_extension(filename):
  """
  Retrieves the file extension and returns it in uppercase.

  Args:
    filename: The name of the file.

  Returns:
    The file extension in uppercase, or an empty string if there's no extension.
  """
  _, extension = os.path.splitext(filename)
  return extension.upper().lstrip('.')

def log_filename(base_name="content_services_api"):
    rigth_now = datetime.datetime.now()
    timestamp = rigth_now.strftime("%Y-%m-%d")  # Format: YYYYmmdd_HHMMSS
    log_file_name = f"{base_name}_{timestamp}.txt"  
    return log_file_name   
  