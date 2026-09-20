#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import random
import time
from instagrapi import Client
from instagrapi.exceptions import (
    RateLimitError,
    PleaseWaitFewMinutes,
    ChallengeRequired,
    ClientForbiddenError,
    LoginRequired,
)

# ======================== CONFIG ========================
SESSION_ID = "16081805661%3AjOIM53DGWfqK9q%3A6%3AAYlQvSao6Z9XadaUjV9XrXtItJcjfJJdlJb64Yp4aA"   # ← yahan apna Instagram sessionid cookie daalo

MESSAGE_TEMPLATE = """⛩ ✦KING-RISHI-RAYSHIT-TRB-KRISHU-SERVER DOG✦ 
⛩ 𝗖 𝗛 𝗨 𝗗 𖣔・✦・⭑・✦・𖣔𖣔・✦・⭑・✦・𖣔
⛩ ✦KING-RISHI-RAYSHIT-TRB-KRISHU-SERVER DOG✦ 
⛩ 𝗖 𝗛 𝗨 𝗗 𖣔・✦・⭑・✦・𖣔𖣔・✦・⭑・✦・𖣔
⛩ ✦KING-RISHI-RAYSHIT-TRB-KRISHU-SERVER DOG✦ 
⛩ 𝗖 𝗛 𝗨 𝗗 𖣔・✦・⭑・✦・𖣔𖣔・✦・⭑・✦・𖣔
⛩ ✦KING-RISHI-RAYSHIT-TRB-KRISHU-SERVER DOG✦ 
⛩ 𝗖 𝗛 𝗨 𝗗 𖣔・✦・⭑・✦・𖣔𖣔・✦・⭑・✦・𖣔
⛩ ✦KING-RISHI-RAYSHIT-TRB-KRISHU-SERVER DOG✦ 
⛩ 𝗖 𝗛 𝗨 𝗗 𖣔・✦・⭑・✦・𖣔𖣔・✦・⭑・✦・𖣔
⛩ ✦KING-RISHI-RAYSHIT-TRB-KRISHU-SERVER DOG✦ 
⛩ 𝗖 𝗛 𝗨 𝗗 𖣔・✦・⭑・✦・𖣔𖣔・✦・⭑・✦・𖣔
⛩ ✦KING-RISHI-RAYSHIT-TRB-KRISHU-SERVER DOG✦ 
⛩ 𝗖 𝗛 𝗨 𝗗 𖣔・✦・⭑・✦・𖣔𖣔・✦・⭑・✦・𖣔
⛩ ✦KING-RISHI-RAYSHIT-TRB-KRISHU-SERVER DOG✦ 
⛩ 𝗖 𝗛 𝗨 𝗗 𖣔・✦・⭑・✦・𖣔𖣔・✦・⭑・✦・𖣔
⛩ ✦KING-RISHI-RAYSHIT-TRB-KRISHU-SERVER DOG✦ 
⛩ 𝗖 𝗛 𝗨 𝗗 𖣔・✦・⭑・✦・𖣔𖣔・✦・⭑・✦・𖣔
⛩ ✦KING-RISHI-RAYSHIT-TRB-KRISHU-SERVER DOG✦ 
⛩ 𝗖 𝗛 𝗨 𝗗 𖣔・✦・⭑・✦・𖣔𖣔・✦・⭑・✦・𖣔
⛩ ✦KING-RISHI-RAYSHIT-TRB-KRISHU-SERVER DOG✦ 
⛩ 𝗖 𝗛 𝗨 𝗗 𖣔・✦・⭑・✦・𖣔𖣔・✦・⭑・✦・𖣔
⛩ ✦KING-RISHI-RAYSHIT-TRB-KRISHU-SERVER DOG✦ 
⛩ 𝗖 𝗛 𝗨 𝗗 𖣔・✦・⭑・✦・𖣔𖣔・✦・⭑・✦・𖣔
⛩ ✦KING-RISHI-RAYSHIT-TRB-KRISHU-SERVER DOG✦ 
⛩ 𝗖 𝗛 𝗨 𝗗 𖣔・✦・⭑・✦・𖣔𖣔・✦・⭑・✦・𖣔
⛩ ✦KING-RISHI-RAYSHIT-TRB-KRISHU-SERVER DOG✦ 
⛩ 𝗖 𝗛 𝗨 𝗗 𖣔・✦・⭑・✦・𖣔𖣔・✦・⭑・✦・𖣔
⛩ ✦KING-RISHI-RAYSHIT-TRB-KRISHU-SERVER DOG✦ 
⛩ 𝗖 𝗛 𝗨 𝗗 𖣔・✦・⭑・✦・𖣔𖣔・✦・⭑・✦・𖣔
⛩ ✦KING-RISHI-RAYSHIT-TRB-KRISHU-SERVER DOG✦ 
⛩ 𝗖 𝗛 𝗨 𝗗 𖣔・✦・⭑・✦・𖣔𖣔・✦・⭑・✦・𖣔
⛩ ✦KING-RISHI-RAYSHIT-TRB-KRISHU-SERVER DOG✦ 
⛩ 𝗖 𝗛 𝗨 𝗗 𖣔・✦・⭑・✦・𖣔𖣔・✦・⭑・✦・𖣔"""

MAX_RETRIES = 10

# ======================== HELPERS ========================

def create_client(session_id):
    cl = Client()
    try:
        cl.login_by_sessionid(session_id)
        print("✅ Logged in using session ID.")
        user_id = cl.user_id
        print(f"✅ Session validated. User ID: {user_id}")
        return cl, True
    except Exception as e:
        print(f"❌ Session ID login failed: {e}")
        return None, False


def get_group_threads(client, limit=20):
    try:
        print(f"🔄 Fetching {limit} threads...")
        threads = client.direct_threads(amount=limit, thread_message_limit=1)

        if threads is None:
            print("[!] direct_threads() returned None.")
            return []

        print(f"✅ Total threads returned: {len(threads)}")

        group_threads = []
        for t in threads:
            try:
                if hasattr(t, 'is_group') and t.is_group:
                    group_threads.append(t)
                elif hasattr(t, 'users') and len(t.users) > 2:
                    group_threads.append(t)
            except Exception as e:
                print(f"⚠️ Error checking thread {t.id}: {e}")
                continue

        print(f"\n✅ Found {len(group_threads)} group chats out of {len(threads)} total threads.")
        return group_threads
    except Exception as e:
        print(f"[!] Failed to fetch threads: {e}")
        return []


def send_message_with_retry(client, thread_id, message):
    """
    Returns:
      "ok"     -> message sent (status 200)
      "rate"   -> 429 / rate limit (GC ko nahi hatana)
      "remove" -> 200 aur 429 ke alawa koi bhi error -> GC remove karo
      "login"  -> session expired -> exit
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            client.direct_send(message, thread_ids=[thread_id])
            print(f"✅ Sent to {thread_id}")
            return "ok"

        except RateLimitError:
            wait = 120 * attempt
            print(f"⚠️ 429 Rate limit – wait {wait}s ({attempt}/{MAX_RETRIES})")
            time.sleep(wait)

        except PleaseWaitFewMinutes:
            wait = 600
            print(f"⏳ Please wait – wait {wait}s")
            time.sleep(wait)

        except ChallengeRequired:
            print("🔒 Challenge – pausing 1 hour")
            time.sleep(3600)

        except LoginRequired:
            print("🔐 Session expired. Need fresh sessionid.")
            return "login"

        except Exception as e:
            # 200 aur 429 ke alawa koi bhi error → GC remove
            print(f"🚫 Error on {thread_id}: {e} → removing GC")
            return "remove"

    # Retries khatam
    print(f"❌ Max retries reached for {thread_id}")
    return "remove"


def generate_random_band():
    min_delay = random.uniform(30, 50)
    spread = random.uniform(5, 15)
    max_delay = min(min_delay + spread, 65)
    return (min_delay, max_delay)


def build_round_queue(gc_list):
    if not gc_list:
        return []

    base_order = random.sample(gc_list, len(gc_list))
    queue = list(base_order)

    repeat_count = random.randint(1, 3)
    repeat_targets = random.sample(gc_list, min(repeat_count, len(gc_list)))

    for target in repeat_targets:
        indices = [i for i, item in enumerate(queue) if item == target]
        if indices:
            pos = indices[0]
            insert_pos = random.randint(pos + 1, len(queue))
            queue.insert(insert_pos, target)

    return queue


# ======================== MAIN LOOP ========================

def main():
    if not SESSION_ID or SESSION_ID.strip() == "":
        sys.exit("[!] SESSION_ID code mein set nahi hai.")
    session_id = SESSION_ID.strip()

    client, ok = create_client(session_id)
    if not ok:
        sys.exit("[!] Initial login failed. Exiting.")

    gc_list = get_group_threads(client, limit=20)
    if not gc_list:
        print("\n[!] No group chats found.")
        sys.exit("[!] Exiting.")

    # Mutable alive list
    gc_ids = [t.id for t in gc_list]
    forbidden_gcs = set()
    print(f"\n📋 Group chat IDs: {gc_ids}")

    current_band = generate_random_band()
    last_band_change = time.time()
    band_interval = random.uniform(3600, 7200)

    last_break_time = time.time()
    break_interval = random.uniform(3600, 7200)

    msg_count = 0
    round_num = 0

    print(f"\n🚀 Started – initial band: {current_band[0]:.1f}-{current_band[1]:.1f}s")
    print(f"📨 Sending to {len(gc_ids)} group chats")
    print("Press Ctrl+C to stop.\n")

    while True:
        try:
            if not gc_ids:
                print("\n[!] Saari GCs remove ho gayi. Exiting.")
                print(f"📊 Final total messages sent: {msg_count}")
                print(f"🚫 Removed GCs: {forbidden_gcs}")
                break

            round_num += 1
            print(f"\n{'='*50}")
            print(f"🔄 ROUND {round_num} STARTING")
            print(f"{'='*50}")

            queue = build_round_queue(gc_ids)
            print(f"📋 Queue length: {len(queue)} (base: {len(gc_ids)} + repeats)")

            i = 0
            while i < len(queue):
                thread_id = queue[i]

                # Agar ye GC pehle hi remove ho chuki hai → replace karo
                if thread_id not in gc_ids:
                    replacement = _pick_replacement(gc_ids, queue)
                    if replacement:
                        queue[i] = replacement
                        print(f"♻️ Replaced dead GC at position {i} with {replacement}")
                    else:
                        queue.pop(i)
                        print(f"🗑️ Removed dead GC at position {i}, no replacement available")
                    continue

                # Message banao
                num = random.randint(1, 10**10)
                if random.choice([True, False]):
                    full_msg = f"{num} {MESSAGE_TEMPLATE}"
                else:
                    full_msg = f"{MESSAGE_TEMPLATE} {num}"

                result = send_message_with_retry(client, thread_id, full_msg)

                if result == "ok":
                    msg_count += 1
                    print(f"📊 Total sent this session: {msg_count}")

                elif result == "login":
                    print("🔐 Session expired. Restart.")
                    print(f"📊 Final total messages sent: {msg_count}")
                    sys.exit("[!] Session expired.")

                elif result == "remove":
                    # GC ko alive list se hatao
                    if thread_id in gc_ids:
                        gc_ids.remove(thread_id)
                    forbidden_gcs.add(thread_id)
                    print(f"🗑️ Removed GC {thread_id}. Alive: {len(gc_ids)}")

                    # Queue mein us position pe dusri alive GC daalo
                    replacement = _pick_replacement(gc_ids, queue)
                    if replacement:
                        queue[i] = replacement
                        print(f"♻️ Replaced with {replacement} at position {i}")
                        # Ab isi position pe naya GC process karo (i wahi rahega)
                        continue
                    else:
                        # Koi replacement nahi mila → pop
                        queue.pop(i)
                        print(f"🗑️ No replacement, popped position {i}")
                        continue

                # rate case: delay karo (retries ke andar hi wait ho gaya)
                # delay lagao
                delay = random.uniform(current_band[0], current_band[1])
                print(f"⏱️ Waiting {delay:.2f}s (band: {current_band[0]:.1f}-{current_band[1]:.1f}s)")
                time.sleep(delay)

                # Band rotation
                if time.time() - last_band_change >= band_interval:
                    current_band = generate_random_band()
                    last_band_change = time.time()
                    band_interval = random.uniform(3600, 7200)
                    print(f"🔄 New random band: {current_band[0]:.1f}-{current_band[1]:.1f}s")

                # Extra break
                if time.time() - last_break_time >= break_interval:
                    extra = random.uniform(60, 180)
                    print(f"☕ Extra break: {extra:.0f}s")
                    time.sleep(extra)
                    last_break_time = time.time()
                    break_interval = random.uniform(3600, 7200)

                i += 1

            print(f"\n✅ ROUND {round_num} COMPLETE")
            print(f"📊 Sent this round: {len(queue)}")
            print(f"📊 Grand total: {msg_count}")
            print(f"📋 Alive GCs: {len(gc_ids)} | Removed: {len(forbidden_gcs)}")

        except KeyboardInterrupt:
            print("\n🛑 Stopped by user")
            print(f"📊 Final total messages sent: {msg_count}")
            print(f"🚫 Removed GCs: {forbidden_gcs}")
            break
        except Exception as e:
            print(f"💥 Main loop crash: {e} – restarting in 60s")
            time.sleep(60)
            continue


def _pick_replacement(gc_ids, current_queue):
    """
    Pick an alive GC that is NOT already anywhere in the remaining queue.
    Returns None if no GC available.
    """
    used = set(current_queue)
    candidates = [g for g in gc_ids if g not in used]
    if not candidates:
        return None
    return random.choice(candidates)


if __name__ == "__main__":
    main()