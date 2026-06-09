# Economic Calendar Subscription

这个仓库会自动生成一个可订阅的经济日历 ICS：

https://aka-han.github.io/ZXSK/calendar.ics

## 功能

- 每 6 小时自动更新一次
- 读取 Forex Factory weekly JSON
- 默认只保留 High Impact 事件
- 默认只保留 USD 事件
- 每个事件包含：
  - DESCRIPTION: Forecast / Previous / Impact / Currency / 说明
  - LOCATION: Forex Factory
  - URL: https://www.forexfactory.com/calendar
- 默认提醒：
  - 30 分钟前
  - 5 分钟前

## 使用步骤

1. 在 GitHub 创建一个新仓库：`ZXSK`
2. 上传本 ZIP 解压后的所有文件
3. 进入仓库 Settings → Pages
4. Source 选择：Deploy from a branch
5. Branch 选择：main / root
6. 等 1–2 分钟后访问：

```text
https://aka-han.github.io/ZXSK/calendar.ics
```

7. iPhone 订阅：
   Settings → Apps → Calendar → Calendar Accounts → Add Account → Other → Add Subscribed Calendar

填入：

```text
https://aka-han.github.io/ZXSK/calendar.ics
```

## 注意

Forex Factory 的公开 JSON 通常是 weekly feed，所以它会持续滚动更新未来一周左右的事件。
如果要全年固定版，可以另外上传静态 `2026.ics`。
