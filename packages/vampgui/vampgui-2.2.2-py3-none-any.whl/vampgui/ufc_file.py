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
#
#
import tkinter as tk
from tkinter import ttk, messagebox
from vampgui.file_io import InputFileViewer 
from vampgui.helpkey import  show_help

class ufcFile:
    def __init__(self, tab):
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
# Create a canvas
        canvas = tk.Canvas(tab)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
# Add a frame inside the canvas
        frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=frame, anchor=tk.NW)
# Add a vertical scrollbar to the canvas
        v_scrollbar = tk.Scrollbar(tab, orient=tk.VERTICAL, command=canvas.yview, bg='black')
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.config(yscrollcommand=v_scrollbar.set)
# Add a horizontal scrollbar to the canvas
        h_scrollbar = tk.Scrollbar(tab, orient=tk.HORIZONTAL, command=canvas.xview, bg='black')
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.config(xscrollcommand=h_scrollbar.set)
# Bind the canvas scrolling to the mouse wheel
        canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(-1 * int(event.delta / 120), "units"))
        canvas.bind_all("<Shift-MouseWheel>", lambda event: canvas.xview_scroll(-1 * int(event.delta / 120), "units"))
# Bind a function to adjust the canvas scroll region when the frame size changes
        frame.bind("<Configure>", configure_scroll_region)
# Frame for buttons
        button_frame = tk.Frame(frame) 
        button_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)      
        tk.Button(button_frame, bg='cyan', text="Save UCF File", command=self.generate_ucf_file).grid(row=0, column=0, padx=5, pady=5,sticky="w")
        tk.Button(button_frame, bg='#ffff99', text="View/Edit sample.ucf", command=self.open_sample_file).grid(row=0, column=3,padx=5, pady=5,sticky="w")
        
        tk.Button(button_frame,  text="help", command=lambda kw="ufc_file": show_help(kw)).grid(row=0, column=5,padx=5, pady=25,sticky="w")
        
        #Generate button
        #self.generate_button = tk.Button(frame, text="Generate UCF File", command=self.generate_ucf_file)
        #self.generate_button.grid(row=0, column=0, columnspan=4)
         
        self.mode = tk.LabelFrame(frame, text="Crystal system: ", font=("Helvetica", 14, "bold"))
        self.mode.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=8, pady=(8, 8))
        # Filename
        self.filename_label = tk.Label(self.mode, text="Enter ucf filename:")
        self.filename_label.grid(row=0, column=0, sticky='w', pady=5)
        self.filename_entry = tk.Entry(self.mode, width=30,bg='white')
        self.filename_entry.insert(0, "sample_unit_cell.ucf")
        self.filename_entry.grid(row=0, column=1, columnspan=8, sticky='w', pady=5)

        # Crystal system
        self.crystal_system_label = tk.Label(self.mode, text="Select crystal system:")
        self.crystal_system_label.grid(row=1, column=0, sticky='w' , pady=5)
        self.crystal_system_var = tk.StringVar()
        self.crystal_system_options = ["cubic", "tetragonal", "orthorhombic", "hexagonal", "monoclinic", "rhombohedral", "triclinic"]
        self.crystal_system_var.set(self.crystal_system_options[0])
        self.crystal_system_menu = tk.OptionMenu(self.mode, self.crystal_system_var, *self.crystal_system_options, command=self.lock_unlock_lattice_entries)
        self.crystal_system_menu.grid(row=1, column=1, columnspan=8,  sticky='w' , pady=5)

        # Lattice constants
                
        self.lattice_label = tk.Label(self.mode, text="Enter lattice constants:")
        self.lattice_label.grid(row=2, column=1, sticky='w' , pady=5)
        self.lattice_entries = []
        for i, label in enumerate(['a', 'b', 'c']):
            lbl = tk.Label(self.mode ,text=f"{label}:")
            lbl.grid(row=2, column=3*i + 2, sticky='e' , pady=5)
            entry = tk.Entry(self.mode , width=10, bg='white')
            entry.grid(row=2, column=3*i+3, sticky='w' , pady=5)
            self.lattice_entries.append(entry)

        # Vectors
        self.vector_labels = ['x', 'y', 'z']
        self.vector_entries = []
        for vec_num in range(3):
            lbl = tk.Label(self.mode, text=f"Enter vector {vec_num + 1}:")
            lbl.grid(row=3 + vec_num, column=1, sticky='w' , pady=5)
            for i, label in enumerate(self.vector_labels):
                lbl = tk.Label(self.mode ,text=f"{label}:")
                lbl.grid(row=3+ vec_num, column=3*i + 2, sticky='e' , pady=5)
                entry = tk.Entry(self.mode , width=10, bg='white')
                entry.grid(row=3 + vec_num, column=3*i + 3, sticky='w' , pady=5)
                self.vector_entries.append(entry)



        # Number of materials
        self.number_of_materials_label = tk.Label(self.mode, text="Enter number material (from .mat file):")
        self.number_of_materials_label.grid(row=7, column=0, sticky='w' , pady=5)
        self.number_of_materials_entry = tk.Entry(self.mode , width=10, bg='white')
        self.number_of_materials_entry.grid(row=7, column=1, sticky='w' , pady=5)

        # Exchange type
        #self.exchange_type_label = tk.Label(self.mode, text="Enter exchange type")
        #self.exchange_type_label.grid(row=10, column=0, sticky='w' , pady=5)
        #self.exchange_type_entry = tk.Entry(self.mode , width=10, bg='white')
        #self.exchange_type_entry.grid(row=10, column=1, sticky='w' , pady=5)

        # Number of atoms
        self.number_of_atoms_label = tk.Label(self.mode, text="Enter number of atoms")
        self.number_of_atoms_label.grid(row=9, column=0, sticky='w' , pady=5)
        self.number_of_atoms_entry = tk.Entry(self.mode , width=10, bg='white')
        self.number_of_atoms_entry.grid(row=9, column=1, sticky='w' , pady=5)
        
        self.add_atom_parameters_button = tk.Button(self.mode, text="Add Atom Parameters", command=self.add_atom_parameters)
        self.add_atom_parameters_button.grid(row=9, column=2, columnspan=2, sticky='w' , pady=5)
        
        self.mode_p = tk.LabelFrame(frame, text="# Atom parameters: ", font=("Helvetica", 14, "bold"))
        self.mode_p.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=8, pady=(8, 8))
        # Atom parameters

        self.atom_parameters_frame = tk.Frame(self.mode_p)
        self.atom_parameters_frame.grid(row=1, column=0, columnspan=4, sticky='w' , pady=5)
        self.atom_parameters_entries = []
        # Initial lock/unlock of lattice entries
        self.lock_unlock_lattice_entries()

        self.mode_text = tk.LabelFrame(frame, text="## Manually add interaction parameters here: ", font=("Helvetica", 14, "bold"))
        self.mode_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=8, pady=(8, 8))

        self.text_output = tk.Text(self.mode_text, height=40, width=140, wrap='none', bg="white")
        self.text_output.grid(row=4, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

        ## Ensure the columns expand properly
        self.mode_text.grid_columnconfigure(0, weight=1)
        self.mode_text.grid_columnconfigure(1, weight=1)
        self.mode_text.grid_columnconfigure(2, weight=1)
        self.mode_text.grid_columnconfigure(3, weight=1)
        self.mode_text.grid_rowconfigure(4, weight=1)

    def open_sample_file(self):
        InputFileViewer(self.filename_entry.get())

    def lock_unlock_lattice_entries(self, *args):
        crystal_system = self.crystal_system_var.get()

        for entry in self.lattice_entries:
            entry.config(state=tk.NORMAL)

        if crystal_system in ["cubic", "rhombohedral"]:
            self.lattice_entries[1].config(state=tk.DISABLED)
            self.lattice_entries[2].config(state=tk.DISABLED)
        elif crystal_system in ["hexagonal", "tetragonal"]:
            self.lattice_entries[1].config(state=tk.DISABLED)
            self.lattice_entries[2].config(state=tk.NORMAL)
        elif crystal_system in ["orthorhombic", "monoclinic", "triclinic"]:
            for entry in self.lattice_entries:
                entry.config(state=tk.NORMAL)
        else:
            messagebox.showerror("Error", "Crystal system does not exist")

    def add_atom_parameters(self):
        for widget in self.atom_parameters_frame.winfo_children():
            widget.destroy()

        try:
            num_atoms = int(self.number_of_atoms_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number of atoms.")
            return

        self.atom_parameters_entries = []
        for atom_index in range(num_atoms):
            lbl = tk.Label(self.atom_parameters_frame, text=f"Atom {atom_index + 1}")
            lbl.grid(row=atom_index, column=0, sticky='w', pady=5)
            row_entries = []
            for param_index, param_label in enumerate(['id', 'cx', 'cy', 'cz', 'mat', 'lc', 'hc']):
                lbl = tk.Label(self.atom_parameters_frame, text=f"{param_label}:")
                lbl.grid(row=atom_index, column=param_index * 2 + 1, sticky='w', pady=5)
                entry = tk.Entry(self.atom_parameters_frame, width=10, bg='white')
                entry.grid(row=atom_index, column=param_index * 2 + 2, sticky='w', pady=5)
                row_entries.append(entry)
            self.atom_parameters_entries.append(row_entries)

    def generate_ucf_file(self):
       
        filename = self.filename_entry.get()
        crystal_system = self.crystal_system_var.get()
        lattice_constant = [entry.get() for entry in self.lattice_entries]
        
        if not filename:
            messagebox.showerror("Error", "Please enter a filename.")
            return
        
        if crystal_system in ["cubic", "rhombohedral"]:
            a = lattice_constant[0]
            lattice_constant = [a, a, a]
        elif crystal_system in ["hexagonal", "tetragonal"]:
            a, c = lattice_constant[0], lattice_constant[2]
            lattice_constant = [a, a, c]
        elif crystal_system in ["orthorhombic", "monoclinic", "triclinic"]:
            pass
        else:
            messagebox.showerror("Error", "Crystal system does not exist")
            return
        try:
            lattice_constant = [float(entry) for entry in lattice_constant]
        except ValueError:
            messagebox.showerror("Error", "Please enter valid lattice constants.")
            return

        try:
            vector1 = [float(self.vector_entries[i].get()) for i in range(3)]
            vector2 = [float(self.vector_entries[i+3].get()) for i in range(3)]
            vector3 = [float(self.vector_entries[i+6].get()) for i in range(3)]
        except ValueError:
            messagebox.showerror("Error", "Please enter valid vector components.")
            return

        try:
            number_of_materials = int(self.number_of_materials_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number of materials.")
            return
        #try:
            #exctype = int(self.exchange_type_entry.get())
            #if exctype not in [0,1,2]:
                #messagebox.showerror("Error", "Please enter exchange type:\n 0=isotropic, 1=vector, 2=tensor")
                
        #except ValueError:
            #messagebox.showerror("Error", "Please enter exchange type:\n 0=isotropic, 1=vector, 2=tensor")
            #return
        
        try:
            number_of_atoms = int(self.number_of_atoms_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number of atoms.")
            return

        if not self.atom_parameters_entries:
            messagebox.showerror("Error", "Please add atom parameters.")
            return

        try:
            atom_parameters = [
                [self.atom_parameters_entries[i][j].get() for j in range(7)]
                for i in range(number_of_atoms)
            ]
        except IndexError:
            messagebox.showerror("Error", "Mismatch in the number of atoms and parameters provided.")
            return

        
        #exctype = self.exchange_type_entry.get()

        with open(filename, 'w') as f:
            print("# Unit cell size:", file=f)
            print(lattice_constant[0], "\t", lattice_constant[1], "\t", lattice_constant[2], sep="", file=f)

            print("# Unit cell vectors: ", file=f)
            print(vector1[0], vector1[1], vector1[2], file=f)
            print(vector2[0], vector2[1], vector2[2], file=f)
            print(vector3[0], vector3[1], vector3[2], file=f)

            print("# Atoms num, num-materials, then id     cx  cy  cz  mat lc  hc", file=f)
            print(number_of_atoms,number_of_materials, file=f)
            for i in range(number_of_atoms):
                print("\t".join(atom_parameters[i]), file=f)



            print("#interaction parameters (id i j dx dy dz Jij). These currently must be added manually.", file=f)
            additional_parameters = self.text_output.get("1.0", tk.END).strip()
            print(additional_parameters, file=f)
        
        messagebox.showinfo("Success", f"{filename} has been generated.")


 
