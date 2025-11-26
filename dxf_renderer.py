import ezdxf
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf import bbox
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import matplotlib.font_manager as fm

class DXFRenderer:
    """DXF渲染器，用于将DXF文件渲染为图像"""
    
    @staticmethod
    def render_dxf_to_image(doc, output_path=None, figsize=(10, 10), dpi=150):
        """
        将DXF文档渲染为图像
        
        Args:
            doc: ezdxf文档对象
            output_path: 输出图像路径，如果为None则显示图像而不保存
            figsize: 图像大小
            dpi: 图像分辨率
        """
        try:
            # 创建绘图环境
            fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
            
            # 尝试设置中文字体以避免警告
            plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
            plt.rcParams['axes.unicode_minus'] = False
            
            # 创建渲染上下文和后端
            ctx = RenderContext(doc)
            ctx.set_current_layout(doc.modelspace())
            backend = MatplotlibBackend(ax)
            
            # 渲染
            frontend = Frontend(ctx, backend)
            frontend.draw_layout(doc.modelspace())
            
            # 设置坐标轴
            ax.margins(0.1)
            ax.xaxis.tick_top()
            ax.set_title('DXF结果预览')
            
            # 保存或显示图像
            if output_path:
                plt.savefig(output_path, dpi=dpi, bbox_inches='tight', pad_inches=0.1)
                plt.close(fig)
                print(f"图像已保存至: {output_path}")
                return True
            else:
                plt.show()
                plt.close(fig)
                return True
                
        except Exception as e:
            print(f"渲染DXF文件时出错: {e}")
            return False
    
    @staticmethod
    def render_placements_to_image(placements, container_width, container_height, 
                                 output_path=None, figsize=(10, 10), dpi=150):
        """
        将排样结果渲染为图像，并为每个子项添加尺寸标注
        
        Args:
            placements: 排样结果列表
            container_width: 容器宽度
            container_height: 容器高度
            output_path: 输出图像路径，如果为None则显示图像而不保存
            figsize: 图像大小
            dpi: 图像分辨率
        """
        try:
            # 创建绘图环境
            fig, ax = plt.subplots(1, 1, figsize=figsize, dpi=dpi)
            
            # 尝试设置中文字体以避免警告
            plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
            plt.rcParams['axes.unicode_minus'] = False
            
            # 绘制容器边界
            container = patches.Rectangle((0, 0), container_width, container_height, 
                                       linewidth=2, edgecolor='black', facecolor='none')
            ax.add_patch(container)
            
            # 绘制每个放置的矩形
            colors = plt.cm.Set3(np.linspace(0, 1, len(placements)))
            for i, placement in enumerate(placements):
                box = placement['box']
                pos_x, pos_y = placement['position']
                width = box['width']
                height = box['height']
                rotation = placement.get('rotation', 0)
                name = box['doc_info']['name']
                
                # 创建矩形
                rect = patches.Rectangle((pos_x, pos_y), width, height, 
                                       linewidth=1, 
                                       edgecolor='black', 
                                       facecolor=colors[i],
                                       alpha=0.7,
                                       label=f"Part {i+1}")
                ax.add_patch(rect)
                
                # 添加文本标签（文件名和尺寸）
                label_text = f"{name}\n{width:.1f}×{height:.1f}mm"
                ax.text(pos_x + width/2, pos_y + height/2, label_text, 
                       ha='center', va='center', fontsize=8, weight='bold')
                
                # 添加尺寸标注线（虚线，小箭头）
                # 水平尺寸标注
                ax.annotate('', xy=(pos_x, pos_y - 2), xytext=(pos_x + width, pos_y - 2),
                           arrowprops=dict(arrowstyle='<->', color='blue', lw=0.5, linestyle='dashed'))
                ax.text(pos_x + width/2, pos_y - 5, f'{width:.1f}', 
                       ha='center', va='center', fontsize=7, color='blue', weight='bold')
                
                # 垂直尺寸标注
                ax.annotate('', xy=(pos_x - 2, pos_y), xytext=(pos_x - 2, pos_y + height),
                           arrowprops=dict(arrowstyle='<->', color='blue', lw=0.5, linestyle='dashed'))
                ax.text(pos_x - 5, pos_y + height/2, f'{height:.1f}', 
                       ha='center', va='center', rotation=90, fontsize=7, color='blue', weight='bold')
            
            # 设置坐标轴
            ax.set_xlim(0, container_width)
            ax.set_ylim(0, container_height)
            ax.set_aspect('equal')
            ax.grid(True, linestyle='--', alpha=0.7)
            ax.set_xlabel('X (mm)')
            ax.set_ylabel('Y (mm)')
            ax.set_title('排样结果预览')
            
            # 保存或显示图像
            if output_path:
                plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
                plt.close(fig)
                print(f"排样预览图像已保存至: {output_path}")
                return True
            else:
                plt.show()
                plt.close(fig)
                return True
                
        except Exception as e:
            print(f"渲染排样结果时出错: {e}")
            return False
    
    @staticmethod
    def render_final_result_with_annotations(doc, placements, output_path=None, figsize=(10, 10), dpi=150):
        """
        将最终DXF结果渲染为图像，并添加每个子项的尺寸标注（白色）
        
        Args:
            doc: ezdxf文档对象
            placements: 排样结果列表（用于标注）
            output_path: 输出图像路径，如果为None则显示图像而不保存
            figsize: 图像大小
            dpi: 图像分辨率
        """
        try:
            # 创建绘图环境
            fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
            
            # 尝试设置中文字体以避免警告
            plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
            plt.rcParams['axes.unicode_minus'] = False
            
            # 创建渲染上下文和后端
            ctx = RenderContext(doc)
            ctx.set_current_layout(doc.modelspace())
            backend = MatplotlibBackend(ax)
            
            # 渲染
            frontend = Frontend(ctx, backend)
            frontend.draw_layout(doc.modelspace())
            
            # 添加每个子项的尺寸标注（仅长宽，使用白色，虚线，小箭头）
            for i, placement in enumerate(placements):
                box = placement['box']
                pos_x, pos_y = placement['position']
                width = box['width']
                height = box['height']
                name = box['doc_info']['name']
                
                # 添加尺寸标注线（白色，虚线，小箭头）
                # 水平尺寸标注
                ax.annotate('', xy=(pos_x, pos_y - 1), xytext=(pos_x + width, pos_y - 1),
                           arrowprops=dict(arrowstyle='<->', color='white', lw=0.5, linestyle='dashed'))
                ax.text(pos_x + width/2, pos_y - 3, f'{width:.1f}mm', 
                       ha='center', va='center', fontsize=8, color='white', weight='bold',
                       bbox=dict(boxstyle="round,pad=0.2", facecolor='black', alpha=0.2))
                
                # 垂直尺寸标注
                ax.annotate('', xy=(pos_x - 1, pos_y), xytext=(pos_x - 1, pos_y + height),
                           arrowprops=dict(arrowstyle='<->', color='white', lw=0.5, linestyle='dashed'))
                ax.text(pos_x - 3, pos_y + height/2, f'{height:.1f}mm', 
                       ha='center', va='center', rotation=90, fontsize=8, color='white', weight='bold',
                       bbox=dict(boxstyle="round,pad=0.1", facecolor='black', alpha=0.2))
            
            # 设置坐标轴
            ax.margins(0.1)
            ax.xaxis.tick_top()
            ax.set_title('DXF结果预览（带子项尺寸标注）')
            
            # 保存或显示图像
            if output_path:
                plt.savefig(output_path, dpi=dpi, bbox_inches='tight', pad_inches=0.1)
                plt.close(fig)
                print(f"带标注的结果预览图像已保存至: {output_path}")
                return True
            else:
                plt.show()
                plt.close(fig)
                return True
                
        except Exception as e:
            print(f"渲染带标注的DXF文件时出错: {e}")
            return False