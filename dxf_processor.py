import ezdxf
from ezdxf import bbox
import os
import math
from typing import List, Tuple, Dict
import numpy as np

class DXFProcessor:
    def __init__(self):
        self.documents = []
        self.bounding_boxes = []
        
    def read_dxf_files(self, file_paths: List[str]) -> bool:
        """读取多个DXF文件"""
        self.documents = []
        
        for file_path in file_paths:
            try:
                doc = ezdxf.readfile(file_path)
                self.documents.append({
                    'doc': doc,
                    'file_path': file_path,
                    'name': os.path.basename(file_path)
                })
                print(f"成功读取文件: {file_path}")
            except Exception as e:
                print(f"读取文件失败 {file_path}: {e}")
                return False
                
        return True
    
    def calculate_bounding_boxes(self) -> bool:
        """计算每个DXF文件的最小外包矩形"""
        self.bounding_boxes = []
        
        for doc_info in self.documents:
            try:
                doc = doc_info['doc']
                msp = doc.modelspace()
                
                # 计算包围盒
                bounding_box = bbox.extents(msp)
                if bounding_box.has_data:
                    extent = bounding_box.extmax - bounding_box.extmin
                    width = extent.x
                    height = extent.y
                    
                    self.bounding_boxes.append({
                        'doc_info': doc_info,
                        'bbox': bounding_box,
                        'width': width,
                        'height': height,
                        'original_extmin': bounding_box.extmin.copy(),
                        'original_extmax': bounding_box.extmax.copy()
                    })
                    print(f"文件 {doc_info['name']} 的外包矩形: {width:.2f} x {height:.2f}")
                else:
                    print(f"警告: 文件 {doc_info['name']} 没有找到几何实体")
                    return False
                    
            except Exception as e:
                print(f"计算外包矩形失败 {doc_info['name']}: {e}")
                return False
                
        return True
    
    def pack_rectangles(self, container_width: float = 100.0, container_height: float = 100.0, gap: float = 0.5) -> List[Dict]:
        """网格排样算法 - 从左到右，从上到下排列，然后整体居中"""
        # 按面积降序排序
        sorted_boxes = sorted(self.bounding_boxes, 
                            key=lambda x: x['width'] * x['height'], 
                            reverse=True)
        
        # 计算网格行列数
        total_area = sum(box['width'] * box['height'] for box in sorted_boxes)
        avg_width = sum(box['width'] for box in sorted_boxes) / len(sorted_boxes) if sorted_boxes else 1
        avg_height = sum(box['height'] for box in sorted_boxes) / len(sorted_boxes) if sorted_boxes else 1
        
        # 估算网格尺寸
        grid_cols = max(1, int(math.sqrt(len(sorted_boxes) * avg_width / avg_height * container_height / container_width)))
        grid_rows = max(1, math.ceil(len(sorted_boxes) / grid_cols))
        
        # 动态调整网格大小直到能容纳所有图形
        while True:
            # 计算每个网格单元的大小
            max_width_in_col = [0] * grid_cols
            max_height_in_row = [0] * grid_rows
            
            # 为每个图形分配网格位置并计算行列最大尺寸
            for i, box in enumerate(sorted_boxes):
                row = i // grid_cols
                col = i % grid_cols
                if row < grid_rows and col < grid_cols:
                    max_width_in_col[col] = max(max_width_in_col[col], box['width'])
                    max_height_in_row[row] = max(max_height_in_row[row], box['height'])
            
            # 计算总宽度和高度
            total_width = sum(max_width_in_col) + (grid_cols - 1) * gap
            total_height = sum(max_height_in_row) + (grid_rows - 1) * gap
            
            # 检查是否适合容器
            if total_width <= container_width and total_height <= container_height:
                break
            
            # 如果不适合，增加网格尺寸
            if total_width > container_width:
                grid_cols += 1
            if total_height > container_height:
                grid_rows = max(1, math.ceil(len(sorted_boxes) / grid_cols))
            
            # 避免无限循环
            if grid_cols > len(sorted_boxes):
                grid_cols = len(sorted_boxes)
                grid_rows = 1
                break
        
        # 重新计算行列最大尺寸
        max_width_in_col = [0] * grid_cols
        max_height_in_row = [0] * grid_rows
        
        for i, box in enumerate(sorted_boxes):
            row = i // grid_cols
            col = i % grid_cols
            if row < grid_rows and col < grid_cols:
                max_width_in_col[col] = max(max_width_in_col[col], box['width'])
                max_height_in_row[row] = max(max_height_in_row[row], box['height'])
        
        # 计算整体偏移以居中放置
        total_width = sum(max_width_in_col) + (grid_cols - 1) * gap
        total_height = sum(max_height_in_row) + (grid_rows - 1) * gap
        offset_x = (container_width - total_width) / 2
        offset_y = (container_height - total_height) / 2
        
        # 计算每个图形的位置
        placements = []
        current_y = offset_y
        
        for row in range(grid_rows):
            current_x = offset_x
            for col in range(grid_cols):
                index = row * grid_cols + col
                if index < len(sorted_boxes):
                    box = sorted_boxes[index]
                    # 在网格单元内居中放置
                    pos_x = current_x + (max_width_in_col[col] - box['width']) / 2
                    pos_y = current_y + (max_height_in_row[row] - box['height']) / 2
                    
                    placements.append({
                        'box': box,
                        'position': (pos_x, pos_y),
                        'rotation': 0
                    })
                current_x += max_width_in_col[col] + gap
            if row < grid_rows - 1:  # 非最后一行才更新Y坐标
                current_y += max_height_in_row[row] + gap
        
        return placements
    
    def create_merged_dxf(self, placements: List[Dict], output_path: str = "merged_output.dxf") -> bool:
        """创建合并后的DXF文件"""
        try:
            # 创建新的DXF文档
            merged_doc = ezdxf.new('R2010')
            merged_msp = merged_doc.modelspace()
            
            # 添加边框以显示10x10cm区域
            self._add_border(merged_msp, 100.0, 100.0)
            
            # 复制并放置每个图形
            for placement in placements:
                box = placement['box']
                pos_x, pos_y = placement['position']
                rotation = placement.get('rotation', 0)
                
                # 计算平移向量
                original_min = box['original_extmin']
                target_min = ezdxf.math.Vec3(pos_x, pos_y, 0)
                translation_vector = target_min - original_min
                
                # 如果有旋转，则先将实体复制到临时空间进行旋转
                if rotation != 0:
                    # 创建临时模型空间用于旋转操作
                    temp_doc = ezdxf.new()
                    temp_msp = temp_doc.modelspace()
                    
                    # 复制实体到临时空间（不进行平移）
                    self._copy_entities(box['doc_info']['doc'].modelspace(), temp_msp, ezdxf.math.Vec3(0, 0, 0))
                    
                    # 对临时空间中的所有实体进行旋转
                    for entity in temp_msp:
                        if hasattr(entity, 'rotate_z'):
                            # 使用角度制旋转
                            entity.rotate_z(math.radians(rotation))
                    
                    # 将旋转后的实体复制到目标文件并应用平移
                    self._copy_entities(temp_msp, merged_msp, translation_vector)
                else:
                    # 复制实体并应用平移
                    self._copy_entities(box['doc_info']['doc'].modelspace(), 
                                      merged_msp, translation_vector)
            
            # 保存文件
            merged_doc.saveas(output_path)
            print(f"合并后的DXF文件已保存: {output_path}")
            return True
            
        except Exception as e:
            print(f"创建合并DXF文件失败: {e}")
            return False
    
    def _add_border(self, msp, width: float, height: float):
        """添加边框"""
        points = [
            (0, 0),
            (width, 0),
            (width, height),
            (0, height),
            (0, 0)
        ]
        
        msp.add_lwpolyline(points)
    
    def _copy_entities(self, source_msp, target_msp, translation: ezdxf.math.Vec3):
        """复制实体并应用平移"""
        for entity in source_msp:
            try:
                # 复制实体
                copied_entity = entity.copy()
                
                # 应用平移 - 修复translate方法调用
                if hasattr(copied_entity, 'translate'):
                    # translate方法需要三个参数：dx, dy, dz
                    copied_entity.translate(translation.x, translation.y, translation.z)
                
                # 添加到目标模型空间
                target_msp.add_entity(copied_entity)
                
            except Exception as e:
                print(f"复制实体失败: {e}")
                continue