# HƯỚNG DẪN SỬ DỤNG DETECT-ROW PACKAGE

## Tổng quan

Package `detect-row` là một thư viện Python được thiết kế để **phát hiện và trích xuất các hàng từ bảng trong ảnh**, với khả năng tích hợp OCR. Đã được publish lên PyPI tại: https://pypi.org/project/detect-row/

## Cài đặt

```bash
pip install detect-row
```

## Các chức năng chính

### 1. **AdvancedTableExtractor** - Phát hiện và trích xuất bảng

```python
from detect_row import AdvancedTableExtractor
import os

# Khởi tạo
table_extractor = AdvancedTableExtractor(
    input_dir=os.path.dirname("image0524.png"),  # Thư mục chứa ảnh
    output_dir="output/tables"                   # Thư mục lưu bảng đã trích xuất
)

# Xử lý ảnh
result = table_extractor.process_image("image0524.png", margin=5, check_text=True)

# Tìm các bảng đã trích xuất
table_files = []
tables_dir = "output/tables"

if os.path.exists(tables_dir):
    table_files = [f for f in os.listdir(tables_dir) if f.endswith('.jpg')]
    table_files.sort()

print(f"✅ Trích xuất được {len(table_files)} bảng")
```

### 2. **AdvancedRowExtractorMain** - Trích xuất rows từ bảng

```python
from detect_row import AdvancedRowExtractorMain
import cv2

# Khởi tạo
row_extractor = AdvancedRowExtractorMain()

# Đọc ảnh bảng
table_image = cv2.imread("output/tables/table_0.jpg")
table_name = "table_0"

# Trích xuất rows
rows_result = row_extractor.extract_rows_from_table(table_image, table_name)

# Xử lý kết quả
rows = []
if isinstance(rows_result, list):
    rows = rows_result
elif isinstance(rows_result, dict) and 'rows' in rows_result:
    rows = rows_result['rows']

print(f"✅ Trích xuất được {len(rows)} rows")

# Lưu từng row
for i, row_data in enumerate(rows):
    if isinstance(row_data, dict) and 'image' in row_data:
        row_image = row_data['image']
    elif isinstance(row_data, np.ndarray):
        row_image = row_data
    
    if row_image is not None:
        filename = f"{table_name}_row_{i:02d}.jpg"
        cv2.imwrite(f"output/rows/{filename}", row_image)
        print(f"💾 Đã lưu: {filename}")
```

### 3. **Phát hiện đường gạch dọc và OCR cột STT**

```python
import cv2
import numpy as np
import pytesseract
import re

def extract_first_column_stt(row_image, table_name, row_index):
    """Phát hiện đường gạch dọc và OCR cột đầu tiên (STT)"""
    height, width = row_image.shape[:2]
    
    # Chuyển sang grayscale nếu cần
    if len(row_image.shape) == 3:
        gray = cv2.cvtColor(row_image, cv2.COLOR_BGR2GRAY)
    else:
        gray = row_image.copy()
    
    # Phát hiện đường thẳng dọc bằng HoughLinesP
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    
    # Tìm đường thẳng dọc
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=int(height*0.3), 
                          minLineLength=int(height*0.5), maxLineGap=10)
    
    vertical_lines = []
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            # Kiểm tra đường thẳng dọc (góc gần 90 độ)
            if abs(x2 - x1) < 10:  # Đường gần như thẳng đứng
                vertical_lines.append((x1 + x2) // 2)  # Lấy tọa độ x trung bình
    
    # Tìm đường gạch dọc đầu tiên (gần nhất với bên trái)
    if vertical_lines:
        vertical_lines.sort()
        # Lọc các đường quá gần bên trái (có thể là viền bảng)
        valid_lines = [x for x in vertical_lines if x > width * 0.05]
        
        if valid_lines:
            first_column_width = valid_lines[0]
            print(f"🔍 Phát hiện đường gạch dọc tại x={first_column_width}px")
        else:
            # Fallback: sử dụng 20% nếu không tìm thấy đường gạch dọc hợp lệ
            first_column_width = int(width * 0.2)
            print(f"⚠️ Không tìm thấy đường gạch dọc, sử dụng 20% chiều rộng: {first_column_width}px")
    else:
        # Fallback: sử dụng 20% nếu không phát hiện được đường gạch dọc
        first_column_width = int(width * 0.2)
        print(f"⚠️ Không phát hiện đường gạch dọc, sử dụng 20% chiều rộng: {first_column_width}px")
    
    # Cắt cột đầu tiên
    first_column = row_image[:, :first_column_width]
    
    # Lưu cột đầu tiên để debug
    first_col_filename = f"{table_name}_row_{row_index:02d}_stt.jpg"
    cv2.imwrite(f"output/rows/{first_col_filename}", first_column)
    
    # OCR cột đầu tiên bằng pytesseract
    # Cấu hình OCR cho số
    custom_config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789'
    stt_text = pytesseract.image_to_string(first_column, config=custom_config).strip()
    
    # Lọc chỉ lấy số
    stt_numbers = re.findall(r'\d+', stt_text)
    stt = stt_numbers[0] if stt_numbers else ""
    
    if stt:
        print(f"📝 Row {row_index}: STT = {stt}")
    else:
        print(f"⚠️ Row {row_index}: Không phát hiện STT (raw: '{stt_text}')")
    
    return {
        "stt": stt,
        "raw_ocr_text": stt_text,
        "first_column_file": first_col_filename,
        "first_column_width": first_column_width
    }

# Sử dụng
for i, row_data in enumerate(rows):
    if isinstance(row_data, np.ndarray):
        row_image = row_data
        stt_result = extract_first_column_stt(row_image, "table_0", i)
        print(f"STT Row {i}: {stt_result['stt']}")
```

## Workflow hoàn chỉnh

### Bước 1: Tiền xử lý ảnh (tùy chọn)

```python
import cv2
import numpy as np

def preprocess_image(image_path):
    """Phát hiện và sửa góc nghiêng"""
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Phát hiện cạnh và đường thẳng
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)
    
    if lines is None:
        return image_path
    
    # Tính góc nghiêng
    angles = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        if x2 - x1 != 0:
            angle = np.arctan2(y2 - y1, x2 - x1) * 180.0 / np.pi
            if abs(angle) < 45:
                angles.append(angle)
    
    if not angles or abs(np.mean(angles)) < 1.0:
        return image_path
    
    # Xoay ảnh nếu cần
    angle_mean = np.mean(angles)
    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle_mean, 1.0)
    
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])
    new_w = int((h * sin) + (w * cos))
    new_h = int((h * cos) + (w * sin))
    
    M[0, 2] += (new_w / 2) - center[0]
    M[1, 2] += (new_h / 2) - center[1]
    
    rotated = cv2.warpAffine(img, M, (new_w, new_h), 
                            flags=cv2.INTER_LINEAR, 
                            borderMode=cv2.BORDER_CONSTANT, 
                            borderValue=(255, 255, 255))
    
    rotated_path = image_path.replace('.png', '_rotated.png')
    cv2.imwrite(rotated_path, rotated)
    return rotated_path
```

### Bước 2: Phát hiện và trích xuất bảng

```python
from detect_row import AdvancedTableExtractor

def extract_tables(image_path, output_dir="./output"):
    """Phát hiện và trích xuất bảng từ ảnh"""
    extractor = AdvancedTableExtractor(
        input_dir=os.path.dirname(image_path),
        output_dir=f"{output_dir}/tables",
        debug_dir=f"{output_dir}/debug"
    )
    
    result = extractor.process_image(image_path, margin=5, check_text=True)
    
    # Xử lý kết quả
    if isinstance(result.get('tables'), list):
        num_tables = len(result['tables'])
    else:
        num_tables = result.get('tables', 0)
    
    print(f"✅ Phát hiện {num_tables} bảng")
    return result
```

### Bước 3: Trích xuất hàng từ bảng

```python
import os
import cv2
import numpy as np

def extract_rows_from_tables(table_dir, row_output_dir):
    """Trích xuất hàng từ các bảng đã phát hiện"""
    os.makedirs(row_output_dir, exist_ok=True)
    
    table_files = [f for f in os.listdir(table_dir) if f.endswith(('.jpg', '.png'))]
    total_rows = 0
    
    for table_file in table_files:
        table_path = os.path.join(table_dir, table_file)
        table_name = os.path.splitext(table_file)[0]
        
        # Đọc ảnh bảng
        img = cv2.imread(table_path)
        if img is None:
            continue
        
        # Chuyển sang ảnh xám
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Phát hiện đường kẻ ngang
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (img.shape[1]//10, 1))
        horizontal = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)
        
        # Tìm vị trí đường kẻ
        h_sum = np.sum(horizontal, axis=1)
        threshold = np.max(h_sum) * 0.3
        
        line_positions = []
        for i, val in enumerate(h_sum):
            if val > threshold:
                line_positions.append(i)
        
        # Lọc đường kẻ gần nhau
        if len(line_positions) > 1:
            filtered = [line_positions[0]]
            for pos in line_positions[1:]:
                if pos - filtered[-1] > 20:  # Khoảng cách tối thiểu
                    filtered.append(pos)
            line_positions = filtered
        
        # Cắt hàng
        rows_count = 0
        if len(line_positions) >= 2:
            for i in range(len(line_positions) - 1):
                y1 = max(0, line_positions[i])
                y2 = min(img.shape[0], line_positions[i + 1])
                
                if y2 - y1 > 15:  # Chiều cao tối thiểu
                    row_img = img[y1:y2, :]
                    row_path = os.path.join(row_output_dir, f"{table_name}_row_{i:02d}.jpg")
                    cv2.imwrite(row_path, row_img)
                    rows_count += 1
                    total_rows += 1
        
        print(f"  Trích xuất {rows_count} hàng từ {table_file}")
    
    print(f"✅ Tổng cộng trích xuất {total_rows} hàng từ {len(table_files)} bảng")
    return total_rows
```

### Bước 4: OCR (tùy chọn)

```python
from detect_row import TesseractRowExtractor

def perform_ocr(image_path, output_dir="./output"):
    """Thực hiện OCR trên ảnh"""
    extractor = TesseractRowExtractor(
        input_dir=os.path.dirname(image_path),
        output_dir=f"{output_dir}/ocr",
        debug_dir=f"{output_dir}/ocr_debug"
    )
    
    result = extractor.process_image(
        image_path,
        lang="vie+eng",           # Tiếng Việt + Tiếng Anh
        config="--oem 1 --psm 6", # Cấu hình Tesseract
        output_format="json"
    )
    
    # Xử lý kết quả OCR
    total_text_rows = 0
    if 'data' in result and result['data']:
        total_text_rows = sum(item.get('rows', 0) for item in result['data'])
    
    print(f"✅ OCR phát hiện {total_text_rows} hàng có text")
    return result
```

## Ví dụ sử dụng hoàn chỉnh

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import cv2
import numpy as np
import json
from datetime import datetime
from detect_row import AdvancedTableExtractor, AdvancedRowExtractorMain
import pytesseract
import re

def ensure_dir(path: str):
    """Tạo thư mục nếu chưa có"""
    os.makedirs(path, exist_ok=True)
    print(f"📁 Created directory: {path}")

def extract_first_column_stt(row_image, table_name, row_index, output_dir):
    """Phát hiện đường gạch dọc và OCR cột đầu tiên (STT)"""
    height, width = row_image.shape[:2]
    
    # Chuyển sang grayscale nếu cần
    if len(row_image.shape) == 3:
        gray = cv2.cvtColor(row_image, cv2.COLOR_BGR2GRAY)
    else:
        gray = row_image.copy()
    
    # Phát hiện đường thẳng dọc bằng HoughLinesP
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=int(height*0.3), 
                          minLineLength=int(height*0.5), maxLineGap=10)
    
    vertical_lines = []
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if abs(x2 - x1) < 10:  # Đường gần như thẳng đứng
                vertical_lines.append((x1 + x2) // 2)
    
    # Tìm đường gạch dọc đầu tiên
    if vertical_lines:
        vertical_lines.sort()
        valid_lines = [x for x in vertical_lines if x > width * 0.05]
        
        if valid_lines:
            first_column_width = valid_lines[0]
            print(f"🔍 Phát hiện đường gạch dọc tại x={first_column_width}px")
        else:
            first_column_width = int(width * 0.2)
            print(f"⚠️ Sử dụng 20% chiều rộng: {first_column_width}px")
    else:
        first_column_width = int(width * 0.2)
        print(f"⚠️ Không phát hiện đường gạch dọc, sử dụng 20%: {first_column_width}px")
    
    # Cắt cột đầu tiên
    first_column = row_image[:, :first_column_width]
    
    # Lưu cột đầu tiên
    first_col_filename = f"{table_name}_row_{row_index:02d}_stt.jpg"
    first_col_path = os.path.join(output_dir, "rows", first_col_filename)
    cv2.imwrite(first_col_path, first_column)
    
    # OCR cột đầu tiên
    custom_config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789'
    stt_text = pytesseract.image_to_string(first_column, config=custom_config).strip()
    
    # Lọc chỉ lấy số
    stt_numbers = re.findall(r'\d+', stt_text)
    stt = stt_numbers[0] if stt_numbers else ""
    
    return {
        "stt": stt,
        "raw_ocr_text": stt_text,
        "first_column_file": first_col_filename,
        "first_column_width": first_column_width
    }

def process_image_complete(image_path="image0524.png", output_base="output"):
    """Xử lý ảnh hoàn chỉnh từ A đến Z"""
    
    print(f"🚀 TRÍCH XUẤT BẢNG SỬ DỤNG PACKAGE DETECT-ROW")
    print(f"📸 Ảnh đầu vào: {image_path}")
    print(f"📁 Thư mục đầu ra: {output_base}")
    print(f"⏰ Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not os.path.exists(image_path):
        print(f"❌ Không tìm thấy ảnh: {image_path}")
        return
    
    # Tạo thư mục output
    ensure_dir(output_base)
    ensure_dir(f"{output_base}/tables")
    ensure_dir(f"{output_base}/rows")
    ensure_dir(f"{output_base}/ocr")
    
    # Bước 1: Trích xuất bảng
    print(f"\n{'='*60}")
    print("BƯỚC 1: TRÍCH XUẤT BẢNG")
    print(f"{'='*60}")
    
    table_extractor = AdvancedTableExtractor(
        input_dir=os.path.dirname(image_path),
        output_dir=f"{output_base}/tables"
    )
    
    result = table_extractor.process_image(image_path, margin=5, check_text=True)
    
    # Tìm các bảng đã trích xuất
    table_files = []
    tables_dir = f"{output_base}/tables"
    
    if os.path.exists(tables_dir):
        table_files = [f for f in os.listdir(tables_dir) if f.endswith('.jpg')]
        table_files.sort()
    
    if not table_files:
        print("❌ Không trích xuất được bảng nào!")
        return
    
    print(f"✅ Trích xuất được {len(table_files)} bảng")
    
    # Bước 2: Trích xuất rows
    print(f"\n{'='*60}")
    print("BƯỚC 2: TRÍCH XUẤT ROWS VÀ OCR STT")
    print(f"{'='*60}")
    
    all_results = []
    row_extractor = AdvancedRowExtractorMain()
    
    for table_file in table_files:
        table_path = os.path.join(tables_dir, table_file)
        table_name = os.path.splitext(table_file)[0]
        
        print(f"\n--- Xử lý {table_name} ---")
        
        # Đọc ảnh bảng
        table_image = cv2.imread(table_path)
        if table_image is None:
            continue
        
        # Trích xuất rows
        rows_result = row_extractor.extract_rows_from_table(table_image, table_name)
        
        # Xử lý kết quả
        rows = []
        if isinstance(rows_result, list):
            rows = rows_result
        elif isinstance(rows_result, dict) and 'rows' in rows_result:
            rows = rows_result['rows']
        
        if not rows:
            print("⚠️ Không trích xuất được rows")
            continue
        
        print(f"✅ Trích xuất được {len(rows)} rows")
        
        # Lưu từng row và OCR STT
        ocr_results = []
        for i, row_data in enumerate(rows):
            row_image = None
            
            if isinstance(row_data, dict) and 'image' in row_data:
                row_image = row_data['image']
            elif isinstance(row_data, np.ndarray):
                row_image = row_data
            
            if row_image is not None:
                # Lưu row
                filename = f"{table_name}_row_{i:02d}.jpg"
                filepath = os.path.join(output_base, "rows", filename)
                cv2.imwrite(filepath, row_image)
                print(f"💾 Đã lưu: {filename}")
                
                # OCR STT
                try:
                    stt_result = extract_first_column_stt(row_image, table_name, i, output_base)
                    row_ocr = {
                        "row_index": i,
                        "filename": filename,
                        **stt_result
                    }
                    ocr_results.append(row_ocr)
                    
                    if stt_result['stt']:
                        print(f"📝 Row {i}: STT = {stt_result['stt']}")
                    else:
                        print(f"⚠️ Row {i}: Không phát hiện STT")
                        
                except Exception as e:
                    print(f"⚠️ Lỗi OCR row {i}: {e}")
        
        # Lưu kết quả OCR
        ocr_file = os.path.join(output_base, "ocr", f"{table_name}_ocr.json")
        with open(ocr_file, 'w', encoding='utf-8') as f:
            json.dump(ocr_results, f, indent=2, ensure_ascii=False)
        
        all_results.append({
            "table_name": table_name,
            "total_rows": len(rows),
            "ocr_results": ocr_results,
            "success": True
        })
    
    # Tổng kết
    total_tables = len(all_results)
    total_rows = sum(r['total_rows'] for r in all_results)
    
    print(f"\n🎉 HOÀN THÀNH!")
    print(f"✅ Đã xử lý: {total_tables} bảng")
    print(f"✅ Đã trích xuất: {total_rows} rows")
    print(f"📁 Kết quả lưu tại: {output_base}/")
    
    return all_results

# Sử dụng
if __name__ == "__main__":
    results = process_image_complete("image0524.png", "my_output")
```

## Các tham số quan trọng

### AdvancedTableExtractor

- `margin`: Khoảng cách viền xung quanh bảng (mặc định: 5)
- `check_text`: Kiểm tra text trong bảng (mặc định: True)

### TesseractRowExtractor

- `lang`: Ngôn ngữ OCR ("vie", "eng", "vie+eng")
- `config`: Cấu hình Tesseract
  - `--oem 1`: OCR Engine Mode
  - `--psm 6`: Page Segmentation Mode 
- `min_row_height`: Chiều cao tối thiểu của hàng (pixel)

## Lưu ý

1. **Yêu cầu hệ thống:**
   - Python >= 3.6
   - OpenCV
   - Tesseract OCR (cho chức năng OCR)

2. **Cài đặt Tesseract:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr tesseract-ocr-vie
   
   # Windows: Download từ https://github.com/UB-Mannheim/tesseract/wiki
   ```

3. **Chất lượng ảnh:**
   - Ảnh nên có độ phân giải cao (>= 300 DPI)
   - Tránh ảnh bị mờ hoặc nghiêng quá nhiều
   - Đường kẻ bảng rõ ràng sẽ cho kết quả tốt hơn

4. **Phát hiện đường gạch dọc:**
   - Thuật toán HoughLinesP được sử dụng để phát hiện đường gạch dọc
   - Nếu không phát hiện được, sẽ fallback về 20% chiều rộng
   - Đường gạch dọc giúp cắt cột STT chính xác hơn

5. **OCR cột STT:**
   - Sử dụng pytesseract với cấu hình chỉ nhận diện số (0-9)
   - Kết quả được lọc bằng regex để chỉ lấy số
   - Lưu cả ảnh cột STT và kết quả OCR để debug

## Cấu trúc output

```
output/
├── tables/                    # Các bảng đã trích xuất
│   ├── table_0.jpg
│   └── table_1.jpg
├── rows/                      # Các hàng đã cắt từ bảng
│   ├── table_0_row_00.jpg     # Row đầy đủ
│   ├── table_0_row_00_stt.jpg # Cột STT đã cắt
│   ├── table_0_row_01.jpg
│   ├── table_0_row_01_stt.jpg
│   ├── table_1_row_00.jpg
│   ├── table_1_row_00_stt.jpg
│   └── ...
├── ocr/                       # Kết quả OCR STT
│   ├── table_0_ocr.json       # Kết quả OCR bảng 0
│   └── table_1_ocr.json       # Kết quả OCR bảng 1
└── analysis/                  # Phân tích và báo cáo
    ├── summary_visualization.png
    ├── pip_package_summary.json
    └── pip_package_report.txt
```

### Ví dụ nội dung file OCR JSON:

```json
[
  {
    "row_index": 0,
    "filename": "table_0_row_00.jpg",
    "first_column_file": "table_0_row_00_stt.jpg",
    "stt": "1",
    "raw_ocr_text": "1",
    "first_column_width": 108
  },
  {
    "row_index": 1,
    "filename": "table_0_row_01.jpg",
    "first_column_file": "table_0_row_01_stt.jpg",
    "stt": "2",
    "raw_ocr_text": "2",
    "first_column_width": 108
  }
]
```

## Xử lý lỗi thường gặp

### 1. Import Error
```python
# Đảm bảo đã cài đặt
pip install detect-row

# Kiểm tra version
import detect_row
print(detect_row.__version__)
```

### 2. Tesseract not found
```bash
# Cài đặt Tesseract và thêm vào PATH
# Hoặc set đường dẫn trong code:
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### 3. Unicode encoding (Windows)
```python
# Sử dụng UTF-8 encoding
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
```

## Tích hợp vào dự án

Package này được thiết kế để dễ dàng tích hợp vào các dự án xử lý tài liệu, đặc biệt phù hợp với:
- Xử lý phiếu bầu cử
- Digitization tài liệu
- Trích xuất dữ liệu từ bảng biểu
- OCR tài liệu tiếng Việt

## Support

- GitHub: (Nếu có)
- PyPI: https://pypi.org/project/detect-row/
- Issues: Báo cáo lỗi qua GitHub Issues

---

*Hướng dẫn này được tạo dựa trên package detect-row version 1.0.1* 