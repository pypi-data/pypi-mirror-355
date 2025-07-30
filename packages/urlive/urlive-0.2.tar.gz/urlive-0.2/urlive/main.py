import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import threading
import pandas as pd
import time
import os

# Hacker-style colors
GREEN = "\033[92m"
CYAN = "\033[96m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

def show_banner():
    os.system("cls" if os.name == "nt" else "clear")  # Clear screen

    banner = f"""
{BOLD}{GREEN}
    ██╗   ██╗██████╗ ██╗     ██╗██╗   ██╗███████╗
    ██║   ██║██╔══██╗██║     ██║██║   ██║██╔════╝
    ██║   ██║██████╔╝██║     ██║██║   ██║█████╗  
    ██║   ██║██╔══██╗██║     ██║╚██╗ ██╔╝██╔══╝  
    ╚██████╔╝██║  ██║███████╗██║ ╚████╔╝ ███████╗
     ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝  ╚══════╝
                  - BY  THIRUMURUGAN                                                                                            
{CYAN}                          Author  : GTSIVAM
                          Contact    : https://github.com/GTSivam
                          Version : 0.2v
                          Status  : Initial Release 🚀
{RESET}
"""

    print(banner)
    time.sleep(1.5)

class URLStatusCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🌐 URLive Checker")
        self.root.geometry("800x600")
        self.root.configure(bg="#121212")

        style = ttk.Style(self.root)
        style.theme_use('default')
        style.configure("TNotebook", background="#121212", foreground="#fff", borderwidth=0)
        style.configure("TNotebook.Tab", background="#1e1e1e", foreground="#fff", lightcolor="#121212", borderwidth=0)
        style.map("TNotebook.Tab", background=[("selected", "#333")])

        self.urls = []
        self.success_list = []
        self.fail_list = []

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True)

        self.success_tab = ttk.Frame(self.notebook)
        self.fail_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.success_tab, text="✅ Success")
        self.notebook.add(self.fail_tab, text="❌ Failure")

        self.create_widgets()

    def create_widgets(self):
        top_frame = tk.Frame(self.root, bg="#121212")
        top_frame.pack(pady=10)

        self.start_button = tk.Button(top_frame, text="🚀 Start Scan", command=self.start_scan, bg="#333", fg="#0f0", font=("Arial", 12))
        self.start_button.pack(side="left", padx=5)

        self.load_button = tk.Button(top_frame, text="📂 Load URLs", command=self.load_urls, bg="#444", fg="#0f0", font=("Arial", 12))
        self.load_button.pack(side="left", padx=5)

        self.export_button = tk.Button(top_frame, text="💾 Export CSV", command=self.export_csv, bg="#555", fg="#0f0", font=("Arial", 12))
        self.export_button.pack(side="left", padx=5)

        self.status_label = tk.Label(top_frame, text="Count...", fg="#0f0", bg="#121212", font=("Consolas", 11, "bold"))
        self.status_label.pack(side="left", padx=10)

        self.success_listbox = tk.Listbox(self.success_tab, bg="#101010", fg="#00ff00", font=("Consolas", 10))
        self.success_listbox.pack(fill="both", expand=True, padx=10, pady=10)

        self.fail_listbox = tk.Listbox(self.fail_tab, bg="#101010", fg="#ff4444", font=("Consolas", 10))
        self.fail_listbox.pack(fill="both", expand=True, padx=10, pady=10)

    def load_urls(self):
        file_path = filedialog.askopenfilename(title="Select URL List File", filetypes=[("Text Files", "*.txt")])
        if file_path:
            with open(file_path, "r") as f:
                self.urls = [line.strip() for line in f if line.strip()]
            messagebox.showinfo("Loaded", f"{len(self.urls)} URLs loaded from:\n{file_path}")

    def start_scan(self):
        if not self.urls:
            messagebox.showerror("Error", "No URLs loaded!")
            return

        self.success_listbox.delete(0, tk.END)
        self.fail_listbox.delete(0, tk.END)
        self.success_list.clear()
        self.fail_list.clear()
        self.status_label.config(text="🔄 Scanning...")

        self.active_threads = len(self.urls)

        for url in self.urls:
            t = threading.Thread(target=self.check_url, args=(url,))
            t.start()

    def check_url(self, url):
        time.sleep(0.1)  # animation delay
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "http://" + url

        try:
            response = requests.head(url, allow_redirects=True, timeout=5)
            code = response.status_code
        except Exception:
            code = "FAILED"

        self.root.after(0, self.update_result, url, code)

    def update_result(self, url, code):
        text = f"{url} - {code}"
        if code != "FAILED" and 200 <= int(code) < 400:
            self.success_listbox.insert(tk.END, text)
            self.success_list.append((url, code))
        else:
            self.fail_listbox.insert(tk.END, text)
            self.fail_list.append((url, code))

        self.status_label.config(text=f"✅ {len(self.success_list)} | ❌ {len(self.fail_list)}")

    def export_csv(self):
        if not self.success_list and not self.fail_list:
            messagebox.showerror("Error", "No results to export.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".csv", title="Save CSV File")
        if file_path:
            df_success = pd.DataFrame(self.success_list, columns=["URL", "Status"])
            df_fail = pd.DataFrame(self.fail_list, columns=["URL", "Status"])
            df = pd.concat([df_success, df_fail])
            df.to_csv(file_path, index=False)
            messagebox.showinfo("Saved", f"Results exported to:\n{file_path}")


def show_splash_screen(root, on_close):
    splash = tk.Toplevel(root)
    splash.geometry("400x200+500+300")
    splash.overrideredirect(True)
    splash.configure(bg="black")

    label = tk.Label(
        splash,
        text="🚀 URLive Checker\nby THIRUMURUGAN (GTSivam)",
        fg="lime",
        bg="black",
        font=("Consolas", 18, "bold"),
        bd=4,                        # Border width
        relief="solid",              # Solid border
        highlightbackground="lime", # Border color (macOS/Linux)
        highlightthickness=1        # Highlight border thickness
    )
    label.pack(expand=True, padx=20, pady=20)

    def destroy_splash():
        splash.destroy()
        on_close()

    root.after(3000, destroy_splash)



def run_app():
    show_banner()
    root = tk.Tk()
    root.withdraw()
    show_splash_screen(root, lambda: [root.deiconify(), URLStatusCheckerApp(root)])
    root.mainloop()


if __name__ == "__main__":
    run_app()