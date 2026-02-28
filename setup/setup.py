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
    Description="Street View Locate Plugin for AutoCAD"
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
    # AUTOCAD DETECTION
    # =====================================================

    # def detect_autocad(self):
    #     try:
    #         key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
    #                              r"SOFTWARE\Autodesk\AutoCAD\R24.2")
    #         return True
    #     except:
    #         return False

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
icon_base = b'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'

if __name__ == "__main__":
    APP_VERSION = SetupApp.get_latest_version()
    print(APP_VERSION)
    icon_path = write_icon_to_temp(icon_base)
    root = tk.Tk()
    root.iconbitmap(icon_path)
    os.remove(icon_path)
    app = SetupApp(root)
    root.mainloop()