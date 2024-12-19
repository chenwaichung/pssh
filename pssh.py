import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog, scrolledtext
import paramiko
import threading
import json
import os
from datetime import datetime

class EnhancedBatchSSH:
    def __init__(self, root):
        self.root = root
        self.root.title("高级批量SSH工具")
        self.root.geometry("800x500")
        
        # 创建主界面
        self.create_main_ui()  # 确保在这里初始化 host_tree
        
        # 加载配置
        self.load_config()  # 在这里调用 load_config
        
        # 创建菜单
        self.create_menu()
        
        # 初始化SSH连接池
        self.ssh_pool = {}
        
        print(f"host_tree initialized: {hasattr(self, 'host_tree')}")
        
    def create_menu(self):
        menubar = tk.Menu(self.root)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="导入主机", command=self.import_hosts)
        file_menu.add_command(label="导出配置", command=self.export_config)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        menubar.add_cascade(label="文件", menu=file_menu)
        
        # 设置菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="连接设置", command=self.show_settings)
        menubar.add_cascade(label="工具", menu=tools_menu)
        
        self.root.config(menu=menubar)
        
    def create_main_ui(self):
        # 创建左右分隔面板
        paned = ttk.PanedWindow(self.root, orient='horizontal')
        paned.pack(fill='both', expand=True)
        
        # 左侧主机列表
        left_frame = ttk.Frame(paned)
        paned.add(left_frame)

        # 添加按钮区
        button_frame = ttk.Frame(left_frame)
        button_frame.grid(row=0, column=0, padx=5, pady=5, sticky='ew')
        
        # 添加全选按钮
        ttk.Button(button_frame, text="全选", command=self.select_all_hosts).pack(side='left', padx=5)
        
        # 添加取消全选按钮
        ttk.Button(button_frame, text="取消全选", command=self.deselect_all_hosts).pack(side='left', padx=5)
        
        # 添加批量清除按钮
        ttk.Button(button_frame, text="批量清除", command=self.clear_selected_hosts).pack(side='left', padx=5)

        # 主机列表
        host_frame = ttk.LabelFrame(left_frame, text="主机列表")
        host_frame.grid(row=1, column=0, padx=5, pady=5, sticky='nsew')
        
        # 创建滚动条
        self.host_tree = ttk.Treeview(host_frame, columns=('host', 'status'), show='headings')
        self.host_tree.heading('host', text='主机')
        self.host_tree.heading('status', text='状态')
        
        # 垂直滚动条
        vsb = ttk.Scrollbar(host_frame, orient="vertical", command=self.host_tree.yview)
        self.host_tree.configure(yscrollcommand=vsb.set)
        
        self.host_tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

        # 右侧命令和结果区
        right_frame = ttk.Frame(paned)
        paned.add(right_frame)
        
        # 命令输入区
        cmd_frame = ttk.LabelFrame(right_frame, text="命令输入")
        cmd_frame.grid(row=0, column=0, padx=5, pady=5, sticky='ew')
        
        self.cmd_entry = scrolledtext.ScrolledText(cmd_frame, height=5, wrap=tk.WORD)  # 使用 ScrolledText
        self.cmd_entry.pack(padx=5, pady=5, fill='x')
        
        # 按钮区
        btn_frame = ttk.Frame(right_frame)
        btn_frame.grid(row=1, column=0, padx=5, pady=5, sticky='ew')
        
        self.execute_button = ttk.Button(btn_frame, text="执行", command=self.execute)
        self.execute_button.pack(side='left', padx=5)
        
        # 初始状态禁用执行按钮
        self.execute_button.config(state=tk.DISABLED)
        
        ttk.Button(btn_frame, text="清空", command=self.clear_results).pack(side='left', padx=5)
        
        # 结果显示区
        result_frame = ttk.LabelFrame(right_frame, text="执行结果")
        result_frame.grid(row=2, column=0, padx=5, pady=5, sticky='nsew')
        
        # 创建结果文本框和滚动条
        self.result_text = tk.Text(result_frame)
        self.result_text.pack(padx=5, pady=5, fill='both', expand=True)

        # 垂直滚动条
        result_vsb = ttk.Scrollbar(result_frame, orient="vertical", command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=result_vsb.set)
        result_vsb.pack(side='right', fill='y')

        # 调整列权重
        left_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        
        # 调整行权重
        paned.grid_rowconfigure(0, weight=1)
        paned.grid_columnconfigure(0, weight=1)
        
        # 确保主机列表和结果区域的行权重
        left_frame.grid_rowconfigure(1, weight=1)  # 主机列表行
        right_frame.grid_rowconfigure(2, weight=1)  # 执行结果行

        # 绑定选择事件
        self.host_tree.bind('<<TreeviewSelect>>', self.on_host_select)
        
    def load_config(self):
        try:
            if not os.path.exists('config.json'):
                # 如果配置文件不存在，创建默认配置
                self.config = {
                    'hosts': [],
                    'default_user': 'vagrant',
                    'default_port': 22,
                    'timeout': 10,
                    'default_password': 'vagrant'
                }
                self.save_config()  # 保存默认配置
            else:
                with open('config.json', 'r') as f:
                    self.config = json.load(f)
            
            # 加载主机到树形视图
            for host in self.config['hosts']:
                self.host_tree.insert('', 'end', values=(host, '未连接'))
        except json.JSONDecodeError as e:
            messagebox.showerror("错误", f"配置文件格式错误：{str(e)}")
            self.config = {
                'hosts': [],
                'default_user': 'vagrant',
                'default_port': 22,
                'timeout': 10,
                'default_password': 'vagrant'
            }
            self.save_config()  # 保存默认配置
        except Exception as e:
            messagebox.showerror("错误", f"加载配置失败：{str(e)}")
            self.config = {
                'hosts': [],
                'default_user': 'vagrant',
                'default_port': 22,
                'timeout': 10,
                'default_password': 'vagrant'
            }
            self.save_config()  # 保存默认配置

        print(self.config)  # 在加载配置后打印配置内容
        
    def save_config(self):
        with open('config.json', 'w') as f:
            json.dump(self.config, f)
            
    def import_hosts(self):
        # 创建一个新的窗口
        dialog = tk.Toplevel(self.root)
        dialog.title("添加主机")
        
        # 选项变量
        host_type = tk.StringVar(value="单个")  # 默认选中"单个"
        
        # 创建单选框
        single_radio = tk.Radiobutton(dialog, text="单个主机", variable=host_type, value="单个")
        single_radio.grid(row=0, column=0, padx=10, pady=5)
        
        range_radio = tk.Radiobutton(dialog, text="IP段", variable=host_type, value="网段")
        range_radio.grid(row=0, column=1, padx=10, pady=5)
        
        # 输入框
        host_entry = tk.Entry(dialog, width=30)
        host_entry.grid(row=1, column=0, columnspan=2, padx=10, pady=10)
        
        # 确认按钮
        ttk.Button(dialog, text="确认", command=lambda: self.confirm_import(host_entry, host_type, dialog)).grid(row=2, columnspan=2, pady=10)

    def confirm_import(self, host_entry, host_type, dialog):
        host_input = host_entry.get().strip()  # 去除前后空格
        if host_type.get() == "单个":  # 如果选择了单个主机
            if host_input and host_input not in self.config['hosts']:
                self.config['hosts'].append(host_input)
                self.host_tree.insert('', 'end', values=(host_input, '未连接'))
                self.save_config()
                messagebox.showinfo("成功", f"主机 {host_input} 已添加。")
            else:
                messagebox.showwarning("警告", "主机已存在或输入无效。")
        else:  # 否则处理为IP段
            if host_input:
                try:
                    start_ip, end_ip = host_input.split('-')
                    start_ip_parts = list(map(int, start_ip.split('.')))
                    end_ip_parts = list(map(int, end_ip.split('.')))
                    
                    # 确保起始IP和结束IP在同一网段
                    if start_ip_parts[:3] != end_ip_parts[:3]:
                        messagebox.showerror("错误", "起始IP和结束IP必须在同一网段。")
                        return
                    
                    for i in range(start_ip_parts[2], end_ip_parts[2] + 1):
                        for j in range(start_ip_parts[3], end_ip_parts[3] + 1):
                            host = f"{start_ip_parts[0]}.{start_ip_parts[1]}.{start_ip_parts[2]}.{j}"
                            if host not in self.config['hosts']:
                                self.config['hosts'].append(host)
                                self.host_tree.insert('', 'end', values=(host, '未连接'))
                            else:
                                messagebox.showwarning("警告", f"主机 {host} 已存在，跳过添加。")
                    self.save_config()
                    messagebox.showinfo("成功", f"IP段 {host_input} 已添加。")
                except Exception as e:
                    messagebox.showerror("错误", f"导入失败：{str(e)}")
            else:
                messagebox.showwarning("警告", "请输入有效的IP段。")
        
        dialog.destroy()  # 关闭对话框
        
    def execute(self):
        command = self.cmd_entry.get("1.0", "end").strip()  # 获取多行输入并去除前后空格
        if not command:
            messagebox.showwarning("警告", "请输入命令")
            return
        
        # 获取所有主机
        all_items = self.host_tree.get_children()
        if not all_items:
            messagebox.showwarning("警告", "没有可执行的主机")
            return
        
        for item in all_items:
            host = self.host_tree.item(item)['values'][0]
            threading.Thread(target=self.ssh_execute,
                             args=(item, host, command)).start()
        
        self.update_execute_button_state()  # 更新执行按钮状态
        
    def ssh_execute(self, item, host, command):
        try:
            # 更新状态
            self.host_tree.set(item, 'status', '执行中')
            
            # 获取或创建SSH连接
            if host not in self.ssh_pool:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                # 解析主机信息
                if '@' in host:
                    user, host_port = host.split('@')
                else:
                    user = self.config['default_user']
                    host_port = host
                    
                if ':' in host_port:
                    hostname, port = host_port.split(':')
                    port = int(port)
                else:
                    hostname = host_port
                    port = self.config['default_port']
                    
                print(f"Connecting to {hostname}:{port} with user {user} and password {self.config['default_password']}")
                
                # 使用密码进行连接
                ssh.connect(hostname, port, user, self.config['default_password'], 
                            timeout=self.config['timeout'], 
                            look_for_keys=False, 
                            allow_agent=False)
                self.ssh_pool[host] = ssh
            else:
                ssh = self.ssh_pool[host]
            
            # 执行命令
            stdin, stdout, stderr = ssh.exec_command(command)
            result = stdout.read().decode()
            error = stderr.read().decode()
            
            # 显示结果
            log_entry = f"\n[{host} - {datetime.now()}]\n{command}\n{result}{error}\n"
            self.show_result(log_entry)
            
            # 将结果写入日志文件
            with open("execution_log.txt", "a") as log_file:
                log_file.write(log_entry)
            
            # 更新状态
            self.host_tree.set(item, 'status', '完成')
            
        except Exception as e:
            error_message = f"\n[{host}] Error: {str(e)}\n"
            self.show_result(error_message)
            
            # 将错误信息写入日志文件
            with open("execution_log.txt", "a") as log_file:
                log_file.write(error_message)
            
            self.host_tree.set(item, 'status', '失败')
            
            # 删除失败的连接
            if host in self.ssh_pool:
                del self.ssh_pool[host]
                
    def show_result(self, text):
        self.root.after(0, lambda: self.result_text.insert('end', text))
        self.root.after(0, lambda: self.result_text.see('end'))
        
    def clear_results(self):
        self.result_text.delete('1.0', 'end')
        
    def show_settings(self):
        settings = tk.Toplevel(self.root)
        settings.title("连接设置")
        settings.geometry("300x250")
        
        ttk.Label(settings, text="默认用户名:").grid(row=0, column=0, padx=10, pady=5, sticky='e')
        user_entry = ttk.Entry(settings)
        user_entry.insert(0, self.config['default_user'])
        user_entry.grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Label(settings, text="默认密码:").grid(row=1, column=0, padx=10, pady=5, sticky='e')
        password_entry = ttk.Entry(settings, show="*")  # 密码输入框
        password_entry.insert(0, self.config.get('default_password', ''))  # 如果有默认密码则填入
        password_entry.grid(row=1, column=1, padx=10, pady=5)
        
        ttk.Label(settings, text="默认端口:").grid(row=2, column=0, padx=10, pady=5, sticky='e')
        port_entry = ttk.Entry(settings)
        port_entry.insert(0, str(self.config['default_port']))
        port_entry.grid(row=2, column=1, padx=10, pady=5)
        
        ttk.Label(settings, text="超时时间(秒):").grid(row=3, column=0, padx=10, pady=5, sticky='e')
        timeout_entry = ttk.Entry(settings)
        timeout_entry.insert(0, str(self.config['timeout']))
        timeout_entry.grid(row=3, column=1, padx=10, pady=5)
        
        ttk.Button(settings, text="保存", command=lambda: self.save_settings(user_entry, password_entry, port_entry, timeout_entry)).grid(row=4, columnspan=2, pady=10)

    def save_settings(self, user_entry, password_entry, port_entry, timeout_entry):
        self.config['default_user'] = user_entry.get()
        self.config['default_password'] = password_entry.get()  # 保存密码
        self.config['default_port'] = int(port_entry.get())
        self.config['timeout'] = int(timeout_entry.get())
        self.save_config()
        messagebox.showinfo("成功", "设置已保存")  # 确认消息

    def export_config(self):
        filename = filedialog.asksaveasfilename(defaultextension=".json")
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.config, f, indent=4)
                messagebox.showinfo("成功", "配置已导出")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败：{str(e)}")
                
    def __del__(self):
        # 关闭所有SSH连接
        for ssh in self.ssh_pool.values():
            try:
                ssh.close()
            except:
                pass

    def select_all_hosts(self):
        for item in self.host_tree.get_children():
            self.host_tree.selection_add(item)  # 选择所有主机
        self.update_execute_button_state()  # 更新执行按钮状态

    def clear_selected_hosts(self):
        selected_items = self.host_tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "请先选择要删除的主机")
            return
        
        for item in selected_items:
            host = self.host_tree.item(item)['values'][0]
            self.config['hosts'].remove(host)  # 从配置中删除主机
            self.host_tree.delete(item)  # 从树形视图中删除主机
        
        self.save_config()  # 保存更新后的配置
        messagebox.showinfo("成功", "已成功删除选定的主机")

    def deselect_all_hosts(self):
        self.host_tree.selection_remove(self.host_tree.selection())  # 取消选择所有主机
        self.update_execute_button_state()  # 更新执行按钮状态

    def update_execute_button_state(self):
        selected_items = self.host_tree.selection()
        if selected_items:
            self.execute_button.config(state=tk.NORMAL)  # 启用执行按钮
        else:
            self.execute_button.config(state=tk.DISABLED)  # 禁用执行按钮

    def on_host_select(self, event):
        self.update_execute_button_state()  # 更新执行按钮状态

if __name__ == "__main__":
    root = tk.Tk()
    app = EnhancedBatchSSH(root)
    root.mainloop()