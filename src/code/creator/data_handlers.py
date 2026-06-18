from tkinter import filedialog, messagebox
import json

class CreatorDataHandlers:
    def save_grid_template(self):
        template = []
        for row in self.variant_rows:
            template.append({
                "char": row["char"].get(),
                "job": row["job"].get(),
                "id": row["id"].get(),
                "outfits": row["outfits"].get()
            })
        
        data = {
            "global_stats": self.var_global_stats.get(),
            "global_boxes": self.var_global_boxes.get(),
            "generate_imgs": self.var_generate_imgs.get(),
            "rows": template
        }
        
        fp = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if not fp: return
        
        try:
            with open(fp, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            messagebox.showinfo("Saved", "Template saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save template: {e}")

    def load_grid_template(self):
        fp = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not fp: return
        
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if "global_stats" in data: self.var_global_stats.set(data["global_stats"])
            if "global_boxes" in data: self.var_global_boxes.set(data["global_boxes"])
            if "generate_imgs" in data: self.var_generate_imgs.set(data["generate_imgs"])
            
            if "rows" in data:
                # Clear existing rows
                for row in list(self.variant_rows):
                    self.remove_variant_row(row["frame"], row)
                    
                for r in data["rows"]:
                    self.add_variant_row(r.get("char", ""), r.get("job", ""), r.get("id", ""), r.get("outfits", ""))
                    
            messagebox.showinfo("Loaded", "Template loaded successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load template: {e}")

    def import_reference(self):
        # Optionally allow importing the old txt files into the grid if possible, 
        # but for now we'll just say it's not supported in the new grid format
        messagebox.showinfo("Not Supported", "TXT import is no longer supported in the grid layout. Please use Load JSON template instead.")

    def log(self, msg):
        print(f"[FashionCreator] {msg}")
