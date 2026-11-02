# AI IDEA V1.9.2 Alpha — Thử dựng hình ngay trong SketchUp, tự hủy giao dịch

## Mục tiêu

Từ phiên bản này, giao diện SketchUp có thêm lệnh **Extensions → AI IDEA - Self-test in EMPTY model (ABORT)**. Mục tiêu là kiểm tra các API dựng hình, dấu vân tay và kiểm tra hình học V1.9.1 trên chính SketchUp được người dùng cài đặt.

Khác với GitHub Actions, lệnh này **chỉ thật sự xác nhận môi trường SketchUp khi người dùng chủ động chạy nó trên Windows của mình**. Bản này chưa được kết nối máy tính từ xa.

## Quy trình tự kiểm tra

1. Không chạm vào file thiết kế đang có. Chọn **File → New** và bảo đảm mô hình mới *chưa lưu*, *không có bất kỳ hình học nào* (kể cả hình người mẫu mặc định).
2. Cài `AI_IDEA_V192_ALPHA.rbz` qua SketchUp Extension Manager. Bật extension nếu cần.
3. Trong menu **Extensions**, chọn `AI IDEA - Self-test in EMPTY model (ABORT)`.
4. Plugin sẽ kiểm tra lại điều kiện mô hình mới/trống/không bị khóa **trước khi chạy**; sau đó hiển thị hộp thoại đồng ý.
5. Khi đồng ý, nó dựng một tấm **60 × 40 × 17 mm** tại gốc tọa độ tương đối **(5, 10, 3) mm** trong một giao dịch thử, đối chiếu hình hộp lý thuyết và kiểm tra toàn vẹn Group.
6. **Dù kiểm thử thành công hay thất bại, giao dịch thử đều bị hủy**, không có thao tác `commit_operation` trong Self-test.
7. Sau khi hủy, Plugin kiểm tra mô hình không còn hình học được thêm; nếu không sạch, hiển thị lỗi để người dùng kiểm tra mẫu thử.
   Nếu SketchUp trả về `abort_operation = false`, Self-test cũng báo lỗi ngay cả khi phần kiểm tra hình học trước đó đạt.
8. Khi thành công, màn hình báo `AI IDEA SELF-TEST PASSED`. Chỉ có thể coi bài thử SketchUp thực tế là đạt **sau khi người dùng nhìn thấy kết quả này và xác nhận tình trạng mô hình**.

## Bảo vệ thiết kế

- Bị từ chối trên mô hình đã lưu, có Group/Edge/Face, đang sửa Group/Component hoặc có `AI_IDEA.design_locked`.
- Người dùng có thể **Cancel** trước khi bắt đầu.
- Không làm việc nền, không mở cổng mạng, không đụng CNC và không chạy trong file khách hàng.
- Trường hợp hiếm `abort_operation` không dọn sạch hình học, Plugin sẽ báo lỗi rõ ràng; cần kiểm tra mô hình mẫu và không coi Self-test là đạt.

## Mức độ kiểm thử

GitHub Actions kiểm tra Python và mô phỏng Ruby; đây **không tương đương** với SketchUp 2025 thật. Việc người dùng chạy menu Self-test trên SketchUp 2025 là cột mốc độc lập.

## Tiêu chuẩn xưởng giữ nguyên

- Đơn vị mm, MDF thùng thông dụng 17 mm, hậu 7 mm.
- **Chỉ tủ bếp** dùng chân/len chân 100 mm.
- Tủ khác dùng chân/đế 50 mm hoặc 17 mm theo thiết kế đã duyệt.
- Giao thức này kiểm tra hình học *bản thử*, không phải xác nhận cấu tạo tủ hay phát hành CNC.


## Kết quả kiểm thử GitHub xác nhận

- [Workflow #226 — Linux + Windows thành công](https://github.com/thangaao1997-sys/CabinetMakerPro/actions/runs/41368940671)
- Python: 88 kiểm thử trên mỗi hệ điều hành.
- Ruby mô phỏng Self-test: 11/11 tình huống (thành công, từ chối file đã có nội dung, file đã lưu, khóa, edit context, lỗi dựng và lỗi hủy giao dịch).
- RBZ phát hành: `AI_IDEA_V192_ALPHA_RBZ`.
- Windows Starter: `AI_IDEA_V192_WINDOWS_STARTER`.

**Chưa kiểm thử trong phiên SketchUp 2025 thật.**
