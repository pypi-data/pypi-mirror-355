# -*- coding: utf-8 -*-
#
# copyright (c) 06-2024 G. Benabdellah
# Departement of physic
# University of Tiaret , Algeria
# E-mail ghlam.benabdellah@gmail.com
#
# this program is part of VAMgui
# first creation 28-05-2024
#
#
# License: GNU General Public License v3.0
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#  log change:
#
#
import tkinter as tk
from tkinter import filedialog, ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class Plotmain:
    def __init__(self, parent):
        self.parent = parent
        self.data = None
        self.figure = None
        self.canvas = None
        self.create_widgets()
        self.reset_ui()

    def create_widgets(self):
        self.main_frame = ttk.Frame(self.parent, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.setup_file_section()
        self.setup_config_section()
        self.setup_preview_section()
        self.setup_plot_section()

    def setup_file_section(self):
        file_frame = tk.Label(self.main_frame)
        file_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(file_frame, text="Data Source",font=("Helvetica", 14, "bold")).grid(row=0, column=0, sticky='w')
        #tk.Label(file_frame, text="     Vampire Output File:" ,font=("Helvetica", 12, "bold")).grid(row=0, column=1, sticky='w')
        self.file_path = tk.Entry(file_frame, width=65)
        self.file_path.grid(row=0, column=1, padx=5)
        tk.Button(file_frame, text=" Browse ", bg="lightgray", command=self.load_file).grid(row=0, column=2)
        tk.Label(file_frame, text="     Vampire Output File:" ,font=("Helvetica", 12, "bold")).grid(row=0, column=3, sticky='w')

    def setup_config_section(self):
        config_frame = tk.Label(self.main_frame)
        config_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(config_frame,text="Plot Configuration",font=("Helvetica", 14, "bold")).grid(row=0, column=0, sticky='w')

        self.create_axis_controls(config_frame, "X",0, 1)
        self.create_axis_controls(config_frame, "Y",1, 1)

        tk.Label(config_frame, text="Plot Title:",font=("Helvetica", 11, "bold")).grid(row=2, column=1,sticky='e', padx=5, pady=2)
        self.plot_title = tk.Entry(config_frame, width=30)
        self.plot_title.grid(row=2, column=2, sticky='e', padx=5, pady=2)

        btn_frame = tk.Frame(config_frame)
        btn_frame.grid(row=2, column=4,  sticky='e', pady=10)
        tk.Button(btn_frame, text="Generate Plot",font=("Helvetica", 11, "bold"), bg="lightblue", command=self.generate_plot).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Save Plot", bg="lightgreen", command=self.save_plot).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Clear", bg="lightgray",font=("Helvetica", 11, "bold"), command=self.reset_ui).pack(side=tk.LEFT)




    def create_axis_controls(self, parent, axis,row, col):
        tk.Label(parent, text=f"{axis}-Axis Column:",font=("Helvetica", 11, "bold")).grid(row=row, column=col, sticky='e', padx=5, pady=2)
        combo = ttk.Combobox(parent, width=30, state='readonly')
        combo.grid(row=row, column=col+1, sticky='w', padx=5, pady=2)
        setattr(self, f"{axis.lower()}_col", combo)

        tk.Label(parent, text=f"{axis}-Axis Label:").grid(row=row, column=col+2, sticky='e', padx=5, pady=2)
        entry = tk.Entry(parent, width=30)
        entry.grid(row=row, column=col+3, sticky='w', padx=5, pady=2)
        setattr(self, f"{axis.lower()}_label", entry)

    def setup_preview_section(self):
        preview_frame = tk.Label(self.main_frame, text="Data Preview", font=("Helvetica", 12, "bold"))
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.preview_text = tk.Text(preview_frame, wrap=tk.NONE, height=15)
        self.preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        y_scroll = tk.Scrollbar(preview_frame, command=self.preview_text.yview)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.preview_text.config(yscrollcommand=y_scroll.set)

        x_scroll = tk.Scrollbar(preview_frame, orient=tk.HORIZONTAL, command=self.preview_text.xview)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.preview_text.config(xscrollcommand=x_scroll.set)

    def setup_plot_section(self):
        plot_frame = tk.Label(self.main_frame, text="Plot Display", font=("Helvetica", 12, "bold"))
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.plot_container = tk.Frame(plot_frame)
        self.plot_container.pack(fill=tk.BOTH, expand=True)

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Standard Vampire output","output"),("Text files", "*.txt"), ("All files", "*")])
        if not file_path: return

        try:
            with open(file_path, 'r') as f:
                raw_data = f.readlines()
                self.data = self.parse_data(raw_data)

            self.file_path.delete(0, tk.END)
            self.file_path.insert(0, file_path)
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, ''.join(raw_data))

            if self.data.size > 0:
                cols = [f"Column {i+1}" for i in range(self.data.shape[1])]
                self.x_col['values'] = cols
                self.y_col['values'] = cols
                self.x_col.current(0)
                self.y_col.current(1 if self.data.shape[1] > 1 else 0)

        except Exception as e:
            tk.messagebox.showerror("File Error", f"Failed to load file:\n{str(e)}")
            self.reset_ui()

    def parse_data(self, lines):
        data_points = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'): continue
            try: data_points.append([float(x) for x in line.split()])
            except ValueError: continue
        return np.array(data_points) if data_points else np.empty((0, 0))

    def save_plot(self):
        """Save the current plot to an image file"""
        if self.figure is None:
            tk.messagebox.showwarning("Save Error", "No plot available to save")
            return

        file_types = [
            ('PNG Image', '*.png'),
            ('JPEG Image', '*.jpg;*.jpeg'),
            ('PDF Document', '*.pdf'),
            ('SVG Vector', '*.svg'),
            ('All Files', '*.*')
        ]

        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=file_types,
            title="Save Plot As"
        )

        if not file_path:
            return

        try:
            self.figure.savefig(file_path, dpi=300, bbox_inches='tight')
            tk.messagebox.showinfo("Save Successful", f"Plot saved successfully to:\n{file_path}")
        except Exception as e:
            tk.messagebox.showerror("Save Error", f"Failed to save plot:\n{str(e)}")

    def generate_plot(self):
        if self.data is None or self.data.size == 0:
            tk.messagebox.showwarning("Data Error", "No data available for plotting")
            return

        try:
            x_idx = int(self.x_col.get().split()[1]) - 1
            y_idx = int(self.y_col.get().split()[1]) - 1

            if not (0 <= x_idx < self.data.shape[1] and 0 <= y_idx < self.data.shape[1]):
                raise ValueError("Invalid column selection")

            if self.figure: plt.close(self.figure)
            if self.canvas: self.canvas.get_tk_widget().destroy()

            self.figure = plt.Figure(figsize=(8, 8), dpi=100)
            ax = self.figure.add_subplot(111)

            ax.plot(self.data[:, x_idx], self.data[:, y_idx], 'b-', linewidth=1.5)
            ax.set_xlabel(self.x_label.get() or f"Column {x_idx+1}")
            ax.set_ylabel(self.y_label.get() or f"Column {y_idx+1}")
            ax.set_title(self.plot_title.get() or "Vampire Data Plot")
            ax.grid(True, linestyle='--', alpha=0.4)

            self.canvas = FigureCanvasTkAgg(self.figure, self.plot_container)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        except Exception as e:
            tk.messagebox.showerror("Plot Error", f"Failed to generate plot:\n{str(e)}")

    def reset_ui(self):
        self.data = None
        if self.figure: plt.close(self.figure)
        if self.canvas: self.canvas.get_tk_widget().destroy()

        self.file_path.delete(0, tk.END)
        self.preview_text.delete(1.0, tk.END)
        self.x_col.set('')
        self.y_col.set('')
        self.x_label.delete(0, tk.END)
        self.y_label.delete(0, tk.END)
        self.plot_title.delete(0, tk.END)

        empty_label = tk.Label(self.plot_container, text="Plot will appear here", fg="gray")
        empty_label.pack(fill=tk.BOTH, expand=True)

# if __name__ == "__main__":
#     root = tk.Tk()
#     root.title("Vampire Data Plotter")
#     root.geometry("900x700")
#     app = Plotmain(root)
#     root.mainloop()
