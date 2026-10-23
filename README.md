# www.sycamoreagritech.com

Sycamore Agritech Limited（盛楷农业科技有限公司）官网。静态网站，托管在 GitHub Pages，域名解析在阿里云。

## 网站结构

每种语言一套独立页面（方便 Google 分别收录）：

| 页面 | English | 中文 | Français | Português |
|---|---|---|---|---|
| 首页 | `/` | `/zh/` | `/fr/` | `/pt/` |
| 农机租赁 | `/machinery-hire/` | `/zh/machinery-hire/` | `/fr/machinery-hire/` | `/pt/machinery-hire/` |
| 农产品贸易 | `/agricultural-products/` | `/zh/agricultural-products/` | `/fr/agricultural-products/` | `/pt/agricultural-products/` |

这些 HTML 文件以及 `404.html`、`sitemap.xml`、`robots.txt` 都由 `_src/build.py` **自动生成，不要直接改**。

## 修改内容

```
_src/content.json        中文和英文文案（每条 {zh, en, note}）
_src/i18n/fr.json        法语文案
_src/i18n/pt.json        葡萄牙语文案
_src/trade-data.json     农产品目录分类和供应月份
_src/layout.html         页头、页脚等公共部分
_src/pages/*.html        各页面正文（home / hire / trade / 404）
_src/partials/*.html     多个页面共用的片段（联系表单、农时图等）
assets/style.css         样式
assets/main.js           菜单、语言提示、图片放大、询价表单
assets/img/              网站照片（WebP + JPEG）
```

改完后运行：

```bash
python3 _src/build.py
```

构建会提示缺少的法语或葡萄牙语文案，也会检查公司名称有没有写全（必须写 "Sycamore Agritech Limited"，中文页使用「盛楷农业科技有限公司」）。

本地预览：`python3 -m http.server 8737`，然后打开 http://localhost:8737

## 发布

`main` 分支会直接发布到线上，建议先建分支、提 PR，确认后再合并。

```bash
git checkout -b <分支名>
python3 _src/build.py
git add -A && git commit -m "..."
git push -u origin <分支名>
gh pr create
```

## 域名与邮箱（阿里云）

- 网站：主网址是 `www.sycamoreagritech.com`（`CNAME` 文件），不带 www 的 `sycamoreagritech.com` 会自动跳转过来。A 记录指向 GitHub Pages（185.199.108–111.153），`www` CNAME 指向 `afridavvv.github.io`，已强制 HTTPS。网页里的网址统一写成 `www.sycamoreagritech.com`；邮箱地址仍是 `@sycamoreagritech.com`，不加 www。
- 邮箱：阿里邮箱免费版，MX / SPF / DKIM / DMARC 均已配置并验证通过。管理员账号 `postmaster@sycamoreagritech.com`。
- 网站对外只公布 `reception@sycamoreagritech.com`：页脚、联系方式、贸易页按钮、询价表单和结构化数据都用这个地址。要改联系邮箱，需同时改 `_src/layout.html`、`_src/partials/contact.html`、`_src/pages/trade.html`、`_src/build.py` 和 `assets/main.js`。
- Google Search Console 通过解析里的 `google-site-verification` TXT 记录验证网域所有权，**不要删除这条记录**。网站地图已提交。
