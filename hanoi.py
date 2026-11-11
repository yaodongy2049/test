#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""汉诺塔图形演示程序，也支持命令行求解。"""

import argparse


def hanoi_moves(n, source="A", target="C", auxiliary="B"):
    """按顺序生成汉诺塔的最优移动方案。"""
    if n == 1:
        yield source, target, n
        return

    yield from hanoi_moves(n - 1, source, auxiliary, target)
    yield source, target, n
    yield from hanoi_moves(n - 1, auxiliary, target, source)


def run_cli():
    """保留终端交互方式。"""
    print("=" * 50)
    print("汉诺塔问题求解程序")
    print("=" * 50)

    while True:
        try:
            value = input("\n请输入盘子数量（输入 q 退出）: ").strip()
            if value.lower() == "q":
                print("感谢使用，再见！")
                return

            n = int(value)
            if n <= 0:
                print("错误：盘子数量必须是正整数。")
                continue
            if n > 20:
                confirm = input(
                    f"警告：{n} 个盘子需要 {2**n - 1} 步，是否继续？(y/n): "
                ).strip().lower()
                if confirm != "y":
                    print("已取消。")
                    continue

            print(f"\n开始求解 {n} 个盘子的汉诺塔问题...")
            print(f"理论最少步数: {2**n - 1}\n")
            for step, (source, target, disk) in enumerate(hanoi_moves(n), 1):
                print(f"步骤 {step}: 将盘子 {disk} 从 {source} 移动到 {target}")
            print(f"\n完成！共移动了 {2**n - 1} 步。")
        except ValueError:
            print("错误：请输入有效的整数。")
        except KeyboardInterrupt:
            print("\n程序被中断，再见！")
            return


class HanoiApp:
    """Tkinter 汉诺塔棋盘和交互控件。"""

    COLORS = ["#5b8def", "#f0a35e", "#69b88a", "#a77be8", "#e36f7b",
              "#48a9a6", "#d4ad45", "#7488a8", "#db7ab6", "#7bb4dc"]

    def __init__(self, root):
        import tkinter as tk
        from tkinter import ttk

        self.root = root
        self.tk = tk
        self.ttk = ttk
        self.root.title("汉诺塔 · 递归演示")
        self.root.geometry("980x740")
        self.root.minsize(800, 640)
        self.root.configure(bg="#f3f5f9")

        self.disk_count = tk.IntVar(value=4)
        self.speed = tk.IntVar(value=550)
        self.towers = {}
        self.history = []
        self.solution = []
        self.solution_index = 0
        self.playback_mode = True
        self.selected_tower = None
        self.after_id = None

        self._build_ui()
        self.reset_game()

    def _build_ui(self):
        tk, ttk = self.tk, self.ttk
        container = tk.Frame(self.root, bg="#f3f5f9", padx=32, pady=24)
        container.pack(fill="both", expand=True)

        header = tk.Frame(container, bg="#f3f5f9")
        header.pack(fill="x", pady=(0, 18))
        tk.Label(
            header, text="汉诺塔", font=("Microsoft YaHei UI", 26, "bold"),
            fg="#202b3c", bg="#f3f5f9",
        ).pack(anchor="w")
        tk.Label(
            header, text="亲手移动圆盘，或播放最优解，看看递归如何完成任务。",
            font=("Microsoft YaHei UI", 10), fg="#718096", bg="#f3f5f9",
        ).pack(anchor="w", pady=(3, 0))

        toolbar = tk.Frame(container, bg="white", padx=16, pady=12)
        toolbar.pack(fill="x", pady=(0, 14))
        tk.Label(
            toolbar, text="圆盘数量", font=("Microsoft YaHei UI", 10, "bold"),
            fg="#39465a", bg="white",
        ).pack(side="left")
        self.count_box = ttk.Spinbox(
            toolbar, from_=1, to=10, width=5, textvariable=self.disk_count,
            command=self.reset_game, font=("Microsoft YaHei UI", 10),
        )
        self.count_box.pack(side="left", padx=(9, 14))
        self.count_box.bind("<Return>", lambda _event: self.reset_game())
        self.count_box.bind("<FocusOut>", lambda _event: self.reset_game())
        ttk.Button(toolbar, text="新游戏", command=self.reset_game).pack(side="left")

        self.status_label = tk.Label(
            toolbar, text="", font=("Microsoft YaHei UI", 10),
            fg="#52647d", bg="white",
        )
        self.status_label.pack(side="left", padx=(18, 0))

        board_frame = tk.Frame(container, bg="white", padx=10, pady=10)
        board_frame.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(
            board_frame, bg="#fbfcfe", highlightthickness=0, height=400,
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _event: self.draw_board())
        self.canvas.bind("<Button-1>", self._on_board_click)

        stats = tk.Frame(container, bg="#f3f5f9")
        stats.pack(fill="x", pady=(14, 12))
        self.moves_label = self._stat_card(stats, "已移动", "0")
        self.optimal_label = self._stat_card(stats, "最少步数", "15")
        self.progress_label = self._stat_card(stats, "目标进度", "0%")

        controls = tk.Frame(container, bg="#f3f5f9")
        controls.pack(fill="x")
        ttk.Button(controls, text="撤销一步", command=self.undo).pack(side="left")
        ttk.Button(controls, text="下一步", command=self.next_step).pack(
            side="left", padx=(8, 0),
        )
        self.play_button = ttk.Button(
            controls, text="自动演示", command=self.toggle_playback,
        )
        self.play_button.pack(side="left", padx=(8, 20))
        tk.Label(
            controls, text="播放速度", font=("Microsoft YaHei UI", 9),
            fg="#718096", bg="#f3f5f9",
        ).pack(side="left")
        ttk.Scale(
            controls, from_=1200, to=120, variable=self.speed,
            orient="horizontal", length=150,
        ).pack(side="left", padx=(8, 0))

        tk.Label(
            container, text="操作提示：点击起始柱，再点击目标柱。大盘不能放在小盘上。",
            font=("Microsoft YaHei UI", 9), fg="#8491a4", bg="#f3f5f9",
        ).pack(anchor="w", pady=(12, 0))

    def _stat_card(self, parent, title, value):
        card = self.tk.Frame(parent, bg="white", padx=16, pady=10)
        card.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.tk.Label(
            card, text=title, font=("Microsoft YaHei UI", 9),
            fg="#8491a4", bg="white",
        ).pack(anchor="w")
        label = self.tk.Label(
            card, text=value, font=("Microsoft YaHei UI", 17, "bold"),
            fg="#26364a", bg="white",
        )
        label.pack(anchor="w", pady=(2, 0))
        return label

    def reset_game(self):
        self._stop_playback()
        try:
            count = int(self.disk_count.get())
        except (ValueError, self.tk.TclError):
            count = 4
        count = max(1, min(10, count))
        self.disk_count.set(count)
        self.towers = {
            "A": list(range(count, 0, -1)),
            "B": [],
            "C": [],
        }
        self.history = []
        self.solution = list(hanoi_moves(count))
        self.solution_index = 0
        self.playback_mode = True
        self.selected_tower = None
        self.status_label.configure(text="点击两根柱子即可移动圆盘。", fg="#52647d")
        self._update_stats()
        self.draw_board()

    def draw_board(self):
        if not hasattr(self, "canvas"):
            return
        canvas = self.canvas
        canvas.delete("all")
        width = max(canvas.winfo_width(), 400)
        height = max(canvas.winfo_height(), 280)
        base_y = height - 46
        xs = [width * 0.2, width * 0.5, width * 0.8]
        count = max(1, int(self.disk_count.get()))
        disk_height = min(28, max(16, (height - 135) / count))
        available = max(100, width * 0.32)

        canvas.create_line(
            width * 0.08, base_y, width * 0.92, base_y,
            fill="#b9c3d1", width=5, capstyle="round",
        )
        for index, peg in enumerate(("A", "B", "C")):
            x = xs[index]
            canvas.create_line(
                x, 48, x, base_y, fill="#d2d9e3", width=8, capstyle="round",
            )
            canvas.create_oval(
                x - 5, 43, x + 5, 53, fill="#c6ceda", outline="",
            )
            if self.selected_tower == peg:
                canvas.create_oval(
                    x - 17, base_y + 12, x + 17, base_y + 46,
                    fill="#e9f0ff", outline="",
                )
            canvas.create_text(
                x, base_y + 27, text=peg, fill="#64748b",
                font=("Microsoft YaHei UI", 11, "bold"),
            )

            for level, disk in enumerate(self.towers[peg]):
                disk_width = available * (0.34 + 0.66 * disk / count)
                y2 = base_y - level * disk_height
                y1 = y2 - disk_height + 2
                color = self.COLORS[(disk - 1) % len(self.COLORS)]
                canvas.create_rectangle(
                    x - disk_width / 2, y1, x + disk_width / 2, y2 - 2,
                    fill=color, outline="",
                )
                canvas.create_line(
                    x - disk_width / 2 + 5, y1 + 2,
                    x + disk_width / 2 - 5, y1 + 2,
                    fill="#ffffff", width=2,
                )

    def _on_board_click(self, event):
        if self.after_id is not None:
            self._stop_playback()
        width = max(self.canvas.winfo_width(), 400)
        xs = {"A": width * 0.2, "B": width * 0.5, "C": width * 0.8}
        peg = min(xs, key=lambda item: abs(xs[item] - event.x))
        if abs(xs[peg] - event.x) > width * 0.13:
            return
        if self.selected_tower is None:
            if not self.towers[peg]:
                self._set_status("这根柱子上没有圆盘。", error=True)
                return
            self.selected_tower = peg
            self._set_status(f"已选择 {peg} 柱，请选择目标柱。")
            self.draw_board()
            return

        source = self.selected_tower
        self.selected_tower = None
        if peg == source:
            self._set_status("已取消选择。")
            self.draw_board()
            return
        self.playback_mode = False
        self._move_disk(source, peg)

    def _move_disk(self, source, target):
        if not self.towers[source]:
            self._set_status(f"{source} 柱上没有可移动的圆盘。", error=True)
            return False
        disk = self.towers[source][-1]
        if self.towers[target] and self.towers[target][-1] < disk:
            self._set_status("不能把大圆盘放在小圆盘上。", error=True)
            return False
        self.towers[source].pop()
        self.towers[target].append(disk)
        self.history.append((source, target, disk))
        self._update_stats()
        self.draw_board()
        if len(self.towers["C"]) == self.disk_count.get():
            self._stop_playback()
            self._set_status(
                f"恭喜完成！用了 {len(self.history)} 步。", success=True,
            )
        else:
            self._set_status(f"盘子 {disk}：{source} → {target}")
        return True

    def next_step(self):
        if not self.playback_mode:
            self._set_status("当前是手动模式；点击“新游戏”后可继续演示。", error=True)
            return
        if self.solution_index >= len(self.solution):
            self._set_status("演示已完成。", success=True)
            return
        source, target, _disk = self.solution[self.solution_index]
        if self._move_disk(source, target):
            self.solution_index += 1

    def toggle_playback(self):
        if self.after_id is not None:
            self._stop_playback()
            self._set_status("演示已暂停。")
            return
        self.selected_tower = None
        if not self.playback_mode or self.history:
            self.reset_game()
        else:
            self.draw_board()
        if self.solution_index >= len(self.solution):
            self.reset_game()
        self.play_button.configure(text="暂停演示")
        self._play_next()

    def _play_next(self):
        self.after_id = None
        if self.solution_index >= len(self.solution):
            self.play_button.configure(text="自动演示")
            return
        self.next_step()
        if self.solution_index < len(self.solution):
            delay = max(120, int(self.speed.get()))
            self.after_id = self.root.after(delay, self._play_next)
        else:
            self.play_button.configure(text="自动演示")

    def _stop_playback(self):
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        if hasattr(self, "play_button"):
            self.play_button.configure(text="自动演示")

    def undo(self):
        self._stop_playback()
        if not self.history:
            self._set_status("还没有可以撤销的移动。", error=True)
            return
        source, target, disk = self.history.pop()
        self.towers[target].pop()
        self.towers[source].append(disk)
        if self.playback_mode and self.solution_index > 0:
            self.solution_index -= 1
        self.selected_tower = None
        self._update_stats()
        self.draw_board()
        self._set_status(f"已撤销：盘子 {disk} 回到 {source} 柱。")

    def _update_stats(self):
        moves = len(self.history)
        minimum = (2 ** self.disk_count.get()) - 1
        progress = round(len(self.towers["C"]) / self.disk_count.get() * 100)
        self.moves_label.configure(text=str(moves))
        self.optimal_label.configure(text=str(minimum))
        self.progress_label.configure(text=f"{progress}%")

    def _set_status(self, message, error=False, success=False):
        color = "#26835b" if success else "#c44949" if error else "#52647d"
        self.status_label.configure(text=message, fg=color)


def run_gui():
    try:
        import tkinter as tk
    except ImportError as error:
        raise SystemExit(
            "当前 Python 未安装 Tkinter，无法启动图形界面。请使用 --cli 运行命令行版本。"
        ) from error

    root = tk.Tk()
    HanoiApp(root)
    root.mainloop()


def main():
    parser = argparse.ArgumentParser(description="汉诺塔递归求解与可视化演示")
    parser.add_argument(
        "--cli", action="store_true", help="使用命令行交互模式",
    )
    args = parser.parse_args()
    if args.cli:
        run_cli()
    else:
        run_gui()


if __name__ == "__main__":
    main()
