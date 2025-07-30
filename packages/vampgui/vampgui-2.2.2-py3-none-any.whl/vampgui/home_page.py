#!/usr/bin/env python3

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
from tkinter import ttk
import os
import sys
from vampgui.material import MainInputTab
from vampgui.vampire_console import RunVampire
from vampgui.plot_output import Plotmain
from vampgui.visualization import VisuaVDC
from vampgui.input_file import InputTab
from vampgui.version import __version__
from vampgui.ufc_file import ufcFile
from vampgui.cif_2_ucf import cif_2_ucf
from tkinter import messagebox




class VampireInputApp:
    def __init__(self, tab):
        self.tab = tab
        tab.title("Create Vampire Input")
        #tab.geometry("1200x800")  # Set window size to 800x600 pixels

        # Create a style for the notebook tabs
        style = ttk.Style()
        style.theme_create('colored_tabs', parent='alt', settings={
            'TNotebook.Tab': {
                'configure': {
                    'padding': [10, 5],
                    #'background': '#ADD8E6'  # Light blue color
                },
                'map': {
                    'background': [('selected', '#ADD8E6')],  # Light blue color when selected
                    'expand': [('selected', [1, 1, 1, 0])]
                }
            }
        })

        # Apply the new style
        style.theme_use('colored_tabs')

        self.notebook = ttk.Notebook(tab, style='TNotebook')
        self.notebook.pack(fill='both', expand=True, pady=15)

        # Create instances of tab classes
        self.tab0 = ttk.Frame(self.notebook)
        self.tab1 = ttk.Frame(self.notebook)
        self.tab2 = ttk.Frame(self.notebook)
        self.tab3 = ttk.Frame(self.notebook)
        self.tab4 = ttk.Frame(self.notebook)
        self.tab5 = ttk.Frame(self.notebook)
        self.tab6 = ttk.Frame(self.notebook)
        self.tab7 = ttk.Frame(self.notebook)
        # Add tabs
        self.notebook.add(self.tab0, text='Main Page')
        self.create_main_page(self.tab0)

        self.notebook.add(self.tab1, text='Cif to ucf')
        cif_2_ucf(self.tab1)
        self.notebook.add(self.tab2, text='ucf File')
        ufcFile(self.tab2)
        self.notebook.add(self.tab3, text='Material File')
        MainInputTab(self.tab3)

        self.notebook.add(self.tab4, text='Input File')
        InputTab(self.tab4)
        
        self.notebook.add(self.tab5, text='Run vampire')
        RunVampire(self.tab5)
        
        self.notebook.add(self.tab6, text='Plot setup')
        Plotmain(self.tab6)
        self.notebook.add(self.tab7, text='Visualization')
        VisuaVDC(self.tab7)
       
        # Create a menu bar
        self.menu_bar = tk.Menu(tab)
        tab.config(menu=self.menu_bar)

        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Main Page", command=lambda: self.notebook.select(self.tab0))
        file_menu.add_command(label="Cif to ucf ", command=lambda: self.notebook.select(self.tab1))
        file_menu.add_command(label="ucf File", command=lambda: self.notebook.select(self.tab2))
        file_menu.add_command(label="Material File", command=lambda: self.notebook.select(self.tab3))

        file_menu.add_command(label="Input File", command=lambda: self.notebook.select(self.tab4))
        file_menu.add_command(label="Run vampire", command=lambda: self.notebook.select(self.tab5))
        file_menu.add_command(label="Plots", command=lambda: self.notebook.select(self.tab6))
        file_menu.add_command(label="Visualization", command=lambda: self.notebook.select(self.tab7))
        
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=tab.quit)
        
 

    def create_main_page(self, parent):
        
        # Update the image path
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
       
       # Create a canvas to hold the background image

    
        canvas = tk.Canvas(parent, width=1200, height=800)
        canvas.pack(fill='both', expand=True)

        # Load the background image 
        background_image_path = os.path.join(base_path, "background.png")
        background_image = tk.PhotoImage(file=background_image_path)  # Replace with actual path
        canvas.create_image(0, 0, anchor=tk.NW, image=background_image)
        canvas.image = background_image
        
        logo_image_path = os.path.join(base_path, "logo.png")
        logo = tk.PhotoImage(file=logo_image_path)  # Replace with actual path
        logo_label = tk.Label(canvas, image=logo, bg="#FFFFFF")
        logo_label.image = logo  # Keep a reference to the image
        canvas.create_window(300, 100, window=logo_label)  # Position the logo

        version =f"version:{__version__}"
        canvas.create_text(450, 175, text=version, justify=tk.LEFT, font="calibri 14 bold", fill="white") 
        

        
        # Description 
        description_text = "GUI interface to:"
        canvas.create_text(540, 200, text=description_text, justify=tk.LEFT, font="calibri 22 bold", fill="white") 
        #description_text = "https://vampire.york.ac.uk/"
        #canvas.create_text(700, 300, text=description_text, justify=tk.LEFT, font="calibri 14 bold", fill="white") 
        # Buttons to switch to other tabs

        btn_material_file = tk.Button(canvas, text="Cif to ucf", width=20, command=lambda: self.notebook.select(self.tab1))
        canvas.create_window(250, 250, window=btn_material_file)  # Position the button

        btn_input_file = tk.Button(canvas,    text="ucf File", width=20, command=lambda: self.notebook.select(self.tab2))
        canvas.create_window(250, 300, window=btn_input_file)  # Position the button

        btn_material_file = tk.Button(canvas, text="Material File", width=20, command=lambda: self.notebook.select(self.tab3))
        canvas.create_window(250, 350, window=btn_material_file)  # Position the button

        btn_input_file = tk.Button(canvas,    text="Input File", width=20, command=lambda: self.notebook.select(self.tab4))
        canvas.create_window(250, 400, window=btn_input_file)  # Position the button
        btn_input_file = tk.Button(canvas,    text="Run vampire", width=20, command=lambda: self.notebook.select(self.tab5))
        canvas.create_window(250, 450, window=btn_input_file)  # Position the button
        btn_input_file = tk.Button(canvas,    text="Plot output", width=20, command=lambda: self.notebook.select(self.tab6))
        canvas.create_window(250, 500, window=btn_input_file)  # Position the button
        btn_input_file = tk.Button(canvas,    text="Visualization", width=20, command=lambda: self.notebook.select(self.tab7))
        canvas.create_window(250, 550, window=btn_input_file)  # Position the button
        
        
        
        description_text = """ Copyright (C) 06-2024 G. Benabdellah
            Departement of physic
            University of Tiaret , Algeria
            E-mail ghlam.benabdellah@gmail.com
            VAMPgui interface to VAMPIRE 
            First creation 28-05-2024
            License: GNU General Public License v3.0
            This program is free software: you can redistribute it and/or modify
            it under the terms of the GNU General Public License as published by
            the Free Software Foundation, either version 3 of the License, or
            (at your option) any later version.
            This program is distributed in the hope that it will be useful,
            but WITHOUT ANY WARRANTY; without even the implied warranty of
            MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
            GNU General Public License for more details.
            You should have received a copy of the GNU General Public License
            along with this program. If not, see <http://www.gnu.org/licenses/>."""
        canvas.create_text(250,750, text=description_text, justify=tk.LEFT, font="calibri 9 bold" , fill="white")
        
   

#def main():
    #root = tk.Tk()
    #app = VampireInputApp(root)
    #root.mainloop()

#if __name__ == "__main__":
    #main()

