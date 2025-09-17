Flask URL Shortener

一个使用Flask + SQLite + SQLAlchemy实现的简易URL短链接服务，支持表单提交和JSON API两种方式。
短链接采用Base62 编码生成，支持过期时间、点击统计 等功能。

功能:
  将长网址缩短为短网址，自动存储到数据库
  短网址点击后自动跳转到原始网址
  统计短链接的点击次数
  支持过期机制（默认 30 天过期）
  同时支持网页表单和 JSON API 调用
  提供所有已注册短链接的查询接口
  自定义全局错误处理，返回统一格式的JSON错误信息
  version2实现了自定义短码

项目结构：
  url_shortener/
  │── app.py              # 主程序入口
  │── venv
  │── README.md           # 使用说明
  │── instance
        │   
        urls.db             # SQLite 数据库（运行时生成）

注意事项：本地Flask不支持https，所以生成https的短码会出现安全拦截

操作（以version2的表单提交为例）：
    1.先进入虚拟环境再运行
    2.进入浏览器 "http://127.0.0.1:5000/" 显示如下画面：
    
   <img width="563" height="195" alt="image" src="https://github.com/user-attachments/assets/a14460da-d95e-45a4-ab2a-b8cbe76890f7" />

    
    3.将长连接填入上方的输入框（必填）
    4.将自定义短码填入下方的输入框（选填）
    5.好啦，接下来就自行探索啦！（没什么功能啦！）
    

扩展方法：
   可以增加token认证（用户登录 / 权限管理）







