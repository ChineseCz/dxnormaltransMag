path = r'E:\Project\dxnormaltransMag\dxnormaltransMag\backend\api\data\dataset.py'
lines = open(path, encoding='utf-8').readlines()
idx = 737  # 0-based index of the fused line
line = lines[idx]
if '):    """' in line:
    lines[idx] = line.replace('):    """', '):\n    """', 1)
    open(path, 'w', encoding='utf-8').writelines(lines)
    print('Fixed line', idx+1)
else:
    print('Pattern not found, line content:', repr(line))

