from dxf_processor import DXFProcessor
from dxf_renderer import DXFRenderer
import ezdxf
import sys
import os

def main():
    # 检查是否提供了命令行参数
    if len(sys.argv) > 1:
        # 命令行模式
        input_files = sys.argv[1:-1]  # 除最后一个外的所有参数都是输入文件
        output_file = sys.argv[-1]    # 最后一个参数是输出文件
    else:
        # 默认模式
        input_files = [
            "file1.dxf",
            "file2.dxf", 
            "file3.dxf"
            # 添加你的DXF文件路径
        ]
        output_file = "merged_result.dxf"
    
    container_size = (100.0, 100.0)  # 10cm x 10cm
    generate_preview = True  # 是否生成预览图像
    gap_size = 8.0  # 图形之间的间隙，单位mm
    
    # 创建处理器实例
    processor = DXFProcessor()
    
    # 1. 读取DXF文件
    print("步骤1: 读取DXF文件...")
    if not processor.read_dxf_files(input_files):
        return
    
    # 2. 计算外包矩形
    print("\n步骤2: 计算外包矩形...")
    if not processor.calculate_bounding_boxes():
        return
    
    # 3. 排样布局
    print("\n步骤3: 排样布局...")
    placements = processor.pack_rectangles(container_size[0], container_size[1], gap_size)
    
    # 显示排样结果
    print("\n排样结果:")
    for i, placement in enumerate(placements):
        box = placement['box']
        pos = placement['position']
        rotation = placement.get('rotation', 0)
        print(f"图形 {i+1}: {box['doc_info']['name']}")
        print(f"  位置: ({pos[0]:.2f}, {pos[1]:.2f})")
        print(f"  尺寸: {box['width']:.2f} x {box['height']:.2f}")
        if rotation != 0:
            print(f"  旋转: {rotation}度")
    
    # 4. 生成排样结果预览图
    if generate_preview:
        print("\n步骤4: 生成排样预览图...")
        DXFRenderer.render_placements_to_image(
            placements, 
            container_size[0], 
            container_size[1], 
            "placement_preview.png"
        )
    
    # 5. 创建合并文件
    print("\n步骤5: 创建合并文件...")
    if processor.create_merged_dxf(placements, output_file):
        print(f"处理完成! 文件已保存至: {output_file}")
        
        # 6. 生成最终结果预览图
        if generate_preview:
            print("\n步骤6: 生成最终结果预览图...")
            try:
                result_doc = ezdxf.readfile(output_file)
                DXFRenderer.render_final_result_with_annotations(result_doc, placements, "annotated_result_preview.png")
            except Exception as e:
                print(f"生成带标注的最终结果预览图失败: {e}")
    else:
        print("处理失败!")

if __name__ == "__main__":
    main()