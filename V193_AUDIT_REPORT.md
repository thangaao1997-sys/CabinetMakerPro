# AI IDEA V1.9.3 Alpha — Báo cáo Audit DRAFT JSON

## Thay đổi

- Thêm menu **Extensions → AI IDEA - Export DRAFT audit report (JSON)**.
- Chọn đúng một Group cha AI IDEA DRAFT, chọn đường dẫn JSON mới để lưu báo cáo.
- Báo cáo `ai-idea.model-audit.v4` ghi kích thước, tọa độ kỳ vọng/thực tế,
  sai lệch có dấu theo thứ tự X/Y/Z và lỗi riêng cho từng tấm.
- Đơn vị mm; tọa độ nằm trong hệ trục Group cha, không phải tọa độ thế giới.
  Phép biến đổi Group cha được kiểm tra riêng. Không suy ra toàn bộ thiết kế
  đạt chỉ từ trạng thái của từng tấm; phải đọc `status` và `errors` cấp báo cáo.
- Cho phép lưu cả báo cáo PASSED và FAILED. Hủy hộp thoại không tạo tệp.
- Không ghi đè báo cáo có sẵn. Chọn tên mới nếu tệp đã tồn tại.
- Khi dữ liệu kích thước thiếu hoặc không hợp lệ, báo cáo FAILED có trường
  đo đạc `null`; không biến dữ liệu thiếu thành kết quả đạt.
- Audit không đổi hình học, lựa chọn, metadata hoặc trạng thái phê duyệt sản xuất.
  Chỉ lệnh xuất báo cáo mới ghi tệp JSON mà người dùng chọn; không gửi mạng.

## Cài đặt và thử tối thiểu

1. Cài `AI_IDEA_V193_ALPHA.rbz` qua Extension Manager; bật extension.
   Nếu V1.9.2 đang được nạp, khởi động lại SketchUp để tránh Ruby giữ mã cũ.
   Bảo vệ/lưu công việc đang có trước khi tự khởi động lại ứng dụng.
2. Tạo mô hình mới, trống, chưa lưu bằng mẫu Woodworking Millimeters.
3. Chạy Self-test; chỉ coi đạt khi có `AI IDEA SELF-TEST PASSED` và mô hình trống.
4. Nhập `examples/scene.json`. Chọn Group cha và chạy Audit DRAFT.
5. Xuất `baseline.json`. Đối chiếu 5 tấm, các mảng đo theo X/Y/Z và sai lệch 0
   trong dung sai 0,1 mm.
6. Trong Group cha, dịch riêng một tấm TOP, thoát chỉnh sửa, chọn Group cha.
   Audit phải FAILED và chỉ rõ vị trí/phép biến đổi thay đổi. Xuất `moved.json`.
7. Undo thao tác Move (SketchUp có thể Undo đóng Group trước), thoát chỉnh sửa,
   chọn Group cha, Audit lại phải PASSED. Xuất `restored.json`.
8. Thử Cancel và tên tệp đã tồn tại; bảo đảm không tạo mới/ghi đè ngoài ý muốn.

## Mốc thử thực tế đã quan sát — V1.9.2

Ngày 02/11/2026, trong phiên Windows/SketchUp 2025 được người dùng cho phép:

- Self-test PASSED và mô hình trống sau rollback.
- Nhập IDEA-DEMO-001, Audit PASSED 5/5 tấm, dung sai 0,1 mm.
- Dịch TOP theo Z: Audit FAILED, `TOP: transformation changed` và
  `TOP: Z origin shifted by 84.342 mm`.
- Undo Move, Audit PASSED 5/5, không còn sai lệch kích thước/vị trí.

Đây là quan sát của phiên chat, chưa phải báo cáo JSON được V1.9.2 xuất ra.
Không dùng kết quả V1.9.2 để tuyên bố V1.9.3 đã kiểm thử trên SketchUp thật.

## Giới hạn

Bản Alpha; `manufacturing_approved=false`. Không xuất CNC, không tạo bảng cắt
sản xuất. Tiêu chuẩn MDF 17 mm/hậu 7 mm và quy tắc chân đế đã duyệt giữ nguyên.
Báo cáo kiểm tra so với metadata của bản DRAFT; không phải chữ ký độc lập của
thiết kế hay chứng nhận đủ điều kiện gia công.
