import os
import argparse


def rename_files_in_directory(folder_path=".", verbose=True):
    if verbose:
        print(f"正在处理目录: {os.path.abspath(folder_path)}\n")

    renamed_count = 0
    for filename in os.listdir(folder_path):
        if filename.startswith("IMG_") or filename.startswith("VID_"):
            new_name = filename[4:]  # 去掉前缀
            src = os.path.join(folder_path, filename)
            dst = os.path.join(folder_path, new_name)
            try:
                os.rename(src, dst)
                renamed_count += 1
                if verbose:
                    print(f"已重命名: {filename} -> {new_name}")
            except Exception as e:
                print(f"重命名失败: {filename} -> {new_name}，错误: {e}")
    if verbose:
        print(f"\n共重命名文件数: {renamed_count}")


def main():
    parser = argparse.ArgumentParser(description="批量移除文件名前缀 IMG_ 和 VID_")
    parser.add_argument("-d", "--directory", type=str, default=".", help="目标文件夹路径")
    parser.add_argument("--no-verbose", action="store_true", help="关闭详细输出")
    args = parser.parse_args()

    rename_files_in_directory(folder_path=args.directory, verbose=not args.no_verbose)


if __name__ == "__main__":
    main()
