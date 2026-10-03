import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="パチンコ 差玉アナライザー", layout="wide")
st.title("🎰 パチンコ 差玉＆スランプグラフ アナライザー")

DB_PATH = "pachi_data.db"

@st.cache_data(ttl=60)
def load_data():
    if not os.path.exists(DB_PATH):
        return None
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query("SELECT * FROM slump_data", conn)
    except Exception as e:
        conn.close()
        raise e
    conn.close()

    if df.empty:
        return df

    # --- 全カラムの安全な型変換＆クレンジング ---
    if 'hall_name' not in df.columns:
        df['hall_name'] = "ワンダーランド西新"
    
    # 文字列カラムの欠損値補正と文字列化
    for col in ['hall_name', 'date', 'unit', 'machine_name']:
        if col in df.columns:
            df[col] = df[col].fillna("不明").astype(str)
        else:
            df[col] = "不明"

    # 数値カラムの数値化（エラー値は0にする）
    if 'diff_balls' in df.columns:
        df['diff_balls'] = pd.to_numeric(df['diff_balls'], errors='coerce').fillna(0).astype(int)
    else:
        df['diff_balls'] = 0

    # 不要なシステム表示データの除外
    df = df[~df['machine_name'].str.contains('しばらくお待ち|台データオンライン', na=False)]

    return df

try:
    df = load_data()

    if df is None or df.empty:
        st.warning("⚠ データベース（pachi_data.db）に有効なデータが存在しません。")
    else:
        st.sidebar.header("🔍 フィルター設定")

        # 店舗選択（文字列としてソート）
        halls = sorted(list(set(df['hall_name'].tolist())))
        selected_hall = st.sidebar.selectbox("店舗を選択", halls)

        df_hall = df[df['hall_name'] == selected_hall]

        # 日付選択
        dates = sorted(list(set(df_hall['date'].tolist())), reverse=True)
        if not dates:
            st.warning("選択した店舗のデータがありません。")
        else:
            selected_date = st.sidebar.selectbox("日付を選択", dates)
            df_filtered = df_hall[df_hall['date'] == selected_date].copy()

            # 機種選択
            machines = ["すべて"] + sorted(list(set(df_filtered['machine_name'].tolist())))
            selected_machine = st.sidebar.selectbox("機種を選択", machines)

            if selected_machine != "すべて":
                df_filtered = df_filtered[df_filtered['machine_name'] == selected_machine]

            # 概要指標（KPI）
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("総台数", f"{len(df_filtered)} 台")
            col2.metric("総差玉", f"{df_filtered['diff_balls'].sum():,} 玉")
            col3.metric("平均差玉", f"{int(df_filtered['diff_balls'].mean() if len(df_filtered)>0 else 0):,} 玉")
            
            plus_count = len(df_filtered[df_filtered['diff_balls'] > 0])
            win_rate = (plus_count / len(df_filtered) * 100) if len(df_filtered) > 0 else 0
            col4.metric("勝率 (プラス台率)", f"{win_rate:.1f} %")

            st.markdown("---")

            # 差玉ランキング/グラフ表示
            st.subheader("📊 台別差玉ランキング")
            
            df_sorted = df_filtered.sort_values(by="diff_balls", ascending=False)

            fig = px.bar(
                df_sorted,
                x="unit",
                y="diff_balls",
                color="diff_balls",
                color_continuous_scale="RdBu_r",
                labels={"unit": "台番号", "diff_balls": "差玉数"},
                title=f"{selected_date} [{selected_hall}] 差玉一覧"
            )
            st.plotly_chart(fig, use_container_width=True)

            # データテーブル
            st.subheader("📋 詳細データ")
            st.dataframe(
                df_sorted[['unit', 'machine_name', 'diff_balls']].rename(
                    columns={'unit': '台番号', 'machine_name': '機種名', 'diff_balls': '差玉'}
                ),
                use_container_width=True
            )

except Exception as e:
    st.error(f"データの読み込み中にエラーが発生しました: {e}")