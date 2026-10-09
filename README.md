# sycamoreagritech.com

Sycamore Agritech Limited 官网：纯静态单页，支持中文、English、Français、Português 四种语言，没有构建步骤，托管在 GitHub Pages，域名解析在阿里云。

```
index.html          页面内容（四种语言写在一起：lang="zh-CN" / "en" / "fr" / "pt"）
assets/style.css    样式
assets/main.js      语言切换、手机菜单、询价表单
assets/photos/      农场与仓库照片（已压缩、去除元数据）
assets/logo-*.png   从公司 logo 抠出的透明图（标志、SYCAMORE 字标，各有深色背景用的浅色版）
assets/logo-original.webp  logo 原图
assets/favicon.png, apple-touch-icon.png  浏览器 / 手机桌面图标
assets/og-image.jpg 微信等社交平台分享链接时显示的图
CNAME               GitHub Pages 自定义域名
```

## 修改内容

- 每段文字都有四种语言版本，相邻放置，例如
  `<span lang="zh-CN">关于我们</span><span lang="en">About</span><span lang="fr">À propos</span><span lang="pt">Sobre nós</span>`，
  修改时四份都要改。下拉选项和输入框提示文字写在 `data-zh` / `data-en` / `data-fr` / `data-pt`（或 `data-ph-*`）属性里。
- 访客第一次打开时按浏览器语言自动选择，其他语言默认显示英文；也可以用 `?lang=zh|en|fr|pt` 指定。
- 联系方式（邮箱、电话、地址）在 `index.html` 的「联系我们」部分，搜 `contact-list`。
- 询价表单会打开访客的邮件应用，收件人是 `info@sycamoreagritech.com`；如需更换，改 `assets/main.js` 顶部的 `EMAIL` 和 `index.html` 里的邮箱。
- 本地预览：`python3 -m http.server 8737`，然后打开 http://localhost:8737

## 部署到 GitHub Pages

```bash
gh auth login
git init -b main && git add . && git commit -m "Initial site"
gh repo create sycamoreagritech.com --public --source=. --push
gh api -X POST repos/{owner}/sycamoreagritech.com/pages -f "source[branch]=main" -f "source[path]=/"
gh api -X PUT repos/{owner}/sycamoreagritech.com/pages -f cname=sycamoreagritech.com
```

之后每次修改：`git commit -am "..." && git push`，约 1 分钟后生效。

## 阿里云 DNS 解析

阿里云控制台 → 云解析 DNS → sycamoreagritech.com → 解析设置 → 添加记录（解析线路选「默认」）：

| 主机记录 | 记录类型 | 记录值 |
|---|---|---|
| @ | A | 185.199.108.153 |
| @ | A | 185.199.109.153 |
| @ | A | 185.199.110.153 |
| @ | A | 185.199.111.153 |
| www | CNAME | `<你的 GitHub 用户名>.github.io` |

解析生效后（通常几分钟到 1 小时），在仓库 Settings → Pages 勾选 **Enforce HTTPS**，或运行：

```bash
gh api -X PUT repos/{owner}/sycamoreagritech.com/pages -F https_enforced=true
```

注意：

- 域名需在阿里云完成**实名认证**，否则会被暂停解析（ServerHold）。
- 托管在海外的 GitHub Pages，不需要 ICP 备案；国内访问速度一般，偶尔不稳定。
- `info@sycamoreagritech.com` 需要另外开通邮箱（如阿里云企业邮箱免费版），并按邮箱服务商的说明添加 MX 记录。
