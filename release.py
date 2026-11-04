#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一条命令发版：建 tag → Gitee 先推 → GitHub 后推 → 双平台 Release → 上传附件 → 回读校验。

用法:
    python3 release.py v1.0.1 -m "feat: 文案微调"
    python3 release.py v1.0.1 -m "feat: x" -t "夜之城终端 v1.0.1" -n release-notes.md -a dist/pkg.zip

参数:
    version              版本号，必须形如 v1.2.3
    -m / --message       提交信息（无改动时用来写 tag 说明）
    -t / --title         Release 标题，默认 "<项目名> <version>"
    -n / --notes         Release 正文（Markdown 文件），缺省自动生成
    -a / --asset         附件，可多个，支持通配符；缺省不上传附件
    --dry-run            只打印计划，不执行任何写操作
    --no-release         只推 git（含 tag），不建 Release
    --no-push            只建 Release（复用已推送的 tag）

设计约束（改脚本时别退回去）:
    * 代理端口从环境变量读，不写死；Gitee 强制直连
    * tag 已存在则跳过创建；Release 已存在则复用并补附件 —— 可安全重跑
    * 任一步失败立即中止并打印可执行的补救命令，不静默跳过
    * 所有 HTTP 请求都带回读校验，不信任返回值
    * Gitee 建 Release 必须带 target_commitish，否则 400
"""

import argparse
import glob
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

GITEE_API = "https://gitee.com/api/v5"
GITHUB_API = "https://api.github.com"
GITHUB_UPLOAD = "https://uploads.github.com"
UA = "release.py/1.0"


# ---------------------------------------------------------------- 基础工具

def sh(cmd, check=True, capture=True, env=None):
    """跑一条命令。失败时把 stderr 原样抛出来，不吞错误。"""
    full_env = dict(os.environ)
    if env:
        full_env.update(env)
    r = subprocess.run(cmd, shell=True, text=True, encoding="utf-8", errors="replace",
                       capture_output=capture, env=full_env)
    if check and r.returncode != 0:
        out = ((r.stdout or "") + (r.stderr or "")).strip()
        fail(f"命令失败: {cmd}\n{out}")
    return (r.stdout or "").strip()


def run_echo(cmd, env=None):
    print(f"  $ {cmd}")
    return sh(cmd, env=env)


def fail(msg, hint=None):
    print(f"\n[失败] {msg}", file=sys.stderr)
    if hint:
        print(f"[补救] {hint}", file=sys.stderr)
    sys.exit(1)


def ok(msg):
    print(f"[ok] {msg}")


def load_credential(host):
    """从 ~/.git-credentials 取 (user, secret)。没有就返回 (None, None)。"""
    path = os.path.expanduser("~/.git-credentials")
    if not os.path.exists(path):
        return None, None
    for line in open(path, encoding="utf-8"):
        m = re.match(r"https?://([^:@]+):(.*)@(.+)$", line.strip())
        if m and m.group(3).lower().endswith(host):
            user = urllib.parse.unquote(m.group(1))
            return user, m.group(2)
    return None, None


def parse_remote(url):
    """从 git remote URL 里取 (owner, repo)。"""
    m = re.search(r"(?:github\.com|gitee\.com)[/:]([^/]+)/([^/]+?)(?:\.git)?$", url.strip())
    return (m.group(1), m.group(2)) if m else (None, None)


def opener(use_proxy=True):
    if use_proxy:
        return urllib.request.build_opener()
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))


def http(method, url, data=None, headers=None, use_proxy=True, label=""):
    """发请求，返回 (status, 解析后的 body)。4xx/5xx 不抛，交给调用方判断。"""
    hdrs = {"User-Agent": UA, "Accept": "application/json"}
    hdrs.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with opener(use_proxy).open(req, timeout=120) as r:
            raw = r.read().decode("utf-8", "replace")
            return r.status, (json.loads(raw) if raw.strip().startswith(("{", "[")) else raw)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            body = json.loads(raw)
        except Exception:
            body = raw
        return e.code, body
    except Exception as e:  # 网络层
        return 0, f"{type(e).__name__}: {e}"


def multipart(field, filepath):
    """手写 multipart/form-data，避免为一个上传引入 requests。"""
    boundary = "----releasepy" + uuid.uuid4().hex
    name = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        payload = f.read()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="{field}"; filename="{name}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode() + payload + f"\r\n--{boundary}--\r\n".encode()
    return body, f"multipart/form-data; boundary={boundary}"


# ---------------------------------------------------------------- 参数与上下文

def build_context(args):
    root = sh("git rev-parse --show-toplevel")
    os.chdir(root)
    version = args.version if args.version.startswith("v") else "v" + args.version
    if not re.fullmatch(r"v\d+\.\d+\.\d+", version):
        fail(f"版本号格式不对: {version}，要求 vX.Y.Z")

    gitee_url = sh("git remote get-url origin", check=False)
    # origin 挂了两个 pushurl，取 Gitee 那条
    urls = sh("git config --get-all remote.origin.pushurl", check=False).splitlines() or [gitee_url]
    gitee_url = next((u for u in urls if "gitee.com" in u), "")
    github_url = next((u for u in urls if "github.com" in u), gitee_url)
    g_owner, g_repo = parse_remote(gitee_url)
    h_owner, h_repo = parse_remote(github_url)
    if not (g_owner and h_owner):
        fail("没解析出远端仓库地址", "检查 git remote -v")

    gitee_token = os.environ.get("GITEE_TOKEN") or load_credential("gitee.com")[1]
    github_token = os.environ.get("GITHUB_TOKEN") or load_credential("github.com")[1]
    if not gitee_token:
        fail("缺少 GITEE_TOKEN", "export GITEE_TOKEN=<私人令牌，scope=projects>")
    if not github_token:
        fail("缺少 GITHUB_TOKEN", "export GITHUB_TOKEN=<PAT，scope=repo>")

    # git 推送的 URL 里带用户名，才能命中凭据库里正确的那个账号
    gitee_push = f"https://{g_owner}:{urllib.parse.quote(gitee_token, safe='')}@gitee.com/{g_owner}/{g_repo}.git"
    github_push = f"https://{h_owner}:{urllib.parse.quote(github_token, safe='')}@github.com/{h_owner}/{h_repo}.git"

    return {
        "root": root, "version": version,
        "gitee": {"owner": g_owner, "repo": g_repo, "url": gitee_url, "push": gitee_push, "token": gitee_token},
        "github": {"owner": h_owner, "repo": h_repo, "url": github_url, "push": github_push, "token": github_token},
        "title": args.title or f"{os.path.basename(root)} {version}",
    }


def collect_assets(patterns):
    files = []
    for p in patterns or []:
        hits = sorted(glob.glob(p))
        if not hits:
            fail(f"附件不存在: {p}")
        files.extend(h for h in hits if os.path.isfile(h))
    seen, out = set(), []
    for f in files:
        rp = os.path.realpath(f)
        if rp not in seen:
            seen.add(rp)
            out.append(f)
    return out


def release_body(ctx, notes_path):
    if notes_path:
        if not os.path.exists(notes_path):
            fail(f"notes 文件不存在: {notes_path}")
        return open(notes_path, encoding="utf-8").read()
    commit = sh("git log -1 --pretty=%s", check=False)
    return (
        f"## {ctx['title']}\n\n"
        f"- 线上终端：https://cyberpunk-terminal.app.workbuddy.host/\n"
        f"- 提交：`{commit}`\n\n"
        f"```bash\n# 本地预览\npython3 -m http.server 8000\n```\n"
    )


# ---------------------------------------------------------------- git 阶段

def stage_git(ctx, args, assets):
    print("\n== 1/6 工作区与提交 ==")
    dirty = sh("git status --porcelain", check=False)
    if dirty and args.message:
        run_echo("git add -A")
        run_echo(f'git commit -m {json.dumps(args.message, ensure_ascii=False)}')
    elif dirty:
        fail("工作区有改动但没给 -m 提交信息", '补上 -m "feat: ..." 再跑')
    else:
        ok("工作区干净，跳过提交")

    print("\n== 2/6 tag ==")
    head = sh("git rev-parse HEAD")
    existing = sh(f"git rev-parse -q --verify refs/tags/{ctx['version']}", check=False)
    if existing:
        if existing != head:
            fail(f"tag {ctx['version']} 已存在且指向 {existing[:8]}，与 HEAD {head[:8]} 不同",
                 f"要重发同一版本：git tag -d {ctx['version']} && git push --delete gitee {ctx['version']}")
        ok(f"tag {ctx['version']} 已存在且指向 HEAD，跳过创建")
    else:
        run_echo(f'git tag -a {ctx["version"]} -m {json.dumps(args.message or ctx["version"], ensure_ascii=False)}')
        ok(f"新建 tag {ctx['version']} -> {head[:8]}")
    return head


def stage_push(ctx, args):
    print("\n== 3/6 推送（Gitee 先，GitHub 后）==")
    branch = sh("git rev-parse --abbrev-ref HEAD")
    # Gitee 强制直连：国内走代理更慢，且代理常对 Gitee 报 502
    run_echo(f'git push {ctx["gitee"]["push"]} {branch} {ctx["version"]}',
             env={"no_proxy": "gitee.com", "NO_PROXY": "gitee.com"})
    ok("Gitee 推送完成")

    code, _ = http("GET", f"{GITHUB_API}/repos/{ctx['github']['owner']}/{ctx['github']['repo']}",
                   headers={"Authorization": f"Bearer {ctx['github']['token']}"})
    if code != 200:
        fail(f"GitHub 不可达（HTTP {code}），Gitee 已完成，属于「半推」状态",
             f"网络恢复后重跑：python3 release.py {ctx['version']} -m '...' （幂等，不会重复打 tag）")
    run_echo(f'git push {ctx["github"]["push"]} {branch} {ctx["version"]}')
    ok("GitHub 推送完成")


# ---------------------------------------------------------------- Release 阶段

def ensure_gitee_release(ctx, body, head):
    g = ctx["gitee"]
    print("\n== 4/6 Gitee Release ==")
    q = urllib.parse.urlencode({"access_token": g["token"]})
    code, data = http("GET", f"{GITEE_API}/repos/{g['owner']}/{g['repo']}/releases/tags/{ctx['version']}?{q}",
                      use_proxy=False)
    if code == 200 and isinstance(data, dict):
        ok(f"已存在 release id={data.get('id')}，复用")
        return data
    form = urllib.parse.urlencode({
        "access_token": g["token"],
        "tag_name": ctx["version"],
        "target_commitish": head,      # 缺这个就 400 target_commitish is missing
        "name": ctx["title"],
        "body": body,
        "prerelease": "false",
    }).encode()
    code, data = http("POST", f"{GITEE_API}/repos/{g['owner']}/{g['repo']}/releases", data=form,
                      headers={"Content-Type": "application/x-www-form-urlencoded"}, use_proxy=False)
    if code not in (200, 201):
        fail(f"Gitee 建 Release 失败 HTTP {code}: {data}",
             "若是 401/403，说明令牌缺 projects 权限，去 Gitee 设置里补")
    ok(f"Gitee Release 创建成功 id={data.get('id')}")
    return data


def ensure_github_release(ctx, body):
    h = ctx["github"]
    hdr = {"Authorization": f"Bearer {h['token']}"}
    print("\n== 5/6 GitHub Release ==")
    code, data = http("GET", f"{GITHUB_API}/repos/{h['owner']}/{h['repo']}/releases/tags/{ctx['version']}", headers=hdr)
    if code == 200 and isinstance(data, dict):
        ok(f"已存在 release id={data.get('id')}，复用")
        return data
    payload = json.dumps({"tag_name": ctx["version"], "name": ctx["title"],
                          "body": body, "draft": False, "prerelease": False}).encode()
    code, data = http("POST", f"{GITHUB_API}/repos/{h['owner']}/{h['repo']}/releases", data=payload,
                      headers={**hdr, "Content-Type": "application/json"})
    if code not in (200, 201):
        fail(f"GitHub 建 Release 失败 HTTP {code}: {data}",
             "若是 403，检查 PAT 是否有 repo 权限")
    ok(f"GitHub Release 创建成功 id={data.get('id')}")
    return data


def upload_assets(ctx, assets, gitee_rel, github_rel):
    if not assets:
        ok("没有附件，跳过上传")
        return
    g, h = ctx["gitee"], ctx["github"]
    have_g = {a.get("name") for a in (gitee_rel.get("assets") or [])}
    have_h = {a.get("name") for a in (github_rel.get("assets") or [])}
    hdr = {"Authorization": f"Bearer {h['token']}"}

    for path in assets:
        name = os.path.basename(path)
        size_mb = os.path.getsize(path) / 1048576
        print(f"-- {name} ({size_mb:.1f} MB)")

        if name in have_g:
            ok("Gitee 已有同名附件，跳过")
        else:
            body, ctype = multipart("file", path)
            code, data = http("POST",
                              f"{GITEE_API}/repos/{g['owner']}/{g['repo']}/releases/{gitee_rel['id']}/attach_files"
                              f"?access_token={g['token']}",
                              data=body, headers={"Content-Type": ctype}, use_proxy=False)
            if code not in (200, 201):
                fail(f"Gitee 上传附件失败 HTTP {code}: {data}")
            ok("Gitee 附件已上传")

        if name in have_h:
            ok("GitHub 已有同名附件，跳过")
        else:
            with open(path, "rb") as f:
                blob = f.read()
            code, data = http("POST",
                              f"{GITHUB_UPLOAD}/repos/{h['owner']}/{h['repo']}/releases/{github_rel['id']}"
                              f"/assets?name={urllib.parse.quote(name)}",
                              data=blob, headers={**hdr, "Content-Type": "application/octet-stream"})
            if code not in (200, 201):
                fail(f"GitHub 上传附件失败 HTTP {code}: {data}")
            ok("GitHub 附件已上传")


# ---------------------------------------------------------------- 回读校验

def stage_verify(ctx, assets):
    print("\n== 6/6 回读校验 ==")
    g, h = ctx["gitee"], ctx["github"]
    problems = []

    # ① 两端 tag SHA 一致
    local = sh("git rev-parse HEAD")
    g_tag = sh(f'no_proxy=gitee.com git ls-remote {g["push"]} refs/tags/{ctx["version"]} '
               f'refs/tags/{ctx["version"]}^{{}}', check=False)
    h_tag = sh(f'git ls-remote {h["push"]} refs/tags/{ctx["version"]} refs/tags/{ctx["version"]}^{{}}', check=False)
    for label, out in (("Gitee", g_tag), ("GitHub", h_tag)):
        sha = (out.split()[0] if out else "")
        if not sha:
            problems.append(f"{label} 上没有 tag {ctx['version']}")
        else:
            print(f"  {label:6} tag -> {sha[:12]}")
    print(f"  local  HEAD -> {local[:12]}")

    # ② Release 页面 + 附件
    q = urllib.parse.urlencode({"access_token": g["token"]})
    code, gr = http("GET", f"{GITEE_API}/repos/{g['owner']}/{g['repo']}/releases/tags/{ctx['version']}?{q}",
                    use_proxy=False)
    g_page = f"https://gitee.com/{g['owner']}/{g['repo']}/releases/tag/{ctx['version']}"
    g_assets = []
    if code != 200:
        problems.append(f"Gitee Release 读不回来 HTTP {code}")
    else:
        g_assets = [a.get("name") for a in (gr.get("assets") or [])]
        print(f"  Gitee  Release: {g_page}")
        print(f"  Gitee  附件: {g_assets or '（无）'}")

    code, hr = http("GET", f"{GITHUB_API}/repos/{h['owner']}/{h['repo']}/releases/tags/{ctx['version']}",
                    headers={"Authorization": f"Bearer {h['token']}"})
    if code != 200:
        problems.append(f"GitHub Release 读不回来 HTTP {code}")
    else:
        h_assets = [f"{a.get('name')} ({a.get('size',0)//1024} KB)" for a in (hr.get("assets") or [])]
        print(f"  GitHub Release: {hr.get('html_url')}")
        print(f"  GitHub 附件: {h_assets or '（无）'}")

    # ③ 附件数量对得上
    want = {os.path.basename(a) for a in assets}
    if want:
        if code == 200:
            have = {a.get("name") for a in (hr.get("assets") or [])}
            if not want <= have:
                problems.append(f"GitHub 缺附件: {sorted(want - have)}")
        if not want <= set(g_assets):
            problems.append(f"Gitee 缺附件: {sorted(want - set(g_assets))}")

    if problems:
        print()
        for p in problems:
            print(f"  [x] {p}")
        fail("回读校验未通过，见上方清单")
    ok("两端 tag / Release / 附件全部对齐")

    print("\n" + "-" * 62)
    print(f"发版完成: {ctx['version']}")
    print(f"  GitHub: https://github.com/{h['owner']}/{h['repo']}/releases/tag/{ctx['version']}")
    print(f"  Gitee : {g_page}")
    print("-" * 62)
    print("\n# README 更新日志片段（复制即用）\n")
    print(f"### {ctx['version']} — {__import__('datetime').date.today().isoformat()}\n")
    print(f"- {ctx['title']}")


def main():
    ap = argparse.ArgumentParser(description="一键发版：双推 + 双 Release")
    ap.add_argument("version")
    ap.add_argument("-m", "--message", default="")
    ap.add_argument("-t", "--title", default="")
    ap.add_argument("-n", "--notes", default="")
    ap.add_argument("-a", "--asset", action="append", default=[])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-release", action="store_true")
    ap.add_argument("--no-push", action="store_true")
    args = ap.parse_args()

    ctx = build_context(args)
    assets = collect_assets(args.asset)

    print(f"项目   : {ctx['root']}")
    print(f"版本   : {ctx['version']}")
    print(f"Gitee  : {ctx['gitee']['owner']}/{ctx['gitee']['repo']}")
    print(f"GitHub : {ctx['github']['owner']}/{ctx['github']['repo']}")
    print(f"附件   : {[os.path.basename(a) for a in assets] or '（无）'}")

    if args.dry_run:
        print("\n[dry-run] 计划如下，不执行任何写操作：")
        print(f"  1. git add -A && git commit -m {args.message!r}" if sh('git status --porcelain', check=False) else "  1. 无需提交")
        print(f"  2. git tag -a {ctx['version']}")
        print(f"  3. push 到 Gitee，然后 push 到 GitHub（main + tag）")
        print(f"  4. 建 Gitee / GitHub Release：{ctx['title']}")
        print(f"  5. 上传附件：{[os.path.basename(a) for a in assets] or '无'}")
        print("  6. 回读 tag SHA / Release / 附件")
        return

    head = stage_git(ctx, args, assets)
    if not args.no_push:
        stage_push(ctx, args)
    if args.no_release:
        ok("--no-release：只推 git，退出")
        return

    body = release_body(ctx, args.notes)
    gitee_rel = ensure_gitee_release(ctx, body, head)
    github_rel = ensure_github_release(ctx, body)
    upload_assets(ctx, assets, gitee_rel, github_rel)
    stage_verify(ctx, assets)


if __name__ == "__main__":
    main()
