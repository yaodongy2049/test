#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
汉诺塔问题求解程序
支持自定义盘子数量
"""


def hanoi(n, source, target, auxiliary, step_count):
    """
    递归求解汉诺塔问题
    
    参数:
        n: 盘子数量
        source: 起始柱子
        target: 目标柱子
        auxiliary: 辅助柱子
        step_count: 步骤计数器（列表，用于在递归中保持计数）
    """
    if n == 1:
        step_count[0] += 1
        print(f"步骤 {step_count[0]}: 将盘子 1 从 {source} 移动到 {target}")
        return
    
    # 将 n-1 个盘子从 source 移动到 auxiliary，使用 target 作为辅助
    hanoi(n - 1, source, auxiliary, target, step_count)
    
    # 将第 n 个盘子从 source 移动到 target
    step_count[0] += 1
    print(f"步骤 {step_count[0]}: 将盘子 {n} 从 {source} 移动到 {target}")
    
    # 将 n-1 个盘子从 auxiliary 移动到 target，使用 source 作为辅助
    hanoi(n - 1, auxiliary, target, source, step_count)


def main():
    """主函数"""
    print("=" * 50)
    print("汉诺塔问题求解程序")
    print("=" * 50)
    print()
    
    while True:
        try:
            n = input("请输入盘子数量（输入 q 退出）: ").strip()
            
            if n.lower() == 'q':
                print("感谢使用，再见！")
                break
            
            n = int(n)
            
            if n <= 0:
                print("错误：盘子数量必须是正整数，请重新输入。")
                print()
                continue
            
            if n > 20:
                confirm = input(f"警告：{n} 个盘子需要 {2**n - 1} 步，可能需要较长时间。是否继续？(y/n): ").strip().lower()
                if confirm != 'y':
                    print("已取消。")
                    print()
                    continue
            
            print()
            print(f"开始求解 {n} 个盘子的汉诺塔问题...")
            print(f"理论最少步数: {2**n - 1}")
            print()
            
            step_count = [0]
            hanoi(n, 'A', 'C', 'B', step_count)
            
            print()
            print(f"完成！共移动了 {step_count[0]} 步。")
            print("=" * 50)
            print()
            
        except ValueError:
            print("错误：请输入有效的整数。")
            print()
        except KeyboardInterrupt:
            print("\n\n程序被中断，再见！")
            break
        except Exception as e:
            print(f"发生错误: {e}")
            print()


if __name__ == "__main__":
    main()
