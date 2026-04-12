# 演示数据与登录（中文速查）

## 1. 准备数据

在项目根目录执行：

```bash
python manage.py seed_sales_reports_demo --days 14 --months 12 --years 5
```

每次执行都会：**创建或更新** `demo_vendor` / `demo_customer`，并把密码设为 `--password`（默认 **`demo123456`**），同时 `is_active=True`。若以前登不上，**再跑一次**本命令即可。

## 2. 启动网站

```bash
python manage.py runserver
```

## 3. 登录

- 地址：**http://127.0.0.1:8000/user/login/**
- 用户名：**demo_vendor**
- 密码：**demo123456**

## 4. 打开销售报表

**http://127.0.0.1:8000/vendor/reports/**

登录后也可点顶部导航里的 **Sales reports**。

## 5. 自定义账号密码

```bash
python manage.py seed_sales_reports_demo --vendor-username 我的商户名 --password 我的密码 --months 12 --years 5
```

然后用你设的用户名、密码登录。
