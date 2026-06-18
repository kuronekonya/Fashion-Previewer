import os
import datetime
from tkinter import messagebox
from collections import OrderedDict

from code.creator.constants import JOBS, CHR_FLAGS

def _fashion_detect_slot(name):
    n = name.lower()
    if "hat" in n or "hair" in n or "hood" in n: return 2, 8
    elif "mask" in n or "glasses" in n or "patch" in n or "ear" in n: return 2, 9
    elif "cloak" in n or "bag" in n or "wing" in n or "cape" in n: return 2, 10
    elif "coat" in n or "shirt" in n or "wrap" in n or "robe" in n or "top" in n: return 2, 12
    elif "pants" in n or "shorts" in n or "skirt" in n or "bottom" in n: return 2, 13
    elif "shoes" in n or "boots" in n or "foot" in n: return 2, 15
    elif "glove" in n or "wrist" in n or "bracelet" in n: return 2, 14
    elif "ring" in n: return 2, 16
    elif "pet" in n: return 2, 17
    elif "sword" in n or "blade" in n or "weapon" in n or "staff" in n or "gun" in n or "dagger" in n: return 2, 1
    elif "shield" in n: return 2, 2
    return 2, 12 # Default coat

class CreatorGenerators:
    def add_to_buffer(self, color, filename, content):
        if not color: color = "Default"
        if not hasattr(self, "export_buffers"):
            self.export_buffers = OrderedDict()
            self.combined_buffer = OrderedDict()
        if color not in self.export_buffers:
            self.export_buffers[color] = OrderedDict()
        if filename not in self.export_buffers[color]:
            self.export_buffers[color][filename] = []
        self.export_buffers[color][filename].append(content)
        
        if filename not in self.combined_buffer:
            self.combined_buffer[filename] = []
        self.combined_buffer[filename].append(content)

    def write_export_buffers(self):
        separate_sets = self.var_sep_sets.get()
        separate_tables = self.var_sep_tables.get()
        generate_imgs = self.var_generate_imgs.get()
        
        colors = list(self.export_buffers.keys())
        if not colors:
            return
            
        root_dir = getattr(getattr(self, 'previewer_app', self), 'root_dir', os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        exports_dir = os.path.join(root_dir, "exports")
        base_export_dir = os.path.join(exports_dir, "custom_pals")
        libconfig_dir = os.path.join(exports_dir, "libconfig")
        sql_dir = os.path.join(exports_dir, "sql")
        os.makedirs(base_export_dir, exist_ok=True)
        os.makedirs(libconfig_dir, exist_ok=True)
        os.makedirs(sql_dir, exist_ok=True)
            
        if separate_sets:
            for combo_name in colors:
                parts = [x.strip() for x in combo_name.split("-")]
                if len(parts) >= 3:
                    char, job, color = parts[0], parts[1], parts[2]
                else:
                    char, job, color = "Unknown", "Unknown", combo_name
                    
                folder_path = os.path.join(base_export_dir, char, job, color)
                os.makedirs(folder_path, exist_ok=True)
                
                buf = self.export_buffers.get(combo_name, OrderedDict())
                
                for filename, contents in buf.items():
                    final_content = "\n".join(contents)
                    if "libcmgds" in filename:
                        final_content = f"<ROOT>\n<CHARACTER count=\"9\">\n{final_content}\n</CHARACTER>\n</ROOT>"
                        with open(os.path.join(sql_dir, filename), "w", encoding="utf-8") as f:
                            f.write(final_content)
                    elif filename.endswith(".sql"):
                        with open(os.path.join(sql_dir, filename), "w", encoding="utf-8") as f:
                            f.write(final_content)
                    else:
                        with open(os.path.join(libconfig_dir, filename), "w", encoding="utf-8") as f:
                            f.write(final_content)
                        
                if generate_imgs and hasattr(self, 'previewer_app') and self.previewer_app:
                    self._export_images_to_folder(folder_path, color)

        else:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            folder_path = os.path.join(base_export_dir, f"Combined_{timestamp}")
            os.makedirs(folder_path, exist_ok=True)
            
            buf = self.combined_buffer
            
            if separate_tables:
                for filename, contents in buf.items():
                    final_content = "\n".join(contents)
                    if "libcmgds" in filename:
                        final_content = f"<ROOT>\n<CHARACTER count=\"9\">\n{final_content}\n</CHARACTER>\n</ROOT>"
                        with open(os.path.join(sql_dir, filename), "w", encoding="utf-8") as f:
                            f.write(final_content)
                    elif filename.endswith(".sql"):
                        with open(os.path.join(sql_dir, filename), "w", encoding="utf-8") as f:
                            f.write(final_content)
                    else:
                        with open(os.path.join(libconfig_dir, filename), "w", encoding="utf-8") as f:
                            f.write(final_content)
            else:
                xml_combined = []
                sql_combined = []
                for filename, contents in buf.items():
                    final_content = "\n".join(contents)
                    if "libcmgds" in filename:
                        final_content = f"<ROOT>\n<CHARACTER count=\"9\">\n{final_content}\n</CHARACTER>\n</ROOT>"
                        with open(os.path.join(sql_dir, filename), "w", encoding="utf-8") as f:
                            f.write(final_content)
                    elif filename.endswith(".sql"):
                        sql_combined.append(f"-- {filename}")
                        sql_combined.append(final_content)
                    else:
                        xml_combined.append(f"<!-- {filename} -->")
                        xml_combined.append(final_content)
                        
                if xml_combined:
                    with open(os.path.join(libconfig_dir, "Combined.xml"), "w", encoding="utf-8") as f:
                        f.write("\n\n".join(xml_combined))
                if sql_combined:
                    with open(os.path.join(sql_dir, "Combined.sql"), "w", encoding="utf-8") as f:
                        f.write("\n\n".join(sql_combined))
                        
            if generate_imgs and hasattr(self, 'previewer_app') and self.previewer_app:
                self._export_images_to_folder(folder_path, "Combined")

    def _export_images_to_folder(self, folder_path, prefix):
        try:
            self.previewer_app.save_frame(os.path.join(folder_path, f"{prefix}_frame.png"))
            self.previewer_app.export_palettes(folder_path, "palettes")
        except Exception as e:
            print(f"Failed to export images: {e}")

    def run_generation_flow(self):
        if not hasattr(self, 'path_contributions') or not self.path_contributions:
            messagebox.showerror("Error", "No items to process! Please configure Step 1 and Step 2.")
            return

        self.export_buffers = OrderedDict()
        self.combined_buffer = OrderedDict()
        
        for combo_name, data in self.path_contributions.items():
            parts = [x.strip() for x in combo_name.split("-")]
            if len(parts) >= 3:
                char, job, color = parts[0], parts[1], parts[2]
            else:
                char, job, color = "Unknown", "Unknown", combo_name
                
            job_idx = JOBS.index(job) if job in JOBS else 0
            chr_flag = CHR_FLAGS.get(char, [0,0,0,0,0])[job_idx]
            
            set_id = data["var_set_id"].get()
            set_items_str = ""
            
            for idx, part in enumerate(data["parts"]):
                live_part = {}
                for k, v in part["_vars"].items():
                    live_part[k] = v.get()
                
                gen_id = live_part["id"]
                i_name = live_part["name"]
                
                fn = live_part["file_name"]
                cfn = live_part["cmt_file"]
                
                comment = live_part["comment"]
                use_txt = live_part["use"]
                
                typ, subtyp = _fashion_detect_slot(i_name)
                options_flags = "1/16" 
                
                # CMItemParam_Fashion
                row = [
                    "<ROW>",
                    f"<ID>{gen_id}</ID>",
                    "<Class>2</Class>",
                    f"<Type>{typ}</Type>",
                    f"<SubType>{subtyp}</SubType>",
                    "<ItemFType>0</ItemFType>",
                    f"<Name><![CDATA[{i_name}]]></Name>",
                    f"<Comment><![CDATA[{comment}]]></Comment>",
                    f"<Use><![CDATA[{use_txt}]]></Use>",
                    "<Name_Eng><![CDATA[ ]]></Name_Eng>",
                    "<Comment_Eng><![CDATA[ ]]></Comment_Eng>",
                    f"<FileName><![CDATA[{fn}]]></FileName>",
                    f"<BundleNum>{live_part['bundle']}</BundleNum>",
                    f"<InvFileName><![CDATA[{fn}]]></InvFileName>",
                    f"<InvBundleNum>{live_part['bundle']}</InvBundleNum>",
                    f"<CmtFileName><![CDATA[{cfn}]]></CmtFileName>",
                    f"<CmtBundleNum>{live_part['cmt_bundle']}</CmtBundleNum>",
                    "<EquipFileName><![CDATA[ ]]></EquipFileName>",
                    "<PivotID>0</PivotID>",
                    "<PaletteId>0</PaletteId>",
                    f"<Options>{options_flags}</Options>",
                    "<HideHat>0</HideHat>",
                    f"<ChrTypeFlags>{chr_flag}</ChrTypeFlags>",
                    "<GroundFlags>0</GroundFlags>",
                    "<SystemFlags>0</SystemFlags>",
                    "<OptionsEx>0</OptionsEx>",
                    "<Weight>0</Weight>",
                    "<Value>0</Value>",
                    "<MinLevel>1</MinLevel>",
                    "<AP>0</AP><HP>0</HP><HPCon>0</HPCon><MP>0</MP><MPCon>0</MPCon>",
                    "<Money>0</Money><APPlus>0</APPlus><ACPlus>0</ACPlus><DXPlus>0</DXPlus>",
                    "<MaxMPPlus>0</MaxMPPlus><MAPlus>0</MAPlus><MDPlus>0</MDPlus>",
                    "<MaxWTPlus>0</MaxWTPlus><DAPlus>0</DAPlus><LKPlus>0</LKPlus>",
                    "<MaxHPPlus>0</MaxHPPlus><DPPlus>0</DPPlus><HVPlus>0</HVPlus>",
                    "<RegHPPlus>0</RegHPPlus><RegMPPlus>0</RegMPPlus><RegHPTimePlus>0</RegHPTimePlus>",
                    "<RegMPTimePlus>0</RegMPTimePlus><FireRst>0</FireRst><WaterRst>0</WaterRst>",
                    "<WindRst>0</WindRst><EarthRst>0</EarthRst><ElecRst>0</ElecRst><LightRst>0</LightRst>",
                    "<DarkRst>0</DarkRst><WPPlus>0</WPPlus><FireAPPlus>0</FireAPPlus><WaterAPPlus>0</WaterAPPlus>",
                    "<WindAPPlus>0</WindAPPlus><EarthAPPlus>0</EarthAPPlus><ElecAPPlus>0</ElecAPPlus>",
                    "<LightAPPlus>0</LightAPPlus><DarkAPPlus>0</DarkAPPlus><ExpPlusRate>0.000000</ExpPlusRate>",
                    "<TMExpPlusRate>0.000000</TMExpPlusRate><PartyExpPlusRate>0.000000</PartyExpPlusRate>",
                    "<PartyTMExpPlusRate>0.000000</PartyTMExpPlusRate><ItemDropRate>0.000000</ItemDropRate>",
                    "<GalderDropRate>0.000000</GalderDropRate><Grade>0</Grade><SetId>0</SetId><LevelPoint>0</LevelPoint>",
                    "<Repair>0</Repair><Movable>0</Movable><ComposeMax>0</ComposeMax>",
                    "</ROW>"
                ]
                
                # Use combo name for file naming if Separate Tables is checked but not Sets
                filename_suffix = ""
                if self.var_sep_tables.get() and not self.var_sep_sets.get():
                    filename_suffix = f"_{char[:3]}{job[:3]}{color}"
                    
                self.add_to_buffer(combo_name, f"CMItemParam_Fashion{filename_suffix}.xml", "\n".join(row))
                
                # Append to set items string
                set_items_str += f"<Item{idx+1}>{gen_id}</Item{idx+1}>\n"
                
                # Generate Acquisition files based on UI selection
                if getattr(self, 'var_acq_myshop', None) and self.var_acq_myshop.get():
                    myshop_row = [
                        f"<ITEM Id=\"{gen_id}\" Type=\"Fashion\">",
                        f"<N>{i_name}</N>",
                        "<S>0</S>",
                        "<M>1000</M>", # Default price
                        "<P>0</P>",
                        "<B>1</B>",
                        "<U>0</U>",
                        "<E>0</E>",
                        "</ITEM>"
                    ]
                    self.add_to_buffer(combo_name, f"libcmgds_e_myshop{filename_suffix}.xml", "\n".join(myshop_row))
                    
                if getattr(self, 'var_acq_shop', None) and self.var_acq_shop.get():
                    shop_row = [
                        f"<ROW>",
                        f"<ID>{gen_id}</ID>",
                        f"<Name><![CDATA[{i_name}]]></Name>",
                        f"<Price>1000</Price>",
                        f"</ROW>"
                    ]
                    self.add_to_buffer(combo_name, f"Shop{filename_suffix}.xml", "\n".join(shop_row))
                    
                if getattr(self, 'var_acq_exchange', None) and self.var_acq_exchange.get():
                    exchange_row = [
                        f"<ROW>",
                        f"<ID>{gen_id}</ID>",
                        f"<Name><![CDATA[{i_name}]]></Name>",
                        f"<ReqItem1>0</ReqItem1>",
                        f"<ReqCount1>0</ReqCount1>",
                        f"</ROW>"
                    ]
                    self.add_to_buffer(combo_name, f"Exchange{filename_suffix}.xml", "\n".join(exchange_row))
                    
                if getattr(self, 'var_acq_compound', None) and self.var_acq_compound.get():
                    compound_row = [
                        f"<ROW>",
                        f"<ID>{gen_id}</ID>",
                        f"<Name><![CDATA[{i_name}]]></Name>",
                        f"<Mat1>0</Mat1>",
                        f"<Count1>0</Count1>",
                        f"</ROW>"
                    ]
                    self.add_to_buffer(combo_name, f"Compound{filename_suffix}.xml", "\n".join(compound_row))
                
            # CMSetItemParam
            set_row = [
                "<ROW>",
                f"<ID>{set_id}</ID>",
                f"<Name><![CDATA[{combo_name} Set]]></Name>",
                f"<Comment><![CDATA[Full set for {combo_name}]]></Comment>",
                f"<EquipItemCount>{len(data['parts'])}</EquipItemCount>",
                set_items_str,
                "<SetAPPlus>0</SetAPPlus><SetACPlus>0</SetACPlus><SetDXPlus>0</SetDXPlus>",
                "<SetMaxMPPlus>0</SetMaxMPPlus><SetMAPlus>0</SetMAPlus><SetMDPlus>0</SetMDPlus>",
                "<SetMaxWTPlus>0</SetMaxWTPlus><SetDAPlus>0</SetDAPlus><SetLKPlus>0</SetLKPlus>",
                "<SetMaxHPPlus>0</SetMaxHPPlus><SetDPPlus>0</SetDPPlus><SetHVPlus>0</SetHVPlus>",
                "<SetRegHPPlus>0</SetRegHPPlus><SetRegMPPlus>0</SetRegMPPlus>",
                "<SetRegHPTimePlus>0</SetRegHPTimePlus><SetRegMPTimePlus>0</SetRegMPTimePlus>",
                "<SetFireRst>0</SetFireRst><SetWaterRst>0</SetWaterRst><SetWindRst>0</SetWindRst>",
                "<SetEarthRst>0</SetEarthRst><SetElecRst>0</SetElecRst><SetLightRst>0</SetLightRst><SetDarkRst>0</SetDarkRst>",
                "<SetWPPlus>0</SetWPPlus><SetFireAPPlus>0</SetFireAPPlus><SetWaterAPPlus>0</SetWaterAPPlus>",
                "<SetWindAPPlus>0</SetWindAPPlus><SetEarthAPPlus>0</SetEarthAPPlus><SetElecAPPlus>0</SetElecAPPlus>",
                "<SetLightAPPlus>0</LightAPPlus><SetDarkAPPlus>0</DarkAPPlus>",
                "<SetSkillId>0</SetSkillId><SetSkillId2>0</SetSkillId2><SetSkillId3>0</SetSkillId3>",
                "</ROW>"
            ]
            self.add_to_buffer(combo_name, f"CMSetItemParam_Fashion{filename_suffix}.xml", "\n".join(set_row))
            
            # BoxItemParam
            if self.var_global_boxes.get():
                box_id = int(set_id) + 1000 # Just an offset
                box_row = [
                    "<ROW>",
                    f"<ID>{box_id}</ID>",
                    "<Class>3</Class><Type>0</Type><SubType>13</SubType><ItemFType>0</ItemFType>",
                    f"<Name><![CDATA[{combo_name} Box]]></Name>",
                    f"<Comment><![CDATA[Contains the {combo_name} set.]]></Comment>",
                    f"<Use><![CDATA[Use it to get the {combo_name} set.]]></Use>",
                    "<Name_Eng><![CDATA[ ]]></Name_Eng><Comment_Eng><![CDATA[ ]]></Comment_Eng>",
                    "<FileName><![CDATA[data\\item\\box_01_c]]></FileName><BundleNum>0</BundleNum>",
                    "<InvFileName><![CDATA[data\\item\\box_01_c]]></InvFileName><InvBundleNum>0</InvBundleNum>",
                    "<CmtFileName><![CDATA[data\\item\\view_illu_box_01_c]]></CmtFileName><CmtBundleNum>0</CmtBundleNum>",
                    "<EquipFileName><![CDATA[ ]]></EquipFileName><PivotID>0</PivotID><PaletteId>0</PaletteId>",
                    "<Options>1/4/16</Options><HideHat>0</HideHat><ChrTypeFlags>1</ChrTypeFlags>",
                    "<GroundFlags>0</GroundFlags><SystemFlags>0</SystemFlags><OptionsEx>0</OptionsEx>",
                    "<Weight>0</Weight><Value>0</Value><MinLevel>1</MinLevel>",
                    f"<BoxItemType>3</BoxItemType><BoxItemArg>{set_id}</BoxItemArg>",
                    "</ROW>"
                ]
                self.add_to_buffer(combo_name, f"BoxItemParam_Fashion{filename_suffix}.xml", "\n".join(box_row))

        self.write_export_buffers()
        messagebox.showinfo("Success", "Generation Flow Completed Successfully!")
