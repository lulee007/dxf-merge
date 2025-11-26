import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import threading
from dxf_processor import DXFProcessor
from dxf_renderer import DXFRenderer
import ezdxf
from PIL import Image, ImageTk

class DXFMergeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DXF文件合并工具")
        self.root.geometry("800x700")
        
        # 文件列表
        self.input_files = []
        
        # 图片相关变量
        self.layout_image = None
        self.result_image = None
        self.layout_photo = None
        self.result_photo = None
        self.layout_scale = 1.0
        self.result_scale = 1.0
        
        # 创建界面
        self.create_widgets()
        
        # 绑定窗口大小变化事件
        self.root.bind("<Configure>", self.on_window_configure)
        self.configure_has_been_called = False
        
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # 文件选择区域
        file_frame = ttk.LabelFrame(main_frame, text="输入文件", padding="10")
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        file_frame.columnconfigure(0, weight=1)
        file_frame.rowconfigure(1, weight=1)
        
        # 添加文件按钮
        add_button = ttk.Button(file_frame, text="添加DXF文件", command=self.add_files)
        add_button.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # 删除文件按钮
        remove_button = ttk.Button(file_frame, text="删除选中文件", command=self.remove_file)
        remove_button.grid(row=0, column=1, sticky=tk.W, pady=(0, 5), padx=(5, 0))
        
        # 文件列表
        self.file_listbox = tk.Listbox(file_frame)
        self.file_listbox.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
        
        # 滚动条
        scrollbar = ttk.Scrollbar(file_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        scrollbar.grid(row=1, column=2, sticky=(tk.N, tk.S), pady=(5, 0))
        self.file_listbox.configure(yscrollcommand=scrollbar.set)
        
        # 设置区域
        settings_frame = ttk.LabelFrame(main_frame, text="设置", padding="10")
        settings_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        settings_frame.columnconfigure(1, weight=1)
        
        # 输出文件路径
        ttk.Label(settings_frame, text="输出文件:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.output_path_var = tk.StringVar(value="merged_result.dxf")
        output_entry = ttk.Entry(settings_frame, textvariable=self.output_path_var)
        output_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=2)
        output_button = ttk.Button(settings_frame, text="浏览", command=self.browse_output)
        output_button.grid(row=0, column=2, sticky=tk.W, pady=2)
        
        # 容器尺寸
        ttk.Label(settings_frame, text="容器尺寸:").grid(row=1, column=0, sticky=tk.W, pady=2)
        size_frame = ttk.Frame(settings_frame)
        size_frame.grid(row=1, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        self.container_width_var = tk.DoubleVar(value=100.0)
        ttk.Entry(size_frame, textvariable=self.container_width_var, width=10).pack(side=tk.LEFT)
        ttk.Label(size_frame, text=" x ").pack(side=tk.LEFT)
        self.container_height_var = tk.DoubleVar(value=100.0)
        ttk.Entry(size_frame, textvariable=self.container_height_var, width=10).pack(side=tk.LEFT)
        ttk.Label(size_frame, text=" mm").pack(side=tk.LEFT)
        
        # 间隙设置
        ttk.Label(settings_frame, text="图形间隙:").grid(row=2, column=0, sticky=tk.W, pady=2)
        gap_frame = ttk.Frame(settings_frame)
        gap_frame.grid(row=2, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        self.gap_size_var = tk.DoubleVar(value=8.0)
        ttk.Entry(gap_frame, textvariable=self.gap_size_var, width=10).pack(side=tk.LEFT)
        ttk.Label(gap_frame, text=" mm").pack(side=tk.LEFT)
        
        # 操作按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(0, 10))
        
        self.process_button = ttk.Button(button_frame, text="开始处理", command=self.start_processing)
        self.process_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.preview_button = ttk.Button(button_frame, text="生成预览", command=self.generate_preview, state=tk.DISABLED)
        self.preview_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # 进度条
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 预览区域
        preview_frame = ttk.LabelFrame(main_frame, text="预览", padding="10")
        preview_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.columnconfigure(1, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # 排样预览
        layout_frame = ttk.Frame(preview_frame)
        layout_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        layout_frame.columnconfigure(0, weight=1)
        layout_frame.rowconfigure(2, weight=1)
        
        ttk.Label(layout_frame, text="排样预览").grid(row=0, column=0)
        
        # 排样预览控制按钮
        layout_control_frame = ttk.Frame(layout_frame)
        layout_control_frame.grid(row=1, column=0, pady=(5, 5))
        
        ttk.Button(layout_control_frame, text="放大", command=lambda: self.zoom_image("layout", 1.2)).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(layout_control_frame, text="缩小", command=lambda: self.zoom_image("layout", 0.8)).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(layout_control_frame, text="重置", command=lambda: self.reset_zoom("layout")).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(layout_control_frame, text="另存为", command=lambda: self.save_image_as("layout")).pack(side=tk.LEFT, padx=(5, 0))
        
        self.layout_canvas = tk.Canvas(layout_frame, bg='white')
        self.layout_canvas.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.layout_canvas.bind("<MouseWheel>", lambda event: self.on_mouse_wheel(event, "layout"))
        self.layout_canvas.bind("<Button-4>", lambda event: self.on_mouse_wheel(event, "layout"))
        self.layout_canvas.bind("<Button-5>", lambda event: self.on_mouse_wheel(event, "layout"))
        
        # 结果预览
        result_frame = ttk.Frame(preview_frame)
        result_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(2, weight=1)
        
        ttk.Label(result_frame, text="结果预览").grid(row=0, column=0)
        
        # 结果预览控制按钮
        result_control_frame = ttk.Frame(result_frame)
        result_control_frame.grid(row=1, column=0, pady=(5, 5))
        
        ttk.Button(result_control_frame, text="放大", command=lambda: self.zoom_image("result", 1.2)).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(result_control_frame, text="缩小", command=lambda: self.zoom_image("result", 0.8)).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(result_control_frame, text="重置", command=lambda: self.reset_zoom("result")).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(result_control_frame, text="另存为", command=lambda: self.save_image_as("result")).pack(side=tk.LEFT, padx=(5, 0))
        
        self.result_canvas = tk.Canvas(result_frame, bg='white')
        self.result_canvas.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.result_canvas.bind("<MouseWheel>", lambda event: self.on_mouse_wheel(event, "result"))
        self.result_canvas.bind("<Button-4>", lambda event: self.on_mouse_wheel(event, "result"))
        self.result_canvas.bind("<Button-5>", lambda event: self.on_mouse_wheel(event, "result"))
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
    def add_files(self):
        files = filedialog.askopenfilenames(
            title="选择DXF文件",
            filetypes=[("DXF files", "*.dxf"), ("All files", "*.*")]
        )
        
        for file in files:
            if file not in self.input_files:
                self.input_files.append(file)
                self.file_listbox.insert(tk.END, os.path.basename(file))
                
    def remove_file(self):
        selection = self.file_listbox.curselection()
        if selection:
            index = selection[0]
            self.file_listbox.delete(index)
            del self.input_files[index]
            
    def browse_output(self):
        filename = filedialog.asksaveasfilename(
            title="保存合并文件",
            defaultextension=".dxf",
            filetypes=[("DXF files", "*.dxf"), ("All files", "*.*")]
        )
        
        if filename:
            self.output_path_var.set(filename)
            
    def start_processing(self):
        if not self.input_files:
            messagebox.showwarning("警告", "请至少选择一个DXF文件")
            return
            
        # 在后台线程中处理
        self.process_button.config(state=tk.DISABLED)
        self.progress.start()
        self.status_var.set("正在处理...")
        
        thread = threading.Thread(target=self.process_files)
        thread.daemon = True
        thread.start()
        
    def process_files(self):
        try:
            # 创建处理器实例
            processor = DXFProcessor()
            
            # 读取DXF文件
            self.root.after(0, lambda: self.status_var.set("正在读取DXF文件..."))
            if not processor.read_dxf_files(self.input_files):
                raise Exception("读取DXF文件失败")
                
            # 计算外包矩形
            self.root.after(0, lambda: self.status_var.set("正在计算外包矩形..."))
            if not processor.calculate_bounding_boxes():
                raise Exception("计算外包矩形失败")
                
            # 排样布局
            container_width = self.container_width_var.get()
            container_height = self.container_height_var.get()
            gap_size = self.gap_size_var.get()
            
            self.root.after(0, lambda: self.status_var.set("正在进行排样布局..."))
            placements = processor.pack_rectangles(container_width, container_height, gap_size)
            
            # 创建合并文件
            output_path = self.output_path_var.get()
            self.root.after(0, lambda: self.status_var.set("正在创建合并文件..."))
            if not processor.create_merged_dxf(placements, output_path):
                raise Exception("创建合并DXF文件失败")
                
            self.output_path = output_path
            self.placements = placements
            self.container_size = (container_width, container_height)
            
            # 启用预览按钮
            self.root.after(0, lambda: self.preview_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.status_var.set(f"处理完成! 文件已保存至: {output_path}"))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"处理过程中出现错误:\n{str(e)}"))
            self.root.after(0, lambda: self.status_var.set("处理失败"))
            
        finally:
            self.root.after(0, lambda: self.process_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.progress.stop())
            
    def generate_preview(self):
        try:
            # 在后台线程中生成预览
            self.preview_button.config(state=tk.DISABLED)
            self.progress.start()
            self.status_var.set("正在生成预览...")
            
            thread = threading.Thread(target=self.create_previews)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            messagebox.showerror("错误", f"生成预览时出现错误:\n{str(e)}")
            self.status_var.set("预览生成失败")
            self.preview_button.config(state=tk.NORMAL)
            self.progress.stop()
            
    def create_previews(self):
        try:
            # 生成排样预览图
            placement_preview = "placement_preview.png"
            DXFRenderer.render_placements_to_image(
                self.placements,
                self.container_size[0],
                self.container_size[1],
                placement_preview
            )
            
            # 生成带标注的结果预览图
            annotated_result_preview = "annotated_result_preview.png"
            result_doc = ezdxf.readfile(self.output_path)
            DXFRenderer.render_final_result_with_annotations(
                result_doc, 
                self.placements, 
                annotated_result_preview
            )
            
            # 在主线程中更新界面
            self.root.after(0, self.update_preview_images)
            self.root.after(0, lambda: self.status_var.set("预览生成完成"))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"生成预览时出现错误:\n{str(e)}"))
            self.root.after(0, lambda: self.status_var.set("预览生成失败"))
            
        finally:
            self.root.after(0, lambda: self.preview_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.progress.stop())
            
    def update_preview_images(self):
        try:
            # 加载并显示排样预览图
            if os.path.exists("placement_preview.png"):
                self.layout_image = Image.open("placement_preview.png")
                self.layout_scale = 1.0
                self.display_image_on_canvas("layout")
            
            # 加载并显示带标注的结果预览图
            if os.path.exists("annotated_result_preview.png"):
                self.result_image = Image.open("annotated_result_preview.png")
                self.result_scale = 1.0
                self.display_image_on_canvas("result")
                
            self.status_var.set("预览图片已生成并显示")
        except Exception as e:
            self.status_var.set(f"显示预览图片时出错: {str(e)}")
    
    def display_image_on_canvas(self, canvas_type):
        if canvas_type == "layout" and self.layout_image:
            # 调整图片大小
            width, height = self.layout_image.size
            
            # 获取画布尺寸
            canvas_width = self.layout_canvas.winfo_width()
            canvas_height = self.layout_canvas.winfo_height()
            
            # 如果画布大小为0（窗口还未完全绘制），使用默认值
            if canvas_width <= 1:
                canvas_width = 350
            if canvas_height <= 1:
                canvas_height = 250
            
            # 计算自适应缩放比例
            scale_x = (canvas_width - 20) / width
            scale_y = (canvas_height - 20) / height
            fit_scale = min(scale_x, scale_y)
            
            # 应用当前缩放因子
            new_width = int(width * fit_scale * self.layout_scale)
            new_height = int(height * fit_scale * self.layout_scale)
            resized_img = self.layout_image.resize((new_width, new_height), Image.LANCZOS)
            
            # 转换为PhotoImage
            self.layout_photo = ImageTk.PhotoImage(resized_img)
            
            # 在画布上显示图片
            self.layout_canvas.delete("all")
            x = canvas_width // 2
            y = canvas_height // 2
            self.layout_canvas.create_image(x, y, image=self.layout_photo, anchor=tk.CENTER)
            
        elif canvas_type == "result" and self.result_image:
            # 调整图片大小
            width, height = self.result_image.size
            
            # 获取画布尺寸
            canvas_width = self.result_canvas.winfo_width()
            canvas_height = self.result_canvas.winfo_height()
            
            # 如果画布大小为0（窗口还未完全绘制），使用默认值
            if canvas_width <= 1:
                canvas_width = 350
            if canvas_height <= 1:
                canvas_height = 250
            
            # 计算自适应缩放比例
            scale_x = (canvas_width - 20) / width
            scale_y = (canvas_height - 20) / height
            fit_scale = min(scale_x, scale_y)
            
            # 应用当前缩放因子
            new_width = int(width * fit_scale * self.result_scale)
            new_height = int(height * fit_scale * self.result_scale)
            resized_img = self.result_image.resize((new_width, new_height), Image.LANCZOS)
            
            # 转换为PhotoImage
            self.result_photo = ImageTk.PhotoImage(resized_img)
            
            # 在画布上显示图片
            self.result_canvas.delete("all")
            x = canvas_width // 2
            y = canvas_height // 2
            self.result_canvas.create_image(x, y, image=self.result_photo, anchor=tk.CENTER)
    
    def zoom_image(self, canvas_type, factor):
        if canvas_type == "layout":
            self.layout_scale *= factor
            self.display_image_on_canvas("layout")
        elif canvas_type == "result":
            self.result_scale *= factor
            self.display_image_on_canvas("result")
    
    def reset_zoom(self, canvas_type):
        if canvas_type == "layout":
            self.layout_scale = 1.0
            self.display_image_on_canvas("layout")
        elif canvas_type == "result":
            self.result_scale = 1.0
            self.display_image_on_canvas("result")
    
    def copy_to_clipboard(self, canvas_type):
        try:
            # 获取要复制的图片
            image_to_copy = None
            if canvas_type == "layout":
                image_to_copy = self.layout_image
            elif canvas_type == "result":
                image_to_copy = self.result_image
            
            if image_to_copy is None:
                messagebox.showwarning("警告", "没有可复制的图片")
                return
            
            # 将图片复制到剪贴板
            self.root.clipboard_clear()
            self.root.clipboard_append("")  # 确保剪贴板已初始化
            
            # 使用PIL将图片放到剪贴板（需要pywin32库在Windows上）
            try:
                from io import BytesIO
                import win32clipboard
                
                output = BytesIO()
                image_to_copy.convert('RGB').save(output, 'BMP')
                data = output.getvalue()[14:]  # BMP格式需要去掉前14字节
                output.close()
                
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
                win32clipboard.CloseClipboard()
                
                self.status_var.set(f"图片已复制到剪贴板")
            except ImportError:
                # 如果没有win32clipboard库，显示提示信息
                messagebox.showinfo("提示", "图片已准备好，但由于缺少必要的库无法直接复制到剪贴板。\n请手动保存图片后使用。")
                self.status_var.set("缺少必要的库来复制图片到剪贴板")
                
        except Exception as e:
            messagebox.showerror("错误", f"复制图片到剪贴板时出错:\n{str(e)}")
            self.status_var.set("复制图片失败")
    
    def on_mouse_wheel(self, event, canvas_type):
        # 处理鼠标滚轮事件进行缩放
        # Windows系统使用event.delta，Linux/Mac使用Button-4和Button-5
        if event.num == 4 or event.delta > 0:
            self.zoom_image(canvas_type, 1.1)
        elif event.num == 5 or event.delta < 0:
            self.zoom_image(canvas_type, 0.9)
    
    def on_window_configure(self, event):
        # 避免在初始化时重复调用
        if not self.configure_has_been_called:
            self.configure_has_been_called = True
            return
            
        # 只有当事件源是主窗口时才刷新图片
        if event.widget == self.root:
            # 延迟执行以确保窗口大小已经稳定
            self.root.after(100, self.refresh_images_on_resize)
    
    def refresh_images_on_resize(self):
        # 当窗口大小改变时刷新图片显示
        if self.layout_image or self.result_image:
            if self.layout_image:
                self.display_image_on_canvas("layout")
            if self.result_image:
                self.display_image_on_canvas("result")

    def save_image_as(self, canvas_type):
        try:
            # 获取要保存的图片
            image_to_save = None
            default_filename = ""
            
            if canvas_type == "layout":
                image_to_save = self.layout_image
                default_filename = "placement_preview.png"
            elif canvas_type == "result":
                image_to_save = self.result_image
                default_filename = "result_preview.png"
            
            if image_to_save is None:
                messagebox.showwarning("警告", "没有可保存的图片")
                return
            
            # 打开文件保存对话框
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                initialfile=default_filename,
                filetypes=[
                    ("PNG files", "*.png"),
                    ("JPEG files", "*.jpg *.jpeg"),
                    ("BMP files", "*.bmp"),
                    ("All files", "*.*")
                ]
            )
            
            if file_path:
                # 保存图片
                image_to_save.save(file_path)
                self.status_var.set(f"图片已保存至: {file_path}")
                messagebox.showinfo("成功", f"图片已成功保存至:\n{file_path}")
                
        except Exception as e:
            error_message = str(e)
            messagebox.showerror("错误", f"保存图片时出错:\n{error_message}")
            self.status_var.set("保存图片失败")
    
def main():
    root = tk.Tk()
    app = DXFMergeGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()