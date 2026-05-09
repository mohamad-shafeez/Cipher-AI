"""
Cipher Skill — Data Forge
Organ: The Visualizer
Generates data visualizations and system metric graphs.
All heavy libraries lazy-loaded — zero boot time cost.
Saves PNG to temp_data/ and auto-opens on screen.
"""

import os
import subprocess
import sys


OUTPUT_DIR = "temp_data"


class DataForgeSkill:
    def __init__(self):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        print(">> Data Forge: ONLINE")

    def execute(self, command: str) -> str | None:
        cmd = command.lower().strip()

        # ── Trigger detection ──────────────────────────────────────────────
        plot_triggers = ["plot ", "graph of ", "show graph", "show a graph", "draw graph"]
        system_triggers = ["visualize cpu", "visualize ram", "visualize disk", "visualize memory",
                           "cpu graph", "ram graph", "disk graph", "memory graph",
                           "show cpu", "show ram", "show disk", "system graph"]
        viz_triggers = ["visualize ", "chart of ", "bar chart", "line chart", "pie chart"]

        if any(t in cmd for t in system_triggers):
            return self._plot_system_metrics(cmd)

        if any(t in cmd for t in plot_triggers + viz_triggers):
            return self._plot_from_command(command)

        return None

    # ── System Metrics Plot ────────────────────────────────────────────────

    def _plot_system_metrics(self, cmd: str) -> str:
        try:
            import psutil
            import matplotlib
            matplotlib.use("Agg")  # Non-interactive backend — no GUI thread needed
            import matplotlib.pyplot as plt
            import matplotlib.patches as mpatches
            from datetime import datetime
        except ImportError as e:
            return f"Missing library: {e}. Run: pip install matplotlib psutil"

        try:
            # Collect metrics
            cpu     = psutil.cpu_percent(interval=1)
            ram     = psutil.virtual_memory()
            disk    = psutil.disk_usage('/')
            battery = psutil.sensors_battery()

            labels  = ["CPU Usage", "RAM Used", "Disk Used"]
            values  = [cpu, ram.percent, disk.percent]
            colors  = ["#00D4FF", "#7B2FFF", "#FF6B35"]

            # Add battery if available
            if battery:
                labels.append("Battery")
                values.append(battery.percent)
                colors.append("#00FF88")

            fig, axes = plt.subplots(1, 2, figsize=(13, 5))
            fig.patch.set_facecolor("#0D0D1A")

            # ── Left: Horizontal bar chart ─────────────────────────────────
            ax1 = axes[0]
            ax1.set_facecolor("#12122B")
            bars = ax1.barh(labels, values, color=colors, height=0.5, edgecolor="none")

            # Value labels on bars
            for bar, val in zip(bars, values):
                ax1.text(
                    min(val + 1.5, 95), bar.get_y() + bar.get_height() / 2,
                    f"{val:.1f}%", va="center", ha="left",
                    color="white", fontsize=11, fontweight="bold"
                )

            ax1.set_xlim(0, 100)
            ax1.set_xlabel("Usage (%)", color="#AAAACC", fontsize=11)
            ax1.set_title("System Resource Usage", color="white", fontsize=14, fontweight="bold", pad=12)
            ax1.tick_params(colors="white")
            ax1.spines[:].set_color("#2A2A4A")
            ax1.xaxis.label.set_color("#AAAACC")
            for label in ax1.get_yticklabels():
                label.set_color("white")
                label.set_fontsize(11)

            # ── Right: Donut chart for RAM breakdown ───────────────────────
            ax2 = axes[1]
            ax2.set_facecolor("#12122B")

            ram_used_gb  = ram.used / (1024 ** 3)
            ram_free_gb  = ram.available / (1024 ** 3)
            ram_total_gb = ram.total / (1024 ** 3)

            donut_vals   = [ram_used_gb, ram_free_gb]
            donut_colors = ["#7B2FFF", "#1E1E3A"]
            wedges, _ = ax2.pie(
                donut_vals,
                colors=donut_colors,
                startangle=90,
                wedgeprops=dict(width=0.45, edgecolor="#0D0D1A", linewidth=2)
            )

            # Center text
            ax2.text(0, 0.08, f"{ram_used_gb:.1f} GB",
                     ha="center", va="center", fontsize=18,
                     fontweight="bold", color="white")
            ax2.text(0, -0.22, f"of {ram_total_gb:.1f} GB used",
                     ha="center", va="center", fontsize=10, color="#AAAACC")
            ax2.set_title("RAM Usage", color="white", fontsize=14, fontweight="bold", pad=12)

            # Legend
            legend_elements = [
                mpatches.Patch(facecolor="#7B2FFF", label=f"Used ({ram_used_gb:.1f} GB)"),
                mpatches.Patch(facecolor="#1E1E3A", label=f"Free ({ram_free_gb:.1f} GB)"),
            ]
            ax2.legend(handles=legend_elements, loc="lower center",
                       facecolor="#12122B", edgecolor="#2A2A4A",
                       labelcolor="white", fontsize=9)

            # Footer timestamp
            fig.text(0.5, 0.01,
                     f"Cipher System Monitor  ·  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                     ha="center", color="#555577", fontsize=9)

            plt.tight_layout(pad=2.0)

            filepath = os.path.join(OUTPUT_DIR, "system_metrics.png")
            plt.savefig(filepath, dpi=150, bbox_inches="tight",
                        facecolor=fig.get_facecolor())
            plt.close(fig)

            self._open_file(filepath)
            return f"System metrics graph saved and opened: {filepath}"

        except Exception as e:
            return f"Data Forge (system metrics) error: {e}"

    # ── Command-driven Custom Plot ─────────────────────────────────────────

    def _plot_from_command(self, command: str) -> str:
        """
        Parse voice command for plot type and data, then render the chart.
        Supports: bar, line, pie charts with inline data or generated sample data.
        Examples:
          "plot sales 100 200 150 300"
          "bar chart of scores 85 90 78 95 88"
          "line chart temperature 22 25 19 28 30"
          "pie chart budget housing 40 food 25 transport 15 other 20"
        """
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import re
            from datetime import datetime
        except ImportError as e:
            return f"Missing library: {e}. Run: pip install matplotlib"

        try:
            cmd = command.lower()

            # Determine chart type
            chart_type = "bar"
            if "line" in cmd:
                chart_type = "line"
            elif "pie" in cmd:
                chart_type = "pie"

            # Extract numbers from the command
            numbers = [float(x) for x in re.findall(r'\b\d+(?:\.\d+)?\b', command)]

            # Extract a label/title — words before the numbers
            words_before = re.split(r'\d', command)[0]
            words_before = re.sub(
                r'(plot|graph|chart|of|show|visualize|bar|line|pie|a|the|me)', '',
                words_before, flags=re.IGNORECASE
            ).strip()
            title = words_before.title() if words_before else "Data Visualization"

            # Use sample data if no numbers detected
            if not numbers or len(numbers) < 2:
                numbers = [23, 45, 38, 67, 52, 41, 78]
                x_labels = [f"Item {i+1}" for i in range(len(numbers))]
            else:
                x_labels = [f"Item {i+1}" for i in range(len(numbers))]

            fig, ax = plt.subplots(figsize=(10, 5))
            fig.patch.set_facecolor("#0D0D1A")
            ax.set_facecolor("#12122B")

            colors_palette = [
                "#00D4FF", "#7B2FFF", "#FF6B35", "#00FF88",
                "#FFD700", "#FF2D78", "#4ECDC4", "#45B7D1"
            ]

            if chart_type == "line":
                ax.plot(x_labels, numbers, color="#00D4FF", linewidth=2.5,
                        marker="o", markersize=7, markerfacecolor="#7B2FFF",
                        markeredgecolor="white", markeredgewidth=1.5)
                ax.fill_between(range(len(numbers)), numbers, alpha=0.15, color="#00D4FF")

            elif chart_type == "pie":
                pie_colors = colors_palette[:len(numbers)]
                wedges, texts, autotexts = ax.pie(
                    numbers, labels=x_labels, colors=pie_colors,
                    autopct="%1.1f%%", startangle=90,
                    wedgeprops=dict(edgecolor="#0D0D1A", linewidth=1.5)
                )
                for text in texts:
                    text.set_color("white")
                for autotext in autotexts:
                    autotext.set_color("white")
                    autotext.set_fontweight("bold")

            else:  # bar (default)
                bar_colors = [colors_palette[i % len(colors_palette)] for i in range(len(numbers))]
                bars = ax.bar(x_labels, numbers, color=bar_colors,
                              edgecolor="none", width=0.6)
                # Value labels on top
                for bar, val in zip(bars, numbers):
                    ax.text(bar.get_x() + bar.get_width() / 2,
                            bar.get_height() + max(numbers) * 0.02,
                            f"{val:.0f}", ha="center", va="bottom",
                            color="white", fontsize=10, fontweight="bold")

            ax.set_title(title, color="white", fontsize=15, fontweight="bold", pad=14)
            ax.tick_params(colors="white")
            ax.spines[:].set_color("#2A2A4A")
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_color("#AAAACC")

            if chart_type != "pie":
                ax.yaxis.grid(True, color="#1E1E3A", linestyle="--", linewidth=0.8)
                ax.set_axisbelow(True)

            fig.text(0.5, 0.01,
                     f"Cipher Data Forge  ·  {datetime.now().strftime('%H:%M:%S')}",
                     ha="center", color="#555577", fontsize=8)

            plt.tight_layout(pad=2.0)

            safe_title = re.sub(r'[^\w]', '_', title)[:30]
            filename = f"{safe_title}_{datetime.now().strftime('%H%M%S')}.png"
            filepath = os.path.join(OUTPUT_DIR, filename)
            plt.savefig(filepath, dpi=150, bbox_inches="tight",
                        facecolor=fig.get_facecolor())
            plt.close(fig)

            self._open_file(filepath)
            return f"Graph '{title}' saved and opened: {filepath}"

        except Exception as e:
            return f"Data Forge (plot) error: {e}"

    # ── Cross-platform file opener ─────────────────────────────────────────

    def _open_file(self, filepath: str):
        """Open a file using the OS default application."""
        try:
            if sys.platform == "win32":
                os.startfile(filepath)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", filepath])
            else:
                subprocess.Popen(["xdg-open", filepath])
        except Exception:
            pass  # Silent fail — file is still saved even if it can't be opened