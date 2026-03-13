import cv2
import numpy as np
import argparse

# Tugas Pengolahan Citra Digital - Grup A
# Anggota Kelompok:
# 1. Putu Gde Kenzie Carlen Mataram - 71230994
# 2. Edrian Sepriadi Irawan - 71231011
# 3. Bernadus Xaverius Hitipeuw - 71231018

def process_image(image_path):
    img = cv2.imread(image_path)
    if img is None:
        print("Error: Gagal memuat citra. Pastikan path file benar.")
        return None, None

    # batas citra input maksimal 720x720 piksel
    h, w = img.shape[:2]
    if max(h, w) > 720:
        scale = 720 / float(max(h, w))
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
        h, w = img.shape[:2]

    cx, cy = w / 2, h / 2

    print("Memproses rotasi tanpa interpolasi (Forward Mapping)...")
    # Rotasi tanpa interpolasi
    out_no_interp = np.ones_like(img) * 255
    y, x = np.indices((h, w))
    dx = x - cx
    dy = y - cy
    
    r = np.sqrt(dx**2 + dy**2)
    
    theta_deg = r / 8.0
    theta_rad = np.radians(theta_deg)

    new_x = cx + dx * np.cos(theta_rad) - dy * np.sin(theta_rad)
    new_y = cy + dx * np.sin(theta_rad) + dy * np.cos(theta_rad)

    new_x = np.round(new_x).astype(int)
    new_y = np.round(new_y).astype(int)

    valid = (new_x >= 0) & (new_x < w) & (new_y >= 0) & (new_y < h)
    out_no_interp[new_y[valid], new_x[valid]] = img[y[valid], x[valid]]

    print("Memproses rotasi dengan interpolasi (Backward Mapping + Bilinear)...")

    # Interpolasi
    X, Y = np.meshgrid(np.arange(w), np.arange(h))
    dX = X - cx
    dY = Y - cy
    R = np.sqrt(dX**2 + dY**2)
    
    Theta_deg = R / 8.0
    Theta_rad = np.radians(Theta_deg)

    map_X = cx + dX * np.cos(Theta_rad) + dY * np.sin(Theta_rad)
    map_Y = cy - dX * np.sin(Theta_rad) + dY * np.cos(Theta_rad)

    map_X = map_X.astype(np.float32)
    map_Y = map_Y.astype(np.float32)

    out_interp = cv2.remap(img, map_X, map_Y, interpolation=cv2.INTER_LINEAR, 
                           borderMode=cv2.BORDER_CONSTANT, borderValue=(255,255,255))

    return out_no_interp, out_interp

if __name__ == "__main__":
    #input dari cmd/terminal
    parser = argparse.ArgumentParser(description="Program Rotasi Citra dengan efek Swirl")
    parser.add_argument("-i", "--input", required=True, help="Path ke file citra input (JPG atau PNG)")
    args = parser.parse_args()
    
    hasil_no_interp, hasil_interp = process_image(args.input)
    
    if hasil_no_interp is not None and hasil_interp is not None:
        cv2.imwrite("hasil_tanpa_interpolasi.jpg", hasil_no_interp)
        cv2.imwrite("hasil_dengan_interpolasi.jpg", hasil_interp)
        print("Selesai! Citra berhasil disimpan sebagai 'hasil_tanpa_interpolasi.jpg' dan 'hasil_dengan_interpolasi.jpg'.")