@echo off
echo 正在安装必要的依赖...
pip install pyinstaller ezdxf numpy matplotlib pillow

echo.
echo 正在打包GUI应用程序...
pyinstaller --noconfirm --onefile --windowed --name="DXF合并工具" ^
    --add-data="dxf_processor.py;." ^
    --add-data="dxf_renderer.py;." ^
    --hidden-import="PIL" ^
    gui_app.py

echo.
echo 打包完成！可执行文件位于 dist 目录中
echo.
pause