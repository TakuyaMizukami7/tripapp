import streamlit as st
import json
import os
import urllib.parse
from datetime import time, datetime
from streamlit_calendar import calendar
import openai

# ── データ保存ファイルのパス ──────────────────────────────────────────────────
DATA_FILE = "schedule_data.json"
USERS_FILE = "users_data.json"
EXPENSES_FILE = "expenses_data.json"
BINGO_FILE = "bingo_data.json"

# ── 日程と基本情報の設定 ──────────────────────────────────────────────────────
DAYS = {
    "day1": {"label": "2/28（土）Day 1", "date": "2026-02-28"},
    "day2": {"label": "3/1（日）Day 2", "date": "2026-03-01"},
}

CATEGORIES = {
    "🚌 移動": {"color": "#1A6E9F"},
    "🍜 食事": {"color": "#E07B39"},
    "🏨 宿泊": {"color": "#7B5EA7"},
    "🎿 観光": {"color": "#2E8B57"},
    "🛒 ショッピング": {"color": "#C0392B"},
    "🎫 アクティビティ/ライブ": {"color": "#D35400"},
    "📝 その他": {"color": "#888888"},
}


# ── データ I/O ────────────────────────────────────────────────────────────────
def load_data(file_path: str, default_val) -> any:
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default_val

def save_data(data: any, file_path: str):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ── ページ設定 ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🗺️ 北海道旅のしおり",
    page_icon="🦌",
    layout="wide",
)

# セッション状態の初期化
if "data" not in st.session_state:
    st.session_state.data = load_data(DATA_FILE, {"day1": [], "day2": []})
if "users" not in st.session_state:
    st.session_state.users = load_data(USERS_FILE, ["自分", "友達"])
if "expenses" not in st.session_state:
    st.session_state.expenses = load_data(EXPENSES_FILE, [])
if "bingos" not in st.session_state:
    default_bingos = [
        {
            "id": "mission",
            "title": "🎯 旅のミッション・ビンゴ",
            "description": "旅行中に2人で達成したい小さな目標（ミッション）をクリアしてビンゴを目指そう！",
            "bingo_count": 0,
            "missions": [
                {"text": "ジンギスカンを食べる", "done": False},
                {"text": "最高の景色で自撮り", "done": False},
                {"text": "地元のコンビニ（セコマ）に行く", "done": False},
                {"text": "誰かに道を尋ねる", "done": False},
                {"text": "予定にない店にふらっと入る", "done": False},
                {"text": "お土産を1つ以上買う", "done": False},
                {"text": "乾杯の写真を撮る", "done": False},
                {"text": "1万歩以上歩く", "done": False},
                {"text": "「最高！」と口に出して言う", "done": False},
            ],
            "memos": []
        },
        {
            "id": "food",
            "title": "🦀 北海道食べたいものビンゴ",
            "description": "北海道の絶品グルメを制覇してビンゴを達成しよう！",
            "bingo_count": 0,
            "missions": [
                {"text": "新鮮な海鮮丼", "done": False},
                {"text": "本場の味噌ラーメン", "done": False},
                {"text": "牧場ソフトクリーム", "done": False},
                {"text": "絶品スープカレー", "done": False},
                {"text": "定番ジンギスカン", "done": False},
                {"text": "贅沢にカニを食べる", "done": False},
                {"text": "ご当地バーガー", "done": False},
                {"text": "ルタオや六花亭", "done": False},
                {"text": "サッポロクラシック", "done": False},
            ],
            "memos": []
        }
    ]
    st.session_state.bingos = load_data(BINGO_FILE, default_bingos)

# ── サイドバー: ユーザー管理 ──────────────────────────────────────────────────
with st.sidebar:
    st.header("👥 メンバー管理")
    st.write("旅行の参加メンバー（経費の計算に使います）")
    
    new_user = st.text_input("新しいメンバーを追加")
    if st.button("追加"):
        if new_user and new_user not in st.session_state.users:
            st.session_state.users.append(new_user)
            save_data(st.session_state.users, USERS_FILE)
            st.rerun()
            
    st.divider()
    st.write("**現在のメンバー:**")
    for i, user in enumerate(st.session_state.users):
        col_u1, col_u2 = st.columns([3, 1])
        col_u1.write(f"- {user}")
        if len(st.session_state.users) > 1:
            if col_u2.button("🗑️", key=f"del_user_{i}", help="削除"):
                st.session_state.users.pop(i)
                save_data(st.session_state.users, USERS_FILE)
                st.rerun()

# ── ヘッダー画像とタイトル ──────────────────────────────────────────────────
header_img_path = os.path.join("image", "header.jpg")
if os.path.exists(header_img_path):
    import base64
    with open(header_img_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    
    st.markdown(
        f"""
        <style>
        .header-img-container {{
            width: 100%;
            height: 250px; /* バナーの高さを指定（お好みで変更可能） */
            overflow: hidden;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .header-img-container img {{
            width: 100%;
            height: 100%;
            object-fit: cover; /* 縦横比を維持しながら枠を埋める */
            object-position: top; /* 上部を中心に表示 */
        }}
        </style>
        <div class="header-img-container">
            <img src="data:image/jpeg;base64,{img_b64}" alt="Header">
        </div>
        """,
        unsafe_allow_html=True
    )

st.title("🦌 北海道旅のしおり")
st.caption("2026年 2/28（土）〜 3/1（日）  1泊2日の旅行スケジューラー")
st.divider()

# ── ヘルパー関数群 ─────────────────────────────────────────────────────────────
def get_map_url(place: str) -> str:
    """Google Mapsの検索用URLを生成"""
    if not place: return ""
    encoded_place = urllib.parse.quote(place)
    return f"https://www.google.com/maps/search/?api=1&query={encoded_place}"

def calculate_split_bill():
    """全出費リスト（expenses）を用いた割り勘計算"""
    items = st.session_state.expenses
    members = st.session_state.users
    
    paid_totals = {member: 0 for member in members}
    owed_totals = {member: 0 for member in members}
    total_cost = 0
    
    for item in items:
        cost = int(item.get("cost", 0))
        if cost == 0: continue
            
        payer = item.get("payer")
        if payer in paid_totals:
            paid_totals[payer] += cost
            total_cost += cost
            
        involved = item.get("involved_members", members)
        involved = [m for m in involved if m in members]
        
        if involved:
            split_cost = cost / len(involved)
            for m in involved:
                owed_totals[m] += split_cost
    
    diffs = {member: paid_totals[member] - owed_totals[member] for member in members}
    return paid_totals, owed_totals, total_cost, diffs

# ── UI: スケジュール追加・編集フォーム ─────────────────────────────────────────
def schedule_form(day_key: str, existing_item=None, index=None):
    mode = "編集" if existing_item else "追加"
    
    st.subheader(f"{'✏️ 予定を編集' if existing_item else '➕ 予定を追加'}")
    
    def_cat = existing_item["category"] if existing_item else list(CATEGORIES.keys())[0]
    category = st.selectbox(
        "カテゴリ", 
        list(CATEGORIES.keys()), 
        index=list(CATEGORIES.keys()).index(def_cat) if def_cat in CATEGORIES else 0,
        key=f"cat_sel_{day_key}_{index if index is not None else 'new'}"
    )

    with st.form(key=f"form_{day_key}_{index if index is not None else 'new'}", clear_on_submit=not existing_item):

        def_st = datetime.strptime(existing_item["start_time"], "%H:%M").time() if existing_item else time(9, 0)
        def_et = datetime.strptime(existing_item["end_time"], "%H:%M").time() if existing_item else time(10, 0)
        def_memo = existing_item.get("memo", "") if existing_item else ""

        col1, col2 = st.columns(2)
        with col1:
            start_t = st.time_input("開始時刻", value=def_st)
        with col2:
            end_t = st.time_input("終了時刻", value=def_et)

        if category == "🚌 移動":
            def_start_place = existing_item.get("start_place", "") if existing_item else ""
            def_end_place = existing_item.get("end_place", "") if existing_item else ""
            
            c_start, c_end = st.columns(2)
            with c_start:
                start_place = st.text_input("出発地", value=def_start_place)
            with c_end:
                end_place = st.text_input("目的地", value=def_end_place)
            
            title = f"{start_place} ➔ {end_place}" if start_place or end_place else "移動"
            place = "" # 移動の時は全体の「場所」は使わない
        else:
            def_title = existing_item.get("title", "") if existing_item else ""
            def_place = existing_item.get("place", "") if existing_item else ""
            
            title = st.text_input("タイトル（例：ごはん、ライブ）", value=def_title)
            place = st.text_input("場所・スポット名", value=def_place, placeholder="例: 札幌時計台")
            start_place = ""
            end_place = ""

        memo = st.text_area("メモ・備考（任意）", value=def_memo, placeholder="例: 開場は18時〜。")
        submitted = st.form_submit_button(f"予定を{mode}する", use_container_width=True)

    if submitted:
        if category == "🚌 移動" and (not start_place or not end_place):
            st.warning("移動の場合は「出発地」と「目的地」の両方を入力してください。")
            return
        elif category != "🚌 移動" and not title:
            st.warning("「タイトル」は必須です。")
            return
        
        new_item = {
            "start_time": start_t.strftime("%H:%M"),
            "end_time": end_t.strftime("%H:%M"),
            "category": category,
            "title": title,
            "place": place,
            "memo": memo,
        }
        
        if category == "🚌 移動":
            new_item["start_place"] = start_place
            new_item["end_place"] = end_place

        if day_key not in st.session_state.data:
            st.session_state.data[day_key] = []

        if existing_item is not None and index is not None:
            st.session_state.data[day_key][index] = new_item
            st.success(f"「{title}」を更新しました！")
        else:
            st.session_state.data[day_key].append(new_item)
            st.success(f"「{title}」を追加しました！")
            
        save_data(st.session_state.data, DATA_FILE)
        st.rerun()

# ── UI: 出費追加・編集フォーム ─────────────────────────────────────────
def expense_form(existing_item=None, index=None):
    mode = "編集" if existing_item else "追加"
    members = st.session_state.users
    
    with st.form(key=f"form_expense_{index if index is not None else 'new'}", clear_on_submit=not existing_item):
        st.subheader(f"{'✏️ 出費を編集' if existing_item else '💸 新しい出費を記録'}")

        def_title = existing_item.get("title", "") if existing_item else ""
        def_cost = existing_item.get("cost", 0) if existing_item else 0
        def_payer = existing_item.get("payer", members[0]) if existing_item else members[0]
        if def_payer not in members: def_payer = members[0]
        def_involved = existing_item.get("involved_members", members) if existing_item else members
        def_involved = [m for m in def_involved if m in members]

        title = st.text_input("出費の名目（例：1日目夜ごはん代、タクシー代）", value=def_title)
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            cost = st.number_input("金額 (円)", min_value=0, value=def_cost, step=100)
        with col_c2:
            payer = st.selectbox("全額支払った人（立て替えた人）", members, index=members.index(def_payer))
            
        involved_members = st.multiselect("この経費に関与した人（割り勘対象者）", members, default=def_involved)

        submitted = st.form_submit_button(f"出費を{mode}する", use_container_width=True)

    if submitted:
        if not title:
            st.warning("出費の名目を入力してください。")
            return
        if cost <= 0:
            st.warning("0円以上の金額を入力してください。")
            return
        if len(involved_members) == 0:
            st.warning("割り勘対象者を少なくとも1人選択してください。")
            return
            
        new_item = {
            "title": title,
            "cost": cost,
            "payer": payer,
            "involved_members": involved_members,
            "date": datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        }
        
        if existing_item is not None and index is not None:
            st.session_state.expenses[index] = new_item
            st.success(f"「{title}」の出費を更新しました！")
        else:
            st.session_state.expenses.append(new_item)
            st.success(f"「{title}」の出費を追加しました！")
            
        save_data(st.session_state.expenses, EXPENSES_FILE)
        st.rerun()

# ── UI: カレンダーとタイムライン表示 ──────────────────────────────────────────
def render_day_content(day_key: str, day_info: dict):
    left_col, right_col = st.columns([1, 1], gap="large")
    items = sorted(st.session_state.data.get(day_key, []), key=lambda x: x["start_time"])

    with left_col:
        schedule_form(day_key)
        
        st.subheader("📋 予定リスト & 編集")
        if not items:
            st.info("まだ予定がありません。追加してください。")
        else:
            for i, item in enumerate(items):
                # アンカーの追加
                st.markdown(f'<div id="event_{day_key}_{i}"></div>', unsafe_allow_html=True)
                
                # スクロール用のスクリプト
                if st.session_state.get(f"scroll_to_{day_key}") == str(i):
                    import streamlit.components.v1 as components
                    components.html(
                        f"""
                        <script>
                        const el = window.parent.document.getElementById('event_{day_key}_{i}');
                        if (el) {{
                            el.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                        }}
                        </script>
                        """,
                        height=0,
                        width=0
                    )
                    st.session_state[f"scroll_to_{day_key}"] = None

                # 表示タイトルのクリーンアップ
                # 移行時の互換性対応
                item_title = item.get("title")
                if not item_title:
                    item_title = item.get("place", "無題") if item.get("category") != "🚌 移動" else ""
                    
                disp_title = f"{item['start_time']}〜{item['end_time']}"
                if item.get("category") == "🚌 移動":
                    disp_title += f" 🚌 {item.get('start_place','')} ➔ {item.get('end_place','')}"
                else:
                    disp_title += f"  {item_title}"
                    
                is_expanded = (st.session_state.get(f"active_exp_{day_key}") == str(i))
                with st.expander(disp_title, expanded=is_expanded):
                    if item.get("category") == "🚌 移動":
                        map_url_s = get_map_url(item.get("start_place", ""))
                        map_url_e = get_map_url(item.get("end_place", ""))
                        st.markdown(f"**📍 出発地: [{item.get('start_place', '')}]({map_url_s})  ➔  目的地: [{item.get('end_place', '')}]({map_url_e})**")
                    else:
                        st.write(f"🏷️ タイトル: {item_title}")
                        if item.get("place"):
                            map_url = get_map_url(item.get('place', ''))
                            st.markdown(f"**📍 場所: [{item.get('place')}]({map_url})**")
                        
                    st.write(f"🏷️ カテゴリ: {item.get('category')}")
                    if item.get("memo"):
                        st.write(f"📝 メモ: {item['memo']}")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("✏️ 編集", key=f"edit_{day_key}_{i}"):
                            st.session_state[f"edit_mode_{day_key}_{i}"] = True
                    with c2:
                        if st.button("🗑️ 削除", key=f"del_{day_key}_{i}"):
                            st.session_state.data[day_key].pop(i)
                            save_data(st.session_state.data, DATA_FILE)
                            st.rerun()
                    
                    if st.session_state.get(f"edit_mode_{day_key}_{i}", False):
                        schedule_form(day_key, existing_item=item, index=i)
                        if st.button("キャンセル", key=f"cncl_{day_key}_{i}"):
                            st.session_state[f"edit_mode_{day_key}_{i}"] = False
                            st.rerun()

    with right_col:
        st.subheader("🗓️ タイムライン (カレンダー表示)")
        if items:
            events = []
            for i, item in enumerate(items):
                start_datetime = f"{day_info['date']}T{item['start_time']}:00"
                end_datetime = f"{day_info['date']}T{item['end_time']}:00"
                cal_color = CATEGORIES.get(item.get("category", "📝 その他"), {}).get("color", "#888888")
                
                # タイトルの調整
                ev_title = item.get("title")
                if not ev_title and item.get("category") != "🚌 移動":
                    ev_title = item.get("place", "")
                elif item.get("category") == "🚌 移動":
                    ev_title = f"{item.get('start_place','')} ➔ {item.get('end_place','')}"

                events.append({
                    "id": str(i),
                    "title": ev_title,
                    "start": start_datetime,
                    "end": end_datetime,
                    "color": cal_color,
                })
                
            calendar_options = {
                "headerToolbar": {
                    "left": "title",
                    "center": "",
                    "right": ""
                },
                "initialView": "timeGridDay",
                "initialDate": day_info["date"],
                "slotMinTime": "00:00:00",
                "slotMaxTime": "24:00:00",
                "scrollTime": "08:00:00",
                "allDaySlot": False,
                "height": 700,
                "slotLabelFormat": {
                    "hour": "2-digit",
                    "minute": "2-digit",
                    "hour12": False
                },
                "eventTimeFormat": {
                    "hour": "2-digit",
                    "minute": "2-digit",
                    "hour12": False
                }
            }
            
            cal_result = calendar(events=events, options=calendar_options, key=f"cal_{day_key}")
            
            if cal_result and "eventClick" in cal_result:
                clicked_id = str(cal_result["eventClick"]["event"]["id"])
                if st.session_state.get(f"active_exp_{day_key}") != clicked_id:
                    st.session_state[f"active_exp_{day_key}"] = clicked_id
                    st.session_state[f"scroll_to_{day_key}"] = clicked_id
                    st.rerun()
        else:
            st.info("予定を追加するとここにカレンダーが表示されます。")


# ── UI: 出費リストと精算タブ ──────────────────────────────────────────
def render_expenses_tab():
    left_col, right_col = st.columns([1, 1], gap="large")
    
    with left_col:
        expense_form()
        
        st.subheader("📋 出費リスト")
        items = st.session_state.expenses
        if not items:
            st.info("まだ出費記録がありません。追加してください。")
        else:
            for i, item in enumerate(items):
                with st.expander(f"¥{int(item['cost']):,} - {item['title']}", expanded=False):
                    st.write(f"👤 支払った人: **{item['payer']}**")
                    st.write(f"👥 割り勘対象: {', '.join(item.get('involved_members', []))}")
                    if "date" in item:
                        st.caption(f"登録日時: {item['date']}")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("✏️ 編集", key=f"edit_exp_{i}"):
                            st.session_state[f"edit_mode_exp_{i}"] = True
                    with c2:
                        if st.button("🗑️ 削除", key=f"del_exp_{i}"):
                            st.session_state.expenses.pop(i)
                            save_data(st.session_state.expenses, EXPENSES_FILE)
                            st.rerun()
                            
                    if st.session_state.get(f"edit_mode_exp_{i}", False):
                        expense_form(existing_item=item, index=i)
                        if st.button("キャンセル", key=f"cncl_exp_{i}"):
                            st.session_state[f"edit_mode_exp_{i}"] = False
                            st.rerun()

    with right_col:
        st.subheader("💸 旅行全体の精算結果")
        paid_totals, owed_totals, total_cost, diffs = calculate_split_bill()
        
        st.metric("旅行の総経費", f"¥ {total_cost:,}")
        if total_cost > 0:
            st.write("**🔽 個人の負担すべき額（対象になった経費の合計）:**")
            for member, owed in owed_totals.items():
                if owed > 0:
                    st.write(f"- {member}: ¥ {int(owed):,} 負担")
                    
            st.write("**🔽 実際の支払い状況（立て替えた額）:**")
            for member, paid in paid_totals.items():
                if paid > 0:
                    st.write(f"- {member}: ¥ {int(paid):,} 支払済")
                
            st.divider()
            st.write("**🔽 最終的な精算アクション 🔽**")
            
            receivers = []
            payers = []
            for member, diff in diffs.items():
                if diff > 0:
                    receivers.append([member, diff])
                elif diff < 0:
                    payers.append([member, abs(diff)])
                    
            receivers.sort(key=lambda x: x[1], reverse=True)
            payers.sort(key=lambda x: x[1], reverse=True)
            
            transactions = []
            i, j = 0, 0
            while i < len(payers) and j < len(receivers):
                payer, p_amount = payers[i]
                receiver, r_amount = receivers[j]
                
                if p_amount == 0:
                    i += 1
                    continue
                if r_amount == 0:
                    j += 1
                    continue
                    
                transfer = min(p_amount, r_amount)
                transactions.append((payer, receiver, transfer))
                
                payers[i][1] -= transfer
                receivers[j][1] -= transfer
                
            if transactions:
                for payer, receiver, amount in transactions:
                    st.error(f"💸 **{payer}** ➔ **{receiver}** に **¥ {int(amount):,}** 支払う")
            else:
                st.success("🎉 精算はすべて完了しています（追加の支払いはありません）。")


# ── UI: 旅のミッション・ビンゴタブ ──────────────────────────────────────────
def check_bingo(missions):
    lines = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8], # 横
        [0, 3, 6], [1, 4, 7], [2, 5, 8], # 縦
        [0, 4, 8], [2, 4, 6]             # 斜め
    ]
    count = 0
    for line in lines:
        if all(missions[i]["done"] for i in line):
            count += 1
    return count

def render_bingo_tab():
    st.header("🎯 旅のビンゴコレクション")
    st.write("旅行をさらに楽しむための2つのビンゴカードです。")
    
    edit_mode = st.toggle("✏️ ミッションを自由に編集する")
    
    # 2つのビンゴをループで処理
    for b_idx, bingo_data in enumerate(st.session_state.bingos):
        st.divider()
        st.subheader(bingo_data["title"])
        st.write(bingo_data["description"])
        
        missions = bingo_data["missions"]
        
        if edit_mode:
            st.info("好きなミッションやご褒美ルールに書き換えてください。")
            with st.form(f"bingo_edit_form_{b_idx}"):
                new_missions = []
                cols = st.columns(3)
                for i in range(9):
                    with cols[i % 3]:
                        st.markdown(f"**マス {i+1}**")
                        new_text = st.text_input("ミッション", value=missions[i]["text"], key=f"edit_m_{b_idx}_{i}", label_visibility="collapsed")
                        new_missions.append({"text": new_text, "done": missions[i]["done"]})
                
                sumbitted = st.form_submit_button("保存", use_container_width=True)
                if sumbitted:
                    st.session_state.bingos[b_idx]["missions"] = new_missions
                    save_data(st.session_state.bingos, BINGO_FILE)
                    st.rerun()
        else:
            # ビンゴ判定
            current_bingo_count = check_bingo(missions)
            prev_bingo_count = bingo_data.get("bingo_count", 0)
            
            if current_bingo_count > prev_bingo_count:
                st.balloons()
                st.success(f"🎉 新しいビンゴ達成！！！ (現在 {current_bingo_count} 列達成)")
            elif current_bingo_count > 0:
                st.success(f"🎉 現在 {current_bingo_count} 列ビンゴ達成中！")
                
            st.session_state.bingos[b_idx]["bingo_count"] = current_bingo_count
            
            # 3x3グリッド描画
            st.write("") # スペーサー
            for row in range(3):
                cols = st.columns(3)
                for col in range(3):
                    idx = row * 3 + col
                    m = missions[idx]
                    
                    with cols[col]:
                        btn_label = f"✅ 達成\n{m['text']}" if m["done"] else f"⬜ 未達成\n{m['text']}"
                        
                        if m["done"]:
                            if st.button(btn_label, key=f"btn_bingo_{b_idx}_{idx}", use_container_width=True, type="primary"):
                                st.session_state.bingos[b_idx]["missions"][idx]["done"] = False
                                save_data(st.session_state.bingos, BINGO_FILE)
                                st.rerun()
                        else:
                            if st.button(btn_label, key=f"btn_bingo_{b_idx}_{idx}", use_container_width=True):
                                st.session_state.bingos[b_idx]["missions"][idx]["done"] = True
                                save_data(st.session_state.bingos, BINGO_FILE)
                                st.rerun()
                                
            # 独立したメモリストの表示エリア
            st.divider()
            st.markdown(f"### 📝 {bingo_data['title']} のメモ・付箋")
            
            # メモの追加
            with st.form(f"memo_add_form_{b_idx}", clear_on_submit=True):
                col1, col2 = st.columns([4, 1])
                with col1:
                    new_memo_text = st.text_input("お店の候補ややりたいことのメモを追加", placeholder="例：〇〇水産の海鮮丼、△△ラーメン...", label_visibility="collapsed")
                with col2:
                    memo_submitted = st.form_submit_button("追加", use_container_width=True)
                    
                if memo_submitted and new_memo_text:
                    if "memos" not in st.session_state.bingos[b_idx]:
                        st.session_state.bingos[b_idx]["memos"] = []
                    st.session_state.bingos[b_idx]["memos"].append(new_memo_text)
                    save_data(st.session_state.bingos, BINGO_FILE)
                    st.rerun()

            # 登録されたメモの表示
            current_memos = bingo_data.get("memos", [])
            if current_memos:
                for idx, memo in enumerate(current_memos):
                    col_m1, col_m2 = st.columns([9, 1])
                    col_m1.info(f"📝 {memo}", icon=None)
                    if col_m2.button("🗑️", key=f"del_memo_{b_idx}_{idx}", help="メモを削除"):
                        st.session_state.bingos[b_idx]["memos"].pop(idx)
                        save_data(st.session_state.bingos, BINGO_FILE)
                        st.rerun()
            else:
                st.caption("現在追加されているメモはありません。")


# ── UI: AIアシスタントタブ ──────────────────────────────────────────────
def render_ai_assistant_tab():
    st.header("🤖 AIコンシェルジュ")
    st.write("現在のスケジュールや未達成のビンゴミッションをもとに、AIが旅行のアドバイスをします！✨")

    # APIキーの取得
    api_key = ""
    try:
        if "OPENAI_API_KEY" in st.secrets:
            api_key = st.secrets["OPENAI_API_KEY"]
    except Exception:
        # secrets.tomlが存在しない場合は無視して手動入力を促す
        pass
        
    if not api_key:
        api_key = st.text_input("OpenAI API Keyを入力してください（このセッションのみ有効）", type="password")

    if not api_key:
        st.warning("AI機能を利用するには、StreamlitのSecretsを設定するか、上記にAPIキーを入力してください。")
        return

    # ユーザーからの自由入力欄
    user_query = st.text_area(
        "AIに聞きたいこと・リクエスト（任意）",
        placeholder="例：今日の夜ごはんでおすすめの海鮮居酒屋を教えて！",
        height=100
    )

    if st.button("AIにアドバイスをもらう✨", type="primary"):
        with st.spinner("AIが旅行全体を分析中..."):
            try:
                client = openai.OpenAI(api_key=api_key)
                
                # コンテキストの作成
                context = "【現在の旅行スケジュール】\n"
                for day_key, day_info in DAYS.items():
                    context += f"--- {day_info['label']} ---\n"
                    items = sorted(st.session_state.data.get(day_key, []), key=lambda x: x["start_time"])
                    if not items:
                        context += "予定なし\n"
                    for item in items:
                        title = item.get("title") or (f"{item.get('start_place','')}➔{item.get('end_place','')}" if item.get("category")=="🚌 移動" else item.get("place", ""))
                        context += f"{item['start_time']}~{item['end_time']} [{item['category']}] {title}\n"
                
                context += "\n【ビンゴ（やりたいこと・食べたいもの）とメモ】\n"
                for bingo in st.session_state.bingos:
                    context += f"--- {bingo['title']} ---\n"
                    for m in bingo["missions"]:
                        status = "達成済" if m["done"] else "未達成"
                        context += f"- {m['text']} ({status})\n"
                    if bingo.get("memos"):
                        context += "（メモ）\n"
                        for memo in bingo["memos"]:
                            context += f"- {memo}\n"

                prompt = f"""あなたは優秀でフレンドリーな旅行コンシェルジュです。
北海道旅行（1泊2日）の「現在のスケジュール」と、「やりたいこと・食べたいもの（ビンゴやメモ）」のデータが以下にあります。"""

                if user_query:
                    prompt += f"""
旅行者からリクエスト（質問）が来ています。
【リクエスト】: 「{user_query}」

この【リクエスト】に対する回答を最も重点的かつ最優先に行ってください。
回答の際は、提供されたスケジュール、未達成のビンゴ、およびメモの内容を最大限に活用し、旅行者の状況に合わせた具体的でワクワクする提案にしてください。
"""
                else:
                    prompt += """
これらを踏まえて、以下の点について簡潔でワクワクするアドバイスを提供してください。
- 現在の予定の良さやポジティブなフィードバック
- スケジュールの空き時間にできそうな「未達成のビンゴ」や「メモに書かれた内容」からの提案
- スケジュール上の注意点（移動時間や現地の配慮など）やワンポイントアドバイス
"""

                prompt += f"\n{context}\n"

                response = client.chat.completions.create(
                    model="gpt-5-mini",
                    messages=[
                        {"role": "system", "content": "あなたはフレンドリーな旅行アシスタントです。"},
                        {"role": "user", "content": prompt}
                    ],
                    max_completion_tokens=2000
                )
                
                st.write("### 🤖 アドバイス")
                st.write(response.choices[0].message.content)
            
            except Exception as e:
                st.error(f"API呼び出しに失敗しました: {e}")

# ── UI: データ管理 (バックアップと復元) タブ ──────────────────────────────────────────
import io
import zipfile

def render_admin_tab():
    st.header("⚙️ データ管理 (バックアップと復元)")
    st.warning("⚠️ Streamlit Cloudの仕様上、GitHubにコードをプッシュする（アプリが更新される）と、クラウド上の最新のデータは消去されてしまいます。必ず更新前にデータをバックアップしてください。")
    
    col_dl, col_ul = st.columns(2, gap="large")
    
    with col_dl:
        st.subheader("📥 データのバックアップ (ダウンロード)")
        st.write("現在のすべてのデータ（予定、メンバー、出費、ビンゴ）をZIP形式でダウンロードします。")
        
        # メモリ上にZIPファイルを作成
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for file_name in [DATA_FILE, USERS_FILE, EXPENSES_FILE, BINGO_FILE]:
                if os.path.exists(file_name):
                    zip_file.write(file_name)
                    
        st.download_button(
            label="📦 すべてのデータをダウンロード (.zip)",
            data=zip_buffer.getvalue(),
            file_name=f"trip_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            mime="application/zip",
            type="primary"
        )
        
    with col_ul:
        st.subheader("📤 データの復元 (アップロード)")
        st.write("バックアップしたZIPファイルをアップロードして、データを上書き復元します。")
        uploaded_file = st.file_uploader("バックアップZIPファイルを選択", type="zip")
        
        if uploaded_file is not None:
            if st.button("🚨 データを復元する（現在のデータは上書きされます）", type="primary"):
                try:
                    with zipfile.ZipFile(uploaded_file, "r") as zip_ref:
                        zip_ref.extractall(".")
                    
                    # セッションステートをクリアしてリロードさせる
                    for key in ["data", "users", "expenses", "bingos"]:
                        if key in st.session_state:
                            del st.session_state[key]
                            
                    st.success("データの復元が完了しました！アプリを再読み込みします...")
                    import time
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"復元中にエラーが発生しました: {e}")

# ── タブごとのレンダリング ────────────────────────────────────────────────────
tab_labels = [info["label"] for key, info in DAYS.items()] + ["💰 割り勘・出費リスト", "🎯 旅のビンゴ", "🤖 AIアシスタント", "⚙️ 管理/バックアップ"]
selected_tab = st.radio("表示切り替え", tab_labels, horizontal=True, label_visibility="collapsed")

# 1日目、2日目タブ
for i, (day_key, day_info) in enumerate(DAYS.items()):
    if selected_tab == tab_labels[i]:
        render_day_content(day_key, day_info)

# 割り勘・出費リストタブ
if selected_tab == "💰 割り勘・出費リスト":
    render_expenses_tab()

# ビンゴタブ
if selected_tab == "🎯 旅のビンゴ":
    render_bingo_tab()

# AIアシスタントタブ
if selected_tab == "🤖 AIアシスタント":
    render_ai_assistant_tab()

# データ管理タブ
if selected_tab == "⚙️ 管理/バックアップ":
    render_admin_tab()

