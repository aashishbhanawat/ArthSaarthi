import zipfile
import os
import shutil
import sys

def patch_wheel(wheel_path, output_path, new_tag):
    print(f"Patching {wheel_path} -> {output_path} with tag {new_tag}...")
    temp_dir = "tmp_patch_dir_v3"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

    with zipfile.ZipFile(wheel_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)

    wheel_file_path = None
    for root, dirs, files in os.walk(temp_dir):
        if "WHEEL" in files and root.endswith(".dist-info"):
            wheel_file_path = os.path.join(root, "WHEEL")
            break

    if not wheel_file_path:
        print("Error: Could not find WHEEL file.")
        return False

    with open(wheel_file_path, 'r') as f:
        lines = f.readlines()

    with open(wheel_file_path, 'w') as f:
        for line in lines:
            if line.startswith("Tag:"):
                f.write(f"Tag: {new_tag}\n")
            else:
                f.write(line)

    with zipfile.ZipFile(output_path, 'w', compression=zipfile.ZIP_DEFLATED) as new_zip:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, temp_dir)
                new_zip.write(file_path, arcname)

    shutil.rmtree(temp_dir)
    return True

if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit(1)
    patch_wheel(sys.argv[1], sys.argv[2], sys.argv[3])
