# AI IDEA V1.9-alpha — Fingerprint hình học chi tiết của từng tấm

**Trạng thái:** Bản thử nghiệm; kiểm thử Ruby trên môi trường mô phỏng và CI. Chưa có bằng chứng chạy trên SketchUp 2025 thực tế.

## Vấn đề được giải quyết

Bộ kiểm tra V1.8 có thể báo PASS khi một cạnh hoặc mặt bên trong tấm bị thay đổi mà bounding box (chiều dài/rộng/cao) và ma trận biến đổi không thay đổi.

V1.9 bổ sung dấu vân tay SHA-256 của dữ liệu hình học **nằm trong tọa độ riêng của từng Group**:

- Liệt kê các `Sketchup::Face` và vòng cạnh qua `face.loops → vertices`.
- Liệt kê các `Sketchup::Edge` cùng hai điểm đầu/cuối.
- Chuẩn hóa tọa độ theo mm, bước làm tròn **0,01 mm**.
- Sắp xếp độc lập thứ tự entity và chiều thứ tự đỉnh trong một loop.
- Tạo chuỗi SHA-256 có phiên bản từ các mặt, vòng và cạnh.
- Lưu `AI_IDEA/geometry_sha256` trong Group ngay khi nhập bản thử.
- Khi chạy **Audit selected DRAFT (READ ONLY)**, tính lại và đối chiếu digest.
- Nếu thiếu metadata hoặc hình học có entity không hỗ trợ, báo FAIL thay vì coi là đạt.

## Các kiểm tra vẫn có

Tên tấm, số lượng Group, kích thước, vị trí, ma trận xoay/dịch chuyển và thông tin `manufacturing_approved=false` vẫn được kiểm tra như V1.8. Sai lệch bounding box được kiểm tra ở mức 0,10 mm.

## Giới hạn bảo mật và chính xác

Đây là **dấu vân tay thay đổi hình học**, không phải chữ ký bảo mật chống giả mạo: người có thể chỉnh sửa model có thể chỉnh metadata, và thuật toán chuẩn hóa không phân biệt mọi loại thay đổi hình học. Dấu vân tay có bước làm tròn 0,01 mm, vì vậy những sai lệch nhỏ hơn ngưỡng chuẩn hóa có thể không bị phát hiện. Vật liệu/texture, layer/tag, đường kích thước và toàn bộ kết cấu CAD chưa được chứng nhận bởi thuật toán này.

Plugin chỉ làm việc với mô hình thử **mới, chưa lưu, trống và không khóa**. Bản dựng tạo ra không được duyệt sản xuất. Mô hình nhập bằng phiên bản cũ thiếu `geometry_sha256` sẽ không đạt kiểm tra mới; tạo lại bản nháp ở một mô hình thử trống.

## Kiểm thử thủ công trên SketchUp 2025

1. Tải bộ **AI_IDEA_V19_WINDOWS_STARTER** từ GitHub Actions của commit được kiểm chứng.
2. Giải nén hai lớp ZIP, chạy `AI_IDEA_CHECK.cmd` để kiểm tra RBZ.
3. Mở mô hình SketchUp mới, rỗng, chưa lưu và cài `AI_IDEA_V19_ALPHA.rbz` trong Extension Manager.
4. Nhập `examples/scene.json`; chọn Group cha AI IDEA; chạy **Audit selected DRAFT (READ ONLY)**. Kết quả kỳ vọng: PASS.
5. Trong mô hình thử dùng riêng, chỉnh một cạnh/mặt của tấm trong Group (nhưng không đổi kích thước bao ngoài). Chạy audit lại: kỳ vọng FAIL với `internal geometry changed`.
6. Undo thay đổi và kiểm tra audit trở lại PASS.
7. Kiểm tra thêm việc khóa thiết kế và thử Undo thao tác import. Không thử trong file khách hàng.

**Không dùng để phát hành bảng cắt hoặc CNC.** Cấu tạo hậu, đế, liên kết thùng, nẹp, chiều vân và phụ kiện vẫn phải có hồ sơ xưởng xác nhận.
