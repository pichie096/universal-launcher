import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import minecraft_launcher_lib
import subprocess
import os
import json
import threading
import requests


class MinecraftLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Universal Launcher")
        self.root.geometry("700x600")
        self.root.resizable(False, False)

        # Configuration file
        self.config_file = "launcher_config.json"
        self.load_config()

        # Minecraft directory
        self.minecraft_dir = self.config.get("minecraft_dir", "minecraft")

        self.setup_ui()
        self.load_versions()
        self.update_installed_display()

    def load_config(self):
        """Load saved configuration"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {
                "username": "Player",
                "minecraft_dir": "minecraft",
                "offline_mode": True,
                "last_version": "",
                "loader_type": "vanilla"
            }

    def save_config(self):
        """Save configuration"""
        self.config["username"] = self.username_var.get()
        self.config["minecraft_dir"] = self.minecraft_dir
        self.config["offline_mode"] = self.offline_var.get()
        self.config["loader_type"] = self.loader_var.get()

        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    def setup_ui(self):
        """Create the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Title
        title_label = ttk.Label(main_frame, text="Minecraft Launcher",
                                font=('Arial', 24, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=10)

        # Username
        ttk.Label(main_frame, text="Username:", font=('Arial', 10)).grid(
            row=1, column=0, sticky=tk.W, pady=5)
        self.username_var = tk.StringVar(value=self.config.get("username", "Player"))
        username_entry = ttk.Entry(main_frame, textvariable=self.username_var, width=40)
        username_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)

        # Offline Mode
        self.offline_var = tk.BooleanVar(value=self.config.get("offline_mode", True))
        offline_check = ttk.Checkbutton(main_frame, text="Offline Mode",
                                        variable=self.offline_var)
        offline_check.grid(row=2, column=1, sticky=tk.W, pady=5)

        # Game Directory
        ttk.Label(main_frame, text="Game Directory:", font=('Arial', 10)).grid(
            row=3, column=0, sticky=tk.W, pady=5)
        dir_frame = ttk.Frame(main_frame)
        dir_frame.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)

        self.dir_label = ttk.Label(dir_frame, text=self.minecraft_dir,
                                   relief=tk.SUNKEN, width=30)
        self.dir_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        dir_button = ttk.Button(dir_frame, text="Browse", command=self.browse_directory)
        dir_button.pack(side=tk.LEFT, padx=(5, 0))

        # Loader Type
        ttk.Label(main_frame, text="Mod Loader:", font=('Arial', 10)).grid(
            row=4, column=0, sticky=tk.W, pady=5)
        self.loader_var = tk.StringVar(value=self.config.get("loader_type", "vanilla"))
        loader_frame = ttk.Frame(main_frame)
        loader_frame.grid(row=4, column=1, sticky=tk.W, pady=5)

        loaders = [
            ("Vanilla", "vanilla"),
            ("Forge", "forge"),
            ("Fabric", "fabric"),
            ("NeoForge", "neoforge"),
            ("Quilt", "quilt")
        ]

        for i, (text, value) in enumerate(loaders):
            ttk.Radiobutton(loader_frame, text=text, variable=self.loader_var,
                            value=value).grid(row=0, column=i, padx=5)

        # Version Selection
        ttk.Label(main_frame, text="Minecraft Version:", font=('Arial', 10)).grid(
            row=5, column=0, sticky=tk.W, pady=5)

        version_frame = ttk.Frame(main_frame)
        version_frame.grid(row=5, column=1, sticky=(tk.W, tk.E), pady=5)

        self.version_var = tk.StringVar()
        self.version_combo = ttk.Combobox(version_frame, textvariable=self.version_var,
                                          state='readonly', width=20)
        self.version_combo.pack(side=tk.LEFT)

        refresh_button = ttk.Button(version_frame, text="Refresh",
                                    command=self.load_versions)
        refresh_button.pack(side=tk.LEFT, padx=(5, 0))

        update_check_button = ttk.Button(version_frame, text="Check Updates",
                                         command=self.check_all_updates)
        update_check_button.pack(side=tk.LEFT, padx=(5, 0))

        # Loader Version (for modded)
        ttk.Label(main_frame, text="Loader Version:", font=('Arial', 10)).grid(
            row=6, column=0, sticky=tk.W, pady=5)

        self.loader_version_var = tk.StringVar()
        self.loader_version_combo = ttk.Combobox(main_frame,
                                                 textvariable=self.loader_version_var,
                                                 state='readonly', width=37)
        self.loader_version_combo.grid(row=6, column=1, sticky=(tk.W, tk.E), pady=5)

        # Update loader versions when loader type or MC version changes
        self.loader_var.trace('w', lambda *args: self.load_loader_versions())
        self.version_var.trace('w', lambda *args: self.load_loader_versions())

        # Progress Bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var,
                                            maximum=100)
        self.progress_bar.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E),
                               pady=10)

        # Status Label
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(main_frame, textvariable=self.status_var,
                                 font=('Arial', 9))
        status_label.grid(row=8, column=0, columnspan=2, pady=5)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=9, column=0, columnspan=2, pady=10)

        self.install_button = ttk.Button(button_frame, text="Install Version",
                                         command=self.install_version, width=20)
        self.install_button.pack(side=tk.LEFT, padx=5)

        self.update_button = ttk.Button(button_frame, text="Install Latest",
                                        command=self.install_latest, width=20)
        self.update_button.pack(side=tk.LEFT, padx=5)

        self.launch_button = ttk.Button(button_frame, text="Launch Game",
                                        command=self.launch_game, width=20)
        self.launch_button.pack(side=tk.LEFT, padx=5)

        # Console Output
        ttk.Label(main_frame, text="Console:", font=('Arial', 10)).grid(
            row=10, column=0, sticky=tk.W, pady=5)

        # Installed versions display
        installed_frame = ttk.LabelFrame(main_frame, text="Installed Versions", padding=5)
        installed_frame.grid(row=10, column=1, sticky=(tk.W, tk.E), pady=5)

        self.installed_label = ttk.Label(installed_frame, text="Loading...",
                                         font=('Arial', 8), foreground='green')
        self.installed_label.pack()

        console_frame = ttk.Frame(main_frame)
        console_frame.grid(row=11, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.console_text = tk.Text(console_frame, height=8, width=80,
                                    bg='black', fg='green', font=('Courier', 9))
        self.console_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(console_frame, command=self.console_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.console_text.config(yscrollcommand=scrollbar.set)
        # Add this at the very end of setup_ui(), after the console_frame

       # Made by text at bottom
       credit_label = ttk.Label(main_frame, text="RRP The 3rd",
                        font=('Arial', 8), foreground='gray')
       credit_label.grid(row=12, column=0, columnspan=2, pady=5)

    def browse_directory(self):
        """Browse for minecraft directory"""
        directory = filedialog.askdirectory(initialdir=self.minecraft_dir)
        if directory:
            self.minecraft_dir = directory
            self.dir_label.config(text=directory)
            self.log(f"Game directory set to: {directory}")

    def log(self, message):
        """Add message to console"""
        self.console_text.insert(tk.END, f"{message}\n")
        self.console_text.see(tk.END)
        self.root.update()

    def load_versions(self):
        """Load available Minecraft versions"""
        try:
            self.log("Loading Minecraft versions...")
            versions = minecraft_launcher_lib.utils.get_version_list()

            # Get release versions only
            release_versions = [v['id'] for v in versions if v['type'] == 'release']

            # Get installed versions
            installed = minecraft_launcher_lib.utils.get_installed_versions(self.minecraft_dir)
            installed_vanilla = [v['id'] for v in installed if
                                 'forge' not in v['id'].lower() and 'fabric' not in v['id'].lower()]

            # Mark installed versions with ✓
            version_list = []
            for v in release_versions[:20]:  # Latest 20 versions
                if v in installed_vanilla:
                    version_list.append(f"{v} ✓")
                else:
                    version_list.append(v)

            self.version_combo['values'] = version_list

            if version_list:
                self.version_combo.current(0)

            installed_count = len(installed_vanilla)
            self.log(f"Loaded {len(release_versions)} versions ({installed_count} vanilla installed)")
        except Exception as e:
            self.log(f"Error loading versions: {e}")

    def load_loader_versions(self):
        """Load available versions for selected mod loader"""
        loader = self.loader_var.get()
        mc_version = self.version_var.get().replace(" ✓", "")  # Remove checkmark if present

        if not mc_version:
            return

        try:
            if loader == "vanilla":
                self.loader_version_combo['values'] = []
                self.loader_version_var.set("")
                return

            self.log(f"Loading {loader} versions for {mc_version}...")

            if loader == "forge":
                # Get latest versions from official Forge API
                try:
                    response = requests.get(
                        'https://files.minecraftforge.net/net/minecraftforge/forge/promotions_slim.json', timeout=5)
                    if response.status_code == 200:
                        promos = response.json().get('promos', {})

                        # Get latest and recommended for this MC version
                        latest_key = f"{mc_version}-latest"
                        recommended_key = f"{mc_version}-recommended"

                        versions = []
                        if latest_key in promos:
                            latest = f"{mc_version}-{promos[latest_key]}"
                            versions.append(f"{latest} (Latest)")

                        if recommended_key in promos:
                            recommended = f"{mc_version}-{promos[recommended_key]}"
                            if f"{recommended} (Latest)" not in versions:
                                versions.append(f"{recommended} (Recommended)")

                        # Also get all available versions from minecraft-launcher-lib as fallback
                        all_forge = minecraft_launcher_lib.forge.list_forge_versions()
                        compatible = [v for v in all_forge if mc_version in v]

                        # Add other versions (remove duplicates)
                        for v in compatible[:15]:  # Top 15 versions
                            if not any(v in existing for existing in versions):
                                versions.append(v)

                        self.loader_version_combo['values'] = versions
                    else:
                        # Fallback to minecraft-launcher-lib
                        versions = minecraft_launcher_lib.forge.list_forge_versions()
                        compatible = [v for v in versions if mc_version in v]
                        self.loader_version_combo['values'] = compatible[:20]
                except Exception as e:
                    self.log(f"Warning: Could not fetch from Forge API, using fallback: {e}")
                    versions = minecraft_launcher_lib.forge.list_forge_versions()
                    compatible = [v for v in versions if mc_version in v]
                    self.loader_version_combo['values'] = compatible[:20]

                # Check for updates
                if self.loader_version_combo['values']:
                    latest = self.loader_version_combo['values'][0]
                    installed = self.get_installed_loader_version(loader, mc_version)
                    if installed:
                        latest_clean = latest.replace(" (Latest)", "").replace(" (Recommended)", "")
                        if installed != latest_clean:
                            self.log(f"⚠️ UPDATE AVAILABLE: New Forge {latest}")
                            self.log(f"   (Currently installed: {installed})")
                        else:
                            self.log(f"✓ Forge is up to date: {latest}")

            elif loader == "fabric":
                versions = minecraft_launcher_lib.fabric.get_all_loader_versions()
                loader_versions = [v['version'] for v in versions]
                self.loader_version_combo['values'] = loader_versions

                # Check for updates
                if loader_versions:
                    latest = loader_versions[0]
                    installed = self.get_installed_loader_version(loader, mc_version)
                    if installed and installed != latest:
                        self.log(f"⚠️ UPDATE AVAILABLE: New Fabric {latest}")
                        self.log(f"   (Currently installed: {installed})")
                    elif installed:
                        self.log(f"✓ Fabric is up to date: {latest}")

            elif loader == "neoforge":
                self.loader_version_combo['values'] = ["Check NeoForge website"]
            elif loader == "quilt":
                self.loader_version_combo['values'] = ["Check Quilt website"]

            if self.loader_version_combo['values']:
                self.loader_version_combo.current(0)

        except Exception as e:
            self.log(f"Error loading {loader} versions: {e}")

    def get_installed_loader_version(self, loader, mc_version):
        """Get the currently installed loader version"""
        try:
            installed = minecraft_launcher_lib.utils.get_installed_versions(self.minecraft_dir)

            if loader == "forge":
                forge_versions = [v['id'] for v in installed if 'forge' in v['id'].lower() and mc_version in v['id']]
                if forge_versions:
                    # Extract forge version from ID like "1.20.1-forge-47.3.0"
                    version_id = forge_versions[0]
                    parts = version_id.split('-')
                    if len(parts) >= 3:
                        return f"{mc_version}-{parts[2]}"
                    return version_id

            elif loader == "fabric":
                fabric_versions = [v['id'] for v in installed if 'fabric' in v['id'].lower() and mc_version in v['id']]
                if fabric_versions:
                    # Extract fabric loader version
                    version_id = fabric_versions[0]
                    parts = version_id.split('-')
                    if len(parts) >= 3:
                        return parts[2]
                    return version_id

        except Exception as e:
            self.log(f"Error checking installed version: {e}")
        return None

    def check_all_updates(self):
        """Check for updates on all installed loaders"""
        self.log("=" * 50)
        self.log("CHECKING FOR UPDATES...")
        self.log("=" * 50)

        try:
            installed = minecraft_launcher_lib.utils.get_installed_versions(self.minecraft_dir)

            if not installed:
                self.log("No versions installed yet.")
                return

            # Check Forge updates
            forge_versions = [v['id'] for v in installed if 'forge' in v['id'].lower()]
            for version_id in forge_versions:
                self.check_forge_update(version_id)

            # Check Fabric updates
            fabric_versions = [v['id'] for v in installed if 'fabric' in v['id'].lower()]
            for version_id in fabric_versions:
                self.check_fabric_update(version_id)

            # Check vanilla updates
            vanilla_versions = [v['id'] for v in installed if
                                'forge' not in v['id'].lower() and 'fabric' not in v['id'].lower()]
            if vanilla_versions:
                self.log(f"\nVanilla versions installed: {len(vanilla_versions)}")
                latest_release = minecraft_launcher_lib.utils.get_latest_version()["release"]
                self.log(f"Latest Minecraft release: {latest_release}")

            self.log("=" * 50)
            self.log("Update check complete!")

        except Exception as e:
            self.log(f"Error checking updates: {e}")

    def check_forge_update(self, version_id):
        """Check if a Forge version has an update"""
        try:
            # Extract MC version from forge ID (e.g., "1.20.1-forge-47.3.0")
            parts = version_id.split('-')
            if len(parts) < 3:
                return

            mc_version = parts[0]
            current_forge = parts[2] if len(parts) > 2 else "unknown"

            # Get latest Forge for this MC version
            all_forge = minecraft_launcher_lib.forge.list_forge_versions()
            compatible = [v for v in all_forge if mc_version in v]

            if compatible:
                latest = compatible[0]
                latest_forge = latest.split('-')[1] if '-' in latest else latest

                if latest != version_id:
                    self.log(f"\n🔥 FORGE UPDATE AVAILABLE!")
                    self.log(f"   Installed: {version_id}")
                    self.log(f"   Latest:    {latest}")
                    self.log(f"   → Select Forge and version {mc_version}, then install {latest}")
                else:
                    self.log(f"\n✓ Forge {mc_version} is up to date ({current_forge})")

        except Exception as e:
            self.log(f"Error checking Forge update: {e}")

    def check_fabric_update(self, version_id):
        """Check if a Fabric version has an update"""
        try:
            # Extract versions from fabric ID (e.g., "fabric-loader-0.14.21-1.20.1")
            parts = version_id.split('-')
            if len(parts) < 3:
                return

            mc_version = parts[-1]
            current_loader = parts[2] if len(parts) > 2 else "unknown"

            # Get latest Fabric loader
            all_fabric = minecraft_launcher_lib.fabric.get_all_loader_versions()
            if all_fabric:
                latest_loader = all_fabric[0]['version']

                if current_loader != latest_loader:
                    self.log(f"\n🧵 FABRIC UPDATE AVAILABLE!")
                    self.log(f"   Installed: fabric-loader-{current_loader}-{mc_version}")
                    self.log(f"   Latest:    fabric-loader-{latest_loader}-{mc_version}")
                    self.log(f"   → Select Fabric and version {mc_version}, then install with loader {latest_loader}")
                else:
                    self.log(f"\n✓ Fabric {mc_version} is up to date ({current_loader})")

        except Exception as e:
            self.log(f"Error checking Fabric update: {e}")

    def install_version(self):
        """Install selected version"""
        version = self.version_var.get()
        loader = self.loader_var.get()
        loader_version = self.loader_version_var.get()

        if not version:
            messagebox.showerror("Error", "Please select a Minecraft version")
            return

        # Clean up version strings
        version = version.replace(" ✓", "")
        loader_version = loader_version.replace(" (Latest)", "").replace(" (Recommended)", "")

        # Check if there's a newer version available
        if loader in ["forge", "fabric"]:
            installed = self.get_installed_loader_version(loader, version)
            if installed and loader_version:
                # Compare versions
                if self.is_newer_version_available(installed, loader_version):
                    response = messagebox.askyesno(
                        "Update Available",
                        f"You have {installed} installed.\n\n"
                        f"A newer version is available: {loader_version}\n\n"
                        f"Do you want to install the newer version?",
                        icon='info'
                    )
                    if not response:
                        self.log("Installation cancelled - keeping current version")
                        return

        # Check if exact version is already installed
        if self.is_version_installed(version, loader, loader_version):
            response = messagebox.askyesno(
                "Already Installed",
                f"{loader.capitalize()} {loader_version if loader_version else version} is already installed.\n\nDo you want to reinstall it?",
                icon='warning'
            )
            if not response:
                self.log("Installation cancelled - version already exists")
                return
            self.log("Reinstalling version...")

        self.save_config()

        # Run installation in separate thread
        thread = threading.Thread(target=self._install_thread, args=(version, loader))
        thread.daemon = True
        thread.start()

    def is_newer_version_available(self, current, new):
        """Compare version numbers to see if new is newer than current"""
        try:
            # Extract version numbers from strings like "1.20.1-47.3.0"
            def extract_version(v):
                # Get the last part (forge/fabric version number)
                parts = v.split('-')
                if len(parts) >= 2:
                    # Return the forge/fabric version (e.g., "47.3.0")
                    version_nums = parts[-1].split('.')
                    return [int(x) for x in version_nums if x.isdigit()]
                return [0]

            current_nums = extract_version(current)
            new_nums = extract_version(new)

            # Compare version numbers
            for c, n in zip(current_nums, new_nums):
                if n > c:
                    return True
                elif n < c:
                    return False

            # If all equal so far, check if new has more parts (e.g., 47.3.0.1 > 47.3.0)
            return len(new_nums) > len(current_nums)

        except Exception as e:
            self.log(f"Error comparing versions: {e}")
            return False

    def install_latest(self):
        """Automatically install the latest version of selected loader"""
        version = self.version_var.get().replace(" ✓", "")
        loader = self.loader_var.get()

        if not version:
            messagebox.showerror("Error", "Please select a Minecraft version")
            return

        if loader == "vanilla":
            messagebox.showinfo("Info",
                                "Vanilla Minecraft doesn't have loader versions.\nUse 'Install Version' instead.")
            return

        try:
            # Auto-select the latest version
            if loader == "forge":
                response = requests.get(
                    'https://files.minecraftforge.net/net/minecraftforge/forge/promotions_slim.json', timeout=5)
                if response.status_code == 200:
                    promos = response.json().get('promos', {})
                    latest_key = f"{version}-latest"

                    if latest_key in promos:
                        latest = f"{version}-{promos[latest_key]}"
                        self.log(f"Found latest Forge version: {latest}")

                        # Set it in the dropdown
                        self.loader_version_var.set(f"{latest} (Latest)")

                        # Ask to install
                        response = messagebox.askyesno(
                            "Install Latest Forge",
                            f"Install the latest Forge version?\n\n{latest}",
                            icon='question'
                        )

                        if response:
                            thread = threading.Thread(target=self._install_thread, args=(version, loader))
                            thread.daemon = True
                            thread.start()
                        return

            elif loader == "fabric":
                versions = minecraft_launcher_lib.fabric.get_all_loader_versions()
                if versions:
                    latest = versions[0]['version']
                    self.log(f"Found latest Fabric version: {latest}")

                    # Set it in the dropdown
                    self.loader_version_var.set(latest)

                    # Ask to install
                    response = messagebox.askyesno(
                        "Install Latest Fabric",
                        f"Install the latest Fabric loader?\n\nLoader version: {latest}\nMinecraft: {version}",
                        icon='question'
                    )

                    if response:
                        thread = threading.Thread(target=self._install_thread, args=(version, loader))
                        thread.daemon = True
                        thread.start()
                    return

            messagebox.showinfo("Info", f"Auto-update not supported for {loader} yet.")

        except Exception as e:
            self.log(f"Error finding latest version: {e}")
            messagebox.showerror("Error", f"Could not fetch latest version: {e}")

    def is_version_installed(self, mc_version, loader, loader_version=None):
        """Check if a specific version is already installed"""
        try:
            installed = minecraft_launcher_lib.utils.get_installed_versions(self.minecraft_dir)

            if loader == "vanilla":
                # Check for vanilla version
                return any(v['id'] == mc_version for v in installed)

            elif loader == "forge":
                # Check for forge version
                if loader_version:
                    # Check for specific forge version
                    return any(loader_version in v['id'] for v in installed)
                else:
                    # Check for any forge version of this MC version
                    return any('forge' in v['id'].lower() and mc_version in v['id'] for v in installed)

            elif loader == "fabric":
                # Check for fabric version
                if loader_version:
                    # Check for specific fabric loader version
                    return any(f'fabric-loader-{loader_version}-{mc_version}' == v['id'] for v in installed)
                else:
                    # Check for any fabric version of this MC version
                    return any('fabric' in v['id'].lower() and mc_version in v['id'] for v in installed)

        except Exception as e:
            self.log(f"Error checking installed versions: {e}")

        return False

    def update_installed_display(self):
        """Update the display of installed versions"""
        try:
            installed = minecraft_launcher_lib.utils.get_installed_versions(self.minecraft_dir)

            vanilla = [v['id'] for v in installed if 'forge' not in v['id'].lower() and 'fabric' not in v['id'].lower()]
            forge = [v['id'] for v in installed if 'forge' in v['id'].lower()]
            fabric = [v['id'] for v in installed if 'fabric' in v['id'].lower()]

            status_text = f"Vanilla: {len(vanilla)} | Forge: {len(forge)} | Fabric: {len(fabric)}"
            self.installed_label.config(text=status_text)

        except Exception as e:
            self.installed_label.config(text="Error loading installed versions")

    def _install_thread(self, version, loader):
        """Installation thread"""
        try:
            # Remove checkmark if present
            version = version.replace(" ✓", "")

            self.install_button.config(state='disabled')
            self.launch_button.config(state='disabled')

            os.makedirs(self.minecraft_dir, exist_ok=True)

            callback = {
                "setStatus": lambda status: self.status_var.set(status),
                "setProgress": lambda progress: self.progress_var.set(progress),
                "setMax": lambda max_val: None
            }

            if loader == "vanilla":
                self.log(f"Installing Minecraft {version}...")
                minecraft_launcher_lib.install.install_minecraft_version(
                    version, self.minecraft_dir, callback=callback
                )
            elif loader == "forge":
                loader_version = self.loader_version_var.get()
                # Remove (Latest) or (Recommended) tags
                loader_version = loader_version.replace(" (Latest)", "").replace(" (Recommended)", "")

                if not loader_version:
                    self.log("Error: Please select a Forge version")
                    return
                self.log(f"Installing Forge {loader_version}...")
                minecraft_launcher_lib.forge.install_forge_version(
                    loader_version, self.minecraft_dir, callback=callback
                )
            elif loader == "fabric":
                loader_version = self.loader_version_var.get()
                if not loader_version:
                    self.log("Error: Please select a Fabric version")
                    return
                self.log(f"Installing Fabric {version}...")
                minecraft_launcher_lib.fabric.install_fabric(
                    version, self.minecraft_dir, loader_version=loader_version,
                    callback=callback
                )
            else:
                self.log(f"{loader} installation not yet supported in this launcher")
                return

            self.log("Installation complete!")
            self.status_var.set("Ready to launch")
            self.update_installed_display()  # Refresh installed versions count
            self.load_versions()  # Refresh version list to show checkmarks

        except Exception as e:
            self.log(f"Installation error: {e}")
            messagebox.showerror("Installation Error", str(e))
        finally:
            self.install_button.config(state='normal')
            self.launch_button.config(state='normal')
            self.progress_var.set(0)

    def launch_game(self):
        """Launch Minecraft"""
        username = self.username_var.get()
        version = self.version_var.get().replace(" ✓", "")  # Remove checkmark if present

        if not username:
            messagebox.showerror("Error", "Please enter a username")
            return

        if not version:
            messagebox.showerror("Error", "Please select a version")
            return

        self.save_config()

        try:
            self.log(f"Launching Minecraft {version} as {username}...")

            # Get installed versions
            installed = minecraft_launcher_lib.utils.get_installed_versions(self.minecraft_dir)
            version_id = version
            loader = self.loader_var.get()

            # Find the correct version ID based on loader
            if loader == "forge":
                # Find forge version that matches the selected MC version
                forge_versions = [v['id'] for v in installed if 'forge' in v['id'].lower() and version in v['id']]
                if forge_versions:
                    version_id = forge_versions[0]
                    self.log(f"Found Forge version: {version_id}")
                else:
                    self.log("Error: Forge version not installed!")
                    messagebox.showerror("Error",
                                         f"Forge for {version} is not installed.\nPlease install it first using 'Install Version' button.")
                    return

            elif loader == "fabric":
                # Find fabric version that matches the selected MC version
                fabric_versions = [v['id'] for v in installed if 'fabric' in v['id'].lower() and version in v['id']]
                if fabric_versions:
                    version_id = fabric_versions[0]
                    self.log(f"Found Fabric version: {version_id}")
                else:
                    self.log("Error: Fabric version not installed!")
                    messagebox.showerror("Error",
                                         f"Fabric for {version} is not installed.\nPlease install it first using 'Install Version' button.")
                    return
            else:
                # Vanilla - check if it exists
                vanilla_versions = [v['id'] for v in installed if v['id'] == version]
                if not vanilla_versions:
                    self.log("Error: Vanilla version not installed!")
                    messagebox.showerror("Error",
                                         f"Minecraft {version} is not installed.\nPlease install it first using 'Install Version' button.")
                    return

            self.log(f"Using version ID: {version_id}")

            options = {
                'username': username,
                'uuid': '',
                'token': ''
            }

            command = minecraft_launcher_lib.command.get_minecraft_command(
                version_id, self.minecraft_dir, options
            )

            self.log(f"Starting game process...")
            subprocess.Popen(command)

            self.log("Game launched successfully!")
            self.status_var.set("Game running")

        except Exception as e:
            self.log(f"Launch error: {e}")
            messagebox.showerror("Launch Error", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = MinecraftLauncher(root)
    root.mainloop()
