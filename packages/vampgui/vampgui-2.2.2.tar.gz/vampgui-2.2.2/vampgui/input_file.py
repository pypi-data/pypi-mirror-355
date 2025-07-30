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
# Vampire input:  kyeword:subkeyword = value

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from vampgui.file_io import   InputFileViewer
from vampgui.helpkey import  show_help
from vampgui.version import __version__
from tkinter import scrolledtext, messagebox
from tkinter import filedialog
import re
import os

class InputTab:
    def __init__(self, tab):

        canvas, frame = self._canvas(tab)
        self.input_v = "input_v"
        self._button_frame(frame)
        self.__create_onglet__(frame)

     




#==========================
    def _canvas(self,tab):
        # Create a canvas
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        canvas = tk.Canvas(tab)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=frame, anchor=tk.NW)
        v_scrollbar = tk.Scrollbar(tab, orient=tk.VERTICAL, command=canvas.yview, bg='black')
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.config(yscrollcommand=v_scrollbar.set)
        h_scrollbar = tk.Scrollbar(tab, orient=tk.HORIZONTAL, command=canvas.xview, bg='black')
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.config(xscrollcommand=h_scrollbar.set)
        canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(-1 * int(event.delta / 120), "units"))
        canvas.bind_all("<Shift-MouseWheel>", lambda event: canvas.xview_scroll(-1 * int(event.delta / 120), "units"))
        frame.bind("<Configure>", configure_scroll_region)
        return canvas, frame

#==========================
    def _button_frame(self, frame):
        """Create a frame containing action buttons for sample management.
        Args:
        frame: Parent widget where the button frame will be placed.
        """
        button_frame = tk.Frame(frame)
        button_frame.pack(side=tk.TOP, fill=tk.X, padx=20, pady=8)
        buttons = [
            {"text": "Import from input", "bg": "bisque", "command": self.load_file},
            {"text": f"Save to {self.input_v}", "bg": "#99ff99", "command": self.save_to_file},
            {"text": f"View/Edit {self.input_v}", "bg": "#ffff99", "command": self.open_input_file},
            {"text": "                      ", "bg": button_frame.cget("bg"), "command": None},  # Spacer
            {"text": "Deselect All", "bg": "#ff9999", "command": self.deselect_all_checkboxes}
        ]

        for col, btn_config in enumerate(buttons):
            btn = tk.Button(
                button_frame,
                text=btn_config["text"],
                bg=btn_config["bg"],
                command=btn_config["command"] if btn_config["command"] else None
            )
            sticky_pos = "w" if col < 4 else "e"  # Left-align first 4, right-align last 3
            btn.grid(row=0, column=col, padx=5, pady=5, sticky=sticky_pos)


#==========================

    def __create_onglet__(self, frame):
        """Create a notebook widget for organizing attribute tabs.
        Args:
            frame: Parent widget where the notebook will be placed.
        """
        style = ttk.Style()
        style.configure("CustomNotebook.TNotebook.Tab",
                    foreground="black",
                    font=("Helvetica", 11, "bold"))
        sub_notebook = ttk.Notebook(frame, style="CustomNotebook.TNotebook")
        sub_notebook.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.last_selected = tk.StringVar(value="cube")

        """
        Keywords List & Tab Header.
        Changing the order of keywords will update the order of the subtabs.
        """
        # "prefix" ,  "onglet_title"
        onglet_dic={"create" :"Creation",
                "material" : "Material attributes",
                "dimensions" :"Dimensions System",
                "sim" : "Simulation",
                "montecarlo" :"Montecarlo",
                "exchange" : "Exchange cal.",
                "anisotropy"  :"Anisotropy cal.",
                "dipole" :"Dipole field cal.",
                "hamr" :"HAMR cal.",
                "output" : "Output" ,
                "config"  : "Configuration",
                "screen" :"Screen" ,
                "cells" : "Cells",
                }
        self.prefix_list = onglet_dic.keys()
        self.all_suffix_values()
        self.user_input = []

        for prefix, onglet_title in onglet_dic.items():
            self.suffix_list = list(getattr(self, f"{prefix}_default_values"))


            #if prefix in [self.prefix_list[0], self.prefix_list[1]]:
                ## include 2 lists in same subtab
                #if prefix == self.prefix_list[0]:
                    #self.create_tab = ttk.Frame(sub_notebook)
                    #sub_notebook.add(self.create_tab, text=f"{onglet_title.capitalize()} ")


                    #self.add_prefix_list(self.create_tab, prefix)
                #elif prefix == self.prefix_list[1]:

                    #self.add_prefix_list(self.create_tab, prefix)

            #elif prefix in [self.prefix_list[3], self.prefix_list[4]]:

                #if prefix == self.prefix_list[3]:
                    #self.create_tab = ttk.Frame(sub_notebook)
                    #sub_notebook.add(self.create_tab, text=f"{onglet_title.capitalize()} ")


                    #self.add_prefix_list(self.create_tab, prefix)
                #elif prefix == self.prefix_list[4]:

                    #self.add_prefix_list(self.create_tab, prefix)
            #elif prefix in [self.prefix_list[6], self.prefix_list[7], self.prefix_list[8]]:

                #if prefix == self.prefix_list[6]:
                    #self.create_tab = ttk.Frame(sub_notebook)
                    #sub_notebook.add(self.create_tab, text=f"{onglet_title.capitalize()} ")


                    #self.add_prefix_list(self.create_tab, prefix)
                #elif prefix == self.prefix_list[7]:

                    #self.add_prefix_list(self.create_tab, prefix)
                #elif prefix == self.prefix_list[8]:

                    #self.add_prefix_list(self.create_tab, prefix)
            #else:

            self.create_tab = ttk.Frame(sub_notebook)
            sub_notebook.add(self.create_tab, text=f"{onglet_title.capitalize()} ")


            self.add_prefix_list(self.create_tab, prefix)





#==========================
    def add_prefix_list(self, tab, prefix):
        # Create frame with appropriate title
        frame_title = " Simulation attributes :  " if prefix == "sim" else f"{prefix.capitalize()} attributes : "
        frame = tk.LabelFrame(tab, text=frame_title, font=("Helvetica", 14, "bold"))
        frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Configuration values
        widget_config = {
            "crystal-structure": {
                "type": "combobox", "values": ["sc", "fcc", "bcc", "hcp", "heusler", "kagome", "rocksalt", "spinel"]
                },
            "interfacial-roughness-type": {
                "type": "combobox", "values": ["peaks", "troughs"]
                },
            "program": {
                "type": "combobox", "values": ["benchmark", "time-series", "hysteresis-loop", "static-hysteresis-loop",
                    "curie-temperature", "field-cool", "localised-field-cool", "laser-pulse", "hamr-simulation",
                    "cmc-anisotropy", "hybrid-cmc", "reverse-hybrid-cmc", "LaGrange-Multiplier", "partial-hysteresis-loop",
                    "localised-temperature-pulse", "effective-damping", "fmr", "diagnostic-boltzmann", "setting"]
                },
            "integrator": {
                "type": "combobox", "values": ["llg-heun", "monte-carlollg-midpoint", "constrained-monte-carlo",
                        "hybrid-constrained-monte-carlo", "monte-carlo"]
                },
            "laser-pulse-temporal-profile": {
                "type": "combobox", "values": ["square", "two-temperature", "double-pulse-two-temperature", "double-pulse-square"]
                },
            "cooling-function": {
                "type": "combobox", "values": ["exponential", "gaussian", "double-gaussian", "linear", "cooling-function"]
                },
            "save-checkpoint": {
                "type": "combobox", "values": ["end", "continuous"]
                },
            "load-checkpoint": {
                "type": "combobox", "values": ["restart", "continue"]
                },
            "atoms": {
                "type": "combobox", "values": ["", "end", "continuous"]
                },
            "macro-cells": {
                "type": "combobox", "values": ["", "end", "continuous"]
                },
            "output-format": {
                "type": "combobox", "values": ["text", "binary"]
                },
            "output-mode": {
                "type": "combobox", "values": ["file-per-node", "legacy", "mpi-io", "file-per-process"]
                },
            "solver": {
                "type": "combobox", "values": ["macrocell", "tensor", "atomistic"]
                },
            "function": {
                "type": "combobox", "values": ["nearest-neighbour", "exponential"]
                },
            "algorithm": {
                "type": "combobox", "values": ["adaptive", "spin-flip", "uniform", "angle", "hinzke-nowak"]
                },
        }

        # Boolean fields
        boolean_fields = {
            "enable-bulk-neel-anisotropy", "column-headers", "voronoi-rounded-grains", "voronoi-row-offset",
            "crystal-sublattice-materials", "select-material-by-height", "select-material-by-geometry",
            "fill-core-shell-particles", "material-interfacial-roughness", "interfacial-roughness"
        }
        self.shaps = ["none","full", "cube", "cylinder", "ellipsoid", "sphere", "truncated-octahedron", "particle","tear-drop", "particle-array","hexagonal-particle-array", "voronoi-film", "particle-centre-offset"]
        # Setup parameters
        max_row = 4 if prefix == "material" else 20
        width = 35 if prefix == "material" else 20
        padx = 2
        entries = {}

        # Create widgets for each subkeyword
        for idx, suffix in enumerate(self.suffix_list):
            clean_suffix = suffix.strip().strip("=").strip()
            loaded_value = getattr(self, f"{prefix}_default_values")[suffix]

            # Determine row and column position
            row = idx % max_row
            col = idx // max_row
            col_start = col * 3

            # Create checkbox
            var = tk.BooleanVar()
            check = tk.Checkbutton(frame, text=suffix, variable=var, font=13)
            check.config(command=lambda skw=suffix, v=var, chk=check: self.update_last_selected(skw, v, chk))
            check.grid(row=row, column=col_start+1, sticky="w")

            # Create help button
            help_btn = tk.Button(frame, text="?", command=lambda sk=suffix: show_help(sk))
            help_btn.grid(row=row, column=col_start + 3, sticky="w")

            # Create input widget based on field type
            if clean_suffix in widget_config:
                config = widget_config[clean_suffix]
                entry = ttk.Combobox(frame, values=config["values"], state="readonly", width=width)
                entry.set(loaded_value if loaded_value in config["values"] else config["values"][0])
            elif clean_suffix in boolean_fields:
                entry = ttk.Combobox(frame, values=["false", "true"], state="readonly", width=width)
                entry.set(loaded_value.lower() if loaded_value.lower() in ("false", "true") else "false")
            elif loaded_value == "none":
                entry = tk.Entry(frame, width=width, state='disabled')
                entry.insert(0, loaded_value)
            else:
                entry = tk.Entry(frame, bg='white', width=width)
                entry.insert(0, loaded_value)

            # Position widget and save reference
            entry.grid(row=row, column=col_start + 2, padx=padx, sticky="w")
            entries[suffix] = (var, entry, check)

        self.user_input.append((prefix, entries))
        #self.create_list.append((frame, entries))


#============================================

    def update_last_selected(self, suffix, var, check):
        """Handle checkbox selection with exclusive shape selection"""
        suffix_shaps = self.clean_key(suffix)
        if var.get():
            color = 'blue'
            if suffix_shaps in self.shaps:
                color = 'green'
                self.deselect_other_shapes(suffix)
            self.set_checkbox_color(check, color)
        else:
            self.set_checkbox_color(check, 'black')
        self.last_selected.set(suffix)

#============================================
    def clean_key(self, suffix):
        """Clean and normalize keyword"""
        return suffix.strip().strip("=").strip()

#============================================
    def deselect_other_shapes(self, current_suffix):
        current_key = self.clean_key(current_suffix)
        last_selected = self.last_selected.get()
        if not last_selected:
            return
        last_suffix = self.clean_key(last_selected)

        # Only deselect if it's a different shape
        if last_suffix in self.shaps and last_suffix != current_key:
            for _, entries in self.user_input:
                if last_selected in entries:
                    var, _, check = entries[last_selected]
                    var.set(False)
                    self.set_checkbox_color(check, 'black')

#============================================
    def set_checkbox_color(self, checkbutton, color):
        """Set checkbox text color"""
        checkbutton.config(fg=color)

#============================================
    def deselect_all_checkboxes(self):
        """Deselect all checkboxes in the interface"""
        for _, entries in self.user_input:
            for (var, _, check) in entries.values():
                var.set(False)
                self.set_checkbox_color(check, 'black')
# ##=============================================================
#     def load_input_values(self, file_path):
#         skywd=[]
#         for _, entries in self.user_input:
#             for subkeyword, (var, entry, check) in entries.items():
#                 skywd.append(subkeyword.strip().strip("="))
#         try:
#             with open(file_path, "r") as f:
#                 self.deselect_all_checkboxes()  # Correctly call the method
#                 lines = f.readlines()
#                 Totkey=0
#                 numkey=0
#                 txtlog=""
#                 stxtlog=""
#
#                 for line in lines:
#                     line = line.lstrip()
#                     str_line = line.strip()
#                     if ":" in line and not str_line.startswith('#'):
#                         Totkey +=1
#                         keysubkey, value = re.split(r'\s|=', line, maxsplit=1)
#                         key = keysubkey.strip().split(":")[0]
#                         sky = keysubkey.strip().split(":")[1]
#                         sky =sky.strip().strip("=")
#                         value = value.strip().strip("=").strip()
#                         #print (value)
#
#                         if key in self.prefix_list:
#                             #print(key, f":{Totkey}-----------------")
#                             if sky in skywd:
#                                 numkey +=1
#                                 subkey = keysubkey.strip().split(":")[1]
#                                 subkey = subkey.strip().strip("=")
#                                 value = value.strip().strip("=")
#                                 if key=="output" and subkey=="applied-field-strength":
#                                     subkey="applied-field-strengths"
#                                 if key=="output" and subkey=="applied-field-unit-vector":
#                                     subkey="applied-field-unit-vectors"
#                                 if key=="cells" and subkey == "macro-cell-size":
#                                     subkey="macro-cell-sizes"
#                                 if key=="screen" and subkey == "magnetisation-length":
#                                     subkey="magnetisation-lengths"
#                                 if key=="screen" and subkey == "mean-magnetisation-length":
#                                     subkey="mean-magnetisation-lengths"
#                                 if key=="screen" and subkey == "temperature":
#                                     subkey="temperatures"
#                                 if key=="output" and  subkey == "temperature":
#                                     subkey="temperature."
#                                 if key=="screen" and subkey == "time-steps":
#                                    subkey="time-steps."
#
#                                 for keyword, entries in self.user_input:
#                                     for subkeyword, (var, entry, check) in entries.items():
#                                         if subkeyword.strip("=").strip() == subkey:
#                                             var.set(True)
#                                             self.set_checkbox_color(check, 'blue')
#                                             if isinstance(entry, tk.Entry):
#                                                 print("entry", value)
#                                                 entry.delete(0, tk.END)
#                                                 entry.insert(0, value)
#                                             if isinstance(entry, ttk.Combobox):
#                                                 if value in entry['values']:
#                                                     entry.set(value)
#                                                     entry.insert(0, value)
#                                                     print("-----------combox", value)
#                             else:
#                                 stxtlog =  f" {stxtlog} \n {keysubkey}"
#                         else:
#                             txtlog =  f" {txtlog} \n {keysubkey}"
#                 if txtlog != "" or stxtlog != "":
#                     with open("keys_subkeys_errors.log", 'w') as flog:
#                         flog.write("the list keywords  not found in List of VGUI\n")
#                         flog.write("---------------------------------------------\n")
#                         flog.write(f"{txtlog}")
#                 self.inputfile = file_path
#             if txtlog != "" or stxtlog != "":
#                 messagebox.showinfo("Echec !!",f"number of lines not loaded: {Totkey-numkey} \n Keyword error:\n{txtlog} \n Sub keyword error:\n  {stxtlog}"    )
#             else:
#                 messagebox.showinfo("Success" ,f"File loaded successfully! \n Number of loaded keyword: {numkey} \n Number of Total keyword: {Totkey}\n")
#         except FileNotFoundError:
#             print(f"File {file_path} not found.")
#         except Exception as e:
#             print(f"An error occurred: {e}")



    def load_input_values(self, file_path):
        # Precompute valid subkeywords
        valid_suffix = {input_suffix.strip().strip("=") for _, entries in self.user_input
                        for input_suffix in entries.keys()}

        # Mapping for special case conversions
        special_cases = {
            ("output", "applied-field-strength"): "applied-field-strengths",
            ("output", "applied-field-unit-vector"): "applied-field-unit-vectors",
            ("cells", "macro-cell-size"): "macro-cell-sizes",
            ("screen", "magnetisation-length"): "magnetisation-lengths",
            ("screen", "mean-magnetisation-length"): "mean-magnetisation-lengths",
            ("screen", "temperature"): "temperatures",
            ("output", "temperature"): "temperature.",
            ("screen", "time-steps"): "time-steps."
        }

        try:
            with open(file_path, "r") as f:
                self.deselect_all_checkboxes()
                lines = f.readlines()
                total_lines = 0   # valide lines
                loaded_lines = 0
                prefix_errors = []
                suffix_errors = []

                for line in lines:
                    line = line.lstrip()
                    stripped = line.strip()

                    # Skip comments and invalid lines
                    if not stripped or stripped.startswith('#') or ':' not in line:
                        continue

                    total_lines += 1

                    # Parse key and suffix
                    parts = re.split(r'\s|=', line, maxsplit=1)
                    if len(parts) < 2:
                        continue

                    prefix_suffix , value = parts
                    prefix, suffix = prefix_suffix.strip().split(':', 1)
                    prefix = prefix.strip()
                    suffix = suffix.strip().strip("=")
                    value = value.strip().strip("=").strip()

                    # Handle special cases
                    case_prefix = (prefix, suffix)
                    if case_prefix in special_cases:
                        suffix = special_cases[case_prefix]

                    # Process valid prefixs
                    if prefix in self.prefix_list:
                        if suffix in valid_suffix:
                            loaded_lines += 1
                            self.update_gui_element(suffix, value)
                        else:
                            suffix_errors.append(f"{prefix}:{suffix}")
                    else:
                        prefix_errors.append(f"{prefix}:{suffix}")

                # Error reporting
                self.handle_import_errors(prefix_errors, suffix_errors, total_lines, loaded_lines)
                self.inputfile = file_path

        except FileNotFoundError:
            messagebox.showerror("Error", f"File not found: {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Import failed: {str(e)}")




    def update_gui_element(self, suffix, value):
        """Update GUI elements for a valid suffix-value pair"""
        for _, entries in self.user_input:
            for full_suffix, (var, entry, check) in entries.items():
                clean_suffix = full_suffix.strip("=").strip()
                if clean_suffix == suffix:
                    var.set(True)
                    self.set_checkbox_color(check, 'blue')
                    if isinstance(entry, tk.Entry):
                        entry.delete(0, tk.END)
                        entry.insert(0, value)

                    if isinstance(entry, ttk.Combobox) and value in entry["values"]:
                        entry.set(value)

                    #return  # Found match, exit early

    def handle_import_errors(self, prefix_errors, suffix_errors, total_lines, loaded_lines):
        """Generate error logs and user messages"""
        if not prefix_errors and not suffix_errors:
            messagebox.showinfo("Success",
                f"File loaded successfully!\nLoaded keys: {loaded_lines}/{total_lines}")
            return

        # Create error log
        error_log = []
        error_log.append(f"Loaded lines : {loaded_lines}/{total_lines}")
        if prefix_errors:
            error_log.append(f"\n*** Invalid prefix number: {len(prefix_errors)} ***")
            error_log.extend(prefix_errors)
        if suffix_errors:
            error_log.append(f"\n*** Invalid suffix number: {len(suffix_errors)} ***")
            error_log.extend(suffix_errors)

        # Write to file
        with open("input_load.log", 'w') as flog:
            flog.write("Unrecognized prefix in VGUI:\n")
            flog.write("=" * 50 + "\n")
            flog.write("\n".join(error_log))
        messagebox.showwarning("Partial Import ", "\n".join(error_log))






#============================================
    def load_file(self):
        file_path = filedialog.askopenfilename(title="Select file", filetypes=[("input files", "*"), ("All files", "*.*")])
        if file_path:
            self.load_input_values(file_path)      
#=============================================
    def open_input_file(self):
        InputFileViewer(self.input_v)
#=============================================                  
#     def save_to_file(self):
#         filename = self.input_v
#         with open(filename, 'w') as file:
#             file.write("#------------------------------------------\n")
#             file.write("# Sample vampire input file to perform\n")
#             file.write("#------------------------------------------\n\n")
#             tstkeyword="init"
#             for index, (keyword, entries) in enumerate(self.user_input, start=1):
#
#                 for subkeyword, (var, entry,_) in entries.items():
#                     subk=subkeyword
#                     if var.get():
#                         if keyword != tstkeyword :
#                             if keyword == "sim":
#                                 file.write("#------------------------------------------\n")
#                                 file.write(f"#   {keyword.capitalize()}ulation ;; attributes & config \n")
#                                 file.write("#------------------------------------------\n\n")
#                             else:
#                                 file.write("#------------------------------------------\n")
#                                 file.write(f"#   {keyword.capitalize()} ;; \n")
#                                 file.write("#------------------------------------------\n\n")
#                         if entry:
#                             entry_value = entry.get().strip()
#                             if entry_value == "none":
#                                 if subk == "applied-field-strengths ":
#                                     subk="applied-field-strength "
#                                 if subk == "applied-field-unit-vectors=":
#                                     subk="applied-field-unit-vector="
#                                 if subk == "macro-cell-sizes=":
#                                     subk="macro-cell-size="
#                                 if subk == "magnetisation-lengths ":
#                                     subk="magnetisation-length "
#                                 if subk == "material-magnetisations ":
#                                     subk="material-magnetisation "
#                                 if subk == "mean-magnetisation-lengths ":
#                                     subk="mean-magnetisation-length "
#                                 if subk == "temperatures ":
#                                     subk="temperature "
#                                 if  subk == "temperature. ":
#                                     subk="temperature "
#                                 if subk == "time-steps. ":
#                                     subk="time-steps "
#                                 file.write(f"{keyword}:{subk} \n")
#                             else:
#                                 if subk == "applied-field-strengths ":
#                                     subk="applied-field-strength "
#                                 if subk == "applied-field-unit-vectors=":
#                                     subk="applied-field-unit-vector="
#                                 if subk == "macro-cell-sizes=":
#                                     subk="macro-cell-size="
#                                 if subk == "magnetisation-lengths ":
#                                     subk="magnetisation-length "
#                                 if subk == "material-magnetisations ":
#                                     subk="material-magnetisation "
#                                 if subk == "mean-magnetisation-lengths ":
#                                     subk="mean-magnetisation-length "
#                                 if subk == "temperatures ":
#                                     subk="temperature "
#                                 if  subk == "temperature. ":
#                                     subk="temperature "
#                                 if subk == "time-steps. ":
#                                     subk="time-steps "
#                                 file.write(f"{keyword}:{subk}{entry_value} \n")
#                         tstkeyword=keyword
#             file.write("\n")
#             messagebox.showinfo("Success", f"File '{filename}' saved successfully!")
    def save_to_file(self):
        filename = self.input_v
        if not filename:
            messagebox.showerror("Error", "No filename specified")
            return

        # Subkey normalization mapping
        SUBKEY_MAPPING = {
            "applied-field-strengths": "applied-field-strength",
            "applied-field-unit-vectors=": "applied-field-unit-vector=",
            "macro-cell-sizes=": "macro-cell-size=",
            "magnetisation-lengths": "magnetisation-length",
            "material-magnetisations": "material-magnetisation",
            "mean-magnetisation-lengths": "mean-magnetisation-length",
            "temperatures": "temperature",
            "temperature.": "temperature",
            "time-steps.": "time-steps"
        }

        try:
            with open(filename, 'w') as file:
                # Write file header
                file.write("#"+"+" * 42 +"#"+"\n")
                file.write("#   Input file  for Vampire v-7 \n")
                file.write(f"#     File created  by vampgui {__version__}\n")
                file.write("#"+"+" * 42 +"#"+"\n\n")

                current_keyword = None

                # Group entries by keyword
                keyword_groups = {}
                for keyword, entries in self.user_input:
                    if keyword not in keyword_groups:
                        keyword_groups[keyword] = []
                    keyword_groups[keyword].append(entries)

                # Process each keyword group
                for keyword, entries_list in keyword_groups.items():
                    has_active_entries = False
                    keyword_entries = []

                    # Collect all active entries for this keyword
                    for entries in entries_list:
                        for subkeyword, (var, entry, _) in entries.items():
                            if var.get():
                                has_active_entries = True
                                entry_value = entry.get().strip()
                                keyword_entries.append((subkeyword, entry_value))

                    # Skip keywords with no active entries
                    if not has_active_entries:
                        continue

                    # Write section header
                    if keyword == "sim":
                        section_title = "Simulation attributes "
                    else:
                        section_title = f"{keyword.capitalize()} parameters"

                    file.write("#"+"-" * 42 + "\n")
                    file.write(f"# {section_title}\n")
                    file.write("#"+"-" * 42 + "\n\n")

                    # Process each entry
                    for subkeyword, entry_value in keyword_entries:
                        # Normalize subkey
                        clean_subkey = subkeyword.strip()
                        normalized_subkey = SUBKEY_MAPPING.get(clean_subkey, clean_subkey)

                        # Format output line
                        if entry_value == "none":
                            line = f"{keyword}:{normalized_subkey}\n"
                        else:
                            # Add space if needed for readability
                            if not normalized_subkey.endswith("=") and not normalized_subkey.endswith(" "):
                                normalized_subkey += " "
                            line = f"{keyword}:{normalized_subkey} {entry_value}\n"

                        file.write(line)

                    file.write("\n")  # Add space between sections

                messagebox.showinfo("Success", f"File '{filename}' saved successfully!")

        except IOError as e:
            messagebox.showerror("Save Error", f"Failed to save file: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")
#===================================================================================================================================           
         
    def all_suffix_values(self):
        self.create_default_values = {
                    "crystal-structure=": "sc",
                    "periodic-boundaries-x ": "none",
                    "periodic-boundaries-y ": "none",
                    "periodic-boundaries-z ": "none",
                    #
                    "full ": "none",
                    "cube ": "none",
                    "cylinder ": "none",
                    "ellipsoid ": "none",
                    "sphere ": "none",
                    "truncated-octahedron ": "none",
                    "tear-drop" : "none" ,
                    "particle ": "none",
                    "particle-array ": "none",
                    "hexagonal-particle-array" : "none",
                    "voronoi-film ": "none",
                    #
                    
                    "particle-centre-offset ": "none",
                    "single-spin ": "none",
                    "select-material-by-height=": "true",
                    "select-material-by-geometry=": "true",
                    "fill-core-shell-particles=": "true",
                    "interfacial-roughness=": "true",
                    "material-interfacial-roughness=": "true",
                    "interfacial-roughness-random-seed=": "2e6",
                    "interfacial-roughness-number-of-seed-points=": "0",
                    "interfacial-roughness-type=": "peaks",
                    "interfacial-roughness-seed-radius=": "0.0 !nm",
                    "interfacial-roughness-seed-radius-variance=": "0.0",
                    "interfacial-roughness-mean-height=": "0.0",
                    "interfacial-roughness-maximum-height=": "0.01 !nm",
                    "interfacial-roughness-height-field-resolution=": "0.01 !nm",
                    #
                    "voronoi-grain-substructure" : "none",
                    "voronoi-size-variance=": "0.01",
                    "voronoi-random-seed=": "10",  
                    "voronoi-rounded-grains-area=": "0.9", 
                    "voronoi-row-offset ": "none",
                    "voronoi-rounded-grains ": "none",
                    "single-spin" : "none",
                    #"crystal-sublattice-materials=": "false3",
                    "alloy-random-seed=": "683614233",
                    "grain-random-seed=": "1527349271",
                    "dilution-random-seed=": "465865253",
                    "intermixing-random-seed=": "100181363",
                    "spin-initialisation-random-seed=": "123456"
                    }
   
        
    
    
        self.dimensions_default_values = {
                    "unit-cell-size=": "3.54  !nm", 
                    "unit-cell-size-x=": "0.01 !nm ",
                    "unit-cell-size-y=": "0.01 !nm",
                    "unit-cell-size-z=": "0.01 !nm",
                    "system-size=": "0.01 !nm",
                    "system-size-x=": "0.01 !nm ",
                    "system-size-y=": "0.01 !nm ",
                    "system-size-z=": "0.01 !nm ",
                    "particle-size=": "0.01 !nm ",
                    "particle-spacing=": "0.01 !nm ",
                    "particle-shape-factor-x=": "1.0",
                    "particle-shape-factor-y=": "1.0",
                    "particle-shape-factor-z=": "1.0",
                    "particle-array-offset-x=": "0.1 !mm", 
                    "particle-array-offset-y=": "0.1 !nm ",
                    "macro-cell-size=": " "
                    }
         
                
        self.material_default_values = {
                    "file=": "sample.mat",
                    "unit-cell-file=": "sample_unit_cell.ucf"
                    }
        self.sim_default_values = {
                    "integrator="  :  "llg-heun",
                    "program="  :  "", 
                    "enable-dipole-fields=" : " ", 
                    "enable-fmr-field ": "none",
                    "enable-fast-dipole-fields="  :  "false", 
                    "dipole-field-update-rate="  :  "1000", 
                    "time-step=" : "0.01 !ps", 
                    "total-time-steps=":"0", 
                    "loop-time-steps=": "0", 
                    "time-steps-increment=" : "1",
                    "equilibration-time-steps=" : "0", 
                    "simulation-cycles=" : "100",
                    "temperature=" : "0",
                    "minimum-temperature=" : "0", 
                    "maximum-temperature=" : "1000", 
                    "temperature-increment=" : "25",
                    "equilibration-temperature=" : " ",
                    "cooling-time=": "1 !ns ",
                    "laser-pulse-temporal-profile=" : " ",
                    "laser-pulse-time=" : " ",
                    "laser-pulse-power=" : " ",
                    "second-laser-pulse-time=": " ",
                    "second-laser-pulse-power=": " ",
                    "second-laser-pulse-maximum-temperature=": "0",
                    "second-laser-pulse-delay-time=": " ",
                    "two-temperature-heat-sink-coupling=": " ",
                    "two-temperature-electron-heat-capacity=" : " ",
                    "two-temperature-phonon-heat-capacity=" : " ",
                    "two-temperature-electron-phonon-coupling=" : " ",
                    "cooling-function=" : " ",
                    "applied-field-strength=" : " ",
                    "maximum-applied-field-strength=": " ", 
                    "equilibration-applied-field-strength=" : " ",
                    "applied-field-strength-increment=" : " ",
                    "applied-field-angle-theta=": " ",
                    "applied-field-angle-phi=": " ",
                    "applied-field-unit-vector=": " ",
                    "demagnetisation-factor="  :  "000", 
                    "integrator-random-seed="  :  "12345", 
                    "constraint-rotation-update=": "0",
                    "constraint-angle-theta="  :  "0", 
                    "constraint-angle-theta-minimum=": "0", 
                    "constraint-angle-theta-maximum=": " ", 
                    "constraint-angle-theta-increment="  :  "5", 
                    "constraint-angle-phi-minimum=" : " ",
                    "constraint-angle-phi-maximum=" : " ",
                    "constraint-angle-phi-increment=" : " ",
                    "checkpoint=" : "false" ,
                    "save-checkpoint=" : "continuous",
                    "save-checkpoint-rate=" : "1",
                    "load-checkpoint=" : "continue",
                    "load-checkpoint-if-exists " : "none",
                    "preconditioning-steps="  :  "0", 
                    "electrical-pulse-time="  :  "1.0 !ns", 
                    "electrical-pulse-rise-time="  :  "0.0 !ns", 
                    "electrical-pulse-fall-time="  :  "0.0 !ns", 
                    "mpi-mode=" : " ",
                    "mpi-ppn=" : "1",
                        }
        self.montecarlo_default_values = {
                    "algorithm " : "",
                    "constrain-by-grain " : "none"
                        }
        self.exchange_default_values = {
                    "interaction-range="  : "100",
                    "function=" : " " ,
                    "decay-multiplier " : "",
                    "decay-length=" : "1",
                    "decay-shift " : "",
                    "ucc-exchange-parameters[i][j]=" : "",
                    "dmi-cutoff-range=" : "",
                    "ab-initio=" : "",
                    "four-spin-cutoff-1=" : "1.0",
                    "four-spin-cutoff-2=" :  "1.4"
                        }
        self.anisotropy_default_values = {
                    "surface-anisotropy-threshold=" : "0",
                    "surface-anisotropy-nearest-neighbour-range=" : "0.0",
                    "enable-bulk-neel-anisotropy" : "false" ,
                    "neel-anisotropy-exponential-range=" :"2.5" ,
                    "neel-anisotropy-exponential-factor=" : "5.52"
                    }
        self.dipole_default_values = {
                    "solver=" : "   ",
                    "field-update-rate=" : "1000",
                    "cutoff-radius=" : "2" ,
                    "output-atomistic-dipole-field " : "none"
                        }
        self.hamr_default_values = {
                    "laser-FWHM-x="  :  "20.0 !nm",
                    "laser-FWHM-y="  :  "20.0 !nm", 
                    "head-speed="  :  "30.0 !m/s", 
                    "head-field-x="  :  " 20.0 !nm", 
                    "head-field-y="  :  " 20.0 !nm", 
                    "field-rise-time="  :  " 1 !ps", 
                    "field-fall-time="  :  " 1 !ps", 
                    "NPS="  :  " 0.0 !nm", 
                    "bit-size="  :  " 0.0 !nm",
                    "track-size="  :  " 0.0 !nm", 
                    "track-padding="  :  " 0.0 !nm", 
                    "number-of-bits="  :  " 0", 
                    "bit-sequence-type="  :  "  ", 
                    "bit-sequence="  :  " " 
                        }
        self.output_default_values = {
                    "column-headers=" : "true",
                    "time-steps " : "none",
                    "real-time " : "none",
                    "temperature. " : "none",
                    "applied-field-strengths " : "none",
                    "applied-field-unit-vectors " : "none",
                    "applied-field-alignment " : "none",
                    "material-applied-field-alignment " : "none",
                    "magnetisation " : "none",
                    "magnetisation-length ": " ",
                    "mean-magnetisation-length " : "none",
                    "mean-magnetisation " : "none",
                    "material-magnetisation " : "none",
                    "material-mean-magnetisation-length " : "none",
                    "material-mean-magnetisation " : "none",
                    "total-torque " : "none",
                    "mean-total-torque " : "none",
                    "constraint-phi " : "none",
                    "constraint-theta " : "none",
                    "material-mean-torque " : "none",
                    "mean-susceptibility " : "none",
                    "material-mean-susceptibility " : "none",
                    "material-standard-deviation " : "none",
                    "electron-temperature " : "none",
                    "phonon-temperature " : "none",
                    "total-energy " : "none",
                    "mean-total-energy " : "none",
                    "anisotropy-energy " : "none",
                    "mean-anisotropy-energy " : "none",
                    "exchange-energy " : "none",
                    "mean-exchange-energy " : "none",
                    "applied-field-energy " : "none",
                    "mean-applied-field-energy " : "none",
                    "magnetostatic-energy " : "none",
                    "mean-magnetostatic-energy " : "none",
                    "material-total-energy " : "none",
                    "material-mean-total-energy " : "none",
                    "mean-specific-heat " : "none",
                    "material-mean-specific-heat " : "none",
                    "fractional-electric-field-strength " : "none",
                    "mpi-timings " : "none",
                    "gnuplot-array-format " : "none",
                    "output-rate=": "1",
                    "precision=" : "6",
                    "fixed-width " : "none"
                        }       
        self.config_default_values = {
                    "atoms=" : "end",
                    "macro-cells=" : " ",
                    "output-format="  : "text", 
                    "output-mode=" : "file-per-node",
                    "output-nodes=" : "1" ,
                    "atoms-output-rate=" : "1000",
                    "atoms-minimum-x=" : "0.0",
                    "atoms-minimum-y=" : "0.0",
                    "atoms-minimum-z=" : "0.0",
                    "atoms-maximum-x=" : "0.0",
                    "atoms-maximum-y=" : "0.0",
                    "atoms-maximum-z=" : "0.0",
                    "macro-cells-output-rate " : "0",
                    "identify-surface-atoms " : "none",
                    "field-range-descending-minimum": " 0.0 T",
                    "field-range-descending-maximum": " 0.0 T",
                    "field-range-ascending-minimum": " 0.0 T",
                    "field-range-ascending-maximum": " 0.0 T",
                        }
        self.screen_default_values = {
                    "time-steps. " :"none",
                    "temperatures ": "none",
                    "magnetisation-lengths ":"none",
                    "mean-magnetisation-lengths ": "none",
                    "material-magnetisations " : "none"
                        }
        self.cells_default_values = {
                    "macro-cell-sizes=" :"2 !nm",
                        }
#===================================================================================================================================

 
