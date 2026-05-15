# 🛡️ PROJECT AEGIS: SOVEREIGN DEFENSE MASTER BLUEPRINT
**Trạng thái:** Dự án Pilot (Thử nghiệm Sức mạnh Wisdom)
**Phiên bản:** 1.0 (2026-05-11)
**Đặc tính:** Dual-Use (Quân sự - Dân sự), Open-Source Core, AI-Driven.

---

## 👁️ LỚP 1: CẢM BIẾN (THE EYES)
- **Radar PLFM (Golden Node 66):** 10.5 GHz Phased Array, tầm xa 20km.
  - *Files:* `blueprints/PLFM_RADAR/4_Schematics`, `9_Firmware`.
- **Optical Fusion (Camera):** Camera nhiệt (Thermal) + Camera Zoom quang học.
  - *Blueprints:* `TUM-DFT/Radar-Camera-Fusion`.

## 🕸️ LỚP 2: KẾT NỐI (THE NERVOUS SYSTEM)
- **Wireless Serial Gateway:** `esp-link` chạy trên ESP32. Biến Radar Serial thành WiFi.
- **Fast Roaming WiFi:** Hệ điều hành OpenWRT (802.11r) đảm bảo Drone không rớt mạng khi bay xa.
- **Data Router:** `mavlink-router` để điều phối lệnh từ Radar đến bầy đàn Drone.

## 🧠 LỚP 3: TRÍ TUỆ NHÂN TẠO (THE BRAIN)
- **Signal Analysis:** `Micro-Doppler-Classification` để phân loại Drone vs Chim vs Động vật.
- **Vision Recognition:** `YOLOv8` để xác nhận mục tiêu bằng hình ảnh.
- **Autonomous Guidance:** `iq_gnc` (Guidance, Navigation, Control) để Drone tự động "đón bắn" mục tiêu.

## 🚀 LỚP 4: ĐỘNG LỰC HỌC (THE LEGS)
- **Propulsion:** `PCB-Motor` (Carl Bugeja) - In động cơ lên thân máy bay để giảm trọng lượng.
- **Motor Control:** `SimpleFOC` & `VESC` cho tốc độ và độ chính xác cực cao.
- **High-Speed Frame:** Thiết kế khung Drone Interceptor in 3D chịu lực cao.

## ⚔️ LỚP 5: THỰC THI & TIÊU DIỆT (THE ARMS)
- **Interception:** Bắn lưới (Net Gun) hoặc Drone cảm tử (Rammmer).
- **Anti-Swarm:** Mô phỏng vi ba công suất cao (HPM) bằng `openEMS`.
- **Cyber Takeover:** `DroneSploit` để bẻ khóa và chiếm quyền điều khiển drone địch.

## 🏭 LỚP 6: NHÀ MÁY SẢN XUẤT (THE WOMB)
- **Embedded Factory:** `PlatformIO Core` cho quy trình build/flash code chuẩn công nghiệp.
- **Sandbox Testing:** `Wokwi` để mô phỏng logic trước khi ráp mạch thật.
- **PCB Fabrication:** JLC-PCB (vật liệu Rogers 4350B cho RF).

---

### 📥 DANH MỤC TÀI LIỆU CẦN CHUẨN BỊ CHO CLAUDE:
1. `blueprints/PLFM_RADAR/` (Đã Clone).
2. `docs/SEED_40_AI_REPOS.md` (Node 55-68).
3. Các file cấu hình `platformio.ini` mẫu cho dự án.
4. Sơ đồ kết nối WiFi Mesh sử dụng OpenWRT.

**MỤC TIÊU PILOT:** 
"Xây dựng một hệ thống có thể phát hiện, bám bắt và vô hiệu hóa tự động 1 drone mục tiêu trong phạm vi 3km bằng phương pháp Drone-vs-Drone sử dụng AI hoàn toàn."
