import tkinter as tk
from tkinter import ttk, messagebox
import requests
import zipfile
import os
import shutil
import tempfile
import getpass
import threading
import winreg
import base64
import xml.etree.ElementTree as ET

GITHUB_API = "https://api.github.com/repos/BHUTUU/streetViewLocate/releases/latest"
APP_NAME = "StreetViewLocate"
APP_VERSION = ""


def write_icon_to_temp(base_64_val):
    icon_bytes = base64.b64decode(icon_base)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".ico")
    temp_file.write(icon_bytes)
    temp_file.close()
    return temp_file.name

class SetupApp:

    # =====================================================
    # INIT
    # =====================================================

    def __init__(self, root):
        self.root = root
        self.root.title("StreetViewLocate Setup")
        self.root.geometry("700x500")
        self.root.resizable(False, False)

        self.cancel_event = threading.Event()
        self.temp_dir = None

        self.apply_dark_theme()

        self.frame = ttk.Frame(root, padding=25)
        self.frame.pack(fill="both", expand=True)

        self.create_welcome_page()

    # =====================================================
    # DARK THEME
    # =====================================================

    def apply_dark_theme(self):
        self.root.configure(bg="#1e1e1e")
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background="#1e1e1e")
        style.configure("TLabel", background="#1e1e1e", foreground="white")
        style.configure("TButton", padding=8)
        style.configure("Horizontal.TProgressbar",
                        troughcolor="#2d2d2d",
                        background="#00b894")

    # =====================================================
    # UI HELPERS
    # =====================================================

    def clear_frame(self):
        for widget in self.frame.winfo_children():
            widget.destroy()

    def update_status(self, text):
        self.root.after(0, lambda: self.status_label.config(text=text))

    def update_progress(self, value):
        self.root.after(0, lambda: self.progress.config(value=value))

    # =====================================================
    # PAGE 1 – WELCOME
    # =====================================================

    def create_welcome_page(self):
        self.clear_frame()

        ttk.Label(self.frame,
                  text="Welcome to StreetViewLocate Setup Wizard",
                  font=("Arial", 16, "bold")).pack(pady=30)

        ttk.Label(self.frame,
                  wraplength=600,
                  text="This wizard will install StreetViewLocate for AutoCAD2023 - 2025. \n\nClick Next to continue."
                  ).pack(pady=20)

        ttk.Button(self.frame,
                   text="Next",
                   command=self.create_license_page).pack(pady=20)

    # =====================================================
    # PAGE 2 – LICENSE
    # =====================================================

    def create_license_page(self):
        self.clear_frame()

        ttk.Label(self.frame,
                  text="License Agreement",
                  font=("Arial", 14, "bold")).pack(pady=10)

        license_text = tk.Text(self.frame, height=12,
                               bg="#2d2d2d", fg="white",
                               insertbackground="white")
        license_text.insert("1.0",
                            "END USER LICENSE AGREEMENT (EULA)\n\n"
                            "IMPORTANT: PLEASE READ THIS AGREEMENT CAREFULLY BEFORE INSTALLING OR USING THIS SOFTWARE.\n\n"
                            "This End User License Agreement (\"Agreement\") is a legal agreement between you  (\"User\") "
                            "and the software provider (\"BHUTUU\") for the StreetViewLocate \napplication (\"Software\").\n\n"
                            "1. LICENSE GRANT\n"
                            "The Developer grants you a limited, non-exclusive, non-transferable license to \ninstall and use "
                            "the Software for personal or internal business use.\n\n"
                            "2. RESTRICTIONS\n"
                            "You may not modify, reverse engineer, decompile, distribute, sublicense, rent, \nor lease the Software.\n\n"
                            "3. THIRD-PARTY SERVICES\n"
                            "The Software may integrate third-party services including Google Maps, Microsoft WebView2, "
                            "and AutoCAD APIs. Use of such services is subject to their respective terms and conditions.\n\n"
                            "4. DISCLAIMER OF WARRANTY\n"
                            "The Software is provided \"AS IS\" without warranties of any kind, express or \nimplied. "
                            "The developer does not guarantee uninterrupted or error-free operation.\n\n"
                            "5. LIMITATION OF LIABILITY\n"
                            "In no event shall the Developer be liable for any indirect, incidental, special, \nor consequential "
                            "damages arising out of the use or inability to use the \nSoftware.\n\n"
                            "6. TERMINATION\n"
                            "This Agreement is effective until terminated. It will terminate automatically if you fail "
                            "to comply with its terms.\n\n"
                            "By clicking Install, you acknowledge that you have read, understood, and agree \nto be bound "
                            "by this Agreement.\n\n"
                            "Author: Suman Kumar ~BHUTUU\n"
                            "Github: https://github.com/BHUTUU\n"
                            )
        license_text.config(state="disabled")
        license_text.pack(fill="both", expand=True)

        self.accept_var = tk.BooleanVar()
        ttk.Checkbutton(self.frame,
                        text="I accept the agreement",
                        variable=self.accept_var).pack(pady=10)

        ttk.Button(self.frame,
                   text="Install",
                   command=self.start_installation).pack(pady=10)

    # =====================================================
    # INSTALL START
    # =====================================================

    def start_installation(self):
        if not self.accept_var.get():
            messagebox.showwarning("Warning", "You must accept the agreement.")
            return

        if self.is_already_installed():
            messagebox.showinfo("Info", "Latest version already installed.")
            return

        self.create_install_page()

        thread = threading.Thread(target=self.install)
        thread.start()

    # =====================================================
    # PAGE 3 – INSTALL PROGRESS
    # =====================================================

    def create_install_page(self):
        self.clear_frame()

        ttk.Label(self.frame,
                  text="Installing StreetViewLocate",
                  font=("Arial", 14, "bold")).pack(pady=20)

        self.progress = ttk.Progressbar(self.frame,
                                        orient="horizontal",
                                        length=550,
                                        mode="determinate")
        self.progress.pack(pady=15)

        self.status_label = ttk.Label(self.frame, text="")
        self.status_label.pack(pady=10)

        ttk.Button(self.frame,
                   text="Cancel",
                   command=self.cancel_installation).pack(pady=10)

    # =====================================================
    # CANCEL
    # =====================================================

    def cancel_installation(self):
        self.cancel_event.set()
        self.update_status("Cancelling...")

    # =====================================================
    # INSTALL LOGIC
    # =====================================================

    def install(self):
        try:
            self.download_and_install()
            if not self.cancel_event.is_set():
                self.update_progress(100)
                self.create_finish_page()
        except Exception as e:
            self.rollback()
            messagebox.showerror("Error", str(e))

    # =====================================================
    # DOWNLOAD WITH REAL PROGRESS
    # =====================================================

    def download_file(self, url, path, start, end):
        r = requests.get(url, stream=True)
        total = int(r.headers.get("content-length", 0))
        downloaded = 0

        with open(path, "wb") as f:
            for chunk in r.iter_content(8192):
                if self.cancel_event.is_set():
                    raise Exception("Installation cancelled.")
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    percent = downloaded / total if total else 0
                    overall = start + (end - start) * percent
                    self.update_progress(overall)

    # =====================================================
    # MAIN INSTALL PROCESS
    # =====================================================

    def download_and_install(self):

        self.temp_dir = tempfile.mkdtemp()

        username = getpass.getuser()
        local_appdata = os.path.join("C:\\Users", username, "AppData", "Local")
        programdata = "C:\\ProgramData\\Autodesk\\ApplicationPlugins"
        bundle_path = os.path.join(programdata, APP_NAME + ".bundle")
        win64_path = os.path.join(bundle_path, "Contents", "Win64")

        if os.path.exists(bundle_path):
            self.update_status("Removing previous version...")
            shutil.rmtree(bundle_path)

        os.makedirs(win64_path, exist_ok=True)

        self.update_status("Fetching release info...")
        response = requests.get(GITHUB_API)
        data = response.json()

        zip1 = None
        zip2 = None

        for asset in data["assets"]:
            if asset["name"] == "StreetViewBySumanKumarBHUTUU.zip":
                zip1 = asset["browser_download_url"]
            if asset["name"].startswith("StreetViewLocate_V"):
                zip2 = asset["browser_download_url"]

        if not zip1 or not zip2:
            raise Exception("Release assets not found.")

        zip1_path = os.path.join(self.temp_dir, "file1.zip")
        zip2_path = os.path.join(self.temp_dir, "file2.zip")

        self.update_status("Downloading resources...")
        self.download_file(zip1, zip1_path, 0, 40)

        self.update_status("Downloading plugin...")
        self.download_file(zip2, zip2_path, 40, 80)

        self.update_status("Extracting files...")
        with zipfile.ZipFile(zip1_path) as z:
            z.extractall(local_appdata)

        with zipfile.ZipFile(zip2_path) as z:
            z.extractall(win64_path)

        self.update_status("Writing PackageContents.xml...")
        self.write_full_package_xml(bundle_path)

        self.download_cuix(programdata)
        self.write_cuix_autoload_lisp(programdata)

        shutil.rmtree(self.temp_dir)

    # =====================================================
    # FULL XML
    # =====================================================

    def write_full_package_xml(self, bundle_path):

        xml_content = f"""<?xml version="1.0" encoding="utf-8"?>
<ApplicationPackage
    SchemaVersion="1.0"
    AutodeskProduct="AutoCAD|Civil3D"
    Name="{APP_NAME}"
    Description="Street View Locate Plugin for AutoCAD/CIVIL 3D"
    AppVersion="{APP_VERSION}"
    Author="Suman Kumar"
    ProductType="Application">

  <CompanyDetails Name="BHUTUU Technologies" Url="https://github.com/BHUTUU" />

  <Components>

    <RuntimeRequirements
        OS="Win64"
        SeriesMin="R24.2"
        SeriesMax="R25.1" />

    <ComponentEntry
        AppName="{APP_NAME}"
        ModuleName="./Contents/Win64/StreetViewLocate_V{APP_VERSION}/StreetViewLocate.dll"
        AppDescription="StreetView Locate"
        LoadOnAutoCADStartup="True" />

  </Components>

</ApplicationPackage>
"""

        with open(os.path.join(bundle_path, "PackageContents.xml"), "w", encoding="utf-8") as f:
            f.write(xml_content)

    # =====================================================
    # DOWNLOAD CUIX
    # =====================================================

    def download_cuix(self, programdata):
        self.update_status("Downloading customization file...")
        url = "https://raw.githubusercontent.com/BHUTUU/streetViewLocate/main/setup/bhutuu.cuix"
        response = requests.get(url)
        if response.status_code == 200:
            cuix_path = os.path.join(programdata, "bhutuu.cuix")
            if os.path.exists(cuix_path):
                os.remove(cuix_path)
            with open(cuix_path, "wb") as f:
                f.write(response.content)
        else:
            raise Exception("Failed to download cuix file.")
        
    # =====================================================
    # CUIX AUTOLOAD LISP
    # =====================================================

    def write_cuix_autoload_lisp(self, programdata):
        self.update_status("Configuring AutoCAD to load customization...")
        cui_autoload_script = """
(defun loadMyCUIX ( / cuixName cuixPath loaded )

  ;;<<<-----------set your cuix group name----------->>>
  (setq cuixName "BHUTUU")

  ;;<<<-----------full path----------->>>
  (setq cuixPath "C:\\\\ProgramData\\\\Autodesk\\\\ApplicationPlugins\\\\bhutuu.cuix")

  ;;<<<-----------get loaded menu groups----------->>>
  (vl-load-com)
  (setq loaded nil)

  (vlax-for g (vla-get-MenuGroups (vlax-get-acad-object))
    (if (= (strcase (vla-get-Name g)) (strcase cuixName))
      (setq loaded T)
    )
  )

  ;;<<<-----------load if not loaded----------->>>
  (if (not loaded)
    (progn
      (command "_.cuiload" cuixPath)
      (princ (strcat "\\nLoaded CUIX: " cuixName))
    )
    (princ (strcat "\\nCUIX already loaded: " cuixName))
  )

  (princ)
)
;;<<<-----------RUN AT CORRECT TIME----------->>>
(defun S::STARTUP ()
  (loadMyCUIX)
)"""
        r_versions = ["R24.2", "R24.3", "R25.0"]
        all_autocad_years = ["2023", "2024", "2025"]
        for r, y in zip(r_versions, all_autocad_years):
            print(f"Configuring for AutoCAD {y} ({r})...")
            support_folder_path = os.path.join(os.path.expandvars("%APPDATA%"), f"Autodesk\\AutoCAD {y}\\{r}\\enu\\Support")
            print(f"Looking for support folder at: {support_folder_path}")
            if os.path.exists(support_folder_path):
                print(f"Found support folder: {support_folder_path}")
                lisp_path = os.path.join(support_folder_path, "acad.lsp")
                if os.path.exists(lisp_path):
                    print(f"Found existing acad.lsp at: {lisp_path}")
                    with open(lisp_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    if cui_autoload_script not in content:
                        print("Appending autoload command to existing acad.lsp...")
                        with open(lisp_path, "a", encoding="utf-8") as f:
                            f.write("\n" + cui_autoload_script + "\n")
                else:
                    print(f"No acad.lsp found. Creating new one at: {lisp_path}")
                    with open(lisp_path, "w", encoding="utf-8") as f:
                        f.write(cui_autoload_script + "\n")

    # =====================================================
    # FINISH PAGE
    # =====================================================

    def create_finish_page(self):
        self.clear_frame()

        ttk.Label(self.frame,
                  text="Installation Complete!",
                  font=("Arial", 16, "bold")).pack(pady=30)

        ttk.Label(self.frame,
                  text="StreetViewLocate has been installed successfully."
                  ).pack(pady=10)

        ttk.Button(self.frame,
                   text="Finish",
                   command=self.root.quit).pack(pady=20)

    # =====================================================
    # VERSION CHECK
    # =====================================================

    def is_already_installed(self):
        path = r"C:\ProgramData\Autodesk\ApplicationPlugins\StreetViewLocate.bundle\PackageContents.xml"
        if not os.path.exists(path):
            return False

        tree = ET.parse(path)
        root = tree.getroot()
        version = root.attrib.get("AppVersion")

        return version == APP_VERSION

    # =====================================================
    # ROLLBACK
    # =====================================================

    def rollback(self):
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    # =====================================================
    # LATEST RELEASE VERSION GET
    # =====================================================
    @staticmethod
    def get_latest_version():
        response = requests.get(GITHUB_API)
        data = response.json()
        tag = data.get("tag_name", "")
        tag = tag.replace("StreetViewLocate_V", "")
        return tag
# =========================================================
# MAIN
# =========================================================
icon_base = b'AAABAAEAICAAAAEAIACoEAAAFgAAACgAAAAgAAAAQAAAAAEAIAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAD9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//f7+//z+/f/8/v3//P79//z+/f/8/v3//P7+//z+/f/8/v3//P7+//z+/f/8/v3//P39//z+/v/8/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//P39//r6+//7+/v//Pz8//z9/f/8/f3//P39//z9/f/8/f3//f7+//39/f/8/f3//P39//z9/f/8/f3//P39//z9/f/7+/v/+/r7//z9/f/9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//f7+//v8/P/9/f7////////////////////////////////////////////8//7//f/+/////////////////////////////////////////////f3+//v8/P/9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//f7+//3+/v/8/P3///////fz9P/Gp6//pXR//5xlcf+ZYW7/mGBt/5hgbP+XX2z/lV1q/6dtfP+kaXj/lVxp/5hea/+XXWr/ll5r/5ZfbP+ZY2//onJ9/8OlrP/28vP///////z9/f/9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//Pz9///////q3+L/j09e/3IiNP92Jzn/eCk8/3cpO/94KTv/eCo8/3gqPP9yJjb/nk1l/5ZFXP9yJTb/eCo8/3cpO/92KTv/dyk7/3YpOv90Jzj/cCIz/4pMWv/o3N////////z8/f/9/v7//f7+//3+/v/9/v7//f7+//z9/f/+////+vf4/4tLWv92JTj/hTtN/4I2SP+CNkj/gTVH/4A1R/+BNkf/gDZH/3szRP+UR1v/j0NX/3szQ/9+NEX/fjRG/381Rv+ANUb/fzVG/381R/+DOkv/cCM0/4hMWv/8+fr//f////39/f/9/v7//f7+//3+/v/9/v7//Pz8///////owdD/s1x5/4g/Uf99L0H/hTVJ/4Q1SP+CNUf/gjRG/4AzRf99M0X/eCo5/307T/96N0j/cSg2/3YwQf96MUL/fTJD/34yRP+ANEb/gTRG/3gtPf+MRVf/tl99/+bCz////////Pz8//3+/v/9/v7//f7+//3+/v/8/Pz//////8eKn/+9X4H/yHSS/59QZv+CM0X/hTRH/4c3Sv+ENUj/gDRG/3cuPf9hM0b/EYrV/xFwu/9UIi//Zic2/3UuP/98MkP/gjVH/38xQv9/NEX/pFZu/8l0k/+0Vnb/xYue///////8/Pz//f7+//3+/v/9/v7//f7+//z9/f//////xoCZ/7FSdP+6Xn7/yG6P/7hlgP+VQlf/iDNH/4k2Sv+GOE3/jScx/09ZhP8Aof//AIv1/1dCZv+DKTL/fjVI/4MzRf+CMkX/lEZb/7xnhP/DaIj/s1l2/6xNbf/EgZj///////z9/f/8/v7//f7+//3+/v/8/f7//P39//////+jZHX/lD1X/6hRbP+wVHL/vWGB/8Rriv+xWnT/mUJa/5YxRP9lYob/EqLx/wac9/8GoPj/D4Pe/2lIcP+SNEX/lkNa/7NdeP/HbY3/rVRx/51HYf+oUWv/lTxV/6ltff///////P39//3+/v/9/v7//f7+//3+/v/8/f3//////5NYZf9yIzX/ezBA/5M6Uf+cQFn/n0Rc/7BTbf+wV3H/tEZc/z2Zzf8Cs///CZ33/wqi+P8Akfz/RWev/7lMXv+2XHr/t1Zz/6pIY/+TPFL/jDZL/4o3Sv93JDb/nGJv///////8/P3//f7+//3+/v/9/v7//f7+//z9/f//////l1tp/3gnOv+FNUn/kzlR/5k6U/+PNEj/nz5U/79Wcf/jaoX/R6Tj/wGo//8Lnvj/BZv3/wCI8f9VeMb/7G+H/7FLZv+gO1P/ojxV/481Sv+PN03/mz1V/4IrP/+eZHH///////z9/f/9/v7//f7+//3+/v/8/f7//P39//////+VWmj/eCc6/5U7VP+YO1T/nD1W/5M3TP+3TWf/5WmM/95dev9jhL7/CYfi/wBw2/8Ygdr/A3LY/2Njqf/jY3z/1GCC/7dMaP+nQFr/pEJc/5E4Tv+fPVf/kjBK/6pmeP///////P39//3+/v/9/v7//f7+//3+/v/8/f3//////6Fgcf+HLUX/lTtU/5c6U/+fP1j/1F1//9tqif/Vi53/x3uN/+fKzf/Mzdr/i6LM/9jQ2f/JxtL/r3CH/8d6i//SfJP/1Vt+/9Zcgf/CU3T/r0ll/6dCXf+UMEr/sGd7///////8/f3//f7+//3+/v/9/v7//f7+//z9/f//////qWN3/48wS/+WPFX/lztT/58/WP/bX4T/3nCO/+7n5v/s5ub/7OTk//Lk4///7+L/8OTg/+3e3f/k09L/5uTi/92tuP/PUHX/3WCH/7NHZv+1SGf/zlZ7/5kyTf+uZnn///////z9/f/8/v7//f7+//3+/v/8/v7//P39//////+nYnX/jjBK/5Y8Vf+ROFD/nz9Y/9hhhP/VU3f/4qy5//Ht7P/t4OL/9ezs/9C84v/l1ef/7uPh/+XY2v/m2dr/zm2G/85QdP/TWX7/yWWF/8Jff//OVHr/v0Rq/8dzjf///////P39//3+/v/9/v7//f7+//3+/v/8/f3//////6hid/+NL0n/mz9Z/8RUd//SW4D/11+E/9JRdf/Wf5X/8e3t//ju7v/Mv8X/hVDU/5Zzvv/o39b/7eTm/96+w//FT27/y1B0/9NpjP+jVGz/tGF8/9Jrjv/EQ2v/13qZ//7////8/f3//f7+//3+/v/9/v7//f7+//z9/f//////qWN3/40vSv+hQl7/21+I/9hbhP/TWX//0FJ3/9BphP/w5+j//PX2/4d7fv9/a4b/a1lq/7ywsP/69vX/16qz/8FGZ//HTnH/0WyO/4c7Tv+YSmD/2Haa/7w+ZP/PdZP//v////z9/f/9/v7//f7+//3+/v/8/v7//P39//////+nYXX/iC1G/5w/Wv/PVn7/z1V9/89Ve//MT3X/yVt5//Pl6P/w6uv/vbO0///9+P/f2Nb/w7e6//n39f/Voaz/vEJi/8FNbv/FUXX/zm6Q/9F0lv/EVnn/u0Bl/8xzj////////P39//3+/v/9/v7//f7+//39/v/8/f3//////65kev+kOlv/vk9z/8tTe//KUXj/yVB3/8lPc//DT2//9+Tp/9fT0/8nEhb/7+jr/4h7fv9NOz///////9CWo/+4PV7/vkxt/7pGaP+8R2r/vEdq/7tIav+3PmL/x2+K///////8/f3//f7+//3+/v/9/v7//f3+//39/v/+////0nWU/8pKdv/LUnv/xk52/8VNc//FTHL/xU5y/75BZf/nwcv/+Pv6/8C4uf/89/j/3dfY/8rAw//9/Pv/x3uO/7Q8Xf+4SGj/tkVn/7VFZv+1RWb/t0ho/7E7Xf/Dboj///////z9/f/8/v7//f7+//3+/v/9/v7//P39//7////PdJL/vkNr/8FMcv/BS3H/v0pv/75Jbv+/Sm7/ukBk/8hwiP/9/Pz///////v4+f/8+fr//////+vY3P+zSWX/skNi/7FDZP+wQmP/sEJi/69CYv+vQ2L/qjdZ/8Bvh////////P39//3+/v/9/v7//f7+//3+/v/8/P3//////8x4k/+3Pmb/u0lu/7pHa/+6R2v/uUZq/7hFaP+5R2n/sz1e/8uClv/06+3///////39/f/r19z/umB4/6s7Wv+uQ2L/rUFh/6s/X/+pPl7/qT5e/6pBYP+kM1T/v3WL///////8/Pz//f7+//3+/v/9/v7//f7+//v7/P//////05ap/641W/+2SGv/s0Nm/7NDZf+zQmX/skJk/7FCY/+xRGP/rDhZ/7FKZ/+/boT/vGqA/6tBXv+pOln/qkBf/6g9Xf+nPl3/pj1c/6Q8W/+jO1n/p0Be/5wsTf/Mlqb///////v7+//9/v7//f7+//3+/v/9/v7//Pz9///////x4eb/rD9h/6w8Xv+vRGT/rUFh/61BYf+tQGH/qj9e/6o/Xv+rQV//qDxb/6Q1VP+jNVT/pz5c/6hAXv+lPVv/ozxa/6I7Wv+hO1n/oTtZ/6I9W/+dNVP/njpX//Di5////////Pz9//3+/v/9/v7//f7+//3+/v/9/v7//Pz8///////hvMf/pTla/58uUP+iNFX/ojZW/6I1Vf+hNFT/oDRU/58zU/+gNVT/oDdV/541VP+dNFL/nTRT/5wzUv+bM1H/mzNR/5oyUP+YME7/lSlJ/5kzUf/cusT///////z8/P/9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//Pz8///////t2uD/xYSY/7NfeP+uVnH/rVZv/61Vbv+sU23/q1Ns/6pSa/+pUWv/qFFq/6dRaf+oUWr/p1Bp/6dQav+oUWr/p1Fq/6pZcf+9f5H/6tjd///////8/Pz//f7+//3+/v/9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//Pz8//7//////////v////z8/f/8/Pz/+/v8//v7+//7+/v/+/r7//v6+//7+vr/+/r6//v5+v/7+fr/+/r6//v6+v/7+vv//f7+///////+/v///Pz8//3+/v/9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//Pz8//v6+//8/f3//f7+//3+/v/9/////f////3////9/////f////3////9/////f////3////9/////f////3////9/v7/+/v7//z8/P/9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//P7+//3+/v/9/v7//f7+//3+/v/9/v7//f7+//z9/f/8/f3//P39//z9/f/8/f3//P39//z9/f/8/f3//P39//z9/f/8/f3//P39//z9/f/8/f3//P39//z9/f/9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7//f7+//3+/v/9/v7/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA='
if __name__ == "__main__":
    APP_VERSION = SetupApp.get_latest_version()
    icon_path = write_icon_to_temp(icon_base)
    root = tk.Tk()
    root.iconbitmap(icon_path)
    os.remove(icon_path)
    app = SetupApp(root)
    root.mainloop()