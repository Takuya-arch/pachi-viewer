import streamlit as st
import sqlite3
import matplotlib.pyplot as plt

st.title("パチンコ スランプグラフ・ビューア")
st.write("長期蓄積データの動的分析ダッシュボード")

# データベースから保存されているすべての台番号を自動で取得
def get_available_units():
    conn = sqlite3.connect("pachi_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT unit FROM slump_data ORDER BY unit ASC")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

units = get_available_units()

if not units:
    st.warning("データベースに台データがまだありません。")
else:
    # 複数台から選べるプルダウン
    unit_choice = st.selectbox("確認したい台番号を選択してください", units)

    # 期間の選択
    days_choice = st.radio("表示期間を選択", ["直近 7日間", "直近 30日間"])
    days_num = 7 if "7日間" in days_choice else 30

    def get_data_from_db(unit, days):
        conn = sqlite3.connect("pachi_data.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date, diff_balls FROM slump_data
            WHERE unit = ?
            ORDER BY date ASC
            LIMIT ?
        """, (unit, days))
        rows = cursor.fetchall()
        conn.close()
        return [row[0] for row in rows], [row[1] for row in rows]

    dates, diffs = get_data_from_db(unit_choice, days_num)

    if not dates:
        st.warning(f"{unit_choice}番台のデータが見つかりませんでした。")
    else:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(dates, diffs, marker='o', color='purple', linewidth=2)
        ax.set_title(f"Slump Graph (Unit {unit_choice} - {days_choice})", fontsize=14)
        ax.set_xlabel("Date", fontsize=12)
        ax.set_ylabel("Diff Balls", fontsize=12)
        plt.xticks(rotation=45)
        ax.grid(True)
        fig.tight_layout()

        st.pyplot(fig)
        st.success(f"{unit_choice}番台のデータを正常に読み込みました（{len(dates)}日分）")
