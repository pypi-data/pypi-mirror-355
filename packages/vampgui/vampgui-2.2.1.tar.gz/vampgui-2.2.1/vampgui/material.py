# -*- coding: utf-8 -*-
#
# Author: G. Benabdellah
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
# 04/11/2024
# 10/06/2025 :  fix bug load file.
#               upgrade theme.

import re
import os
import tkinter as tk
from tkinter import filedialog
from tkinter import scrolledtext, messagebox,ttk
from vampgui.file_io import InputFileViewer 
from vampgui.helpkey import  show_help
from vampgui.version import __version__




class MainInputTab:
    def __init__(self, tab):
        canvas, frame = self._canvas(tab)
        self.simple_mat="sample.mat"
        self._button_frame(frame)

        self.material_attributes(tab)
        self.index_sample = 0
        self.new_indices = {}                                     # for added indexed suffix like exchange-matrix[index]
        self.k_list = []                                          # to add more indexed suffix  to list
        self.samples = []
        self.all_material_suffix = list(self.default_values.keys())  # full material attributes  keywords
        self._sub_notebook(frame)
        self.add_sample(self.sample_tab)

#==========================
    def _canvas(self,tab):
        # Create a canvas
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        canvas = tk.Canvas(tab)  #, bg='white'
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
        #self.frame=frame
        return canvas, frame

#==========================
    def _button_frame(self, frame):
        """Create a frame containing action buttons for sample management.
        Args:
        frame: Parent widget where the button frame will be placed.
        """

        button_frame = tk.Frame(frame)
        button_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        buttons = [
            {"text": "Add Sample", "bg": "cyan", "command": lambda: self.add_sample(self.sample_tab)},
            {"text": "Import from file.mat", "bg": "bisque", "command": self.load_file},
            {"text": f"Save to {self.simple_mat}", "bg": "#99ff99", "command": self.save_to_file},
            {"text": f"View/Edit {self.simple_mat}", "bg": "#ffff99", "command": self.open_sample_file},
            {"text": "                      ", "bg": button_frame.cget("bg"), "command": None},  # Spacer
            {"text": "Deselect All", "bg": "#ff9999", "command": self.deselect_all_checkboxes},
            {"text": "Remove Last Sample", "bg": "#ff9999", "command": self.remove_sample}
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

    def _sub_notebook(self, frame):
        """Create a notebook widget for organizing sample and material tabs.
        Args:
            frame: Parent widget where the notebook will be placed.
        """
        style = ttk.Style()
        style.configure("CustomNotebook.TNotebook.Tab",
                    foreground="black",
                    font=("arial", 11, "bold"))

        self.sub_notebook = ttk.Notebook(frame, style="CustomNotebook.TNotebook")
        self.sub_notebook.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.sample_tab = ttk.Frame(self.sub_notebook)
        self.sub_notebook.add(self.sample_tab, text="Note: Before importing .mat file or adding samples, add the necessary indexed material suffixes using the (+) button)")
        self.tabs = {
            'samples': [self.sample_tab],
            'current_index': '1'
        }

#==========================

    def add_sample(self, tab):
        """Add a new sample material tab with configurable attributes."""
        self.index_sample = len(self.samples) + 1
        frame = tk.LabelFrame(
            tab,
            text=f"Sample {self.index_sample}: Material attributes",
            font=("Arial", 12, "bold")
        )
        frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

        entries = {}
        row, col = 0, 0
        self.max_row = 14
        padx = 0
        width = 14

        indexed_suffixes = [
            "exchange-matrix[1]=",
            "biquadratic-exchange[1]=",
            "neel-anisotropy-constant[1]=",
            "alloy-fraction[1]=",
            "intermixing[1]=",
            "four-spin-constant[1]="
        ]

        for mat_suffix in self.all_material_suffix:
            ncol = 3*col
            var = tk.BooleanVar()
            check = tk.Checkbutton(frame, text=mat_suffix, variable=var, font=13)
            check.config(command=lambda skw=mat_suffix, v=var, chk=check: self.set_color_selected_prefix(skw, v, chk))
            check.grid(row=row, column=ncol+1, sticky="w")

            loaded_value = self.default_values[mat_suffix]
            pure_suffix = mat_suffix.strip().strip("=").strip()

            if pure_suffix == "num-materials":
                entry = self._create_disabled_entry(frame, width, loaded_value)
                var.set(True)
            elif pure_suffix == "alloy-distribution":
                entry = self._create_combobox(
                    frame, width, padx,
                    ["native", "reciprocal", "homogeneous"],
                    loaded_value.lower() if loaded_value.lower() in ["native", "reciprocal", "homogeneous"] else "native"
                )
            elif loaded_value == "none":
                entry = self._create_disabled_entry(frame, width, loaded_value)
            else:
                entry = self._create_standard_entry(frame, width, loaded_value)

            entry.grid(row=row, column=ncol+2, sticky="w", padx=padx)
            entries[mat_suffix] = (var, entry, check)

            tk.Button(frame, text="?", command=lambda kw=mat_suffix: show_help(kw)) \
                .grid(row=row, column=ncol+3, padx=1, sticky="w")

            if mat_suffix in indexed_suffixes:
                tk.Button(
                    frame,
                    text="+",
                    command=lambda skw=mat_suffix: self.add_indexed_suffix(frame, skw)
                ).grid(row=row, column=ncol+3, padx=35, sticky="e")

            row += 1
            if row == self.max_row:
                row = 0
                col += 1

        self.last_row = row
        self.max_col = col
        self.samples.append((frame, entries))
        self.k_list.append((f'material[{self.index_sample}]', entries))


    def _create_disabled_entry(self, parent, width, value):
        entry = tk.Entry(parent, width=width, state='disabled')
        entry.insert(0, value)
        return entry

    def _create_standard_entry(self, parent, width, value):
        entry = tk.Entry(parent, bg='white', width=width)
        entry.insert(0, value)
        return entry

    def _create_combobox(self, parent, width, padx, values, default):
        cb = ttk.Combobox(parent, values=values, state="readonly", width=width)
        cb.set(default)
        return cb

#--------------------------------------------------------
    def add_indexed_suffix(self, frame, suffix):
        pur_suffix = suffix.strip().strip("=").strip()
        indexed_suffix = pur_suffix.split("[")[0]

        # Initialize the index for this  suffix type if not already done
        if indexed_suffix not in self.new_indices:
            self.new_indices[indexed_suffix] = 2
        else:
            # Increment the index for this suffix type
            self.new_indices[indexed_suffix] += 1

        new_suffix = f"{indexed_suffix}[{self.new_indices[indexed_suffix]}]="
        if self.last_row == self.max_row:
            self.last_row = 0
            self.max_col += 1

        row = self.last_row
        col = self.max_col

        var = tk.BooleanVar()
        check = tk.Checkbutton(frame, text=new_suffix, variable=var, font=13)
        check.config(command=lambda skw=new_suffix, v=var, chk=check: self.set_color_selected_prefix(skw, v, chk))
        check.grid(row=row, column=3 * col + 1, sticky="w")

        entry = tk.Entry(frame, bg='white', width=10)
        entry.grid(row=row, column=3 * col + 2, sticky="w")
        entry.insert(0, "0.0")
        self.all_material_suffix.append(new_suffix)

        # Add the new suffix to default_values with an initial default value
        self.default_values[new_suffix] = "0.0"  # Set the initial value as needed

        # Update self.samples and self.k_list
        self.samples[-1][1][new_suffix] = (var, entry, check)
        self.k_list[-1][1][new_suffix] = (var, entry, check)
        self.last_row += 1
#==========================

    def set_color_selected_prefix(self, subkeyword, var, check):
        if var.get():
            self.set_checkbox_color(check, 'blue')
            sub_key=subkeyword.strip().strip("=").strip() 
        else:
            self.set_checkbox_color(check, 'black')
#==========================
    def open_sample_file(self):
        InputFileViewer(self.simple_mat)
##==========================
    #def deselect_checkbox(self, suffix):
        #pur_suffix=suffix.strip().strip("=").strip()
        #if pur_suffix in shaps:
            #for keyword, entries in self.k_list:
                #if suffix in entries:
                    #entries[suffix][0].set(False)
##======================                
    def set_checkbox_color(self, checkbutton, color):
        checkbutton.config(fg=color) 
#==========================        
    #def select_checkbox(self, subkeyword):
        #sub_key=subkeyword.strip().strip("=").strip()
        #if sub_key in shaps:
            #for keyword, entries in self.k_list:
                #if subkeyword in entries:
                    #entries[subkeyword][0].set(True)
#==========================
# deselect all chekedbox
    def deselect_all_checkboxes(self):
        for keyword , entries in self.k_list:
            for var, _ , check in entries.values():
                var.set(False)      
                self.set_checkbox_color(check, 'black')
#==========================
    def remove_sample(self):

        if self.samples:
            frame, entries = self.samples.pop()
            if frame.winfo_exists():  # Check if the widget still exists
                frame.destroy()
                self.k_list.pop()
                self.index_sample -=1
                #print(self.index_sample )
                if self.index_sample == 0:
                    self.add_sample(self.sample_tab)
##==========================

    def load_input_values(self, file_path):
        error_log_path = os.path.join("mat_load.log")
        if os.path.exists(error_log_path):
            os.remove(error_log_path)

        for _ in range(self.index_sample):
            self.remove_sample()

        suffix_list = [suffix_words.strip().strip("=") for _, entries in self.k_list for suffix_words in entries]

        try:
            with open(file_path, "r") as file:
                self.deselect_all_checkboxes()    # deselect all checkboxes before import a new file
                lines = file.readlines()
                total_lines=0
                loaded_lines=0

                pattern="num-materials"
                for line in lines:
                    if line.strip().startswith("#"):
                        continue
                    match=re.search(fr"{pattern}\s*=\s*(\d+)", line)
                    if match:
                        #print(f'Found number after "{pattern}": {match.group(1)}')
                        num =int(match.group(1))
                        if num >1 and   num > int(self.index_sample):
                                for _ in range(num-1):
                                    self.add_sample(self.sample_tab)

                        break

                suffix_values={}
                unknown_prefix=""
                unknown_suffix=""
                for line in lines:
                    line = line.lstrip()
                    if line.startswith("#") or not ":" in line:
                        continue
                    total_lines +=1
                    try:
                        material_suffix, value = re.split(r'\s|=', line, maxsplit=1)
                        material = material_suffix.strip().split(":")[0]
                        mat=material.split("[")[0]
                        material =material.strip() #split("[")[0]
                        suffix = material_suffix.strip().split(":")[1]
                        suffix =suffix.strip().strip("=")
                        value = value.strip().strip("=").strip()


                        if mat =="material":
                            if suffix in suffix_list:
                                loaded_lines +=1
                            else:
                                unknown_suffix =  f"{unknown_suffix}    {suffix}\n"
                        else:
                            unknown_prefix =  f"{unknown_prefix}    {mat}\n"

                        for nmat in range(1, num + 1):
                            if material == f"material[{nmat}]" and material != "material:":
                                if suffix in suffix_list:
                                    if suffix == "alloy-host":
                                        suffix = "host-alloy"

                                    if suffix not in suffix_values:
                                        suffix_values[suffix] = ["not"] * num  # Correct initialization
                                    value = value.strip().strip("=")
                                    suffix_values[suffix][nmat-1] = value
                    except ValueError:
                        continue


                if unknown_prefix or unknown_suffix:
                    with open("mat_load.log", 'w') as flog:
                        flog.write("Keywords not found in VAMGUI list\n")
                        flog.write("---------------------------------------------\n")
                        if unknown_prefix:
                            flog.write(f"Unknown prefixes:\n{unknown_prefix}")
                        if unknown_suffix:
                            flog.write(f"Unknown suffixes:\n{unknown_suffix}")

                self.inputfile = file_path

                for suffix, values in suffix_values.items():
                    i=0
                    for _, entries in self.k_list:
                        for suffix_words, (var, entry, check) in entries.items():
                            if suffix_words.strip("=").strip() == suffix and i < len(values):
                                if values[i] != "not":
                                    var.set(True)
                                    self.set_checkbox_color(check, 'blue')
                                    if isinstance(entry, tk.Entry):
                                        entry.delete(0, tk.END)
                                        entry.insert(0, values[i])
                                    elif isinstance(entry, ttk.Combobox):
                                        if values[i] in entry['values']:
                                            entry.set(values[i])
                                i += 1


            if unknown_prefix  and unknown_suffix :
                messagebox.showinfo("Echec !!",f"Loaded lines: {loaded_lines}/{total_lines} \n\nUnknown prefix:\n{unknown_prefix}\nUnknown suffix:\n{unknown_suffix}")
            elif unknown_prefix:
                messagebox.showinfo("Echec !!",f"Loaded lines: {loaded_lines}/{total_lines} \n\nUnknown prefix:\n{unknown_prefix}")
            elif unknown_suffix:
                messagebox.showinfo("Echec !!",f"Loaded lines: {loaded_lines}/{total_lines} \n\nUnknown suffix:\n{unknown_suffix}")
            else:
                messagebox.showinfo("Success" ,f"File loaded successfully!\nNumber of loaded lines: {loaded_lines}/{total_lines}\n")

        except FileNotFoundError:
            messagebox.showinfo("Echec !!",f"File {file_path} not found." )
            #print(f"File {file_path} not found.")
        except Exception as e:
            messagebox.showinfo("Echec !!",f"An error occurred: {e}\n check .mat file ( num-materials ..)")
            #print(f"An error occurred: {e}")


#============================================
    def load_file(self):
        file_path = filedialog.askopenfilename(title="Select file", filetypes=[("input files", "*"), ("All files", "*.*")])
        if file_path:
            self.load_input_values(file_path)
#=============================================    
    # Add other methods as needed"""
    def close_window(self):
        # Save the file before closing
        self.save_to_file()
        # Close the window
        # Add your code to close the window here
#==========================
    def save_to_file(self):
        filename = self.simple_mat
        with open(filename, 'w') as file:
            file.write("#"+"+" * 42 +"#"+"\n")
            file.write("#    Material file (.mat) for Vampire v-7:\n")
            file.write(f"#     File created  by vampgui {__version__}\n")
            file.write("#"+"+" * 42 +"#"+"\n\n")

            file.write(f"material:num-materials={len(self.samples)}\n\n")
            for n_sample, (frame, entries) in enumerate(self.samples, start=1):

                file.write("#"+"-" * 42+"\n")
                file.write(f"# sample:  {n_sample}\n")
                file.write("#"+"-" * 42+"\n")
                for subkeys, (var, entry, _) in entries.items():
                    if subkeys.strip().strip("=") != "num-materials":
                        if var.get():
                            file.write(f"material[{n_sample}]:{subkeys} {entry.get().strip()}\n")
                file.write("\n")
        messagebox.showinfo("Success", f"File '{filename}' saved successfully!")
#==========================
    def material_attributes(self, tab):
            # Dictionary of default values
            self.default_values = {
            "num-materials=": "none",
            "unit-cell-category=": "0",
            "material-name=": "Cobalt", 
            "damping-constant=": "1.0", 
            "exchange-matrix[1]=": "0.0 J/link",
            #"exchange-matrix[2]=": "0.0 J/link", 
            #"exchange-matrix[3]=": "0.0 J/link", 
            #"exchange-matrix-1st-nn[1]=": "0.0 J/link", 
            #"exchange-matrix-1st-nn[2]=": "0.0 J/link",
            #"exchange-matrix-2nd-nn[1]=": "0.0 J/link",
            #"exchange-matrix-2nd-nn[2]=": "0.0 J/link", 
            #"exchange-matrix-3rd-nn[1]=": "0.0 J/link",
            #"exchange-matrix-3rd-nn[2]=": "0.0 J/link", 
            #"exchange-matrix-4th-nn[1]=": "0.0 J/link",
            #"exchange-matrix-4th-nn[2]=": "0.0 J/link", 
            "biquadratic-exchange[1]=": "0.0 J/link", 
            #"biquadratic-exchange[2]=": "0.0 J/link",
            "atomic-spin-moment=": "1.72 !muB", 
            "surface-anisotropy-constant=": "0.0 J/atom", 
            "neel-anisotropy-constant[1]=": "0.0 J", 
            #"neel-anisotropy-constant[2]=": "0.0 J", 
            "lattice-anisotropy-constant=": "0.0 J/atom", 
            "relative-gamma=": "1",
            "initial-spin-direction=": "0, 0, 1",
            "material-element=": "Fe", 
            "alloy-fraction[1]=": "0.0",
            #"alloy-fraction[2]=": "0.0",  
            "minimum-height=": "0.0", 
            "maximum-height=": "1.0", 
            "core-shell-size=": "1.0", 
            "interface-roughness=": "1.0",
            "intermixing[1]=": "1.0",
            #"intermixing[2]=": "1.0", 
            "density=": "1.0",
            "uniaxial-anisotropy-constant=": "0.0 J/atom",
            "uniaxial-anisotropy-direction=": "0,0,1",
            "cubic-anisotropy-constant=": "0.0 J/atom", 
            "second-order-uniaxial-anisotropy-constant=": "0.0  J/atom", 
            "fourth-order-uniaxial-anisotropy-constant=": "0.0  J/atom", 
            "sixth-order-uniaxial-anisotropy-constant" : "0.0 J/atom" ,
            "fourth-order-cubic-anisotropy-constant=" : "0.0 J/atom",
            "sixth-order-cubic-anisotropy-constant=" :  "0.0 J/atom",
            #"couple-to-phononic-temperature=": "off",
            "temperature-rescaling-exponent=": "1.0", 
            "temperature-rescaling-curie-temperature=": "0.0",
            "non-magnetic ": "none",
            "host-alloy ": "none",
            "continuous ": "none",
            "fill-space ": "none",
            "geometry-file=": " ", 
            "lattice-anisotropy-file=": " ",
            "alloy-distribution" : " ",
            "alloy-variance" : "0.0",
            "four-spin-constant[1]=" :"-0.23e-21"
            #"voltage-controlled-magnetic-anisotropy-coefficient=": "0.0 J/V"
        }

#def main():
    #root = tk.Tk()
    #app = MainInputTab (root)
    #root.mainloop()

#if __name__ == "__main__":
    #main()
    
  
