import cv2
from deepface import DeepFace
import os
import json
from datetime import datetime

# Đường dẫn đến file JSON và thư mục lưu ảnh
DATA_FILE = "danh_sach_vat_dung.json"
FACE_IMAGE_DIR = "face_images"
if not os.path.exists(FACE_IMAGE_DIR):
    os.makedirs(FACE_IMAGE_DIR)

# Hàm chụp ảnh từ camera
def capture_face_image():
    cap = cv2.VideoCapture(0)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    img_path = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        cv2.imshow("Quét khuôn mặt - Nhấn SPACE để chụp, ESC để thoát", frame)

        key = cv2.waitKey(1)
        if key == 27:  # ESC
            break
        if key == 32 and len(faces) > 0:  # SPACE
            # Lưu ảnh khuôn mặt đầu tiên tìm được
            (x, y, w, h) = faces[0]
            face_img = frame[y:y+h, x:x+w]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            img_path = os.path.join(FACE_IMAGE_DIR, f"face_{timestamp}.jpg")
            cv2.imwrite(img_path, face_img)
            break

    cap.release()
    cv2.destroyAllWindows()
    return img_path

# Hàm so sánh khuôn mặt
def verify_face(image_path1, image_path2):
    try:
        result = DeepFace.verify(image_path1, image_path2, model_name="Facenet", distance_metric="euclidean_l2")
        return result["verified"]  # Độ chính xác cao với Facenet (~91%+)
    except Exception as e:
        print(f"Lỗi khi so sánh khuôn mặt: {e}")
        return False

# Hàm thêm thông tin người mượn
def add_borrower_info(device_id, borrower_info):
    face_image = capture_face_image()
    if not face_image:
        print("Không thể chụp ảnh người mượn.")
        return False

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    for device in data:
        if device["id"] == device_id:
            borrower_info["anh_nguoi_muon"] = face_image
            borrower_info["da_tra"] = False
            device["ban_ghi_muon"].append(borrower_info)
            break
    
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Đã thêm thông tin người mượn với ảnh: {face_image}")
    return True

# Hàm kiểm tra và xử lý người trả
def check_returner(device_id):
    returner_image = capture_face_image()
    if not returner_image:
        print("Không thể chụp ảnh người trả.")
        return False

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    for device in data:
        if device["id"] == device_id:
            for record in device["ban_ghi_muon"]:
                if not record.get("da_tra", False):
                    borrower_image = record.get("anh_nguoi_muon")
                    if borrower_image and verify_face(borrower_image, returner_image):
                        record["da_tra"] = True
                        record["ngay_tra_thuc_te"] = datetime.now().strftime("%Y-%m-%d")
                        record["anh_nguoi_tra"] = returner_image
                        with open(DATA_FILE, "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        print(f"Người trả là {record['nguoi_muon']}. Đã cập nhật trạng thái trả.")
                        return True
                    else:
                        # Người trả không phải người mượn ban đầu
                        new_returner_info = {
                            "nguoi_tra": input("Nhập tên người trả: "),
                            "so_dien_thoai": input("Nhập số điện thoại: "),
                            "dia_chi": input("Nhập địa chỉ: "),
                            "ngay_tra_thuc_te": datetime.now().strftime("%Y-%m-%d"),
                            "anh_nguoi_tra": returner_image
                        }
                        record["da_tra"] = True
                        record.update(new_returner_info)
                        with open(DATA_FILE, "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        print("Người trả không phải người mượn ban đầu. Đã lưu thông tin mới.")
                        return True
    print("Không tìm thấy bản ghi mượn phù hợp.")
    return False

# Hàm kiểm tra người chưa từng mượn
def check_new_borrower():
    face_image = capture_face_image()
    if not face_image:
        print("Không thể chụp ảnh.")
        return None

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    for device in data:
        for record in device["ban_ghi_muon"]:
            if record.get("anh_nguoi_muon") and verify_face(record["anh_nguoi_muon"], face_image):
                print(f"Người này đã mượn đồ trước đó: {record['nguoi_muon']}")
                return record
    
    # Người chưa từng mượn, yêu cầu nhập thông tin mới
    new_borrower_info = {
        "nguoi_muon": input("Nhập tên người mượn: "),
        "so_dien_thoai": input("Nhập số điện thoại: "),
        "dia_chi": input("Nhập địa chỉ: "),
        "ngay_muon": datetime.now().strftime("%Y-%m-%d"),
        "ngay_tra": input("Nhập ngày trả dự kiến (YYYY-MM-DD): "),
        "so_luong": int(input("Nhập số lượng: ")),
        "anh_nguoi_muon": face_image
    }
    print("Người này chưa từng mượn đồ. Đã tạo thông tin mới.")
    return new_borrower_info

# Ví dụ sử dụng
if __name__ == "__main__":
    # Kiểm tra người mượn mới
    borrower_info = check_new_borrower()
    if borrower_info:
        add_borrower_info(1, borrower_info)
    
    # Kiểm tra người trả
    check_returner(1)