import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
from PIL import Image, ImageTk
import os
import shutil

# Mengimpor fungsi dari file rotasi_citra.py
from imgRotation import process_image

class RotasiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Aplikasi Rotasi Citra - PCD Grup A")
        self.root.geometry("1000x500")

        # Variabel untuk menyimpan data gambar
        self.img_path = None
        self.img_result_no_interp = None
        self.img_result_interp = None

        self.setup_ui()

    def setup_ui(self):
        # Frame Atas (Tombol Pilih File)
        top_frame = tk.Frame(self.root, pady=10)
        top_frame.pack(side=tk.TOP, fill=tk.X)

        self.btn_open = tk.Button(top_frame, text="Pilih Gambar", command=self.open_image, font=("Arial", 12))
        self.btn_open.pack(side=tk.TOP)

        # Frame Tengah (Area Preview Gambar)
        self.preview_frame = tk.Frame(self.root)
        self.preview_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Label untuk preview
        self.lbl_orig = tk.Label(self.preview_frame, text="Citra Asli", compound=tk.TOP)
        self.lbl_orig.pack(side=tk.LEFT, expand=True)

        self.lbl_no_interp = tk.Label(self.preview_frame, text="Tanpa Interpolasi", compound=tk.TOP)
        self.lbl_no_interp.pack(side=tk.LEFT, expand=True)

        self.lbl_interp = tk.Label(self.preview_frame, text="Dengan Interpolasi", compound=tk.TOP)
        self.lbl_interp.pack(side=tk.LEFT, expand=True)

        # Frame Bawah (Tombol Unduh)
        bottom_frame = tk.Frame(self.root, pady=10)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.btn_save = tk.Button(bottom_frame, text="Simpan Hasil Rotasi", command=self.save_images, font=("Arial", 12), state=tk.DISABLED)
        self.btn_save.pack(side=tk.TOP)

    def display_image(self, cv_img, label_widget, max_size=300):

        rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_img)
        
        pil_img.thumbnail((max_size, max_size))
        
        tk_img = ImageTk.PhotoImage(image=pil_img)
        
        label_widget.configure(image=tk_img)
        label_widget.image = tk_img

    def open_image(self):
        filetypes = (("Image files", "*.jpg *.jpeg *.png"), ("All files", "*.*"))
        self.img_path = filedialog.askopenfilename(title="Pilih Gambar", filetypes=filetypes)

        if self.img_path:
            img_orig = cv2.imread(self.img_path)
            if img_orig is not None:
                self.display_image(img_orig, self.lbl_orig)
                self.process_and_show()
            else:
                messagebox.showerror("Error", "Gagal membaca gambar.")

    def process_and_show(self):
        self.root.config(cursor="watch")
        self.root.update()

        try:
            # Memproses gambar
            no_interp, interp = process_image(self.img_path)

            if no_interp is not None and interp is not None:
                self.img_result_no_interp = no_interp
                self.img_result_interp = interp

                # Tampilkan di UI
                self.display_image(self.img_result_no_interp, self.lbl_no_interp)
                self.display_image(self.img_result_interp, self.lbl_interp)

                # Aktifkan tombol simpan
                self.btn_save.config(state=tk.NORMAL)
            else:
                messagebox.showerror("Error", "Gagal memproses gambar.")
        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan: {str(e)}")
        
        self.root.config(cursor="")

    def save_images(self):
        # Membuka dialog untuk memilih folder penyimpanan
        save_dir = filedialog.askdirectory(title="Pilih Folder Penyimpanan")
        
        if save_dir:
            # Buat nama file default
            base_name = os.path.basename(self.img_path)
            name, ext = os.path.splitext(base_name)
            
            path_no_interp = os.path.join(save_dir, f"{name}_tanpa_interpolasi.jpg")
            path_interp = os.path.join(save_dir, f"{name}_dengan_interpolasi.jpg")

            # Simpan menggunakan OpenCV
            cv2.imwrite(path_no_interp, self.img_result_no_interp)
            cv2.imwrite(path_interp, self.img_result_interp)

            messagebox.showinfo("Berhasil", f"Gambar berhasil disimpan di:\n{save_dir}")

if __name__ == "__main__":
    root = tk.Tk()
    app = RotasiApp(root)
    root.mainloop()