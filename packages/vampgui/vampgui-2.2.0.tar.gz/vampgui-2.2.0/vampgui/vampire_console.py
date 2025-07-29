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
from tkinter import ttk, filedialog, messagebox
import subprocess
import platform
import os
import sys

class RunVampire:
    def __init__(self, tab):
        # Create scrollable frame
        self.canvas, self.frame = self.create_scrollable_frame(tab)
        self.tab=tab

        # Create UI sections
        self.create_serial_section()
        self.create_parallel_section()
        self.create_log_section()

        # Load configurations
        self.load_config_serial()
        self.load_config_para()

        # Track command execution
        self.command_running = False

    def create_scrollable_frame(self, parent):
        """Create a scrollable frame with canvas and scrollbars"""
        canvas = tk.Canvas(parent)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar = tk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.config(yscrollcommand=v_scrollbar.set)
        frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=frame, anchor=tk.NW)
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1 * int(e.delta/120), "units"))
        return canvas, frame

    def create_serial_section(self):
        """Create UI elements for serial execution"""
        serial_frame = tk.LabelFrame(
            self.frame,
            text="Serial Mode",
            font=("Helvetica", 14, "bold"),
            padx=10,
            pady=10
        )
        serial_frame.pack(fill=tk.X, padx=8, pady=8)

        # Program path
        tk.Label(serial_frame, text="Vampire Serial Program Path:",
                font=("Helvetica", 12, "bold")).grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.path_entry = ttk.Entry(serial_frame, width=70)
        self.path_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Button(serial_frame, text="Browse", bg="#e6e6e6",
                 command=self.browse_vampire_serial).grid(row=0, column=2, padx=10, pady=5)

        # Input file
        tk.Label(serial_frame, text="Input File Name:",
                font=("Helvetica", 12, "bold")).grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.file_entry = ttk.Entry(serial_frame, width=70)
        self.file_entry.grid(row=1, column=1, padx=10, pady=5)

        # Run button
        self.run_serial_button = tk.Button(
            serial_frame,
            text="Run Vampire Serial",
            bg="lightgray",  # Green color
            fg="black",
            font=("Helvetica", 12, "bold"),
            command=lambda: self.run_vampire("serial")
        )
        self.run_serial_button.grid(row=2, column=0, columnspan=3, pady=15)

    def create_parallel_section(self):
        """Create UI elements for parallel execution"""
        parallel_frame = tk.LabelFrame(
            self.frame,
            text="Parallel Mode",
            font=("Helvetica", 14, "bold"),
            padx=10,
            pady=10
        )
        parallel_frame.pack(fill=tk.X, padx=8, pady=8)

        # Info label
        tk.Label(parallel_frame, text="mpirun -np n vampire_parallel --input_file input",
                font=("Helvetica", 12)).grid(row=0, column=0, columnspan=4, padx=10, pady=5, sticky="w")

        # Program path
        tk.Label(parallel_frame, text="Vampire Program Path:",
                font=("Helvetica", 12, "bold")).grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.path_para_entry = ttk.Entry(parallel_frame, width=70)
        self.path_para_entry.grid(row=1, column=1, padx=10, pady=5, columnspan=3)

        tk.Button(parallel_frame, text="Browse", bg="#e6e6e6",
                 command=self.browse_vampire_para).grid(row=1, column=4, padx=10, pady=5)

        # Number of processes
        tk.Label(parallel_frame, text="Number of Processes (n):",
                font=("Helvetica", 12, "bold")).grid(row=2, column=0, padx=10, pady=5, sticky="w")

        self.n_entry = ttk.Entry(parallel_frame, width=15)
        self.n_entry.grid(row=2, column=1, padx=10, pady=5)

        # Input file
        tk.Label(parallel_frame, text="Input File Name:",
                font=("Helvetica", 12, "bold")).grid(row=2, column=2, padx=10, pady=5, sticky="w")

        self.file_para_entry = ttk.Entry(parallel_frame, width=30)
        self.file_para_entry.grid(row=2, column=3, padx=10, pady=5)

        # Run button
        self.run_para_button = tk.Button(
            parallel_frame,
            text="Run Vampire Parallel",
            bg="lightgray",  # Blue color
            fg="black",
            font=("Helvetica", 12, "bold"),
            command=lambda: self.run_vampire("para")
        )
        self.run_para_button.grid(row=3, column=0, columnspan=4, pady=15)

    def create_log_section(self):
        """Create log display section"""
        log_frame = tk.LabelFrame(
            self.frame,
            text="Log File",
            font=("Helvetica", 14, "bold"),
            padx=10,
            pady=10
        )
        log_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # View log button
        tk.Button(log_frame, text="View Log File", bg="#FF9800", fg="white",
                 command=self.log_file).grid(row=0, column=0, pady=5, sticky="w")

        # Text output with scrollbars
        self.text_output = tk.Text(log_frame, height=25, width=120, wrap='none', bg="white",
                                 font=("Consolas", 10))
        self.text_output.grid(row=1, column=0, sticky="nsew")

        # Scrollbars
        y_scroll = tk.Scrollbar(log_frame, command=self.text_output.yview)
        y_scroll.grid(row=1, column=1, sticky="ns")
        self.text_output.config(yscrollcommand=y_scroll.set)

        x_scroll = tk.Scrollbar(log_frame, orient=tk.HORIZONTAL, command=self.text_output.xview)
        x_scroll.grid(row=2, column=0, sticky="ew")
        self.text_output.config(xscrollcommand=x_scroll.set)

        # Configure grid weights
        log_frame.grid_rowconfigure(1, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

    def get_vampire_dir(self):
        """Get the appropriate vampire directory path"""
        home_dir = os.path.expanduser("~")
        if sys.platform == "win32":
            return os.path.join(home_dir, "vampire_tmp")
        return os.path.join(home_dir, ".vampire")

    def create_vampire_dir(self):
        """Create vampire directory if it doesn't exist"""
        vampire_dir = self.get_vampire_dir()
        if not os.path.exists(vampire_dir):
            os.makedirs(vampire_dir)
        return vampire_dir

    def browse_vampire_serial(self):
        file_path = filedialog.askopenfilename(title="Select Vampire Serial Executable", filetypes=[("vampire serial executable","vampire-serial")])
        if file_path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, file_path)

    def browse_vampire_para(self):
        file_path = filedialog.askopenfilename(title="Select Vampire Parallel Executable", filetypes=[("vampire parallel executable","vampire-parallel")])
        if file_path:
            self.path_para_entry.delete(0, tk.END)
            self.path_para_entry.insert(0, file_path)

    def save_config_serial(self):
        base_path = self.create_vampire_dir()
        try:
            with open(os.path.join(base_path, "config_serial.txt"), "w") as file:
                file.write(self.path_entry.get() + "\n")
                file.write(self.file_entry.get() + "\n")
        except Exception as e:
            print(f"Error saving serial config: {e}")

    def save_config_para(self):
        base_path = self.create_vampire_dir()
        try:
            with open(os.path.join(base_path, "config_para.txt"), "w") as file:
                file.write(self.path_para_entry.get() + "\n")
                file.write(self.n_entry.get() + "\n")
                file.write(self.file_para_entry.get() + "\n")
        except Exception as e:
            print(f"Error saving parallel config: {e}")

    def load_config_serial(self):
        base_path = self.create_vampire_dir()
        try:
            with open(os.path.join(base_path, "config_serial.txt"), "r") as file:
                lines = file.readlines()
                if len(lines) >= 1:
                    self.path_entry.insert(0, lines[0].strip())
                if len(lines) >= 2:
                    self.file_entry.insert(0, lines[1].strip())
        except FileNotFoundError:
            pass

    def load_config_para(self):
        base_path = self.create_vampire_dir()
        try:
            with open(os.path.join(base_path, "config_para.txt"), "r") as file:
                lines = file.readlines()
                if len(lines) >= 1:
                    self.path_para_entry.insert(0, lines[0].strip())
                if len(lines) >= 2:
                    self.n_entry.insert(0, lines[1].strip())
                if len(lines) >= 3:
                    self.file_para_entry.insert(0, lines[2].strip())
        except FileNotFoundError:
            pass

    def log_file(self):
        """Display the log file contents"""
        try:
            with open("log", 'r') as file:
                data = file.read()
                self.text_output.delete(1.0, tk.END)
                self.text_output.insert(tk.END, data)
        except FileNotFoundError:
            self.text_output.delete(1.0, tk.END)
            self.text_output.insert(tk.END, "Log file not found")
        except Exception as e:
            self.text_output.delete(1.0, tk.END)
            self.text_output.insert(tk.END, f"Error reading log file: {str(e)}")

    def detect_terminal(self):
        """Detect the appropriate terminal for the current platform"""
        system = platform.system()
        if system == 'Windows':
            return 'cmd'
        elif system == 'Darwin':
            return 'open -a Terminal'
        else:  # Linux
            terminals = [
                'gnome-terminal', 'konsole', 'xterm',
                'xfce4-terminal', 'mate-terminal', 'tilix'
            ]
            for term in terminals:
                if subprocess.call(['which', term], stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0:
                    return term
            return 'xterm'

    def run_vampire(self, run_mode):
        """Execute Vampire with the specified mode"""
        # Check if command is already running
        if self.command_running:
            messagebox.showinfo("Already Running", "A command is already running.")
            return

        # Validate inputs based on mode
        if run_mode == "serial":
            path = self.path_entry.get()
            input_file = self.file_entry.get()
            if not path or not input_file:
                messagebox.showerror("Input Error", "Please provide both Vampire path and input file name")
                return
            command = f"{path} --input-file {input_file}"
            self.save_config_serial()

        elif run_mode == "para":
            path = self.path_para_entry.get()
            n = self.n_entry.get()
            input_file = self.file_para_entry.get()
            if not path or not n or not input_file:
                messagebox.showerror("Input Error", "Please provide all required fields for parallel mode")
                return
            try:
                n = int(n)
                if n <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Input Error", "Number of processes must be a positive integer")
                return
            command = f"mpirun -np {n} {path} --input-file {input_file}"
            self.save_config_para()

        else:
            messagebox.showerror("Mode Error", "Unknown run mode")
            return

        # Get terminal command
        terminal = self.detect_terminal()
        terminal_commands = {
            'cmd': f'start cmd /k "{command}"',
            'open -a Terminal': f'open -a Terminal.app -n --args bash -c "{command}; exec bash"',
            'gnome-terminal': f'gnome-terminal -- bash -c "{command}; exec bash"',
            'konsole': f'konsole -e bash -c "{command}; exec bash"',
            'xterm': f'xterm -e bash -c "{command}; exec bash"',
            'xfce4-terminal': f'xfce4-terminal --command="{command}; exec bash"',
            'mate-terminal': f'mate-terminal -- bash -c "{command}; exec bash"',
            'tilix': f'tilix -- bash -c "{command}; exec bash"'
        }

        terminal_command = terminal_commands.get(terminal)
        if not terminal_command:
            messagebox.showerror("Terminal Error", "No suitable terminal found for your system")
            return

        try:
                # Update UI state
                self.command_running = True
                if run_mode == "serial":
                    self.run_serial_button.config(state=tk.DISABLED, text="Running...")
                else:
                    self.run_para_button.config(state=tk.DISABLED, text="Running...")

                # Execute command
                process = subprocess.Popen(terminal_command, shell=True)
                messagebox.showinfo("Execution Started", f"Vampire is running in a new terminal window.\nCommand:\n{command}")

                # Wait for completion in background - FIXED: use self.tab.after
                self.tab.after(100, self.check_process, process, run_mode)

        except Exception as e:
            self.reset_run_state(run_mode)
            messagebox.showerror("Execution Error", f"Failed to start Vampire:\n{str(e)}")

    def check_process(self, process, run_mode):
        """Check if process has completed and update UI"""
        if process.poll() is None:  # Still running
            self.tab.after(100, self.check_process, process, run_mode)
        else:
            self.reset_run_state(run_mode)
            messagebox.showinfo("Execution Complete", "Vampire has finished running")

    def reset_run_state(self, run_mode):
        """Reset UI after execution completes"""
        self.command_running = False
        if run_mode == "serial":
            self.run_serial_button.config(state=tk.NORMAL, text="Run Vampire Serial")
        else:
            self.run_para_button.config(state=tk.NORMAL, text="Run Vampire Parallel")
    
 
        
    

