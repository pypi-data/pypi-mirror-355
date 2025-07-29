#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trích xuất bảng và rows - Phiên bản Advanced
==========================================

Script này sử dụng các kỹ thuật nâng cao:
1. Phát hiện bảng với contour analysis
2. Phân tích cấu trúc bảng (grid detection)
3. Trích xuất rows với machine learning approach
4. Loại bỏ header thông minh
5. Optimization cho độ chính xác cao

Sử dụng: python extract_table_advanced.py
"""

import os
import cv2
import numpy as np
import json
from datetime import datetime
from typing import List, Tuple, Dict, Any
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN

# Import detect_row
try:
    from detect_row import AdvancedTableExtractor
    print(f"✅ Imported detect_row successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)

def ensure_dir(path: str):
    """Tạo thư mục nếu chưa có"""
    os.makedirs(path, exist_ok=True)
    print(f"📁 Created directory: {path}")

def advanced_line_detection(image: np.ndarray, min_line_length: int = 50) -> List[List[int]]:
    """
    Phát hiện đường kẻ ngang nâng cao với HoughLinesP
    
    Args:
        image: Ảnh đầu vào (grayscale)
        min_line_length: Độ dài tối thiểu của đường kẻ
    
    Returns:
        List[List[int]]: Danh sách các đường kẻ ngang [x1, y1, x2, y2]
    """
    # Canny edge detection
    edges = cv2.Canny(image, 50, 150, apertureSize=3)
    
    # HoughLinesP để phát hiện đường kẻ
    lines = cv2.HoughLinesP(
        edges, 
        rho=1, 
        theta=np.pi/180, 
        threshold=100,
        minLineLength=min_line_length,
        maxLineGap=10
    )
    
    horizontal_lines = []
    
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            
            # Kiểm tra xem có phải đường ngang không (góc nhỏ)
            if abs(y2 - y1) <= 5:  # Độ lệch dọc nhỏ
                horizontal_lines.append([x1, y1, x2, y2])
    
    print(f"🔍 Phát hiện {len(horizontal_lines)} đường kẻ ngang bằng HoughLines")
    return horizontal_lines

def cluster_horizontal_lines(lines: List[List[int]], eps: int = 10) -> List[int]:
    """
    Gom nhóm các đường kẻ ngang thành các nhóm theo tọa độ y
    
    Args:
        lines: Danh sách đường kẻ ngang
        eps: Khoảng cách tối đa để gom nhóm
    
    Returns:
        List[int]: Danh sách tọa độ y đại diện cho từng nhóm
    """
    if not lines:
        return []
    
    # Lấy tọa độ y trung bình của mỗi đường kẻ
    y_coords = []
    for line in lines:
        x1, y1, x2, y2 = line
        y_avg = (y1 + y2) // 2
        y_coords.append([y_avg])
    
    # Sử dụng DBSCAN để gom nhóm
    if len(y_coords) > 1:
        clustering = DBSCAN(eps=eps, min_samples=1).fit(y_coords)
        labels = clustering.labels_
        
        # Tính tọa độ y trung bình cho mỗi cluster
        unique_labels = set(labels)
        clustered_lines = []
        
        for label in unique_labels:
            if label != -1:  # Bỏ qua noise
                cluster_points = [y_coords[i][0] for i in range(len(labels)) if labels[i] == label]
                avg_y = int(np.mean(cluster_points))
                clustered_lines.append(avg_y)
        
        clustered_lines.sort()
        print(f"📊 Gom nhóm thành {len(clustered_lines)} đường kẻ chính")
        return clustered_lines
    else:
        return [y_coords[0][0]] if y_coords else []

def analyze_table_structure(image: np.ndarray) -> Dict[str, Any]:
    """
    Phân tích cấu trúc bảng nâng cao
    
    Args:
        image: Ảnh bảng
    
    Returns:
        Dict: Thông tin cấu trúc bảng
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    height, width = gray.shape
    
    # Phát hiện đường kẻ ngang
    horizontal_lines = advanced_line_detection(gray, min_line_length=width//4)
    
    # Gom nhóm đường kẻ
    clustered_y = cluster_horizontal_lines(horizontal_lines, eps=15)
    
    # Thêm viền trên và dưới nếu cần
    if not clustered_y or clustered_y[0] > 20:
        clustered_y.insert(0, 0)
    if not clustered_y or clustered_y[-1] < height - 20:
        clustered_y.append(height)
    
    # Phân tích rows
    rows_info = []
    for i in range(len(clustered_y) - 1):
        y1 = clustered_y[i]
        y2 = clustered_y[i + 1]
        row_height = y2 - y1
        
        # Phân tích nội dung row
        row_region = gray[y1:y2, :]
        
        # Tính mật độ pixel tối (text)
        _, binary = cv2.threshold(row_region, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        text_density = np.sum(binary == 255) / binary.size
        
        # Phân tích horizontal projection
        h_projection = np.sum(binary, axis=1)
        has_strong_text = np.max(h_projection) > width * 10  # Ngưỡng text mạnh
        
        row_info = {
            "index": i,
            "y1": y1,
            "y2": y2,
            "height": row_height,
            "text_density": text_density,
            "has_strong_text": has_strong_text,
            "is_likely_header": i == 0 and (text_density > 0.05 or row_height > 50)
        }
        rows_info.append(row_info)
    
    structure = {
        "total_rows": len(rows_info),
        "rows": rows_info,
        "horizontal_lines": horizontal_lines,
        "clustered_lines": clustered_y,
        "table_height": height,
        "table_width": width
    }
    
    return structure

def extract_rows_advanced(image: np.ndarray, structure: Dict[str, Any], skip_header: bool = True) -> List[Dict[str, Any]]:
    """
    Trích xuất rows với phương pháp nâng cao
    
    Args:
        image: Ảnh bảng gốc
        structure: Cấu trúc bảng đã phân tích  
        skip_header: Có bỏ qua header không
    
    Returns:
        List[Dict]: Danh sách thông tin rows đã trích xuất
    """
    extracted_rows = []
    
    for row_info in structure["rows"]:
        i = row_info["index"]
        y1 = row_info["y1"]
        y2 = row_info["y2"]
        
        # Quyết định có trích xuất row này không
        should_extract = True
        skip_reason = ""
        
        # Bỏ qua header nếu cần
        if skip_header and row_info.get("is_likely_header", False):
            should_extract = False
            skip_reason = "Header row"
        
        # Bỏ qua row quá thấp
        if row_info["height"] < 20:
            should_extract = False
            skip_reason = "Too small"
        
        # Bỏ qua row không có text
        if row_info["text_density"] < 0.005:
            should_extract = False
            skip_reason = "No text content"
        
        if should_extract:
            # Trích xuất row với margin nhỏ
            margin = 2
            y1_adj = max(0, y1 + margin)
            y2_adj = min(image.shape[0], y2 - margin)
            
            row_image = image[y1_adj:y2_adj, :]
            
            # Lưu thông tin row đã trích xuất
            extracted_info = {
                "original_index": i,
                "extracted_index": len(extracted_rows),
                "y1": y1_adj,
                "y2": y2_adj,
                "height": y2_adj - y1_adj,
                "text_density": row_info["text_density"],
                "has_strong_text": row_info["has_strong_text"],
                "row_image": row_image,
                "skip_reason": None
            }
            extracted_rows.append(extracted_info)
            
            print(f"✅ Trích xuất Row {len(extracted_rows)}: y={y1_adj}-{y2_adj} (h={y2_adj - y1_adj}px) - Density: {row_info['text_density']:.3f}")
        else:
            print(f"⏭️ Bỏ qua Row {i}: {skip_reason} - y={y1}-{y2} (h={row_info['height']}px)")
    
    return extracted_rows

def save_extracted_rows(rows: List[Dict[str, Any]], output_dir: str, table_name: str) -> List[str]:
    """
    Lưu các rows đã trích xuất
    
    Args:
        rows: Danh sách rows đã trích xuất
        output_dir: Thư mục lưu
        table_name: Tên bảng
    
    Returns:
        List[str]: Danh sách đường dẫn files đã lưu
    """
    saved_files = []
    
    for row_info in rows:
        extracted_idx = row_info["extracted_index"]
        row_image = row_info["row_image"]
        
        # Tạo tên file
        filename = f"{table_name}_row_{extracted_idx:02d}.jpg"
        filepath = os.path.join(output_dir, filename)
        
        # Lưu ảnh
        cv2.imwrite(filepath, row_image)
        saved_files.append(filepath)
        
        print(f"💾 Đã lưu: {filename}")
    
    return saved_files

def create_visualization(image: np.ndarray, structure: Dict[str, Any], output_path: str):
    """
    Tạo visualization cho việc phân tích bảng
    
    Args:
        image: Ảnh bảng gốc
        structure: Cấu trúc đã phân tích
        output_path: Đường dẫn lưu visualization
    """
    fig, axes = plt.subplots(1, 2, figsize=(15, 8))
    
    # Ảnh gốc với đường kẻ được phát hiện
    axes[0].imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    axes[0].set_title('Bảng gốc + Đường kẻ phát hiện')
    
    # Vẽ các đường kẻ đã gom nhóm
    for y in structure["clustered_lines"]:
        axes[0].axhline(y=y, color='red', linestyle='--', linewidth=2, alpha=0.7)
    
    # Đánh số rows
    for i, row in enumerate(structure["rows"]):
        y_center = (row["y1"] + row["y2"]) // 2
        axes[0].text(10, y_center, f'Row {i}', color='blue', fontsize=12, fontweight='bold')
    
    axes[0].set_xlim(0, image.shape[1])
    axes[0].set_ylim(image.shape[0], 0)
    
    # Biểu đồ text density
    row_indices = [r["index"] for r in structure["rows"]]
    text_densities = [r["text_density"] for r in structure["rows"]]
    
    axes[1].bar(row_indices, text_densities, alpha=0.7)
    axes[1].set_title('Mật độ Text theo Row')
    axes[1].set_xlabel('Row Index')
    axes[1].set_ylabel('Text Density')
    axes[1].grid(True, alpha=0.3)
    
    # Đánh dấu header
    for i, row in enumerate(structure["rows"]):
        if row.get("is_likely_header", False):
            axes[1].bar(i, row["text_density"], color='red', alpha=0.8, label='Header')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"📊 Đã lưu visualization: {output_path}")

def main():
    """Hàm chính"""
    image_path = "image0524.png"
    output_base = "advanced_extraction_output"
    
    print(f"🚀 TRÍCH XUẤT BẢNG NÂNG CAO (ADVANCED)")
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
    ensure_dir(f"{output_base}/analysis")
    ensure_dir(f"{output_base}/debug")
    
    # Bước 1: Trích xuất bảng
    print(f"\n{'='*60}")
    print("BƯỚC 1: TRÍCH XUẤT BẢNG")
    print(f"{'='*60}")
    
    extractor = AdvancedTableExtractor(
        input_dir=os.path.dirname(image_path),
        output_dir=f"{output_base}/tables",
        debug_dir=f"{output_base}/debug"
    )
    
    result = extractor.process_image(image_path, margin=5, check_text=True)
    
    # Tìm các bảng đã trích xuất
    table_files = [f for f in os.listdir(f"{output_base}/tables") if f.endswith('.jpg')]
    
    if not table_files:
        print("❌ Không trích xuất được bảng nào!")
        return
    
    print(f"✅ Trích xuất được {len(table_files)} bảng")
    
    # Bước 2: Phân tích và trích xuất rows cho từng bảng
    print(f"\n{'='*60}")
    print("BƯỚC 2: PHÂN TÍCH VÀ TRÍCH XUẤT ROWS")
    print(f"{'='*60}")
    
    all_results = []
    
    for i, table_file in enumerate(sorted(table_files)):
        table_path = os.path.join(f"{output_base}/tables", table_file)
        table_name = os.path.splitext(table_file)[0]
        
        print(f"\n--- Xử lý {table_file} ({i+1}/{len(table_files)}) ---")
        
        # Đọc ảnh bảng
        table_image = cv2.imread(table_path)
        if table_image is None:
            print(f"❌ Không thể đọc {table_path}")
            continue
        
        # Phân tích cấu trúc bảng
        print("🔍 Phân tích cấu trúc bảng...")
        structure = analyze_table_structure(table_image)
        
        print(f"📊 Phát hiện {structure['total_rows']} rows tiềm năng")
        
        # Trích xuất rows (bỏ qua header)
        print("✂️ Trích xuất rows...")
        extracted_rows = extract_rows_advanced(table_image, structure, skip_header=True)
        
        # Lưu rows
        saved_files = save_extracted_rows(extracted_rows, f"{output_base}/rows", table_name)
        
        # Tạo visualization
        viz_path = os.path.join(f"{output_base}/analysis", f"{table_name}_analysis.png")
        create_visualization(table_image, structure, viz_path)
        
        # Lưu phân tích JSON (sửa lỗi serialization)
        analysis_file = os.path.join(f"{output_base}/analysis", f"{table_name}_structure.json")
        try:
            with open(analysis_file, 'w', encoding='utf-8') as f:
                # Loại bỏ row_image và convert numpy types
                clean_structure = {}
                for k, v in structure.items():
                    if k == 'rows':
                        clean_rows_structure = []
                        for row in v:
                            clean_row_struct = {}
                            for rk, rv in row.items():
                                # Convert numpy bool to Python bool
                                if isinstance(rv, (bool, np.bool_)):
                                    clean_row_struct[rk] = bool(rv)
                                elif isinstance(rv, (int, np.integer)):
                                    clean_row_struct[rk] = int(rv)
                                elif isinstance(rv, (float, np.floating)):
                                    clean_row_struct[rk] = float(rv)
                                else:
                                    clean_row_struct[rk] = rv
                            clean_rows_structure.append(clean_row_struct)
                        clean_structure[k] = clean_rows_structure
                    else:
                        clean_structure[k] = v
                
                clean_rows = []
                for row in extracted_rows:
                    clean_row = {}
                    for k, v in row.items():
                        if k != 'row_image':
                            # Convert numpy types to Python types
                            if isinstance(v, (bool, np.bool_)):
                                clean_row[k] = bool(v)
                            elif isinstance(v, (int, np.integer)):
                                clean_row[k] = int(v)
                            elif isinstance(v, (float, np.floating)):
                                clean_row[k] = float(v)
                            else:
                                clean_row[k] = v
                    clean_rows.append(clean_row)
                
                analysis_data = {
                    "table_name": table_name,
                    "structure": clean_structure,
                    "extracted_rows": clean_rows,
                    "saved_files": saved_files
                }
                json.dump(analysis_data, f, indent=2, ensure_ascii=False)
                print(f"📄 Đã lưu phân tích: {analysis_file}")
        except Exception as e:
            print(f"⚠️ Lỗi lưu JSON: {e}, bỏ qua...")
        
        all_results.append({
            "table_name": table_name,
            "total_rows_detected": structure['total_rows'],
            "rows_extracted": len(extracted_rows),
            "saved_files": saved_files
        })
    
    # Bước 3: Tạo báo cáo tổng hợp
    print(f"\n{'='*60}")
    print("BƯỚC 3: BÁO CÁO TỔNG HỢP")
    print(f"{'='*60}")
    
    total_tables = len(all_results)
    total_rows = sum(r["rows_extracted"] for r in all_results)
    
    summary = {
        "timestamp": datetime.now().isoformat(),
        "method": "Advanced Table Extraction",
        "total_tables": total_tables,
        "total_rows_extracted": total_rows,
        "results": all_results
    }
    
    # Lưu báo cáo
    summary_file = os.path.join(output_base, "advanced_summary.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    # Báo cáo text
    report_file = os.path.join(output_base, "advanced_report.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("BÁO CÁO TRÍCH XUẤT BẢNG NÂNG CAO\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Phương pháp: Advanced Table Extraction\n")
        f.write(f"Tổng số bảng: {total_tables}\n")
        f.write(f"Tổng số rows: {total_rows}\n\n")
        
        f.write("CHI TIẾT:\n")
        f.write("-" * 20 + "\n")
        for result in all_results:
            f.write(f"\nBảng: {result['table_name']}\n")
            f.write(f"  Rows phát hiện: {result['total_rows_detected']}\n")
            f.write(f"  Rows trích xuất: {result['rows_extracted']}\n")
            f.write(f"  Files lưu: {len(result['saved_files'])}\n")
    
    # Tổng kết
    print(f"🎉 HOÀN THÀNH TRÍCH XUẤT NÂNG CAO!")
    print(f"✅ Đã xử lý: {total_tables} bảng")
    print(f"✅ Đã trích xuất: {total_rows} rows")
    print(f"📁 Kết quả lưu tại: {output_base}/")
    print(f"  📊 Bảng: {output_base}/tables/")
    print(f"  📋 Rows: {output_base}/rows/")
    print(f"  📈 Phân tích: {output_base}/analysis/")
    print(f"  🐛 Debug: {output_base}/debug/")
    
    # Hiển thị danh sách rows
    rows_dir = f"{output_base}/rows"
    if os.path.exists(rows_dir):
        row_files = sorted([f for f in os.listdir(rows_dir) if f.endswith('.jpg')])
        if row_files:
            print(f"\n📋 {len(row_files)} rows đã trích xuất:")
            for row_file in row_files:
                print(f"  - {row_file}")

if __name__ == "__main__":
    main() 