import importlib.resources
import shutil
import os

def resume():
    dest_file = "Manoj_Kanakam_Resume.pdf"
    with importlib.resources.path("manojkanakam.assets", "Manoj_Kanakam_Resume.pdf") as pdf_path:
        shutil.copy(pdf_path, dest_file)
        print(f"✅ Resume downloaded to {os.path.abspath(dest_file)}")
