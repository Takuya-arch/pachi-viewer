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
        # データの読み込み
        df = pd.read_sql_query("SELECT * FROM slump_data", conn)
    except Exception as e:
        conn.close()
        raise e
    conn.close()

    if df.empty:
        return df

    # 型変換とクレンジング（エラー回避処理）
    df['date'] = df['date'].astype(str)
    
    if 'hall_name' not in df.columns:
        df['hall_name'] = "ワンダーランド西新"
    else:
        df['hall_name'] = df['hall_name'].fillna("ワンダーランド西新").astype(str)

    # unit (台番号) を文字列に統一してソート時のエラーを防止
    df['unit'] = df['unit'].astype(str)
    df['machine_name'] = df['machine_name'].astype(str)
    df['diff_balls'] = pd.to_numeric(df['diff_balls'], errors='coerce').fillna(0).astype(int)

    return df

try:
    df = load_data()

    if df is None or df.empty:
        st.warning("⚠ データベース（pachi_data.db）にデータが存在しないか、ファイルが見つかりません。")
    else:
        # サイドバーフィルター
        st.sidebar.header("🔍 フィルター設定")

        # 店舗選択
        halls = sorted(df['hall_name'].unique().tolist())
        selected_hall = st.sidebar.selectbox("店舗を選択", halls)

        df_hall = df[df['hall_name'] == selected_hall]

        # 日付選択
        dates = sorted(df_hall['date'].unique().tolist(), reverse=True)
        selected_date = st.sidebar.selectbox("日付を選択", dates)

        df_filtered = df_hall[df_hall['date'] == selected_date].copy()

        # 機種選択
        machines = ["すべて"] + sorted(df_filtered['machine_name'].unique().tolist())
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
        
        # 台番号順に並び替え
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