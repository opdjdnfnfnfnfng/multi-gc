#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import random
import threading
import requests
from datetime import datetime
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed

from instagrapi import Client
from instagrapi.exceptions import (
    RateLimitError,
    PleaseWaitFewMinutes,
    ChallengeRequired,
    ClientForbiddenError,
    LoginRequired,
    ClientThrottledError,
    ClientNotFoundError,
    ClientBadRequestError,
)


# ======================== CONFIG ========================
SESSION_FILE = "sessions.txt"
FILE_CHECK_INTERVAL = 60

MESSAGE_TEMPLATE = """Oo hlo side hato sab ham are hai serverdog ki maa ko dihhhhhh dene 🔥🔥🔥🤣🤣🤣🖕🏿🖕🏿🖕🏿 /-Oo hlo side hato sab ham are hai serverdog ki maa ko dihhhhhh dene 🔥🔥🔥🤣🤣🤣🖕🏿🖕🏿🖕🏿 /-Oo hlo side hato sab ham are hai serverdog ki maa ko dihhhhhh dene 🔥🔥🔥🤣🤣🤣🖕🏿🖕🏿🖕🏿 /-Oo hlo side hato sab ham are hai serverdog ki maa ko dihhhhhh dene 🔥🔥🔥🤣🤣🤣🖕🏿🖕🏿🖕🏿 /-Oo hlo side hato sab ham are hai serverdog ki maa ko dihhhhhh dene 🔥🔥🔥🤣🤣🤣🖕🏿🖕🏿🖕🏿 /-Oo hlo side hato sab ham are hai serverdog ki maa ko dihhhhhh dene 🔥🔥🔥🤣🤣🤣🖕🏿🖕🏿🖕🏿 /-Oo hlo side hato sab ham are hai serverdog ki maa ko dihhhhhh dene 🔥🔥🔥🤣🤣🤣🖕🏿🖕🏿🖕🏿 /-Oo hlo side hato sab ham are hai serverdog ki maa ko dihhhhhh dene 🔥🔥🔥🤣🤣🤣🖕🏿🖕🏿🖕🏿 /-Oo hlo side hato sab ham are hai serverdog ki maa ko dihhhhhh dene 🔥🔥🔥🤣🤣🤣🖕🏿🖕🏿🖕🏿 /-"""

PROXY_TIMEOUT = 3
PROXY_CHECK_WORKERS = 100
IG_CHECK_WORKERS = 30
PROXY_BATCH = 300
IG_CHECK_TIMEOUT = 10
LOGIN_MAX_RETRY = 5
RECENT_EVENTS_MAX = 5


# ======================== COLORS ========================
GREEN   = "\033[92m"
RED     = "\033[91m"
YELLOW  = "\033[93m"
CYAN    = "\033[96m"
MAGENTA = "\033[95m"
GRAY    = "\033[90m"
BOLD    = "\033[1m"
RESET   = "\033[0m"

_print_lock = threading.Lock()
_screen_lock = threading.Lock()

_RECENT_EVENTS = deque(maxlen=RECENT_EVENTS_MAX)
_RECENT_LOCK = threading.Lock()


def ts():
    return datetime.now().strftime("%H:%M:%S")


def add_event(text):
    with _RECENT_LOCK:
        _RECENT_EVENTS.append(f"[{ts()}] {text}")


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def safe_print(msg):
    with _print_lock:
        print(msg, flush=True)


def is_proxy_error(e):
    ename = e.__class__.__name__
    return any(k in ename for k in ("Proxy", "Connection", "Timeout", "Connect", "SSL", "ReadError"))


# ======================== SHARED PROXY POOL ========================
_USED_PROXIES = set()
_USED_LOCK = threading.Lock()


def _is_free(proxy):
    with _USED_LOCK:
        return proxy not in _USED_PROXIES


def _release_proxy(proxy):
    if not proxy:
        return
    with _USED_LOCK:
        _USED_PROXIES.discard(proxy)


# ======================== SESSION FILE ========================
def load_sessions_from_file():
    if not os.path.exists(SESSION_FILE):
        return []
    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            return [
                l.strip() for l in f
                if l.strip() and not l.strip().startswith("#")
            ]
    except Exception:
        return []


# ======================== PROXY FETCH ========================
def fetch_pool(tag=""):
    out = []

    try:
        r = requests.get(
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
            timeout=15,
        )
        if r.status_code == 200:
            lines = [l.strip() for l in r.text.splitlines() if l.strip()]
            out += [f"http://{l}" for l in lines if ":" in l]
    except Exception:
        pass

    try:
        r = requests.get(
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            timeout=15,
        )
        if r.status_code == 200:
            lines = [l.strip() for l in r.text.splitlines() if l.strip()]
            out += [f"http://{l}" for l in lines if ":" in l]
    except Exception:
        pass

    try:
        r = requests.get(
            "https://raw.githubusercontent.com/proxmint/free-proxy-list/main/proxies/http.txt",
            timeout=15,
        )
        if r.status_code == 200:
            lines = [l.strip() for l in r.text.splitlines() if l.strip()]
            out += [f"http://{l}" for l in lines if ":" in l]
    except Exception:
        pass

    try:
        r = requests.get(
            "https://api.proxyscrape.com/v4/free-proxy-list/get",
            params={
                "request": "displayproxies",
                "protocol": "http",
                "timeout": 5000,
                "country": "all",
                "ssl": "all",
                "anonymity": "all",
                "limit": 300,
            },
            timeout=20,
        )
        if r.status_code == 200:
            lines = [l.strip() for l in r.text.splitlines() if l.strip()]
            out += [f"http://{l}" for l in lines if ":" in l]
    except Exception:
        pass

    return list(set(out))


# ======================== PROXY CHECK ========================
def check_alive(proxy):
    try:
        r = requests.get(
            "http://httpbin.org/ip",
            proxies={"http": proxy, "https": proxy},
            timeout=PROXY_TIMEOUT,
        )
        return r.status_code == 200 and "origin" in r.text
    except Exception:
        return False


def check_ig(proxy):
    headers_home = {"User-Agent": "Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36"}

    try:
        r = requests.get(
            "https://www.instagram.com/",
            proxies={"http": proxy, "https": proxy},
            timeout=IG_CHECK_TIMEOUT,
            headers=headers_home,
            allow_redirects=True,
        )
        if r.status_code != 200:
            return False
    except Exception:
        return False

    try:
        r = requests.get(
            "https://i.instagram.com/api/v1/si/fetch_headers/?challenge_type=signup&guid=00000000-0000-0000-0000-000000000000",
            proxies={"http": proxy, "https": proxy},
            timeout=IG_CHECK_TIMEOUT,
            headers={
                "User-Agent": "Instagram 269.0.0.18.75 Android (26/8.0.0; 480dpi; 1080x1920; OnePlus; ONEPLUS A6013; OnePlus6T; qcom; en_US; 314665256)",
                "X-IG-App-ID": "567067343352427",
            },
        )
        return r.status_code in (200, 400, 404)
    except Exception:
        return False


def _check_and_claim(proxy, found_box, done_event):
    if done_event.is_set():
        return
    if not _is_free(proxy):
        return
    if check_ig(proxy):
        with _USED_LOCK:
            if proxy not in _USED_PROXIES and found_box[0] is None:
                _USED_PROXIES.add(proxy)
                found_box[0] = proxy
                done_event.set()


def fast_find_working_proxy(tag=""):
    for attempt in range(25):
        add_event(f"{tag} 🔍 proxy attempt {attempt+1}/25")
        candidates = fetch_pool(tag)
        if not candidates:
            time.sleep(2)
            continue

        random.shuffle(candidates)
        batch = candidates[:PROXY_BATCH]

        alive = []
        with ThreadPoolExecutor(max_workers=PROXY_CHECK_WORKERS) as ex:
            futures = {ex.submit(check_alive, p): p for p in batch}
            for fut in as_completed(futures):
                try:
                    if fut.result():
                        alive.append(futures[fut])
                except Exception:
                    pass

        if not alive:
            continue

        add_event(f"{tag} 🧪 {len(alive)} alive → IG check")
        random.shuffle(alive)

        found_box = [None]
        done_event = threading.Event()

        with ThreadPoolExecutor(max_workers=IG_CHECK_WORKERS) as ex:
            for p in alive:
                if done_event.is_set():
                    break
                ex.submit(_check_and_claim, p, found_box, done_event)

        done_event.wait(timeout=IG_CHECK_TIMEOUT + 5)

        if found_box[0]:
            add_event(f"{tag} 🎯 proxy found: {found_box[0][:30]}")
            return found_box[0]

    return None


# ======================== SESSION WORKER ========================
class SessionWorker(threading.Thread):
    def __init__(self, session_id, idx, board=None):
        super().__init__(daemon=True)
        self.session_id = session_id
        self.idx = idx
        self.tag = f"S{idx}"
        self.username = "?"
        self.msg_count = 0
        self.stop_flag = False
        self.current_proxy = None
        self.gc_count = 0
        self.round_num = 0
        self.dead = False
        self.last_delay = 0
        self.board = board

    def log(self, msg):
        add_event(f"{self.tag}@{self.username} {msg}")

    def run(self):
        try:
            self._run()
        finally:
            _release_proxy(self.current_proxy)
            add_event(f"{self.tag}@{self.username} 🛑 stopped")

    def _refresh(self):
        if self.board:
            self.board.render()

    def _login_with_retry(self, cl):
        for attempt in range(LOGIN_MAX_RETRY):
            self.log(f"🔐 login attempt {attempt+1}/{LOGIN_MAX_RETRY}")
            self._refresh()
            try:
                cl.set_proxy(self.current_proxy)
                cl.login_by_sessionid(self.session_id)
                self.username = cl.username or "?"
                self.log(f"✅ logged in (uid {cl.user_id})")
                self._refresh()
                return True

            except LoginRequired:
                self.log(f"{RED}🔐 session expired{RESET}")
                self.dead = True
                self._refresh()
                return False

            except Exception as e:
                if not is_proxy_error(e):
                    self.log(f"{RED}❌ login fail (non-proxy): {str(e)[:60]}{RESET}")
                    self._refresh()
                    return False

                self.log(f"{YELLOW}⚠️ proxy fail — new proxy{RESET}")
                self._refresh()

                _release_proxy(self.current_proxy)
                self.current_proxy = None

                new_p = fast_find_working_proxy(self.tag)
                if not new_p:
                    self.log(f"{RED}❌ no new proxy, wait 5s{RESET}")
                    self._refresh()
                    time.sleep(5)
                    continue

                self.current_proxy = new_p
                self.log(f"✅ new proxy {new_p[:30]}")
                self._refresh()

        return False

    def _run(self):
        self.log("🔍 finding proxy")
        self._refresh()
        proxy = fast_find_working_proxy(self.tag)
        if not proxy:
            self.log(f"{RED}❌ no proxy — abort{RESET}")
            self.dead = True
            self._refresh()
            return
        self.current_proxy = proxy

        cl = Client()

        if not self._login_with_retry(cl):
            return

        self.log("🔄 fetching threads")
        self._refresh()
        try:
            threads = cl.direct_threads(amount=20, thread_message_limit=1)
        except LoginRequired:
            self.log(f"{RED}🔐 session expired at fetch{RESET}")
            self.dead = True
            self._refresh()
            return
        except Exception as e:
            if is_proxy_error(e):
                self.log(f"{YELLOW}⚠️ fetch proxy fail — retry with new proxy{RESET}")
                self._refresh()
                threads = None
                for _ in range(LOGIN_MAX_RETRY):
                    _release_proxy(self.current_proxy)
                    self.current_proxy = None
                    new_p = fast_find_working_proxy(self.tag)
                    if not new_p:
                        time.sleep(5)
                        continue
                    self.current_proxy = new_p
                    try:
                        cl.set_proxy(new_p)
                        cl.login_by_sessionid(self.session_id)
                        threads = cl.direct_threads(amount=20, thread_message_limit=1)
                        break
                    except Exception as e2:
                        if is_proxy_error(e2):
                            continue
                        self.log(f"{RED}❌ fetch fail: {str(e2)[:60]}{RESET}")
                        self._refresh()
                        return
                if not threads:
                    self.log(f"{RED}❌ fetch failed after retries{RESET}")
                    self._refresh()
                    return
            else:
                self.log(f"{RED}❌ fetch fail: {str(e)[:60]}{RESET}")
                self._refresh()
                return

        if not threads:
            self.log(f"{RED}❌ no threads{RESET}")
            self._refresh()
            return

        gc_ids = []
        for t in threads:
            try:
                if getattr(t, "is_group", False) or (hasattr(t, "users") and len(t.users) > 2):
                    gc_ids.append(t.id)
            except Exception:
                continue

        if not gc_ids:
            self.log(f"{RED}❌ no group chats{RESET}")
            self._refresh()
            return

        self.gc_count = len(gc_ids)
        self.log(f"✅ {len(gc_ids)} groups")

        current_band = self._gen_band()
        last_band_change = time.time()
        band_interval = random.uniform(3600, 7200)
        last_break_time = time.time()
        break_interval = random.uniform(3600, 7200)

        self._refresh()

        while not self.stop_flag:
            try:
                if not gc_ids:
                    self.log(f"{RED}all GCs removed — stop{RESET}")
                    self._refresh()
                    return

                self.round_num += 1
                self.log(f"🔄 ROUND {self.round_num} start")
                self._refresh()

                queue = self._build_queue(gc_ids)
                self.log(f"📋 queue: {len(queue)}")
                self._refresh()

                idx_q = 0
                while idx_q < len(queue):
                    if self.stop_flag:
                        return

                    tid = queue[idx_q]
                    idx_q += 1

                    if tid not in gc_ids:
                        continue

                    num = random.randint(1, 10**10)
                    if random.choice([True, False]):
                        full_msg = f"{num} {MESSAGE_TEMPLATE}"
                    else:
                        full_msg = f"{MESSAGE_TEMPLATE} {num}"

                    result = self._send_with_retry(cl, tid, full_msg)

                    if result == "sent":
                        delay = random.uniform(current_band[0], current_band[1])
                        self.last_delay = delay
                        self.msg_count += 1
                        self.log(f"✅ msg #{self.msg_count} → {tid[:8]} | ⏱️ {delay:.1f}s")
                        self._refresh()
                        time.sleep(delay)

                    elif result == "remove":
                        if tid in gc_ids:
                            gc_ids.remove(tid)
                            self.gc_count = len(gc_ids)
                            self.log(f"{YELLOW}🗑️ GC {tid[:8]} removed (left {len(gc_ids)}){RESET}")
                            # Replacement — append a random remaining GC to keep round size
                            if gc_ids:
                                replacement = random.choice(gc_ids)
                                queue.append(replacement)
                            self._refresh()
                        continue

                    elif result == "login_lost":
                        return

                    elif result == "skip":
                        delay = random.uniform(current_band[0], current_band[1])
                        self.last_delay = delay
                        self.log(f"⏱️ {delay:.1f}s")
                        self._refresh()
                        time.sleep(delay)

                    if time.time() - last_band_change >= band_interval:
                        current_band = self._gen_band()
                        last_band_change = time.time()
                        band_interval = random.uniform(3600, 7200)
                        self.log(f"🔄 new band {current_band[0]:.0f}-{current_band[1]:.0f}s")
                        self._refresh()

                    if time.time() - last_break_time >= break_interval:
                        extra = random.uniform(60, 180)
                        self.log(f"☕ break {extra:.0f}s")
                        self._refresh()
                        time.sleep(extra)
                        last_break_time = time.time()
                        break_interval = random.uniform(3600, 7200)

                self.log(f"✅ ROUND {self.round_num} done — total {self.msg_count}")
                self._refresh()

            except KeyboardInterrupt:
                return
            except Exception as e:
                self.log(f"{RED}⚠️ round crash: {str(e)[:60]}{RESET}")
                self._refresh()
                time.sleep(60)
                continue

    def _gen_band(self):
        mn = random.uniform(30, 50)
        sp = random.uniform(5, 15)
        mx = min(mn + sp, 65)
        return (mn, mx)

    def _build_queue(self, gc_list):
        if not gc_list:
            return []
        base = random.sample(gc_list, len(gc_list))
        queue = list(base)
        repeats = random.randint(1, 3)
        targets = random.sample(gc_list, min(repeats, len(gc_list)))
        for t in targets:
            idxs = [i for i, x in enumerate(queue) if x == t]
            if idxs:
                pos = idxs[0]
                ins = random.randint(pos + 1, len(queue))
                queue.insert(ins, t)
        return queue

    def _try_send(self, cl, tid, msg):
        try:
            cl.direct_send(msg, thread_ids=[tid])
            return "ok"
        except (RateLimitError, ClientThrottledError):
            return "rate_limit"
        except PleaseWaitFewMinutes:
            return "rate_limit"
        except LoginRequired:
            self.stop_flag = True
            self.dead = True
            self.log(f"{RED}🔐 session expired{RESET}")
            return "login_lost"
        except (ClientForbiddenError, ClientNotFoundError, ClientBadRequestError):
            return "remove"
        except ChallengeRequired:
            return "remove"
        except Exception as e:
            if is_proxy_error(e):
                return "proxy_fail"
            return "remove"

    def _send_with_retry(self, cl, tid, msg):
        r = self._try_send(cl, tid, msg)

        if r == "ok":
            return "sent"
        if r == "remove":
            return "remove"
        if r == "login_lost":
            return "login_lost"
        if r == "rate_limit":
            self.log(f"{YELLOW}⏳ rate limit — wait 60s{RESET}")
            self._refresh()
            time.sleep(60)
            return "skip"

        self.log("⚠️ proxy fail — retry")
        self._refresh()
        r = self._try_send(cl, tid, msg)
        if r == "ok":
            return "sent"
        if r == "remove":
            return "remove"
        if r == "login_lost":
            return "login_lost"
        if r == "rate_limit":
            time.sleep(60)
            return "skip"

        self.log("🔄 new proxy")
        self._refresh()
        _release_proxy(self.current_proxy)
        self.current_proxy = None

        new_p = fast_find_working_proxy(self.tag)
        if not new_p:
            self.log(f"{RED}❌ no new proxy — skip{RESET}")
            self._refresh()
            return "skip"
        self.current_proxy = new_p
        self.log(f"✅ new proxy {new_p[:30]}")
        self._refresh()

        try:
            cl.set_proxy(new_p)
            cl.login_by_sessionid(self.session_id)
        except LoginRequired:
            self.log(f"{RED}🔐 expired on re-login{RESET}")
            self.stop_flag = True
            self.dead = True
            return "login_lost"
        except Exception as e:
            if is_proxy_error(e):
                self.log(f"{YELLOW}⚠️ re-login proxy fail — skip msg{RESET}")
            else:
                self.log(f"{RED}❌ re-login fail: {str(e)[:50]}{RESET}")
            self._refresh()
            return "skip"

        r = self._try_send(cl, tid, msg)
        if r == "ok":
            return "sent"
        if r == "remove":
            return "remove"
        if r == "login_lost":
            return "login_lost"
        return "skip"


# ======================== BOARD ========================
class Board:
    def __init__(self):
        self.workers_dict = {}
        self.workers_lock = threading.Lock()
        self.started_at = time.time()

    def render(self):
        with _screen_lock:
            with self.workers_lock:
                snapshot = list(self.workers_dict.values())

            clear_screen()

            uptime_sec = int(time.time() - self.started_at)
            uptime_str = f"{uptime_sec//3600}h {(uptime_sec%3600)//60}m {uptime_sec%60}s"

            print(f"{BOLD}{CYAN}{'═' * 68}{RESET}")
            print(f"{BOLD}{CYAN}  ██╗ ██████╗       ██████╗  ██████╗ ████████╗  █████╗ {RESET}")
            print(f"{BOLD}{CYAN}  ██║██╔════╝       ██╔══██╗██╔═══██╗╚══██╔══╝ ██╔══██╗{RESET}")
            print(f"{BOLD}{CYAN}  ██║██║  ███╗      ██████╔╝██║   ██║   ██║    ███████║{RESET}")
            print(f"{BOLD}{CYAN}  ██║██║   ██║      ██╔══██╗██║   ██║   ██║    ██╔══██║{RESET}")
            print(f"{BOLD}{CYAN}  ██║╚██████╔╝      ██████╔╝╚██████╔╝   ██║    ██║  ██║{RESET}")
            print(f"{BOLD}{CYAN}  ╚═╝ ╚═════╝       ╚═════╝  ╚═════╝    ╚═╝    ╚═╝  ╚═╝{RESET}")
            print(f"{BOLD}{CYAN}  GC Spammer  •  Uptime: {uptime_str}  •  Sessions: {len(snapshot)}{RESET}")
            print(f"{BOLD}{CYAN}{'═' * 68}{RESET}")

            print(f"\n{BOLD}{MAGENTA}  📊 SESSIONS{RESET}")
            print(f"  {'─' * 64}")
            print(
                f"  {BOLD}{'ID':<5}{'USERNAME':<20}{'MSGS':<7}{'GCs':<6}"
                f"{'ROUND':<7}{'DELAY':<10}{'PROXY':<18}{RESET}"
            )
            print(f"  {'─' * 64}")

            if not snapshot:
                print(f"  {GRAY}(no active sessions){RESET}")
            else:
                for w in sorted(snapshot, key=lambda x: x.idx):
                    uname = f"@{w.username}" if w.username and w.username != "?" else "(waiting)"
                    proxy_short = ""
                    if w.current_proxy:
                        proxy_short = w.current_proxy.replace("http://", "")[:16]
                    delay_str = f"{w.last_delay:.1f}s" if w.last_delay else "-"
                    status_color = GREEN if w.is_alive() and not w.stop_flag else RED
                    print(
                        f"  {status_color}{w.tag:<5}{RESET}"
                        f"{BOLD}{uname:<20}{RESET}"
                        f"{GREEN}{w.msg_count:<7}{RESET}"
                        f"{w.gc_count:<6}"
                        f"{w.round_num:<7}"
                        f"{YELLOW}{delay_str:<10}{RESET}"
                        f"{GRAY}{proxy_short:<18}{RESET}"
                    )
            print(f"  {'─' * 64}")

            with _RECENT_LOCK:
                events = list(_RECENT_EVENTS)

            print(f"\n{BOLD}{CYAN}  📜 RECENT EVENTS{RESET}")
            print(f"  {'─' * 64}")
            if not events:
                print(f"  {GRAY}(no events yet){RESET}")
            else:
                for ev in events:
                    print(f"  {ev}")
            print(f"  {'─' * 64}\n")


BOARD = Board()


# ======================== FILE WATCHER ========================
def file_watcher(workers_dict, workers_lock, idx_counter):
    while True:
        time.sleep(FILE_CHECK_INTERVAL)
        try:
            sessions_in_file = set(load_sessions_from_file())
            new_added = 0
            stopped = 0

            with workers_lock:
                for sid in sessions_in_file:
                    if sid in workers_dict:
                        continue
                    idx = idx_counter[0]
                    idx_counter[0] += 1
                    w = SessionWorker(sid, idx, board=BOARD)
                    w.start()
                    workers_dict[sid] = w
                    new_added += 1

                for sid in list(workers_dict.keys()):
                    if sid not in sessions_in_file:
                        w = workers_dict[sid]
                        w.stop_flag = True
                        add_event(f"{w.tag}@{w.username} 🛑 removed from file")
                        del workers_dict[sid]
                        stopped += 1

            if new_added or stopped:
                add_event(f"FILE +{new_added} -{stopped} (active {len(workers_dict)})")
            BOARD.render()
        except Exception as e:
            add_event(f"FILE WATCH error: {str(e)[:60]}")


# ======================== MAIN ========================
def main():
    if not os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "w", encoding="utf-8") as f:
                f.write("# Add session IDs — one per line\n")
        except Exception:
            pass

    sessions = load_sessions_from_file()

    workers_dict = {}
    workers_lock = threading.Lock()
    idx_counter = [1]

    with workers_lock:
        for sid in sessions:
            idx = idx_counter[0]
            idx_counter[0] += 1
            w = SessionWorker(sid, idx, board=BOARD)
            w.start()
            workers_dict[sid] = w
            time.sleep(0.3)

    BOARD.workers_dict = workers_dict
    BOARD.workers_lock = workers_lock
    BOARD.render()

    threading.Thread(
        target=file_watcher,
        args=(workers_dict, workers_lock, idx_counter),
        daemon=True,
    ).start()

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        with workers_lock:
            for w in workers_dict.values():
                w.stop_flag = True
        time.sleep(2)

        with _screen_lock:
            clear_screen()
            total = sum(w.msg_count for w in workers_dict.values())
            print(f"\n{GREEN}[✓] Total messages sent: {total}{RESET}")
            for w in workers_dict.values():
                status = "alive" if w.is_alive() else "dead"
                print(f"    {w.tag}@{w.username}: {w.msg_count} msgs [{status}]")


if __name__ == "__main__":
    main()