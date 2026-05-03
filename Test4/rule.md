# Giải thích logic các Rule Tối ưu Amazon Ads (Phase 3)

Tài liệu này tổng hợp toàn bộ các luật (Rule) tối ưu Keyword và Rào chắn an toàn (Guardrails) của hệ thống Test 4. Điểm đặc biệt của kiến trúc này là **Ngưỡng động (Dynamic Thresholds)** kết hợp với **Quản trị bằng Ngoại lệ (Management by Exception)**.

---

## I. TỔNG HỢP CÁC RÀO CHẮN (GUARDRAILS) VÀ VÒNG ĐỜI
Hệ thống AI tự động điều chỉnh Bid, nhưng tuyệt đối không được vượt qua các Rào chắn này nếu không có sự phê duyệt của con người. Nếu đụng rào chắn, nó sẽ giương cờ `REQUIRES_REVIEW` lên Dashboard.

### 1. Nhóm Evergreen (Chiến dịch quanh năm)
*   **Launch Phase (< 30 ngày):** Mua traffic lấy data. `Max CPC: $2.50`, `Min CPC: $0.50`, `Target ACOS: 50%`.
*   **Growth Phase (30 - 90 ngày):** Cân bằng tăng trưởng. `Max CPC: $2.00`, `Min CPC: $0.40`, `Target ACOS: 40%`.
*   **Mature Phase (> 90 ngày, traffic ổn):** Vắt sữa lấy lãi. `Max CPC: $1.50`, `Min CPC: $0.30`, `Target ACOS: 30%`.
*   **Dormant Phase (> 90 ngày, traffic lẹt đẹt):** Kích thích nhẹ. `Max CPC: $1.00`, `Min CPC: $0.20`, `Target ACOS: 25%`.

### 2. Nhóm Seasonal (Chiến dịch mùa vụ)
*   **Pre-Season (Đun nóng):** `Max CPC: $2.00`, `Min CPC: $0.50`, `Target ACOS: 35%`.
*   **Peak-Season (Bùng nổ):** Đua Top CVR. `Max CPC: $3.00`, `Min CPC: $0.80`, `Target ACOS: 45%`. Siết chặt Bleeder.
*   **Post-Season (Tàn cuộc):** Ép giá xuống đáy. `Max CPC: $1.00`, `Min CPC: $0.20`, `Target ACOS: 20%`.

---

## II. CHI TIẾT CÁC RULE TỐI ƯU (ACTION RULES)

### 1. Nhóm Cắt Máu & Phạt (Penalty Rules)

#### 1.1 Fatal_Bleeder_Zero_Sales (Cắt máu ngay lập tức)
*   **Logic Tiêu chuẩn:** `≥ 15 Clicks` mà `0 Orders`.
*   **Action:** `Pause` (Tắt keyword)
*   **Dynamic Phase:** 
    *   *Peak Season:* Siết chặt xuống `≥ 12 Clicks` (Tiền đắt, cắt máu nhanh hơn).
    *   *Post Season:* Siết chặt xuống `≥ 10 Clicks` (Hết mùa cắt thật nhanh).
    *   *Launch Phase:* Cho phép `≥ 20 Clicks` (Cần data để dò đường).

#### 1.2 Poor_CVR_Underperformer (Tỷ lệ chuyển đổi quá tệ)
*   **Logic Tiêu chuẩn:** `≥ 25 Clicks` nhưng chỉ có `≤ 1 Order` (CVR < 4%).
*   **Action:** `Giảm 30% Bid` (Decrease Bid Percentage). Thay vì Pause thẳng tay (để giữ lại lượng traffic tiềm năng).

#### 1.3 High_Traffic_Illusion (Traffic "Ảo")
*   **Logic Tiêu chuẩn:** `≥ 5000 Impressions` và `≥ 30 Clicks` nhưng `0 Orders`.
*   **Action:** `Pause` (Bị rào cản chuyển đổi cực lớn).

#### 1.4 Exact_Match_Relevance_Drop (Keyword Exact bị lệch tệp)
*   **Logic Tiêu chuẩn:** Match = `Exact`, `≥ 2000 Impressions` nhưng click cực thấp `≤ 3 Clicks` (0 Order).
*   **Action:** `Pause` (Tránh bị phạt điểm Relevance).

#### 1.5 Broad_Match_Discovery_Filter (Bộ lọc từ khóa mở rộng)
*   **Logic Tiêu chuẩn:** Match = `Broad/Auto`, `≥ 1000 Impressions`, `≤ 2 Clicks` (0 Order).
*   **Action:** `Giảm 20% Bid` (Hạn chế mua các Search term rác).

#### 1.6 High_ACOS_Bleeder (Giảm thầu Keyword đốt tiền)
*   **Logic Tiêu chuẩn:** Có đơn (`≥ 1 Order`), nhưng `ACOS > 40%`.
*   **Action:** `Giảm 15% Bid` (Ép lợi nhuận).
*   **Dynamic Phase:**
    *   *Peak Season:* Nới lỏng cho phép `ACOS > 50%` mới giảm thầu.
    *   *Mature Phase:* Siết chặt `ACOS > 35%`.
    *   *Launch Phase:* Nới lỏng cho phép `ACOS > 70%`.

### 2. Nhóm Tăng Cường & Nuôi Dưỡng (Scaling Rules)

#### 2.1 Profitable_Winner_Scale (Bơm máu cho Keyword đang thắng)
*   **Logic Tiêu chuẩn:** `≥ 3 Orders` và `ACOS < 20%`.
*   **Action:** `Tăng 20% Bid` (Scale mạnh).
*   **Dynamic Phase:**
    *   *Peak Season:* `ACOS < 25%` là đã cho tăng Bid.
    *   *Launch Phase:* `≥ 2 Orders` và `ACOS < 30%`.
    *   *Post Season:* Tắt rule này (Bằng cách set Orders > 9999).

#### 2.2 Dormant_High_Potential (Đánh thức Keyword ngủ quên)
*   **Logic Tiêu chuẩn:** `Impressions < 1000`, `Clicks ≥ 3`, `Orders ≥ 2`.
*   **Action:** `Tăng $0.15 Bid` (Kích để đẩy lên Trang 1).

#### 2.3 ACOS_Borderline_Tweak (Nắn chỉnh nhẹ Keyword ranh giới)
*   **Logic Tiêu chuẩn:** `Orders ≥ 2` và `25% ≤ ACOS ≤ 40%`.
*   **Action:** `Giảm nhẹ 5% Bid` (Nắn chỉnh liên tục hàng ngày).

---
**Tóm tắt luồng thực thi Phase 3:** Hệ thống lấy Keyword -> Dò tuổi đời -> Kích hoạt Rule tăng/giảm Bid -> So sánh với Guardrails. Nếu đụng Guardrails (ví dụ đòi Bid lên $3.5 trong khi trần là $2.5) -> Bóp Bid lại và gán cờ `REQUIRES_REVIEW`.
