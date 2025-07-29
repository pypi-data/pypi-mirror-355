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
from tkinter import ttk, filedialog, messagebox
import subprocess
import os
import platform
import sys
import webbrowser
from PIL import Image, ImageDraw, ImageFont
from vampgui.helpkey import  show_help

class VisuaVDC:
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

        # Bind the canvas scrolling to the mouse wheel
        canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(-1 * int(event.delta / 120), "units"))
        canvas.bind_all("<Shift-MouseWheel>", lambda event: canvas.xview_scroll(-1 * int(event.delta / 120), "units"))

        # Bind a function to adjust the canvas scroll region when the frame size changes
        frame.bind("<Configure>", configure_scroll_region)
        self.Canvas=canvas
        
        # Get the home directory
        home_dir = os.path.expanduser("~")
        # Determine the .vampire directory based on the operating system
        if sys.platform == "win32":
            vampire_dir = os.path.join(home_dir,  "vampire_tmp")
        else:
            vampire_dir = os.path.join(home_dir, ".vampire")
        # Create the .vampire directory if it doesn't exist
        if not os.path.exists(vampire_dir):
            os.makedirs(vampire_dir)
        # Attribute to track command execution
        self.command_running = False 
        serial="serial"
        para="para"
        # Use this path for your base path
        self.tmp_path = vampire_dir
        
        

        self.path_mode = tk.LabelFrame(frame, text="vdc Program Path: ", font=("Helvetica", 14, "bold"))
        self.path_mode.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=8, pady=(8, 8))
        
        self.path_label = tk.Label(self.path_mode, text="Path/vdc:", font=("Helvetica", 12, "bold"))
        self.path_label.grid(row=0, column=0, padx=20, pady=20, sticky="w")
        self.path_entry = ttk.Entry(self.path_mode, width=50)
        self.path_entry.grid(row=0, column=1, padx=20, pady=20)
       
        self.browse_button = tk.Button(self.path_mode, text="Browse", command=self.browse_vdc)
        self.browse_button.grid(row=0, column=2, padx=10, pady=10)
        self.load_config()
        
        self.flag_mode = tk.LabelFrame(frame, text="1- VDC Converter Flags: ", font=("Helvetica", 14, "bold"))
        self.flag_mode.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=8, pady=(8, 8))
        
        
        # List of flags
        self.flags = {
            "--xyz ": "none",
            "--povray ": "none",
            "--vtk ": "none",
            "--text ": "none",
            "--spin-spin-correlation ": "none", 
            "--3D " : "none",
            "--verbose ": "none",
            "--vector-z ": "0,0,1",
            "--vector-x ": "0,0,1",
            "--slice ": "0,1,0,1,0,1",
            "--slice-void ": " ",
            "--slice-sphere ": " ",
            "--slice-cylinder ": " ", 
            "--remove-material " : " ",
            "--frame-start ": "0",
            "--frame-final ": "0",
            "--afm ": " ",
            "--colourmap ": "BWR",
            "--custom-colourmap " : " "    
        }
        
        self.flag_vars = []
        self.flag_checkbuttons = []
        entries = {}
        row = 1
        col = 0
        max_row = 7
        Wdth = 12
        Padx = 5
        colors=["C2","BWR","CBWR","Rainbow"]
        for i, flag in enumerate(self.flags.keys()):
            var = tk.BooleanVar()
            ncol = 3 * col
            check = tk.Checkbutton(self.flag_mode, text=flag, variable=var, font=13)
            check.grid(row=row, column=ncol+1, sticky="w", padx=10, pady=5)
            
            default_value = self.flags[flag]
            
            
            if flag == "--colourmap ":
                entry = ttk.Combobox(self.flag_mode, values=colors, state="readonly", width=Wdth)
                entry.grid(row=row, column=ncol+2, padx=Padx  , sticky="e")
                
                if default_value in colors:
                    entry.set(default_value)
                    entry.insert(0, default_value)
                    
                else:
                    entry.set("Rainbow")
                    entry.insert(0, "Rainbow")
                entries[flag] = (var, entry, check)            
            
            elif default_value == "none":
                entry = tk.Entry(self.flag_mode, width=Wdth, state='disabled')
                entry.grid(row=row, column=ncol+2,  padx=Padx , sticky="w")
                entry.insert(0, default_value)
                entries[flag] = (var, entry, check)
            else:
                entry = tk.Entry(self.flag_mode, bg='white', width=Wdth)
                entry.grid(row=row, column=ncol+2,  padx=Padx , sticky="w")
                entry.insert(0, default_value)
                entries[flag] = (var, entry, check)
                

            help_button = tk.Button(self.flag_mode, text="?", command=lambda flag=flag: show_help(flag))
            help_button.grid(row=row, column=ncol+3, sticky="w")

            row += 1
            if (i + 1) % max_row == 0:
                row = 1
                col += 1
        self.flag_vars.append((flag, entries))
                
        self.run_vdc_button = tk.Button(self.flag_mode, text="Run vdc", command=self.run_vdc, width=20)
        self.run_vdc_button.grid(row=max_row+1, column=2, columnspan=3, pady=20, sticky="w")
        
        
        
        #----------------------------------------------------------------
        self.vesta_path_mode = tk.LabelFrame(frame, text="VESTA Program Path: ", font=("Helvetica", 14, "bold"))
        self.vesta_path_mode.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=8, pady=(8, 8))
        
        
        

        self.vesta_website_label = tk.Label(self.vesta_path_mode, text="To visualize the structure, run after  'vdc --xyz' command , by using VESTA software", font=("Helvetica", 11))
        self.vesta_website_label.grid(row=0, column=0,columnspan=2, padx=20, pady=20, sticky="w")

        self.vesta_website = tk.Label(
            self.vesta_path_mode, 
            text="https://jp-minerals.org/vesta/en/download.html",
            font=("Helvetica", 11), 
            fg="blue", 
            cursor="hand2"
        )
        self.vesta_website.grid(row=0, column=2,columnspan=4,  padx=5, pady=20, sticky="w")

        # Bind the Label to open the link when clicked
        self.vesta_website.bind("<Button-1>", lambda e: self.open_link("https://jp-minerals.org/vesta/en/download.html"))

        # Optionally, underline the text to make it look more like a link
        self.vesta_website.config(font=('Helvetica', 11, 'underline'))

        self.vesta_path_label = tk.Label(self.vesta_path_mode, text="Path/VESTA:", font=("Helvetica", 12, "bold"))
        self.vesta_path_label.grid(row=1, column=0, padx=20, pady=10, sticky="e")
        
        self.vesta_path_entry = ttk.Entry(self.vesta_path_mode, width=50)
        self.vesta_path_entry.grid(row=1, column=1,columnspan=3, padx=5, pady=10, sticky="w")
       
        self.browse_vesta_button = tk.Button(self.vesta_path_mode, text="Browse", command=self.browse_vesta)
        self.browse_vesta_button.grid(row=1, column=4, padx=5, pady=10, sticky="e")
        
        
        self.run_vesta_button = tk.Button(self.vesta_path_mode, text="VESTA", command=self.run_vesta)
        self.run_vesta_button.grid(row=2, column=0, pady=20, sticky="e")
        
        self.file_label = tk.Label(self.vesta_path_mode, text=" .xyz file:" , font=("Helvetica", 12, "bold"))
        self.file_label.grid(row=2, column=1, padx=10, pady=10, sticky="w")
        
        self.file_entry = ttk.Entry(self.vesta_path_mode, width=30)
       
        self.file_entry.grid(row=2, column=1,columnspan=3, padx=20, pady=20, sticky="e") 
        self.file_entry.insert(0, "crystal.xyz")
        self.load_config_vesta()
        
        #----------------------------------------------------------------
        self.povray_mode = tk.LabelFrame(frame, text="Provy Program: ", font=("Helvetica", 14, "bold"))
        self.povray_mode.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=8, pady=(8, 8))
        
        
        self.povray_label = tk.Label(self.povray_mode, text="To visualize the structure, run after 'vdc --povray' command, by using povray software(To install(UBUNTU): sudo apt install povray", font=("Helvetica", 11))
        self.povray_label.grid(row=0, column=0,columnspan=4, padx=20, pady=10, sticky="w")
   
        
        self.run_povray_button = tk.Button(self.povray_mode, text="povray", command=self.run_povray)
        self.run_povray_button.grid(row=2, column=0, pady=20, sticky="e")
        
        self.file_pov_label = tk.Label(self.povray_mode, text=".pov file:" , font=("Helvetica", 12, "bold"))
        self.file_pov_label.grid(row=2, column=1, padx=10, pady=10, sticky="w")
        
        self.file_pov_entry = ttk.Entry(self.povray_mode, width=30)
        self.file_pov_entry.grid(row=2, column=2, padx=5, pady=20, sticky="w") 
        self.file_pov_entry.insert(0, "spins.pov")
      
#------------------
    def view_png(self):
        plot_path =self.file_pov_entry.get()
        plot_path=plot_path.split(".")[0]
        plot_path =f"{plot_path}.png"
        try:
            # Add widgets on top of the canvas
            plot_show = tk.PhotoImage(file=plot_path)  # Replace with actual path
            plot_show_label = tk.Label(self.Canvas, image=plot_show, bg="#FFFFFF")
            plot_show_label.image = plot_show  # Keep a reference to the image
            self.Canvas.create_window(150, 900, window=plot_show_label, anchor=tk.NW)  # Position the l
        except FileNotFoundError:
            pass
 #--------------------------         
    def run_povray(self):
        command = "povray  " + self.file_pov_entry.get() 
        try:
            result = subprocess.run(command, capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                messagebox.showinfo("Provy Output", "provey finshed")
                self.view_png()
            else:
                messagebox.showerror("Error", f"{self.file_pov_entry.get()} not found")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        
 #--------------------------   
    def open_link(self, url):
        webbrowser.open_new(url)
 #--------------------------         
    def browse_vesta(self):
        filepath = filedialog.askopenfilename(title="Select VESTA executable")
        if filepath:
            self.vesta_path_entry.delete(0, tk.END)
            self.vesta_path_entry.insert(0, filepath)
 #-------------------------- 
    def run_vesta(self):
        vesta_path = self.vesta_path_entry.get()
        command =  vesta_path + " " + self.file_entry.get()
        
        try:
            result = subprocess.run(command, capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                messagebox.showinfo("vesta Output", "Vesta finshed")
            else:
                messagebox.showerror("Error", result.stderr)
        except Exception as e:
            messagebox.showerror("Error", str(e))
        # Save configuration
        self.save_config_vesta()
 #--------------------------         
    def save_config_vesta(self):
        base_path=self.tmp_path
        try:
            with open(os.path.join(base_path, "config_vesta.txt"), "w")  as file:
                file.write(self.vesta_path_entry.get() + "\n")
        
        except FileNotFoundError:
            pass
 #--------------------------     
    def load_config_vesta(self):
        base_path=self.tmp_path
        try:
            with open(os.path.join(base_path, "config_vesta.txt"), "r")  as file:
                lines = file.readlines()
                if lines:
                    self.vesta_path_entry.insert(0, lines[0].strip())
        except FileNotFoundError:
            pass
 #--------------------------         
    def browse_vdc(self):
        filepath = filedialog.askopenfilename(title="Select vdc executable")
        if filepath:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, filepath)    
 #--------------------------    
    def run_vdc(self):
        vdc_path = self.path_entry.get()
        selected_flags = ""
        for _, entries in self.flag_vars:
            for flag, (var, entry, check) in entries.items():
                if var.get():
                    selected_flags += flag + entry.get() + " "
        command = vdc_path + " " + selected_flags
         
        try:
            result = subprocess.run(command, capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                messagebox.showinfo("vdc Output", result.stdout)
            else:
                messagebox.showerror("Error", result.stderr)
        except Exception as e:
            messagebox.showerror("Error", str(e))
        # Save configuration
        self.save_config()
 #--------------------------        
    def save_config(self):
        base_path=self.tmp_path
        try:
            with open(os.path.join(base_path, "config_vdc.txt"), "w")  as file:
                file.write(self.path_entry.get() + "\n")
        except FileNotFoundError:
            pass
 #--------------------------    
    def load_config(self):
        base_path=self.tmp_path
        try:
            with open(os.path.join(base_path, "config_vdc.txt"), "r")  as file:
                lines = file.readlines()
                if lines:
                    self.path_entry.insert(0, lines[0].strip())
        except FileNotFoundError:
            pass
 #--------------------------        
            
            
            

## Assuming you have a root and tab setup somewhere else in your main application
#root = tk.Tk()
#root.title("Visual VDC")

#tab_control = ttk.Notebook(root)
#tab1 = ttk.Frame(tab_control)
#tab_control.add(tab1, text='Tab 1')

#VisuaVDC(tab1)

#tab_control.pack(expand=1, fill='both')

#root.mainloop()


    
