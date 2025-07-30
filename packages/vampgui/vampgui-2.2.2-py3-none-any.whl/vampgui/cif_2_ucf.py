import tkinter as tk
from tkinter import filedialog, messagebox
import logging
from pymatgen.core import Structure
from pymatgen.analysis.magnetism.analyzer import CollinearMagneticStructureAnalyzer
import pymatgen.analysis.magnetism.analyzer as ana
from vampgui.vampire_pymatgen import VampireInput
from vampgui.helpkey import  show_help
from vampgui.file_io import InputFileViewer

class cif_2_ucf:
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
        #tk.Button(button_frame, bg='cyan', text="Save UCF File", command=self.generate_ucf_file).grid(row=0, column=0, padx=5, pady=5,sticky="w")
        tk.Button(button_frame, bg='#ffff99', text="View/Edit sample.ucf", command=self.open_sample_file).grid(row=0, column=3,padx=5, pady=5,sticky="w")

        tk.Button(button_frame,  text="help", command=lambda kw="ufc_file": show_help(kw)).grid(row=0, column=5,padx=5, pady=25,sticky="w")


        self.mode = tk.LabelFrame(frame, text="Create ucf from cif file: (note: this interface is still under test ..) ", font=("Helvetica", 14, "bold"))
        self.mode.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=8, pady=(8, 8))
        # Filename


        # CIF file selection
        self.cif_label = tk.Label(self.mode, text="CIF File:")
        self.cif_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.cif_entry = tk.Entry(self.mode, width=50)
        self.cif_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        self.cif_button = tk.Button(self.mode, text="Browse", command=self.load_cif_file)
        self.cif_button.grid(row=0, column=2, padx=10, pady=10)

        # Magnetic moments
        self.magmom_frame = tk.Frame(self.mode)
        self.magmom_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

        self.magmom_label = tk.Label(self.magmom_frame, text="Magnetic Moments for Elements:")
        self.magmom_label.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="w")

        self.magmom_entries = {}  # To store magnetic moment entry widgets

        # Energy input
        self.energy_label = tk.Label(self.mode, text="Total Energy (eV) of Ferromagnetic Configuration (from DFT) :")
        self.energy_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")

        self.energy_ferro_entry = tk.Entry(self.mode, width=20)
        self.energy_ferro_entry.grid(row=2, column=1,columnspan=3, padx=10, pady=10)

        self.energy_label_antiferro = tk.Label(self.mode, text="Total Energy (eV)of Antiferromagnetic Configuration(from DFT) :")
        self.energy_label_antiferro.grid(row=3, column=0, padx=10, pady=10, sticky="w")

        self.energy_antiferro_entry = tk.Entry(self.mode, width=20)
        self.energy_antiferro_entry.grid(row=3, column=1,columnspan=3, padx=10, pady=10)

        # Submit button
        self.submit_button = tk.Button(self.mode, text="Generate Vampire Input", command=self.generate_vampire_input)
        self.submit_button.grid(row=4, column=0, columnspan=3, padx=10, pady=10)

        self.mode = tk.LabelFrame(frame, text="Log file: ", font=("Helvetica", 14, "bold"))
        self.mode.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=8, pady=(8, 8))
        # Filename

        # Logging Area (Text widget)
        self.log_text = tk.Text(self.mode, height=30, width=150, bg='lightgrey', state='disabled')
        self.log_text.grid(row=1, column=0, columnspan=6, padx=10, pady=10)

        self.structure = None
        self.setup_logging()

        # Create and configure the custom handler for the text widget



    # Add buttons for testing log levels

    def open_sample_file(self):
        try:
            # Open file dialog to select CIF file
            file_path = filedialog.askopenfilename(filetypes=[("ufc Files", "*.ucf")])
            if file_path:
                InputFileViewer(file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load  file: {e}")

    def setup_logging(self):
        handler = TextHandler(self.log_text)
        handler.setLevel(logging.INFO)  # Set logging level to INFO
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        ## Configure the tab logger to use this handler
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)  # Allow all log levels
        logger.addHandler(handler)

    def load_cif_file(self):
        try:

            # Open file dialog to select CIF file
            file_path = filedialog.askopenfilename(filetypes=[("CIF Files", "*.cif")])
            if file_path:
                self.cif_entry.delete(0, tk.END)
                self.cif_entry.insert(0, file_path)

                # Load the structure from CIF file
                self.structure = Structure.from_file(file_path)
                messagebox.showinfo("Info", "Structure loaded successfully")
                logging.info(f"Structure loaded successfully {file_path}")
                logging.info(f"{self.structure}")

                # Get unique elements and create magnetic moment inputs
                unique_elements = self.structure.symbol_set
                for widget in self.magmom_frame.winfo_children():
                    widget.destroy()  # Clear previous entries if any

                self.magmom_label = tk.Label(self.magmom_frame, text="Magnetic Moments for Elements:")
                self.magmom_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

                self.magmom_entries = {}  # Clear previous entries
                for i, element in enumerate(unique_elements):
                    label = tk.Label(self.magmom_frame, text=f"Magnetic Moment for {element}:")
                    label.grid(row=i+1, column=0, padx=10, pady=5, sticky="w")

                    # Create StringVar for the entry to handle default values
                    magmom_var = tk.StringVar()

                    # Set default magnetic moment if available
                    if element in ana.DEFAULT_MAGMOMS:
                        default_magmom = ana.DEFAULT_MAGMOMS[element]
                        magmom_var.set(default_magmom)  # Insert the default value
                        logging.info(f"Default Magnetic Moments for {element}: {default_magmom} uB")
                    else:
                        logging.info(f"Default Magnetic Moments for {element}: 0 uB ")
                        magmom_var.set(0)

                    entry = tk.Entry(self.magmom_frame, width=10, textvariable=magmom_var)
                    entry.grid(row=i+1, column=1, padx=10, pady=5, sticky="w")

                    # Store the StringVar in a dictionary for later use
                    self.magmom_entries[element] = magmom_var

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CIF file: {e}")




    def generate_vampire_input(self):
        try:
            ## Clear the log area before generating new Vampire input
            #self.log_text.config(state='normal')  # Enable the text widget
            #self.log_text.delete(1.0, tk.END)  # Clear all the text in the log area
            #self.log_text.config(state='disabled')  # D
            # Get magnetic moments from user input
            magmom_dict = {}
            for element, entry in self.magmom_entries.items():
                try:
                    magmom_dict[element] = float(entry.get())
                except ValueError:
                    messagebox.showerror("Error", f"Invalid magnetic moment for {element}")
                    return

            # Assign magmom values to the structure based on user input
            magmoms = [magmom_dict[site.specie.symbol] for site in self.structure]
            self.structure.add_site_property('magmom', magmoms)

            # Get energy values
            try:
                energy_ferro = float(self.energy_ferro_entry.get())
                energy_antiferro = float(self.energy_antiferro_entry.get())
            except ValueError:
                messagebox.showerror("Error", "Invalid energy values")
                return

            # Create ferromagnetic configuration
            analyzer = CollinearMagneticStructureAnalyzer(self.structure)
            ordered_structure_ferro = analyzer.get_structure_with_spin()

            # Create antiferromagnetic configuration
            for i in range(len(self.structure)):
                self.structure[i].properties['magmom'] *= (-1) if i % 2 == 1 else 1  # Flip spins for alternating sites

            analyzer_antiferro = CollinearMagneticStructureAnalyzer(self.structure)
            ordered_structure_antiferro = analyzer_antiferro.get_structure_with_spin()

            # Initialize VampireCaller with the two ordered structures and corresponding energies
            ordered_structures = [ordered_structure_ferro, ordered_structure_antiferro]
            energies = [energy_ferro, energy_antiferro]
            vc = VampireInput(ordered_structures, energies=energies)





            messagebox.showinfo("Success", "Vampire input generated successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate Vampire input: {e}")


class TextHandler(logging.Handler):
    """A custom logging handler that writes log messages to a Tkinter Text widget"""
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
        self.setup_tags()


    def emit(self, record):
        """Emit a log record and display it in the Text widget"""
        msg = self.format(record)
        log_level = record.levelno

        self.text_widget.config(state='normal')

        # Customizing appearance based on the log level
        if log_level >= logging.ERROR:
            self.text_widget.insert(tk.END, msg + '\n', 'error')
        elif log_level >= logging.WARNING:
            self.text_widget.insert(tk.END, msg + '\n', 'warning')
        else:
            self.text_widget.insert(tk.END, msg + '\n', 'info')

        self.text_widget.config(state='disabled')
        self.text_widget.yview(tk.END)  # Scroll to the end

    def setup_tags(self):
        """Define tags for log levels (for colors, styles, etc.)"""
        self.text_widget.tag_config('info', foreground='black')  # Info level logs
        self.text_widget.tag_config('warning', foreground='blue' ,font=('Arial', 10, 'bold'))  # Warning level logs
        self.text_widget.tag_config('error', foreground='red', font=('Arial', 10, 'bold'))  # Error level logs

#if __name__ == "__main__":
    #tab = tk.Tk()
    #app = ucf_2_cif(tab)
    #tab.mainloop()
