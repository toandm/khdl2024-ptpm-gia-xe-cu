from pathlib import Path
import sys
import re

def parse_gitignore(gitignore_path):
    """
    Đọc file .gitignore và chuyển thành các mẫu regex để so khớp
    """
    if not Path(gitignore_path).exists():
        return []
    
    patterns = []
    with open(gitignore_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # Chuyển đổi mẫu gitignore thành regex
                pattern = line.replace('.', r'\.').replace('*', '.*')
                patterns.append(f"^{pattern}$")
    
    return [re.compile(pattern) for pattern in patterns]

def should_ignore(path, ignore_patterns, ignore_dirs):
    """
    Kiểm tra xem một đường dẫn có nên bị bỏ qua không
    """
    # Bỏ qua các thư mục bắt đầu bằng dấu chấm
    if path.name.startswith('.'):
        return True
        
    if path.name in ignore_dirs:
        return True
    
    for pattern in ignore_patterns:
        if pattern.match(path.name):
            return True
    
    return False

def print_directory_structure(directory_path, prefix="", is_last=True, 
                               ignore_dirs=['__pycache__', 'venv', 'node_modules'],
                               ignore_patterns=[]):
    """
    In ra cấu trúc thư mục dự án, bỏ qua các file và thư mục trong .gitignore và các thư mục bắt đầu bằng .
    """
    directory_path = Path(directory_path)
    
    # Lấy tất cả các file và thư mục trong directory_path
    contents = []
    for p in directory_path.iterdir():
        if not should_ignore(p, ignore_patterns, ignore_dirs):
            contents.append(p)
    
    # Sắp xếp các file và thư mục
    contents.sort(key=lambda p: (not p.is_dir(), p.name))

    # Đánh dấu xem item hiện tại có phải là item cuối cùng
    is_root = (prefix == "")
    
    if is_root:
        print(f"{directory_path.name}/")
    
    # In ra các item
    for i, path in enumerate(contents):
        is_last_item = (i == len(contents) - 1)
        
        # In tiền tố
        if not is_root:
            print(prefix + ("└── " if is_last else "├── "), end="")
        
        # In tên của file hoặc thư mục
        if path.is_dir():
            print(f"{path.name}/")
            
            # Chuẩn bị tiền tố cho lần gọi đệ quy tiếp theo
            extension = "    " if is_last_item else "│   "
            new_prefix = prefix + extension if not is_root else "    "
            
            # Gọi đệ quy để in cấu trúc của thư mục con
            print_directory_structure(path, new_prefix, is_last_item, ignore_dirs, ignore_patterns)
        else:
            print(path.name)

if __name__ == "__main__":
    # Sử dụng thư mục hiện tại hoặc thư mục được chỉ định trong đối số dòng lệnh
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    
    # Đọc các mẫu từ .gitignore
    gitignore_path = Path(target_dir) / ".gitignore"
    ignore_patterns = parse_gitignore(gitignore_path)
    
    # Các thư mục thường bị bỏ qua (không bao gồm các thư mục bắt đầu bằng dấu chấm vì đã xử lý riêng)
    ignore_dirs = ['__pycache__', 'venv', 'node_modules']
    
    print_directory_structure(target_dir, ignore_dirs=ignore_dirs, ignore_patterns=ignore_patterns)