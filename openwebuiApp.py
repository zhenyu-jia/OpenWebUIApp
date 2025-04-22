import subprocess
import webbrowser
import threading
import pystray
from PIL import Image
import multiprocessing


class WebUITrayApp:
    def __init__(self, icon_path="./icon.png", port=9999):
        self.port = port  # 端口号
        self.process = None
        self.tray_icon = None
        self.icon_image = None
        self.lock = threading.Lock()  # 添加线程锁
        self.success = False  # 是否成功启动服务
        self.icon_path = icon_path
        # 加载图标文件
        self.icon_image = self.load_icon()

        # 初始化菜单项
        self.menu_open_website = pystray.MenuItem("Open Website", self.open_website)
        self.menu_show_help = pystray.MenuItem("Help", self.show_help)
        self.menu_exit_app = pystray.MenuItem("Exit", self.exit_app)

        # 创建系统托盘图标
        if self.icon_image:
            self.tray_icon = pystray.Icon(
                "OpenWebUI",
                self.icon_image,
                "Open WebUI",
                (
                    self.menu_open_website,
                    self.menu_show_help,
                    pystray.Menu.SEPARATOR,
                    self.menu_exit_app
                )
            )

    def load_icon(self):
        """加载图标文件，返回图标对象"""
        try:
            return Image.open(self.icon_path).resize((32, 32))
        except FileNotFoundError:
            print("图标文件未找到，请确保 icon.png 存在于当前目录。")
            return None
        except Exception as e:
            print(f"加载图标文件时发生错误: {e}")
            return None

    def open_website(self, selected):
        """处理 Open Website 菜单项点击事件"""
        self.launch_web_page()

    def show_help(self, selected):
        """处理 Help 菜单项点击事件"""
        self.tray_icon.notify(f"Open WebUI 服务，端口号为 {self.port}\n请打开 http://localhost:{self.port} 使用服务")

    def exit_app(self, selected):
        """处理 Exit 菜单项点击事件"""
        self.stop_web_ui_service()
        self.tray_icon.stop()
        self.tray_icon.notify("Open WebUI 服务已停止")
        print("服务已停止，退出程序")

    def stop_web_ui_service(self):
        """停止 Open WebUI 服务进程"""
        with self.lock:
            if self.process:
                print("停止 Open WebUI 服务进程...")
                try:
                    self.process.terminate()  # 确保进程完全终止
                    self.process.wait()  # 等待进程终止
                except Exception as e:
                    print(f"停止进程时发生错误: {e}")
            else:
                print("没有运行的 Open WebUI 服务进程可以停止")

    def start_web_ui_service(self):
        """启动 Open WebUI 服务进程"""
        print("启动 Open WebUI 服务...")
        with self.lock:
            try:
                self.process = subprocess.Popen(
                    ["open-webui", "serve", "--port", str(self.port)],
                    stderr=subprocess.PIPE,
                    text=True
                )
                threading.Thread(target=self.monitor_process_output, daemon=True).start()
            except Exception as e:
                print(f"启动 Open WebUI 服务时发生错误: {e}")

    def monitor_process_output(self):
        """监控 Open WebUI 服务的输出"""
        keyword = "Application startup complete."
        while True:
            output = self.process.stderr.readline()
            if output == '' and self.process.poll() is not None:
                break  # 进程结束
            if output:
                if keyword in output:
                    print(f"发现关键字：{keyword}")
                    self.success = True
                    self.tray_icon.notify("Open WebUI 服务已启动")
                    break  # 如果找到关键词，退出循环

    def launch_web_page(self):
        """打开浏览器并访问 Web 页面"""
        print(f"打开网页 http://localhost:{self.port}")
        try:
            webbrowser.open(f"http://localhost:{self.port}")
        except Exception as e:
            print(f"打开网页时发生错误: {e}")

    def startup_tasks(self):
        """启动 Open WebUI 服务并打开网页，直到成功启动"""
        self.start_web_ui_service()

        # 在单独的线程中等待服务启动成功后再启动网页
        threading.Thread(target=self.wait_and_launch_web_page, daemon=True).start()

    def wait_and_launch_web_page(self):
        """等待服务启动成功后启动网页"""
        while not self.success:
            threading.Event().wait(1)  # 每秒检查一次

        # 服务启动成功后，启动网页
        self.launch_web_page()

    def tray_icon_callback(self):
        """系统托盘图标回调函数"""
        self.tray_icon.run()

    def run(self):
        """启动系统托盘应用程序"""
        if self.icon_image:
            # 启动回调线程
            threading.Thread(target=self.tray_icon_callback).start()
            threading.Thread(target=self.startup_tasks, daemon=True).start()
        else:
            print("无法启动系统托盘，图标文件未加载成功。")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    app = WebUITrayApp()
    app.run()
