import os
import re
import glob
import shutil
import math

def log_and_exit(error_details,error_state = 1):
    """
    打印错误信息、记录到日志文件，并退出程序。

    参数:
    error_details: 二维列表
        - 第一行: 错误描述的字符串。
        - 第二行及以后: 参数名和值的列表，形式为 [参数名, 参数值]。
    """
    import os
    import sys
    from datetime import datetime

    # 当前时间
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 获取当前工作目录
    current_directory = os.getcwd()

    # 错误日志文件路径
    log_file_path = os.path.join(current_directory, "error.log")

    # 打印第一行错误描述到控制台
    print(f"终止: {error_details[0]}" if error_state == 0 else f"错误: {error_details[0]}")

    # 准备日志内容
    log_content = [f"[{current_time}] {error_details[0]}"]

    if len(error_details) > 1:  # 检查是否有参数
        for param in error_details[1:]:
            if len(param) == 2:  # 确保是 [参数名, 参数值] 的形式
                param_name, param_value = param
                if isinstance(param_value, (list, tuple)):  # 如果值是列表或元组
                    log_content.append(f"{param_name}:")
                    for item in param_value:  # 每项换行
                        log_content.append(f"  {item}")
                else:
                    log_content.append(f"{param_name}: {param_value}")
            else:
                log_content.append(f'传入参数格式错误，长度为{len(param)}，预期为2，请检查函数调用')
    else:
        log_content.append("没有额外的参数信息。")
    
    log_content.append(f'error_state: {error_state}')

    # 写入日志文件（追加模式）
    with open(log_file_path, "a", encoding="utf-8") as log_file:
        log_file.write("\n".join(log_content) + "\n\n")

    # 退出程序
    sys.exit(error_state)


def get_ffmpeg_path():
    """
    检查 ffmpeg 是否在系统 PATH 中。
    如果存在，返回 'ffmpeg'，否则返回当前工作目录中的 ffmpeg.exe 路径。
    """
    # 检查 ffmpeg 是否在系统 PATH 中
    if shutil.which("ffmpeg"):
        print("ffmpeg 已在系统 PATH 中。")
        return "ffmpeg"  # 系统 PATH 中的 ffmpeg

    # 如果 ffmpeg 不在 PATH 中，检查工作目录中的 ffmpeg.exe
    current_directory = os.getcwd()
    local_ffmpeg = os.path.join(current_directory, "ffmpeg.exe")
    if os.path.exists(local_ffmpeg):
        print("ffmpeg 不在系统 PATH 中，但在当前工作目录中找到了 ffmpeg.exe。")
        return local_ffmpeg  # 工作目录中的 ffmpeg.exe

    # 如果两处都没有找到，返回 None 或抛出异常
    print("未找到 ffmpeg，请确保它在系统 PATH 中，或在当前目录中提供 ffmpeg.exe。")
    return None

# 获取 ffmpeg 路径
ffmpeg_path = get_ffmpeg_path()

if ffmpeg_path is None:
    log_and_exit(["未找到 ffmpeg，程序无法运行。"])

# 获取当前工作目录
current_directory = os.getcwd()

# 查找所有 .copy 文件
copy_files = glob.glob(os.path.join(current_directory, '*.copy'))

# 检查文件数量并处理
if len(copy_files) == 1:
    unique_copy_file = copy_files[0]
    print(f"唯一的 copy 文件是: {unique_copy_file}")
elif len(copy_files) == 0:
    log_and_exit([
        "当前目录中没有 copy 文件。",
        ('ffmpeg_path', ffmpeg_path)
        ])
else:
    log_and_exit([
        "当前目录中有多个 copy 文件。",
        ('ffmpeg_path', ffmpeg_path),
        ('copy_files',copy_files)
        ])

# 定义输出日志文件的完整路径
log_file_path = os.path.join(current_directory, 'frame_info.log')

# 输出日志文件
os.system(f'ffmpeg -i "{unique_copy_file}" -vf showinfo -vsync 0 -f null - 2> "{log_file_path}"') 

# 读取日志文件
try:
    with open(f"{log_file_path}", "r", encoding="utf-8") as log:
        lines = log.readlines()
except FileNotFoundError:
    log_and_exit([
        "无法读取日志文件，文件不存在。已知已经执行过输出日志文件命令。建议您更换目录后再次尝试",
        ("log_file_path", log_file_path),
        ("current_directory", current_directory)
    ])
except OSError as e:
    log_and_exit([
        "读取日志文件时发生错误。已知已经执行过输出日志文件命令。建议您更换目录后再次尝试",
        ("log_file_path", log_file_path),
        ("frame_info.log 是否存在", os.path.isfile(log_file_path)),
        ("current_directory", current_directory),
        ("错误信息", str(e))
    ])


# 提取帧时间和帧大小
frame_info = []
i = 0
for line in lines:
    match = re.search(r"pts:\s*(\d+).*?pts_time:(\d+(\.\d+)?).*?s:(\d+)x(\d+)", line)
    if match:
        pts = int(match.group(1))
        pts_time = float(match.group(2))
        frame_x = int(match.group(4))
        frame_y = int(match.group(5))
        frame_info.append((i, pts, pts_time, frame_x, frame_y))
        i += 1

# 检查帧序列是否为空
if not frame_info:
    log_and_exit([
        'frame_info为空，无法继续处理。请排查视频文件是否存在问题',
        ('ffmpeg_path',ffmpeg_path),
        ('unique_copy_file',unique_copy_file),
        ("current_directory", current_directory),
    ])

# 检测帧序列是否过长
if i > 501 :
    print(f'当前视频共有{i}帧，一般不会输出这么多的帧提取，请检查您所选择的视频流是否有误，确定该操作是否为您希望的操作。')
    continue_or_not = 'P'
    while (continue_or_not not in ('Y','y','N','n')) :
        continue_or_not = input('请输入(N/Y)以选择停止操作(N)或者继续操作(Y)，后者可能会消耗较长时间并占用较大硬盘空间：')
    if continue_or_not in ('N','n'):
        log_and_exit([
            '输出长度过长，用户选择终止进程',
            ('ffmpeg_path',ffmpeg_path),
            ('unique_copy_file',unique_copy_file),
            ("current_directory", current_directory),
            ("frame_info",frame_info[:10] + ["..."] + frame_info[-10:])
        ], 0)


# 计算位数并生成动态格式化字符串
digit_count = math.ceil(math.log10(i)) if i > 1 else 1
output_file = os.path.join(current_directory, f'output%0{digit_count}d.png')

# 提取帧
i = 0
while i < len(frame_info):
    pts, pts_time, frame_x, frame_y = frame_info[i][1], frame_info[i][2], frame_info[i][3], frame_info[i][4]
    x = 1  # 用于记录包括此帧在内往后有多少张的帧大小相同
    while (i + x < len(frame_info) and frame_x == frame_info[i + x][3] and frame_y == frame_info[i + x][4]):
        x += 1
    # os.system(f'{ffmpeg_path} -i "{unique_copy_file}" -vf "select=\'between(pts,{i},{i+x-1})\', scale={frame_x}:{frame_y},setdar=1" -vsync 0 -start_number {i} "{output_file}"') # ffmpeg中确实使用between是闭区间
    
    # 部分视频流似乎会出现pts不连续的情况，这里尝试使用帧时间来处理
    os.system(f'{ffmpeg_path} -i "{unique_copy_file}" -ss {pts_time} -to {frame_info[i + x -1][2] + 0.001} -vf "scale={frame_x}:{frame_y},setdar=1" -vsync 0 -start_number {i} "{output_file}"')

    # print("i and x are: ", i, x)
    i += x  # 跳过已处理的帧


