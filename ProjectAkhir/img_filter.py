"""
╔══════════════════════════════════════════════════════════════════╗
║   Face Privacy Filter - Haar Cascade + Ellipse Masking           ║
║   Mata Kuliah : Pemrosesan Citra Digital                         ║
║   Metode      : Haar Cascade + Ellipse Masking + Alpha Blending  ║
║   Output      : 4-Panel Dashboard (cv2.imshow)                   ║
╚══════════════════════════════════════════════════════════════════╝
"""

import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import sys

# ──────────────────────────────────────────────────────────────────
#  KONFIGURASI PARAMETER  (ubah di sini untuk tuning)
# ──────────────────────────────────────────────────────────────────

# ── Haar Cascade ──────────────────────────────────────────────────
CASCADE_PATH    = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
SCALE_FACTOR    = 1.10   # seberapa kecil citra di-scale tiap octave
MIN_NEIGHBORS   = 5      # makin tinggi → makin sedikit false-positive
MIN_FACE_SIZE   = 60     # ukuran wajah minimum (piksel)

# ── Geometri Elips  ───────────────────────────────────────────────
ELLIPSE_W_DIV   = 2.2    # setengah sumbu horizontal  = w / ELLIPSE_W_DIV
ELLIPSE_H_DIV   = 1.8    # setengah sumbu vertikal    = h / ELLIPSE_H_DIV
ELLIPSE_Y_SHIFT = 0.05   # geser pusat elips ke bawah = h * shift

# ── Feathering (Gaussian Blur pada mask) ──────────────────────────
FEATHER_KSIZE   = 51     # kernel blur mask → pinggiran gradasi halus

# ── Blur Privasi (Gaussian Blur pada citra asli) ──────────────────
PRIVACY_KSIZE   = 71     # kernel blur gambar → intensitas sensor

# ── Dashboard ─────────────────────────────────────────────────────
DASHBOARD_MAX_W = 1280           # lebar maksimum jendela dashboard
PANEL_GAP       = 5              # tebal garis pemisah antar panel (piksel)
GAP_COLOR       = 15             # intensitas abu garis pemisah
LABEL_COLOR     = (0, 255, 180)  # warna teks label panel (BGR)
BBOX_COLOR      = (0, 220, 60)   # warna bounding-box Haar (BGR)

# ── Format File ───────────────────────────────────────────────────
SUPPORTED_IMAGE_EXT = (".jpg", ".jpeg", ".png")
SUPPORTED_VIDEO_EXT = (".mp4", ".avi")


# ──────────────────────────────────────────────────────────────────
#  INISIALISASI HAAR CASCADE
# ──────────────────────────────────────────────────────────────────

def load_face_cascade() -> cv2.CascadeClassifier:
    """Muat classifier; lempar RuntimeError jika file tidak ada."""
    if not os.path.isfile(CASCADE_PATH):
        raise RuntimeError(
            f"File Haar Cascade tidak ditemukan:\n{CASCADE_PATH}\n"
            "Pastikan OpenCV terinstal lengkap."
        )
    clf = cv2.CascadeClassifier(CASCADE_PATH)
    if clf.empty():
        raise RuntimeError("CascadeClassifier gagal dimuat (file kosong/rusak).")
    return clf


face_cascade = load_face_cascade()


# ──────────────────────────────────────────────────────────────────
#  STEP 1 - DETEKSI WAJAH (Haar Cascade)
# ──────────────────────────────────────────────────────────────────

def detect_faces(frame_bgr: np.ndarray):
    """
    Konversi BGR → Grayscale, lalu jalankan Haar detectMultiScale.
    Kembalikan: (gray_image, list_of_faces)
    Setiap elemen list_of_faces = (x, y, w, h).
    """
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

    # equalizeHist meningkatkan kontras agar deteksi lebih robust
    gray_eq = cv2.equalizeHist(gray)

    faces = face_cascade.detectMultiScale(
        gray_eq,
        scaleFactor  = SCALE_FACTOR,
        minNeighbors = MIN_NEIGHBORS,
        minSize      = (MIN_FACE_SIZE, MIN_FACE_SIZE),
        flags        = cv2.CASCADE_SCALE_IMAGE,
    )

    # Jika tidak ada wajah, kembalikan list kosong
    if not isinstance(faces, np.ndarray):
        faces = []

    return gray, faces


# ──────────────────────────────────────────────────────────────────
#  STEP 2 - MASKING GEOMETRI (Ellipse Solid)
# ──────────────────────────────────────────────────────────────────

def build_ellipse_mask(frame_shape: tuple, faces) -> np.ndarray:
    """
    Buat kanvas hitam, lalu gambar elips solid putih untuk setiap wajah.
    Elips sengaja dibuat agak lonjong ke bawah agar menutupi dagu.
    Kembalikan: mask uint8 [0, 255] berukuran sama dengan frame.
    """
    h, w = frame_shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)

    for (fx, fy, fw, fh) in faces:
        # Pusat elips: tengah bbox, sedikit digeser ke bawah
        cx = fx + fw // 2
        cy = fy + fh // 2 + int(fh * ELLIPSE_Y_SHIFT)

        # Setengah sumbu elips
        axis_x = int(fw / ELLIPSE_W_DIV)   # sumbu horizontal (lebar wajah)
        axis_y = int(fh / ELLIPSE_H_DIV)   # sumbu vertikal   (lebih panjang)

        # Gambar elips solid putih pada mask
        cv2.ellipse(
            mask,
            center     = (cx, cy),
            axes       = (axis_x, axis_y),
            angle      = 0,
            startAngle = 0,
            endAngle   = 360,
            color      = 255,
            thickness  = cv2.FILLED,
        )

    return mask


# ──────────────────────────────────────────────────────────────────
#  STEP 3 - FEATHERING & ALPHA BLENDING
# ──────────────────────────────────────────────────────────────────

def feather_and_blend(
    frame_bgr: np.ndarray,
    ellipse_mask: np.ndarray,
) -> tuple:
    """
    Proses inti blending tiga sub-langkah:

    3a. Feathering  : Gaussian Blur pada mask → tepian gradasi halus.
    3b. Alpha Map   : Normalisasi mask ke float [0.0, 1.0].
    3c. Blending    : Result = α × Blur_Frame + (1−α) × Original.

    Kembalikan: (feathered_mask, result_bgr)
    feathered_mask dipakai untuk visualisasi heatmap di panel 3.
    """
    # ── 3a. Feathering ───────────────────────────────────────────
    # Kernel harus bilangan ganjil
    fk = FEATHER_KSIZE if FEATHER_KSIZE % 2 == 1 else FEATHER_KSIZE + 1
    feathered_mask = cv2.GaussianBlur(
        ellipse_mask, (fk, fk), sigmaX=fk / 3.0
    )

    # ── 3b. Alpha Map (float 0.0 - 1.0) ─────────────────────────
    alpha    = feathered_mask.astype(np.float32) / 255.0
    alpha_3ch = np.stack([alpha] * 3, axis=-1)   # broadcast ke 3 channel

    # ── 3c. Blur privasi pada frame asli ─────────────────────────
    pk = PRIVACY_KSIZE if PRIVACY_KSIZE % 2 == 1 else PRIVACY_KSIZE + 1
    blurred_frame = cv2.GaussianBlur(frame_bgr, (pk, pk), sigmaX=0)

    # ── 3d. Alpha Blending matematis piksel-per-piksel ────────────
    # Result = (α × Blur) + ((1 − α) × Original)
    orig_f   = frame_bgr.astype(np.float32)
    blur_f   = blurred_frame.astype(np.float32)
    result_f = alpha_3ch * blur_f + (1.0 - alpha_3ch) * orig_f

    result = np.clip(result_f, 0, 255).astype(np.uint8)

    return feathered_mask, result


# ──────────────────────────────────────────────────────────────────
#  PIPELINE UTAMA - SATU FRAME
# ──────────────────────────────────────────────────────────────────

def process_frame(frame_bgr: np.ndarray):
    """
    Jalankan seluruh pipeline untuk satu frame/gambar.
    Kembalikan: (original, gray_with_bbox, alpha_heatmap, result)
    Keempat elemen ini langsung dipakai oleh build_dashboard().
    """
    # Step 1 - deteksi wajah
    gray, faces = detect_faces(frame_bgr)

    # Panel 2: grayscale + bounding box per wajah
    gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    for (fx, fy, fw, fh) in faces:
        cv2.rectangle(gray_bgr, (fx, fy), (fx + fw, fy + fh),
                      BBOX_COLOR, thickness=2, lineType=cv2.LINE_AA)
        cv2.putText(gray_bgr, "face", (fx, fy - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    BBOX_COLOR, 1, cv2.LINE_AA)

    # Step 2 - buat mask elips
    ellipse_mask = build_ellipse_mask(frame_bgr.shape, faces)

    # Step 3 - feathering & blending
    alpha_map, result = feather_and_blend(frame_bgr, ellipse_mask)

    # Panel 3: alpha map ditampilkan sebagai heatmap warna
    alpha_heatmap = cv2.applyColorMap(alpha_map, cv2.COLORMAP_OCEAN)

    return frame_bgr.copy(), gray_bgr, alpha_heatmap, result


# ──────────────────────────────────────────────────────────────────
#  4-PANEL DASHBOARD
# ──────────────────────────────────────────────────────────────────

def build_dashboard(
    panel_original,
    panel_detection,
    panel_alpha_map,
    panel_result,
    max_width: int = DASHBOARD_MAX_W,
) -> np.ndarray:
    """
    Susun 4 panel dalam grid 2×2 dengan label dan garis pemisah.
    Semua panel diseragamkan ke ukuran panel_original (Panel 1).
    """
    PANEL_LABELS = [
        "Panel 1 | Original Image",
        "Panel 2 | Grayscale + Haar BBox",
        "Panel 3 | Alpha Map (COLORMAP_OCEAN)",
        "Panel 4 | Final Result - Smooth Blur",
    ]

    panels = [panel_original, panel_detection, panel_alpha_map, panel_result]
    ref_h, ref_w = panels[0].shape[:2]

    # Seragamkan resolusi semua panel ke Panel 1
    for i in range(1, 4):
        if panels[i].shape[:2] != (ref_h, ref_w):
            panels[i] = cv2.resize(panels[i], (ref_w, ref_h),
                                   interpolation=cv2.INTER_AREA)

    # ── Tambahkan label pada setiap panel ────────────────────────
    def add_label(img: np.ndarray, text: str) -> np.ndarray:
        out     = img.copy()
        bar_h   = 30
        overlay = out.copy()
        cv2.rectangle(overlay, (0, 0), (ref_w, bar_h), (GAP_COLOR,) * 3, -1)
        cv2.addWeighted(overlay, 0.72, out, 0.28, 0, out)
        cv2.putText(out, text, (8, 21),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.50,
                    LABEL_COLOR, 1, cv2.LINE_AA)
        return out

    panels = [add_label(p, l) for p, l in zip(panels, PANEL_LABELS)]

    # ── Susun 2×2 dengan garis pemisah ───────────────────────────
    g        = PANEL_GAP
    make_gap = lambda rows, cols: np.full(
        (rows, cols, 3), GAP_COLOR, dtype=np.uint8
    )

    row_top    = np.hstack([panels[0], make_gap(ref_h, g), panels[1]])
    row_bottom = np.hstack([panels[2], make_gap(ref_h, g), panels[3]])
    separator  = make_gap(g, row_top.shape[1])
    grid       = np.vstack([row_top, separator, row_bottom])

    # ── Scale-down jika terlalu lebar untuk layar ─────────────────
    grid_h, grid_w = grid.shape[:2]
    if grid_w > max_width:
        scale = max_width / grid_w
        grid  = cv2.resize(grid,
                           (int(grid_w * scale), int(grid_h * scale)),
                           interpolation=cv2.INTER_AREA)
    return grid


# ──────────────────────────────────────────────────────────────────
#  HELPER - PATH OUTPUT
# ──────────────────────────────────────────────────────────────────

def build_output_path(source_path: str, suffix: str = "_filtered") -> str:
    """Buat path output dengan suffix sebelum ekstensi, di direktori yang sama."""
    base, ext = os.path.splitext(source_path)
    out_ext   = ".mp4" if ext.lower() in SUPPORTED_VIDEO_EXT else ext
    return base + suffix + out_ext


# ──────────────────────────────────────────────────────────────────
#  PROSES GAMBAR
# ──────────────────────────────────────────────────────────────────

def process_image(filepath: str) -> None:
    try:
        img = cv2.imread(filepath)
        if img is None:
            raise ValueError(f"File tidak dapat dibaca: {filepath}")

        p1, p2, p3, p4 = process_frame(img)
        dashboard       = build_dashboard(p1, p2, p3, p4)

        window_title = "Face Privacy Filter [tekan sembarang tombol]"
        cv2.namedWindow(window_title, cv2.WINDOW_NORMAL)
        cv2.imshow(window_title, dashboard)
        print("[INFO] Dashboard ditampilkan. Tekan sembarang tombol untuk lanjut.")
        cv2.waitKey(0)
        cv2.destroyAllWindows()

        # Simpan hasil akhir (Panel 4) di direktori yang sama
        output_path = build_output_path(filepath)
        cv2.imwrite(output_path, p4)
        print(f"[INFO] Hasil akhir disimpan → {output_path}")

    except Exception as e:
        messagebox.showerror("Error - Gambar", str(e))
        print(f"[ERROR] {e}")


# ──────────────────────────────────────────────────────────────────
#  PROSES VIDEO (real-time)
# ──────────────────────────────────────────────────────────────────

def process_video(filepath: str) -> None:
    cap    = None
    writer = None
    try:
        cap = cv2.VideoCapture(filepath)
        if not cap.isOpened():
            raise ValueError(f"File video tidak dapat dibuka: {filepath}")

        fps   = cap.get(cv2.CAP_PROP_FPS) or 25.0
        delay = max(1, int(1000 / fps))

        WIN_DETECTION = "Face Privacy Filter - Detection  [q = keluar]"
        WIN_RESULT    = "Face Privacy Filter - Result     [q = keluar]"
        cv2.namedWindow(WIN_DETECTION, cv2.WINDOW_NORMAL)
        cv2.namedWindow(WIN_RESULT,    cv2.WINDOW_NORMAL)

        output_path = build_output_path(filepath)
        fourcc      = cv2.VideoWriter_fourcc(*"mp4v")

        frame_count = 0
        print("[INFO] Pemrosesan video dimulai. Tekan 'q' untuk berhenti …")

        while True:
            ret, frame = cap.read()
            if not ret:
                print(f"[INFO] Video selesai ({frame_count} frame diproses).")
                break

            try:
                p1, p2, p3, p4 = process_frame(frame)
            except Exception as frame_err:
                print(f"[WARN] Frame #{frame_count} error, dilewati: {frame_err}")
                frame_count += 1
                continue

            # Inisialisasi VideoWriter setelah ukuran frame diketahui
            if writer is None:
                h, w   = p4.shape[:2]
                writer = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

            cv2.imshow(WIN_DETECTION, p2)   # Panel 2: Grayscale + BBox
            cv2.imshow(WIN_RESULT,    p4)   # Panel 4: Hasil akhir blur
            writer.write(p4)

            frame_count += 1
            if cv2.waitKey(delay) & 0xFF == ord("q"):
                print("[INFO] Dihentikan oleh pengguna.")
                break

        print(f"[INFO] Video hasil disimpan → {output_path}")

    except Exception as e:
        messagebox.showerror("Error - Video", str(e))
        print(f"[ERROR] {e}")
    finally:
        if cap:    cap.release()
        if writer: writer.release()
        cv2.destroyAllWindows()


# ──────────────────────────────────────────────────────────────────
#  ENTRY POINT - GUI FILE PICKER (loop otomatis)
# ──────────────────────────────────────────────────────────────────

def pick_file(root: tk.Tk) -> str | None:
    """Tampilkan dialog pemilihan file dan kembalikan path-nya."""
    filetypes = [
        ("Semua yang didukung", "*.jpg *.jpeg *.png *.mp4 *.avi"),
        ("Gambar",              "*.jpg *.jpeg *.png"),
        ("Video",               "*.mp4 *.avi"),
    ]
    return filedialog.askopenfilename(
        title     = "Face Privacy Filter - Pilih Gambar atau Video",
        filetypes = filetypes,
    )


def main() -> None:
    root = tk.Tk()
    root.withdraw()   # sembunyikan jendela Tkinter utama

    print("[INFO] Face Privacy Filter aktif. Tutup dialog untuk keluar.")

    while True:
        filepath = pick_file(root)

        if not filepath:
            print("[INFO] Tidak ada file dipilih. Program selesai.")
            break

        ext = os.path.splitext(filepath)[1].lower()

        if ext in SUPPORTED_IMAGE_EXT:
            process_image(filepath)
        elif ext in SUPPORTED_VIDEO_EXT:
            process_video(filepath)
        else:
            messagebox.showerror(
                "Format Tidak Didukung",
                f"Format '{ext}' tidak didukung.\nGunakan: .jpg  .png  .mp4  .avi"
            )

        # Tanya apakah ingin memproses file lain
        lanjut = messagebox.askyesno(
            "Face Privacy Filter",
            "Proses file lain?",
        )
        if not lanjut:
            print("[INFO] Program selesai.")
            break

    root.destroy()


if __name__ == "__main__":
    main()