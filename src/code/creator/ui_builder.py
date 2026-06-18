import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os

from code.creator.constants import CHARACTERS, JOBS

class CreatorUIBuilder:
    def build_ui(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Main container
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # State Variables
        self.current_step = 1
        
        # Grid state
        self.variant_rows = [] # List of dicts: char, job, start_id, outfit_names
        
        # Step 2 data
        self.path_contributions = {} # Map combination string -> list of part dicts
        
        # Global Settings
        self.var_global_stats = tk.BooleanVar(value=True)
        self.var_global_boxes = tk.BooleanVar(value=False)
        self.var_generate_imgs = tk.BooleanVar(value=True)
        
        # Step 3 Settings
        self.var_sep_tables = tk.BooleanVar(value=False)
        self.var_sep_sets = tk.BooleanVar(value=False)
        
        # Frames
        self.frame_step1 = ttk.Frame(self.main_container)
        self.frame_step2 = ttk.Frame(self.main_container)
        self.frame_step3 = ttk.Frame(self.main_container)
        
        self.build_step1()
        self.build_step2()
        self.build_step3()
        
        self.show_step(1)

    def show_step(self, step):
        self.frame_step1.pack_forget()
        self.frame_step2.pack_forget()
        self.frame_step3.pack_forget()
        
        if step == 1:
            self.frame_step1.pack(fill=tk.BOTH, expand=True)
        elif step == 2:
            self.refresh_step2()
            self.frame_step2.pack(fill=tk.BOTH, expand=True)
        elif step == 3:
            self.frame_step3.pack(fill=tk.BOTH, expand=True)
            
        self.current_step = step

    def build_step1(self):
        lbl_title = tk.Label(self.frame_step1, text="Step 1: Identity & Equipped Items", font=("Arial", 14, "bold"))
        lbl_title.pack(pady=(10, 20))
        
        # Identity Frame
        lf_id = ttk.LabelFrame(self.frame_step1, text="Current Identity")
        lf_id.pack(fill=tk.X, padx=20, pady=5)
        
        row_frame = ttk.Frame(lf_id)
        row_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(row_frame, text="Character:").grid(row=0, column=0, padx=5, sticky=tk.E)
        self.var_char = tk.StringVar(value="Fox")
        ttk.Combobox(row_frame, textvariable=self.var_char, values=CHARACTERS, state="readonly", width=15).grid(row=0, column=1, padx=5)
        
        ttk.Label(row_frame, text="Job:").grid(row=0, column=2, padx=5, sticky=tk.E)
        self.var_job = tk.StringVar(value="3rd Job")
        ttk.Combobox(row_frame, textvariable=self.var_job, values=JOBS, state="readonly", width=15).grid(row=0, column=3, padx=5)
        
        ttk.Label(row_frame, text="Color Name:").grid(row=0, column=4, padx=5, sticky=tk.E)
        self.var_color = tk.StringVar(value="Golden")
        ttk.Entry(row_frame, textvariable=self.var_color, width=15).grid(row=0, column=5, padx=5)
        
        ttk.Label(row_frame, text="Start ID:").grid(row=0, column=6, padx=5, sticky=tk.E)
        self.var_start_id = tk.StringVar(value="999999")
        ttk.Entry(row_frame, textvariable=self.var_start_id, width=10).grid(row=0, column=7, padx=5)
        
        if hasattr(self, 'init_data') and self.init_data:
            if "id" in self.init_data: self.var_start_id.set(self.init_data["id"])
            if "color" in self.init_data: self.var_color.set(self.init_data["color"])
        
        if hasattr(self, 'previewer_app') and self.previewer_app:
            if hasattr(self.previewer_app, 'character_var'): self.var_char.set(self.previewer_app.character_var.get() or "Fox")
            if hasattr(self.previewer_app, 'job_var'): self.var_job.set(self.previewer_app.job_var.get() or "3rd Job")
                
        # Split frame for Preview and Added Sets
        split_frame = ttk.Frame(self.frame_step1)
        split_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        # Equipped Items Preview
        lf_preview = ttk.LabelFrame(split_frame, text="Currently Equipped Items")
        lf_preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        columns = ("Layer", "Palette")
        self.tree_equipped = ttk.Treeview(lf_preview, columns=columns, show="headings", height=8)
        self.tree_equipped.heading("Layer", text="Layer Name")
        self.tree_equipped.heading("Palette", text="Palette File")
        self.tree_equipped.column("Layer", width=150)
        self.tree_equipped.column("Palette", width=400)
        
        scroll_y = ttk.Scrollbar(lf_preview, orient="vertical", command=self.tree_equipped.yview)
        self.tree_equipped.configure(yscrollcommand=scroll_y.set)
        
        self.tree_equipped.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # Sets Added Preview
        lf_added = ttk.LabelFrame(split_frame, text="Sets Added to Session")
        lf_added.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        cols_added = ("Combo", "Parts")
        self.tree_added = ttk.Treeview(lf_added, columns=cols_added, show="headings", height=8)
        self.tree_added.heading("Combo", text="Combination Name")
        self.tree_added.heading("Parts", text="Parts")
        self.tree_added.column("Combo", width=300)
        self.tree_added.column("Parts", width=100)
        
        scroll_added = ttk.Scrollbar(lf_added, orient="vertical", command=self.tree_added.yview)
        self.tree_added.configure(yscrollcommand=scroll_added.set)
        
        self.tree_added.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scroll_added.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # Add Set Button
        btn_frame = ttk.Frame(self.frame_step1)
        btn_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(btn_frame, text="Add Set to Session", command=self.add_current_set).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Refresh Equipped", command=self.refresh_equipped_view).pack(side=tk.LEFT, padx=5)
        
        # Global Configs
        lf_globals = ttk.LabelFrame(self.frame_step1, text="Global Configuration")
        lf_globals.pack(fill=tk.X, padx=20, pady=5)
        
        ttk.Checkbutton(lf_globals, text="Configure Stats for these items?", variable=self.var_global_stats).grid(row=0, column=0, padx=10, pady=5)
        ttk.Checkbutton(lf_globals, text="Generate Boxes for these items?", variable=self.var_global_boxes).grid(row=0, column=1, padx=10, pady=5)
        ttk.Checkbutton(lf_globals, text="Generate Imgs+Pals in folder?", variable=self.var_generate_imgs).grid(row=0, column=2, padx=10, pady=5)
        
        # Bottom Navigation
        nav_frame = ttk.Frame(self.frame_step1)
        nav_frame.pack(fill=tk.X, padx=20, pady=20)
        ttk.Button(nav_frame, text="Next -> Review Sets", command=lambda: self.show_step(2)).pack(side=tk.RIGHT, padx=5)
        
        # Initial refresh
        self.refresh_equipped_view()
        self.refresh_added_sets_view()
        
    def refresh_added_sets_view(self):
        if hasattr(self, 'tree_added'):
            for item in self.tree_added.get_children():
                self.tree_added.delete(item)
            for combo_name, data in getattr(self, 'path_contributions', {}).items():
                self.tree_added.insert("", "end", values=(combo_name, str(len(data.get("parts", [])))))

    def refresh_equipped_view(self):
        for item in self.tree_equipped.get_children():
            self.tree_equipped.delete(item)
            
        if not hasattr(self, 'previewer_app') or not self.previewer_app:
            return
            
        if hasattr(self.previewer_app, 'palette_layers'):
            for layer in self.previewer_app.palette_layers:
                if getattr(layer, 'active', False) and getattr(layer, 'palette_path', None):
                    layer_name = getattr(layer, 'name', 'Unknown')
                    ptype = getattr(layer, 'palette_type', '')
                    disp_name = layer_name
                    if ptype == 'hair':
                        disp_name = "Hair"
                    elif ptype == '3rd_job_base':
                        disp_name = "3rd Job Base"
                    elif ptype:
                        try:
                            char = self.previewer_app.current_character
                            disp_name = self.previewer_app.get_fashion_type_name(char, ptype)
                        except Exception:
                            disp_name = ptype.replace("fashion_", "Fashion ").replace("_", " ").title()
                            
                    path = getattr(layer, 'palette_path', '')
                    self.tree_equipped.insert("", "end", values=(disp_name, os.path.basename(path)))

    def add_current_set(self):
        char = self.var_char.get()
        job = self.var_job.get()
        color = self.var_color.get()
        try:
            start_id = int(self.var_start_id.get())
        except ValueError:
            start_id = 999999
            
        combo_name = f"{char} - {job} - {color}"
        
        if combo_name in self.path_contributions:
            if not messagebox.askyesno("Overwrite?", f"Set '{combo_name}' already exists. Overwrite?"):
                return
                
        parts = self._auto_populate_parts(char, job, color, start_id)
        
        self.path_contributions[combo_name] = {
            "set_id": start_id,
            "parts": parts,
            "char": char,
            "job": job,
            "color": color
        }
        
        self.refresh_added_sets_view()
        messagebox.showinfo("Success", f"Added '{combo_name}' with {len(parts)} parts.")
    def build_step2(self):
        lbl_title = tk.Label(self.frame_step2, text="Step 2: Review Generated Sets", font=("Arial", 14, "bold"))
        lbl_title.pack(pady=(10, 10))
        
        self.notebook_step2 = ttk.Notebook(self.frame_step2)
        self.notebook_step2.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        nav_frame = ttk.Frame(self.frame_step2)
        nav_frame.pack(fill=tk.X, padx=20, pady=20)
        ttk.Button(nav_frame, text="<- Back to Setup", command=lambda: self.show_step(1)).pack(side=tk.LEFT, padx=5)
        
        # Save and Load for session sets
        ttk.Button(nav_frame, text="Save Sets", command=self.save_grid_template).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="Load Sets", command=self.load_grid_template).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(nav_frame, text="Next -> Acquisition Hub", command=lambda: self.show_step(3)).pack(side=tk.RIGHT, padx=5)

    def refresh_step2(self):
        # Clear existing tabs
        for tab in self.notebook_step2.tabs():
            self.notebook_step2.forget(tab)
            
        if not self.path_contributions:
            frame = ttk.Frame(self.notebook_step2)
            self.notebook_step2.add(frame, text="No Sets Added")
            lbl = ttk.Label(frame, text="You haven't added any sets yet!\n\nGo back to Setup and click 'Add Set to Session'.", font=("Arial", 12), justify=tk.CENTER)
            lbl.pack(expand=True, fill=tk.BOTH, pady=50)
            return
            
            
        for combo_name, data in self.path_contributions.items():
            char = data["char"]
            job = data["job"]
            outfit = data["color"]
            tab_name = f"{char[:3]} {job[:3]} {outfit}"
            self._build_combo_tab(tab_name, combo_name)

    def _auto_populate_parts(self, char, job, outfit, start_id):
        parts = []
        # If we have previewer app, we can extract active palettes
        if hasattr(self, 'previewer_app') and self.previewer_app:
            equipped = []
            if hasattr(self.previewer_app, 'palette_layers'):
                for layer in self.previewer_app.palette_layers:
                    if getattr(layer, 'active', False) and getattr(layer, 'palette_path', None):
                        equipped.append(layer)
            
            if not equipped:
                parts.append({
                    "type": "Zip-up Coat", "id": start_id, 
                    "part_file": "data\\wear_parts\\chrXXX_wYYY",
                    "file_name": "data\\item\\chrXXX_fashion_1_c",
                    "bundle": "0", "cmt_file": "data\\item\\chrXXX_view_illu",
                    "cmt_bundle": "0", "name": f"{char[:3]} {outfit} Coat",
                    "comment": "Customized by Author", "use": "Fashion clothing exclus"
                })
            else:
                for idx, layer in enumerate(equipped):
                    layer_name = getattr(layer, 'name', 'Unknown')
                    ptype = getattr(layer, 'palette_type', '')
                    disp_name = layer_name
                    if ptype == 'hair':
                        disp_name = "Hair"
                    elif ptype == '3rd_job_base':
                        disp_name = "3rd Job Base"
                    elif ptype:
                        try:
                            char_id = self.previewer_app.current_character
                            disp_name = self.previewer_app.get_fashion_type_name(char_id, ptype)
                        except Exception:
                            disp_name = ptype.replace("fashion_", "Fashion ").replace("_", " ").title()
                            
                    part_name = f"{char[:3]} {outfit} {disp_name}"
                    pf = getattr(layer, 'palette_path', "")
                    if pf.startswith("data\\wear_parts\\") or pf.startswith("data/wear_parts/"):
                        pf = pf
                    else:
                        pf = f"data\\wear_parts\\{os.path.basename(pf)}"
                    # Convert to .nri for file_name
                    fn = pf.replace(".pal", ".nri").replace(".bmp", ".nri")
                    
                    parts.append({
                        "type": disp_name, "id": start_id - idx,
                        "part_file": pf,
                        "file_name": fn,
                        "bundle": "0", "cmt_file": fn.replace("_fashion_", "_view_illu_").replace("_hair_", "_view_illu_"),
                        "cmt_bundle": "0", "name": part_name,
                        "comment": "Customized by Author", "use": "Fashion clothing exclus"
                    })
        return parts

    def _build_combo_tab(self, tab_name, combo_name):
        frame = ttk.Frame(self.notebook_step2)
        self.notebook_step2.add(frame, text=tab_name)
        
        # Header
        hdr_frame = ttk.Frame(frame)
        hdr_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(hdr_frame, text=f"Combination: {combo_name}", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        
        def add_remaining():
            data = self.path_contributions[combo_name]
            parts = data["parts"]
            char = data["char"]
            color = data["color"]
            
            last_id = data["set_id"] - len(parts)
            if parts:
                try:
                    last_id = int(parts[-1]["id"]) - 1
                except: pass
                
            parts.append({
                "type": "New Part", "id": last_id,
                "part_file": "", "file_name": "", "bundle": "0", "cmt_file": "",
                "cmt_bundle": "0", "name": f"{char[:3]} {color} New Part",
                "comment": "Added manually", "use": "Fashion clothing exclus"
            })
            self.refresh_step2()
            
        ttk.Button(hdr_frame, text="+ Add Remaining Pieces", command=add_remaining).pack(side=tk.RIGHT)
        
        id_frame = ttk.Frame(frame)
        id_frame.pack(anchor=tk.W, padx=10, pady=5)
        ttk.Label(id_frame, text="Set ID:").pack(side=tk.LEFT)
        var_set_id = tk.StringVar(value=str(self.path_contributions[combo_name]["set_id"]))
        ttk.Entry(id_frame, textvariable=var_set_id, width=15).pack(side=tk.LEFT, padx=5)
        self.path_contributions[combo_name]["var_set_id"] = var_set_id
        
        # Grid
        grid_container = tk.Canvas(frame, highlightthickness=0)
        # Fix Canvas Background for Dark Mode
        bg_color = "#1E1E1E" if getattr(getattr(self, 'previewer_app', self), 'dark_mode', False) else "white"
        grid_container.configure(bg=bg_color)
        grid_scrollbar = ttk.Scrollbar(frame, orient="vertical", command=grid_container.yview)
        grid_frame = ttk.Frame(grid_container)
        
        grid_frame.bind("<Configure>", lambda e: grid_container.configure(scrollregion=grid_container.bbox("all")))
        grid_container.create_window((0, 0), window=grid_frame, anchor="nw")
        grid_container.configure(yscrollcommand=grid_scrollbar.set)
        
        grid_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        grid_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        headers = ["Part Type", "ID", "PartFileName", "FileName", "BundleNum", "CmtFileName", "CmtBundleNum", "Name", "Comment", "Use"]
        for col, h in enumerate(headers):
            ttk.Label(grid_frame, text=h, font=("Arial", 9, "bold")).grid(row=0, column=col, padx=2, sticky=tk.W)
            
        # Draw parts
        for row_idx, part in enumerate(self.path_contributions[combo_name]["parts"]):
            r = row_idx + 1
            part_vars = {}
            for col, key in enumerate(["type", "id", "part_file", "file_name", "bundle", "cmt_file", "cmt_bundle", "name", "comment", "use"]):
                v = tk.StringVar(value=str(part.get(key, "")))
                part_vars[key] = v
                w = 15 if key in ["type", "name", "comment", "use"] else 10 if key in ["id", "bundle", "cmt_bundle"] else 20
                ttk.Entry(grid_frame, textvariable=v, width=w).grid(row=r, column=col, padx=2, pady=2)
            self.path_contributions[combo_name]["parts"][row_idx]["_vars"] = part_vars

    def save_grid_template(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Session Sets"
        )
        if not file_path:
            return
            
        data_to_save = {}
        for combo, data in self.path_contributions.items():
            # Extract current values from StringVars
            parts = []
            for part in data["parts"]:
                part_dict = {}
                for k, v in part.items():
                    if k != "_vars":
                        part_dict[k] = part["_vars"][k].get() if "_vars" in part and k in part["_vars"] else v
                parts.append(part_dict)
                
            data_to_save[combo] = {
                "char": data["char"],
                "job": data["job"],
                "color": data["color"],
                "set_id": data.get("var_set_id", tk.StringVar(value=str(data["set_id"]))).get(),
                "parts": parts
            }
            
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, indent=4)
            messagebox.showinfo("Success", "Session Sets saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save:\n{e}")

    def load_grid_template(self):
        file_path = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Session Sets"
        )
        if not file_path:
            return
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)
                
            self.path_contributions = {}
            for combo, data in loaded_data.items():
                # Convert set_id to int if possible, else keep string
                try:
                    set_id = int(data.get("set_id", 999999))
                except:
                    set_id = data.get("set_id", 999999)
                    
                self.path_contributions[combo] = {
                    "char": data.get("char", "Fox"),
                    "job": data.get("job", "3rd Job"),
                    "color": data.get("color", "Golden"),
                    "set_id": set_id,
                    "parts": data.get("parts", [])
                }
                
            self.refresh_step2()
            messagebox.showinfo("Success", "Session Sets loaded successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load:\n{e}")

    def build_step3(self):
        lbl_title = tk.Label(self.frame_step3, text="Step 3: Acquisition Hub", font=("Arial", 14, "bold"))
        lbl_title.pack(pady=(10, 5))
        
        self.lbl_acq_combo = tk.Label(self.frame_step3, text="Select acquisition methods for all your generated sets.", font=("Arial", 10))
        self.lbl_acq_combo.pack(pady=(5, 20))
        
        # Buttons frame
        btn_frame = ttk.Frame(self.frame_step3)
        btn_frame.pack(pady=10)
        
        # Checkboxes instead of 3 Done buttons
        chk_frame = ttk.Frame(self.frame_step3)
        chk_frame.pack(pady=10)
        ttk.Checkbutton(chk_frame, text="Separate Sets", variable=self.var_sep_sets, command=self._on_sep_sets_changed).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(chk_frame, text="Separate Tables", variable=self.var_sep_tables, command=self._on_sep_tables_changed).pack(side=tk.LEFT, padx=10)
        
        acq_frame = ttk.LabelFrame(self.frame_step3, text="Acquisition Methods")
        acq_frame.pack(pady=10, padx=20, fill=tk.X)
        
        self.var_acq_myshop = tk.BooleanVar(value=True)
        self.var_acq_compound = tk.BooleanVar(value=False)
        self.var_acq_exchange = tk.BooleanVar(value=False)
        self.var_acq_shop = tk.BooleanVar(value=False)
        
        ttk.Checkbutton(acq_frame, text="MyShop", variable=self.var_acq_myshop).pack(side=tk.LEFT, padx=20, pady=10)
        ttk.Checkbutton(acq_frame, text="Compound", variable=self.var_acq_compound).pack(side=tk.LEFT, padx=20, pady=10)
        ttk.Checkbutton(acq_frame, text="Exchange", variable=self.var_acq_exchange).pack(side=tk.LEFT, padx=20, pady=10)
        ttk.Checkbutton(acq_frame, text="Regular Shop", variable=self.var_acq_shop).pack(side=tk.LEFT, padx=20, pady=10)
        

        
        gen_frame = ttk.Frame(self.frame_step3)
        gen_frame.pack(pady=10)
        self.btn_generate = ttk.Button(gen_frame, text="Generate (Combined File)", width=35, command=self.run_generation_flow)
        self.btn_generate.pack()
        
        ttk.Button(self.frame_step3, text="<- Back to Tabs", command=lambda: self.show_step(2)).pack(pady=20)

    def _on_sep_sets_changed(self):
        if self.var_sep_sets.get():
            self.var_sep_tables.set(True)
            self.btn_generate.config(text="Generate (Separate Sets)")
        else:
            self._on_sep_tables_changed()
            
    def _on_sep_tables_changed(self):
        if self.var_sep_sets.get() and not self.var_sep_tables.get():
            self.var_sep_tables.set(True)
        
        if self.var_sep_sets.get():
            self.btn_generate.config(text="Generate (Separate Sets)")
        elif self.var_sep_tables.get():
            self.btn_generate.config(text="Generate (Separate Tables)")
        else:
            self.btn_generate.config(text="Generate (Combined File)")
