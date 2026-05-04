#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
separated 模式数据解交织工具
用于将 COMSOL Dimension=0 的多通道交织数据拆分为独立文件

使用场景：
- 三相变压器的 H1.txt（3通道×81时间步=243列）
- 多线圈系统的全局评估导出数据
- 任何 Dimension=0 且包含多通道交织的输入文件

作者：系统开发团队
日期：2026-04-05
版本：1.0
"""

import numpy as np
import os
import re
import argparse


def detect_channels_from_header(filepath):
    """
    从文件列头自动检测通道数

    Args:
        filepath: COMSOL 导出文件路径

    Returns:
        n_channels: 通道数（如3）
        channel_names: 通道名称列表（如 ['ICoil_1', 'ICoil_4', 'ICoil_7']）
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('%') and '@' in line:
                # 找到列头行，示例：
                # % mf.ICoil_1 (A) @ t=1.16  mf.ICoil_4 (A) @ t=1.16  mf.ICoil_7 (A) @ t=1.16 ...

                # 提取所有通道名称（去重）
                # 模式：匹配 "物理量名 (单位) @ 时间戳"
                pattern = r'([\w.]+)\s*\([^)]+\)\s*@\s*t=[\d.]+'
                all_matches = re.findall(pattern, line)

                if not all_matches:
                    continue

                # 提取唯一的通道名（保持顺序）
                seen = set()
                unique_channels = []
                for ch in all_matches:
                    if ch not in seen:
                        seen.add(ch)
                        unique_channels.append(ch)

                n_channels = len(unique_channels)

                print(f"✓ 检测到 {n_channels} 个通道: {unique_channels}")
                print(f"   列头中共有 {len(all_matches)} 个数据列 (={n_channels}通道 × {len(all_matches)//n_channels if n_channels>0 else 0}时间步)")

                return n_channels, unique_channels

    print("⚠️ 无法自动检测通道数，假设为1个通道")
    return 1, ['Channel_0']


def deinterleave_separated_data(input_file, output_dir=None, n_channels=None, 
                                 time_start=None, time_step=None):
    """
    解交织 separated 模式数据，并添加时间列
    
    Args:
        input_file: 输入文件路径（如 H1.txt）
        output_dir: 输出目录（默认为输入文件同目录）
        n_channels: 手动指定通道数（None则自动检测）
        time_start: 起始时间（None则从列头提取）
        time_step: 时间步长（None则从列头提取）
        
    Returns:
        output_files: 生成的文件列表
    """
    # 1. 自动检测通道数和时间信息
    if n_channels is None:
        n_channels, channel_names = detect_channels_from_header(input_file)
    else:
        channel_names = [f'Channel_{i}' for i in range(n_channels)]
    
    # 2. 从列头提取时间信息
    if time_start is None or time_step is None:
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                if '@' in line and 't=' in line:
                    # 提取时间值：@ t=1.16  @ t=1.16  @ t=1.16  @ t=1.1605  ...
                    times = re.findall(r't=([\d.]+)', line)
                    if len(times) >= n_channels + 1:
                        # 第一个时间
                        time_start = float(times[0])
                        # 第二个不同的时间（跳过相同的通道）
                        time_step = float(times[n_channels]) - time_start
                        print(f"   检测到时间信息: 起始={time_start}s, 步长={time_step}s")
                        break
        
        # 如果没有检测到，使用默认值
        if time_start is None or time_step == 0:
            time_start = 0.0
            time_step = 0.001
            print(f"   ⚠️ 未检测到时间信息，使用默认值: 起始={time_start}s, 步长={time_step}s")
    
    # 3. 加载数据
    print(f"\n📂 读取文件: {input_file}")
    data = np.loadtxt(input_file, encoding='utf-8', comments='%')
    
    print(f"   原始形状: {data.shape}")
    
    # 展平为1维（如果是(1, N)则变为(N,)）
    arr = data.ravel()
    total_elements = len(arr)
    
    # 4. 计算时间步数
    if total_elements % n_channels != 0:
        print(f"⚠️ 警告：数据元素数({total_elements})不能被通道数({n_channels})整除！")
        print(f"   可能通道数设置错误，或数据格式异常")
        return []
    
    n_timesteps = total_elements // n_channels
    print(f"   通道数: {n_channels}")
    print(f"   时间步数: {n_timesteps}")
    print(f"   解交织后形状: ({n_timesteps}, {n_channels})")
    
    # 5. 解交织：[ch0@t0, ch1@t0, ch2@t0, ch0@t1, ...] → (n_timesteps, n_channels)
    reshaped = arr.reshape(n_timesteps, n_channels)
    
    # 6. 生成时间轴
    time_axis = np.arange(n_timesteps) * time_step + time_start
    
    # 7. 保存为独立文件（添加时间列）
    if output_dir is None:
        output_dir = os.path.dirname(input_file) or '.'
    os.makedirs(output_dir, exist_ok=True)
    
    basename = os.path.splitext(os.path.basename(input_file))[0]
    output_files = []
    
    print(f"\n💾 保存拆分后的文件到: {output_dir}")
    for i in range(n_channels):
        channel_name = channel_names[i] if i < len(channel_names) else f'Channel_{i}'
        output_file = os.path.join(output_dir, f"{basename}_{channel_name}.txt")
        
        # 合并时间列和数据列
        output_data = np.column_stack([time_axis, reshaped[:, i]])
        
        # 保存两列数据（时间 + 数值）
        np.savetxt(output_file, output_data, fmt='%.6f', 
                   header=f'Time(s)  {channel_name}',
                   comments='% ')
        output_files.append(output_file)
        
        print(f"   ✓ {os.path.basename(output_file)} ({n_timesteps} 行 × 2 列)")
    
    return output_files


def validate_result(original_file, output_files):
    """验证解交织结果是否正确"""
    print(f"\n🔍 验证解交织结果...")
    
    # 重新读取原始文件
    original = np.loadtxt(original_file, encoding='utf-8', comments='%').ravel()
    
    # 读取所有输出文件并重组（只取数值列，不取时间列）
    channels = []
    for f in output_files:
        data = np.loadtxt(f, comments='%')
        # 如果是两列，取第二列（数值列）
        if data.ndim > 1 and data.shape[1] >= 2:
            channels.append(data[:, 1])
        else:
            channels.append(data)
    
    reconstructed = np.column_stack(channels).ravel(order='C')
    
    # 比较
    if np.allclose(original, reconstructed):
        print("   ✅ 验证通过！解交织结果正确")
        return True
    else:
        print("   ❌ 验证失败！解交织结果与原始数据不一致")
        max_diff = np.max(np.abs(original - reconstructed))
        print(f"      最大误差: {max_diff}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='解交织 COMSOL separated 模式数据（Dimension=0）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:

  # 自动检测通道数
  python deinterleave_separated.py H1.txt
  
  # 手动指定3个通道
  python deinterleave_separated.py H1.txt -c 3
  
  # 指定输出目录
  python deinterleave_separated.py H1.txt -o deinterleaved/
  
  # 批量处理
  python deinterleave_separated.py H1.txt HV1.txt L1.txt -c 3
        """
    )

    parser.add_argument('input_files', nargs='+', help='输入文件路径（支持多个文件）')
    parser.add_argument('-c', '--channels', type=int, default=None,
                        help='手动指定通道数（默认自动检测）')
    parser.add_argument('-o', '--output-dir', type=str, default=None,
                        help='输出目录（默认为输入文件同目录）')
    parser.add_argument('--no-validate', action='store_true',
                        help='跳过验证步骤')

    args = parser.parse_args()

    print("=" * 60)
    print("  COMSOL Separated 模式数据解交织工具 v1.0")
    print("=" * 60)

    all_output_files = []

    for input_file in args.input_files:
        if not os.path.exists(input_file):
            print(f"❌ 文件不存在: {input_file}")
            continue

        print(f"\n{'─' * 60}")
        output_files = deinterleave_separated_data(
            input_file,
            output_dir=args.output_dir,
            n_channels=args.channels
        )

        if output_files and not args.no_validate:
            validate_result(input_file, output_files)

        all_output_files.extend(output_files)

    print(f"\n{'═' * 60}")
    print(f"✅ 完成！共生成 {len(all_output_files)} 个文件")
    print(f"\n💡 下一步操作:")
    print(f"   1. 在数据集管理中创建数据集，选择 'multicolumn' 模式")
    print(f"   2. 上传生成的文件，每个文件设为不同的 'input' 角色")
    print(f"   3. 指定 variableIndex（0, 1, 2, ...）")
    print(f"{'═' * 60}\n")


if __name__ == '__main__':
    main()





