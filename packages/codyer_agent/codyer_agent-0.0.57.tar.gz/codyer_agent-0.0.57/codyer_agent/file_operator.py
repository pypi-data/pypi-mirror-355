from typing import List, Iterator, Optional
import os

FILE_OPERATOR_PROMPT = """
# 文件操作

## 整体协议

%%FILE_OPERATION%%
[操作类型] [文件路径]
[参数键=值]（每行一个）
%%CONTENT%%
[操作内容]
%%END%%

## 限制

- 文件路径只能访问当前目录及其子目录，不能访问其他目录
- 文件路径不能包含 .. 或 /.. 或 \\..\\ 等上级目录
- 文件路径不能以 / 或 \ 开头
- 文件路径不能包含 /etc, /usr, /var, /sys, /proc, /root, /home 等敏感系统路径

## 协议说明

### 读取文件

%%FILE_OPERATION%%
read 文件路径
start_line=[开始行号]
end_line=[结束行号]
%%END%%

### 写入文件

%%FILE_OPERATION%%
write 文件路径
%%CONTENT%%
[内容]
%%END%%

### 追加文件

%%FILE_OPERATION%%
append 文件路径
%%CONTENT%%
[内容]
%%END%%

### 更新文件

%%FILE_OPERATION%%
update 文件路径
%%CONTENT%%
@@ -10,7 +10,7 @@
-    print("Deprecated")
+    logger.warning("Deprecated")
@@ -45,0 +46,2 @@
+    # 新增调试
+    logger.debug("done")
%%END%%

规则
-	每个 @@ … @@ hunk 不得交叉或重叠。
-	删除行以 -，新增行以 +，未改动行以空格前缀保存上下文。
-	推荐保留 2–3 行上下文，减少行号失配风险。

### 删除文件内容

%%FILE_OPERATION%%
delete_range 文件路径
start_line=[开始行号]
end_line=[结束行号]
%%END%%

#### 删除全部

%%FILE_OPERATION%%
delete_all 文件路径
%%END%%


# 文件展示格式

%%FILE_CONTENT%%
FILE_PATH
lines=[总行数]
start_line=[内容开始行号]
end_line=[内容结束行号]
%%CONTENT%%
1: xxx
2: 日志
...
31: 以上就是日志内容
%%END%%

## 示例

### 展示文件内容

%%FILE_CONTENT%%
service.log
%%CONTENT%%
1: Hello, World!
2: Hello, Codyer!
%%END%%

"""


def _is_safe_path(file_path: str) -> bool:
    """
    验证文件路径是否安全
    只允许访问当前目录及其子目录，防止路径遍历攻击
    """
    # 不允许绝对路径
    if os.path.isabs(file_path):
        return False
    
    # 规范化路径，解析 . 和 .. 
    normalized_path = os.path.normpath(file_path)
    
    # 不允许包含 .. 的路径（防止访问上级目录）
    if normalized_path.startswith('..') or '/..' in normalized_path or '\\..\\' in normalized_path:
        return False
    
    # 不允许以 / 或 \ 开头（绝对路径）
    if normalized_path.startswith(('/', '\\')):
        return False
    
    # 检查是否尝试访问敏感系统路径
    dangerous_paths = ['/etc', '/usr', '/var', '/sys', '/proc', '/root', '/home']
    for dangerous in dangerous_paths:
        if normalized_path.startswith(dangerous):
            return False
    
    return True


def parse_llm_file_operate(input: str) -> Optional[str]:
    """
    解析大模型输出的文件操作
    支持多个文件操作，依次处理并返回结果
    """
    import re
    
    try:
        # 查找所有的 FILE_OPERATION 块
        operations = _find_all_file_operations(input)
        
        if not operations:
            return "错误：未找到有效的文件操作格式"
        
        results = []
        for i, operation_text in enumerate(operations):
            try:
                operation_data = _parse_file_operation_format(operation_text)
                result = _execute_file_operation(operation_data)
                results.append(f"操作 {i+1}: {result}")
            except Exception as e:
                results.append(f"操作 {i+1} 失败: {str(e)}")
        
        return "\n".join(results)
        
    except Exception as e:
        return f"错误：{str(e)}"


def _find_all_file_operations(input: str) -> list:
    """
    查找输入文本中的所有 FILE_OPERATION 块
    """
    operations = []
    lines = input.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line == "%%FILE_OPERATION%%":
            # 找到操作开始
            start_idx = i
            end_idx = -1
            
            # 查找对应的 %%END%%
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == "%%END%%":
                    end_idx = j
                    break
            
            if end_idx != -1:
                # 提取完整的操作块
                operation_block = '\n'.join(lines[start_idx:end_idx + 1])
                operations.append(operation_block)
                i = end_idx + 1
            else:
                # 没找到结束标记，跳过这个开始标记
                i += 1
        else:
            i += 1
    
    return operations


def _parse_file_operation_format(input: str) -> dict:
    """
    解析 %%FILE_OPERATION%% 格式
    """
    lines = input.strip().split('\n')
    
    # 找到操作开始和结束位置
    start_idx = -1
    end_idx = -1
    content_idx = -1
    
    for i, line in enumerate(lines):
        if line.strip() == "%%FILE_OPERATION%%":
            start_idx = i
        elif line.strip() == "%%CONTENT%%":
            content_idx = i
        elif line.strip() == "%%END%%":
            end_idx = i
            break
    
    if start_idx == -1 or end_idx == -1:
        raise ValueError("格式错误：缺少 %%FILE_OPERATION%% 或 %%END%% 标记")
    
    # 解析操作类型和文件路径
    if start_idx + 1 >= len(lines):
        raise ValueError("格式错误：缺少操作类型和文件路径")
    
    operation_line = lines[start_idx + 1].strip()
    parts = operation_line.split(' ', 1)
    
    if len(parts) < 2:
        raise ValueError("格式错误：操作类型和文件路径格式不正确")
    
    operation_type = parts[0]
    file_path = parts[1]
    
    result = {
        "type": "file_operation",
        "operation": operation_type,
        "file_path": file_path,
        "parameters": {},
        "content": None
    }
    
    # 解析参数
    param_end_idx = content_idx if content_idx != -1 else end_idx
    for i in range(start_idx + 2, param_end_idx):
        line = lines[i].strip()
        if line and '=' in line:
            key, value = line.split('=', 1)
            # 尝试转换为数字，如果失败则保持字符串
            try:
                value = int(value)
            except ValueError:
                pass
            result["parameters"][key] = value
    
    # 解析内容
    if content_idx != -1:
        content_lines = lines[content_idx + 1:end_idx]
        result["content"] = '\n'.join(content_lines)
    
    return result


def _execute_file_operation(operation_data: dict) -> str:
    """
    执行文件操作并返回结果
    """
    operation = operation_data["operation"]
    file_path = operation_data["file_path"]
    parameters = operation_data["parameters"]
    content = operation_data["content"]

    # 验证file_path是否合法
    # file_path只能在当前目录下，或者在当前目录的子目录下，即 ./ 目录下，其他都是非法的
    if not _is_safe_path(file_path):
        return f"错误：文件路径 '{file_path}' 不安全，只能访问当前目录及其子目录"
    
    try:
        if operation == "read":
            return _execute_read_operation(file_path, parameters)
        elif operation == "write":
            return _execute_write_operation(file_path, content)
        elif operation == "append":
            return _execute_append_operation(file_path, content)
        elif operation == "update":
            return _execute_update_operation(file_path, content)
        elif operation == "delete_range":
            return _execute_delete_range_operation(file_path, parameters)
        elif operation == "delete_all":
            return _execute_delete_all_operation(file_path)
        else:
            return f"错误：不支持的操作类型 '{operation}'"
    except Exception as e:
        return f"操作失败：{str(e)}"


def _execute_read_operation(file_path: str, parameters: dict) -> str:
    """执行读取操作"""
    if not os.path.exists(file_path):
        return f"错误：文件 '{file_path}' 不存在"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        start_line = parameters.get("start_line", 1)
        end_line = parameters.get("end_line", len(lines))
        
        # 确保行号范围有效
        start_line = max(1, start_line)
        end_line = min(len(lines), end_line)
        
        if start_line > end_line:
            return f"错误：开始行号 {start_line} 大于结束行号 {end_line}"
        
        # 构建带行号的文件内容
        result_lines = []
        for i in range(start_line - 1, end_line):
            line_content = lines[i].rstrip('\n')
            result_lines.append(f"{i + 1:4d}: {line_content}")
        
        total_lines = len(lines)
        return f"文件 '{file_path}' 内容 (第{start_line}-{end_line}行，共{total_lines}行):\n" + "\n".join(result_lines)
        
    except Exception as e:
        return f"错误：读取文件失败 - {str(e)}"


def _execute_write_operation(file_path: str, content: str) -> str:
    """执行写入操作"""
    try:
        # 确保目录存在
        dir_path = os.path.dirname(file_path)
        if dir_path:  # 只有当目录路径不为空时才创建
            os.makedirs(dir_path, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"成功：已写入文件 '{file_path}'"
    except Exception as e:
        return f"错误：写入文件失败 - {str(e)}"


def _execute_append_operation(file_path: str, content: str) -> str:
    """执行追加操作"""
    try:
        # 确保目录存在
        dir_path = os.path.dirname(file_path)
        if dir_path:  # 只有当目录路径不为空时才创建
            os.makedirs(dir_path, exist_ok=True)
        
        # 检查文件是否存在以及是否需要添加换行符
        add_newline = False
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
                # 如果文件不为空且不以换行符结尾，需要添加换行符
                if existing_content and not existing_content.endswith('\n'):
                    add_newline = True
        
        with open(file_path, 'a', encoding='utf-8') as f:
            if add_newline:
                f.write('\n')
            f.write(content)
        
        return f"成功：已追加内容到文件 '{file_path}'"
    except Exception as e:
        return f"错误：追加文件失败 - {str(e)}"


def _execute_update_operation(file_path: str, diff_content: str) -> str:
    """执行更新操作(使用diff格式)"""
    if not os.path.exists(file_path):
        return f"错误：文件 '{file_path}' 不存在"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_lines = f.readlines()
        
        # 解析diff格式并应用更改
        updated_lines = _apply_diff(original_lines, diff_content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(updated_lines)
        
        return f"成功：已更新文件 '{file_path}'"
    except Exception as e:
        return f"错误：更新文件失败 - {str(e)}"


def _execute_delete_range_operation(file_path: str, parameters: dict) -> str:
    """执行删除范围操作"""
    if not os.path.exists(file_path):
        return f"错误：文件 '{file_path}' 不存在"
    
    start_line = parameters.get("start_line")
    end_line = parameters.get("end_line")
    
    if start_line is None or end_line is None:
        return "错误：缺少 start_line 或 end_line 参数"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 验证行号范围
        if start_line < 1 or end_line > len(lines) or start_line > end_line:
            return f"错误：无效的行号范围 {start_line}-{end_line}，文件共 {len(lines)} 行"
        
        # 删除指定范围的行
        new_lines = lines[:start_line-1] + lines[end_line:]
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        return f"成功：已删除文件 '{file_path}' 第{start_line}-{end_line}行"
    except Exception as e:
        return f"错误：删除文件内容失败 - {str(e)}"


def _execute_delete_all_operation(file_path: str) -> str:
    """执行删除全部内容操作"""
    if not os.path.exists(file_path):
        return f"错误：文件 '{file_path}' 不存在"
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("")
        
        return f"成功：已清空文件 '{file_path}' 的所有内容"
    except Exception as e:
        return f"错误：清空文件失败 - {str(e)}"



def _apply_diff(original_lines: List[str], diff_text: str) -> List[str]:
    """
    将 unified diff 字符串应用到 original_lines。
    - **完全忽略** @@ 行号信息，只根据行首前缀 (' ', '-', '+') 判断操作。
    - 自动对齐游标，hunk 前若缺少空行等上下文也能正确 patch。
    返回新的代码行列表（每行自带 \n）。
    """
    new_lines: List[str] = []
    i = 0                       # original_lines 游标
    diff_lines = diff_text.splitlines()
    idx = 0

    while idx < len(diff_lines):
        # 定位到下一个 @@ 块
        if not diff_lines[idx].startswith("@@"):
            idx += 1
            continue

        idx += 1  # 跳过 @@ 行
        hunk_start = idx
        while idx < len(diff_lines) and not diff_lines[idx].startswith("@@"):
            idx += 1
        hunk_body = diff_lines[hunk_start:idx]

        # ---------- 1) 对齐：找到第一条 ' ' 或 '-' 行，用它去同步 original_lines ----------
        align_target = next(
            (hl[1:] for hl in hunk_body if hl and hl[0] in (" ", "-")),
            None,
        )
        if align_target is not None:
            while i < len(original_lines) and original_lines[i].rstrip("\n") != align_target:
                new_lines.append(original_lines[i])
                i += 1

        # ---------- 2) 应用 hunk ----------
        for hl in hunk_body:
            if not hl:                # 空行
                continue
            tag, content = hl[0], hl[1:]
            if tag == " ":
                new_lines.append(original_lines[i])  # 用原行，保证换行符一致
                i += 1
            elif tag == "-":
                i += 1                                # 删除：跳过原行
            elif tag == "+":
                # 加入新行，确保带换行符
                new_lines.append(content + ("\n" if not content.endswith("\n") else ""))
            else:
                raise ValueError(f"未知 diff 标记: {tag!r}")

    # ---------- 3) 复制原文件剩余内容 ----------
    new_lines.extend(original_lines[i:])
    return "".join(new_lines)
    
