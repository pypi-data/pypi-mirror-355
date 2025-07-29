## PyCharm 自动生成 requirements.txt

> 使用Python打开自己的工程，然后点击Tools，最后点击Sync Python Requirements
>
> **pip install -r requirements.txt** 

### 其他注意事项：

 - 确保 requirements.txt 文件位于项目的根目录。
 - 在提交代码到版本控制系统之前，更新 requirements.txt 文件。
 - 在使用 pip install -r requirements.txt 安装依赖项时，确保使用与项目环境匹配的 Python 版本。

# 打包执行以下命令

### **```pyinstaller -n [your_exe_name] -F -w -i [your_ico] [your_main].py```** 

>--hidden-import 设置导入要动态加载的类 因为没被引用 所以不会导入需要手动设置
>
>上述命令中的选项说明：
>
>-n NAME, --name NAME: 可执行文件名称。
>
>-F, --onefile: 将整个项目打包为一个单独的可执行文件。
>
>-w, --windowed, --noconsole: 隐藏控制台窗口，将打包的应用程序显示为GUI应用程序。
>
>--add-data: 添加项目资源，支持文件夹和文件，前面是资源路径，后面是输出路径，用分号进行分割。
>
>-i <FILE.ico>, --icon <FILE.ico> :  指定icon
>
>执行上述命令后，会在项目目录下生成一个.spec文件，这个文件会告诉PyInstaller如何将项目打包成exe文件。

# 打包报错排查

- ### <span style="color: red;">无法将“pyinstaller”项识别为 cmdlet、函数、脚本文件或可运行程序的名称。请检查名称的拼写，如果包括路径，请确保路径正确，然后再试一次。</span>

  > 解决方案: 安装 PyInstaller
  >
  > pip install PyInstaller
  >
  > pyinstaller --name=<your_exe_name> --onefile --windowed --add-data "<your_data_folder>;<your_data_folder>" <your_script_name>.py


- ### <span style="color: red;">win32ctypes.pywin32.pywintypes.error: (225, 'EndUpdateResourceW', '无法成功完成操作，因为文件包含病毒或潜在的垃圾软件。</span>

  > 不使用-w --noconsole的命令打包隐藏命令行窗口时，是正常的，
  >
  > 但是使用-w或者--noconsole就会报错win32ctypes.pywin32.pywintypes.error: (225, '', '无法成功完成操作，因为文件包含病毒或潜在的垃圾软件。')
  >
  > 解决方案: 降级 PyInstaller, 安装6.2.0重新打包即可
  > 
  > pip install pyinstaller==6.2.0