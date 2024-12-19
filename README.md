# 高级批量SSH工具

这是一个用于批量管理SSH连接的工具，支持对多个主机进行命令执行和管理。

## 功能

- **主机管理**：可以添加、删除和查看主机列表。
- **批量操作**：支持对多个主机同时执行命令。
- **命令输入**：提供多行命令输入框，支持滚动。
- **执行结果**：显示命令执行的结果，并支持滚动查看。
- **配置管理**：支持导入和导出主机配置。

## 安装

1. 确保您已安装 Python 3.x。
2. 克隆或下载此项目。
3. 在项目目录中，使用以下命令安装所需的依赖：

   ```bash
   pip install -r requirements.txt
   ```

## 使用

1. 运行程序：

   ```bash
   python pssh.py
   ```

2. 在主界面中，您可以：
   - 添加主机：点击“添加主机”按钮，输入主机信息。
   - 执行命令：在命令输入框中输入命令，选择主机后点击“执行”按钮。
   - 批量清除：选择多个主机后，点击“批量清除”按钮。

## 依赖

- `paramiko`：用于SSH连接。
- `tkinter`：用于创建图形用户界面。
- `json`：用于配置文件的读写。
- `threading`：用于处理并发SSH连接。

## 贡献

欢迎任何形式的贡献！请提交问题或拉取请求。

## 许可证

此项目采用 MIT 许可证，详细信息请查看 [LICENSE](LICENSE) 文件。