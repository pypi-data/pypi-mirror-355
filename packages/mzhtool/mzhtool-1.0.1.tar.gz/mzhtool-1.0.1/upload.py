import os
import shutil
import subprocess

# 设置项目路径
project_path = r"C:\Users\19189\Desktop\函数\pip_Mzhtools"
dist_path = os.path.join(project_path, "dist")

# 1. 进入项目目录
os.chdir(project_path)

# 2. 清空 dist 文件夹
if os.path.exists(dist_path):
    shutil.rmtree(dist_path)
os.makedirs(dist_path)

# 3. 打包项目
subprocess.run(["python", "-m", "build"], check=True)

# 检查 dist 是否有内容
dist_files = [
    os.path.join(dist_path, f) for f in os.listdir(dist_path)
    if f.endswith(".tar.gz") or f.endswith(".whl")
]
if not dist_files:
    raise RuntimeError("打包失败，dist 目录中没有可上传的包文件")

# 4. 上传到 PyPI
twine_command = ["twine", "upload"] + dist_files + [
    "--username", "__token__",
    "--password", "pypi-AgEIcHlwaS5vcmcCJGVlMzAzZjUwLTdjZTUtNDk5NC04NjNjLWQwMWM3MzVlMzYyNQACD1sxLFsibXpodG9vbCJdXQACLFsyLFsiMDBiMWU3NWEtMDM4Ny00MWU4LWE1ZDktODI1MDEyOGYxNGU5Il1dAAAGIE20jVLige8LroiUvnHOm8UNAiQm-NDZfxCpirayjw0Q"
]

subprocess.run(twine_command, check=True)
