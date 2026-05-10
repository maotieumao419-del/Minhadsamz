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
*   **Peak-Season (Bùng nổ):** Đua Top CVR. `Max CPC: $2.20`, `Min CPC: $0.80`, `Target ACOS: 45%`.
*   **Post-Season (Tàn cuộc):** Đóng băng. `Max CPC: $0.20`, `Min CPC: $0.10`, `Target ACOS: 20%`.

---

## II. CHI TIẾT CÁC RULE TỐI ƯU (ACTION RULES)

Trong hệ thống, các giai đoạn được chia thành 2 nhóm khi áp dụng luật để AI xử lý:

*   **Nhóm Giai đoạn Tiêu chuẩn (Growth Phase, Dormant Phase, Pre-Season):** Đây là các giai đoạn vận hành cân bằng, không có sự ưu tiên nới lỏng hay siết chặt. Các giai đoạn này **100% sử dụng bộ quy tắc Tiêu chuẩn (Base Rules)**.
*   **Nhóm Giai đoạn Đặc biệt (Launch, Mature, Peak Season, Post Season):** Có sự điều chỉnh linh hoạt (ngoại lệ) để phù hợp với mục tiêu đặc thù của từng giai đoạn.

Dưới đây là chi tiết các quy tắc xử lý:

### 1. Nhóm Cắt Máu & Phạt (Ngăn chặn thất thoát)

#### 1.1 Fatal_Bleeder_Zero_Sales (Cắt máu ngay lập tức)
*   **Đối với Giai đoạn Tiêu chuẩn (Growth, Dormant, Pre-season) và Mature Phase:** Nếu Keyword có từ **15 Clicks** trở lên mà **0 Order** thì sẽ **Pause**.
*   **Đối với Peak Season:** Nếu Keyword có từ **9 Clicks** trở lên mà **0 Order** thì sẽ **Pause** (Cắt máu cực nhanh để bảo vệ biên lợi nhuận của Ornament).
*   **Đối với Post Season:** Nếu Keyword có từ **10 Clicks** trở lên mà **0 Order** thì sẽ **Pause** (Hết mùa, cần cắt lỗ cực nhanh).
*   **Đối với Launch Phase:** Nếu Keyword có từ **20 Clicks** trở lên mà **0 Order** thì sẽ **Pause** (Cho phép cắn nhiều tiền hơn để lấy data ban đầu).

#### 1.2 High_ACOS_Bleeder (Giảm thầu Keyword đốt tiền)
*   **Đối với Giai đoạn Tiêu chuẩn (Growth, Dormant, Pre-season) và Post Season:** Nếu Keyword có đơn (**≥ 1 Order**) nhưng **ACOS ≥ 40%** thì sẽ **giảm 15% Bid**.
*   **Đối với Peak Season:** Nếu Keyword có đơn (**≥ 1 Order**) nhưng **ACOS ≥ 50%** thì sẽ **giảm 15% Bid** (Nới lỏng để tranh giành traffic).
*   **Đối với Launch Phase:** Nếu Keyword có đơn (**≥ 1 Order**) nhưng **ACOS ≥ 70%** thì sẽ **giảm 15% Bid** (Cho phép ACOS cực cao trong giai đoạn dò đường).
*   **Đối với Mature Phase:** Nếu Keyword có đơn (**≥ 1 Order**) nhưng **ACOS ≥ 35%** thì sẽ **giảm 15% Bid** (Siết chặt để vắt sữa lấy lãi).

#### 1.3 Poor_CVR_Underperformer (Tỷ lệ chuyển đổi quá tệ)
*   **Đối với Pre-Season:** Nếu Keyword có từ **35 Clicks** trở lên mà **≤ 1 Order** thì **giảm 30% Bid** (Nới lỏng để phủ phễu khách hàng Window Shopping).
*   **Đối với Peak Season:** Nếu Keyword có từ **20 Clicks** trở lên mà **≤ 1 Order** thì **giảm 30% Bid** (Siết chặt vì khách click mùa này là phải mua).
*   **Đối với các Giai đoạn khác (Base):** Nếu Keyword có từ **25 Clicks** trở lên mà chỉ có lẹt đẹt **≤ 1 Order** (CVR < 4%) thì sẽ **giảm 30% Bid**. (Giữ lại traffic rẻ thay vì tắt đi).

#### 1.4 High_Traffic_Illusion (Traffic "Ảo")
*   **Đối với MỌI GIAI ĐOẠN:** Nếu Keyword có **≥ 5000 Impressions** và **≥ 30 Clicks** mà vẫn **0 Order** thì sẽ **Pause**. (Rào cản chuyển đổi quá lớn).

#### 1.5 Exact_Match_Relevance_Drop (Keyword Exact bị lệch tệp)
*   **Đối với MỌI GIAI ĐOẠN:** Nếu Keyword dạng **Exact** có **≥ 2000 Impressions** mà tỷ lệ click quá thấp (**≤ 3 Clicks**) và **0 Order** thì sẽ **Pause** để tránh bị Amazon phạt điểm Relevance.

#### 1.6 Broad_Match_Discovery_Filter (Bộ lọc từ khóa mở rộng)
*   **Đối với MỌI GIAI ĐOẠN:** Nếu Keyword dạng **Broad/Auto** có **≥ 1000 Impressions**, tỷ lệ click thấp (**≤ 2 Clicks**) và **0 Order** thì sẽ **giảm 20% Bid** (Hạn chế mua nhầm từ khóa rác).

### 2. Nhóm Tăng Cường & Nuôi Dưỡng (Scale Lên)

#### 2.1 Profitable_Winner_Scale (Bơm máu cho Keyword đang thắng)
> [!WARNING]
> Cảnh báo rủi ro đứt hàng (Out of Stock): Ngành Gift/Ornament mùa Peak tiêu thụ rất nhanh. Hiện tại hệ thống tự động scale bid khi đạt ACOS tốt, bạn cần đặc biệt theo dõi số ngày tồn kho (Days of Supply) thủ công để tránh bị đẩy hết hàng trước tuần chót.

*   **Đối với Giai đoạn Tiêu chuẩn (Growth, Dormant, Pre-season) và Mature Phase:** Nếu Keyword có từ **3 Orders** trở lên và **ACOS ≤ 20%** thì sẽ **tăng 20% Bid**.
*   **Đối với Peak Season:** Nếu Keyword có từ **3 Orders** trở lên và **ACOS ≤ 25%** thì sẽ **tăng 20% Bid** (Nới lỏng điều kiện để bơm mạnh tiền, quét sạch đơn hàng).
*   **Đối với Launch Phase:** Nếu Keyword có từ **2 Orders** trở lên và **ACOS ≤ 30%** thì sẽ **tăng 20% Bid** (Chỉ cần 2 đơn và ACOS hơi cao cũng được scale ngay để tạo đà).
*   **Đối với Post Season:** Rule này sẽ bị **vô hiệu hóa** (hệ thống cài đặt cần ≥ 9999 Orders mới tăng thầu) vì không ai scale chiến dịch khi đã qua mùa.

#### 2.2 Dormant_High_Potential (Đánh thức Keyword ngủ quên)
*   **Đối với MỌI GIAI ĐOẠN:** Nếu Keyword hiển thị thấp (**< 1000 Impressions**) nhưng có tỷ lệ chuyển đổi cực tốt (**≥ 3 Clicks** và **≥ 2 Orders**) thì sẽ **tăng $0.15 Bid** vào giá gốc để kích nó nhảy lên trang 1.

### 3. Nhóm Nắn Chỉnh Nhẹ

#### 3.1 ACOS_Borderline_Tweak (Nắn chỉnh từ khóa ranh giới)
*   **Đối với MỌI GIAI ĐOẠN:** Nếu Keyword có từ **2 Orders** trở lên và ACOS lấp lửng từ **25% đến 40%** thì sẽ **giảm nhẹ 5% Bid** để dần nắn ACOS về mức sinh lời tốt hơn.

---
**Tóm tắt luồng thực thi Phase 3:** Hệ thống lấy Keyword -> Dò tuổi đời/mùa vụ -> Kích hoạt Rule tăng/giảm Bid -> So sánh với Guardrails. Nếu hành động vi phạm Guardrails (Ví dụ hệ thống đòi Bid lên $3.5 trong khi Max CPC quy định là $2.5) -> AI sẽ tự động ép Bid lại về mức Max CPC ($2.5) và gán cờ `REQUIRES_REVIEW` lên Dashboard để người dùng kiểm tra.
