import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# ページ基本設定
st.set_page_config(page_title="パチンコ 差玉データアナライザー", layout="wide")

# データベース接続関数
def load_data():
    conn = sqlite3.connect("pachi_data.db")
    df = pd.read_sql_query("SELECT * FROM slump_data", conn)
    conn.close()
    return df

st.title("🎰 パチンコ 差玉＆スランプグラフ アナライザー")

try:
    df = load_data()

    if df.empty:
        st.warning("データベースにまだデータがありません。`test13.py` を実行してデータを収集してください。")
        st.stop()

    # 日付型変換・並び替え
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(['hall_name', 'unit', 'date'])

    # --- サイドバーフィルター ---
    st.sidebar.header("🔍 検索・絞り込み")

    # 1. 店舗選択（hall_nameカラムが無い旧データへの対策付き）
    if 'hall_name' in df.columns:
        hall_list = df['hall_name'].unique().tolist()
        # 未指定データを補正
        hall_list = [h if h else "ワンダーランド西新" for h in hall_list]
        hall_list = sorted(list(set(hall_list)))
    else:
        hall_list = ["ワンダーランド西新"]

    selected_hall = st.sidebar.selectbox("① 店舗を選択", hall_list)

    # 店舗フィルタリング
    if 'hall_name' in df.columns:
        df_filtered = df[df['hall_name'] == selected_hall].copy()
    else:
        df_filtered = df.copy()

    # 2. 機種フィルタ
    machine_list = ["全機種"] + sorted(df_filtered['machine_name'].dropna().unique().tolist())
    selected_machine = st.sidebar.selectbox("② 機種を選択", machine_list)

    if selected_machine != "全機種":
        df_filtered = df_filtered[df_filtered['machine_name'] == selected_machine]

    # 3. 台番号フィルタ
    unit_list = ["全台"] + sorted(df_filtered['unit'].unique().tolist())
    selected_unit = st.sidebar.selectbox("③ 台番号を選択", unit_list)

    if selected_unit != "全台":
        df_filtered = df_filtered[df_filtered['unit'] == selected_unit]

    # --- 通算差玉（累計）の計算 ---
    df_filtered['cum_diff'] = df_filtered.groupby('unit')['diff_balls'].cumsum()

    # --- グラフ表示 ---
    st.subheader(f"📊 {selected_hall} のスランプグラフ")

    if selected_unit != "全台":
        # 単一台の表示：通算スランプグラフ
        fig = px.line(
            df_filtered,
            x='date',
            y='cum_diff',
            markers=True,
            title=f"{selected_unit}番台 [{df_filtered['machine_name'].iloc[-1]}] の差玉推移",
            labels={'date': '日付', 'cum_diff': '累計差玉数（玉）'}
        )
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        st.plotly_chart(fig, use_container_width=True)

    else:
        # 複数台の表示：日別の全台合計または指定機種の合計差玉
        daily_summary = df_filtered.groupby('date')['diff_balls'].sum().reset_index()
        daily_summary['cum_diff'] = daily_summary['diff_balls'].cumsum()

        fig = px.line(
            daily_summary,
            x='date',
            y='cum_diff',
            markers=True,
            title=f"{selected_machine} - 全体通算差玉推移",
            labels={'date': '日付', 'cum_diff': '累計差玉数（玉）'}
        )
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        st.plotly_chart(fig, use_container_width=True)

    # --- データ一覧表表示 ---
    st.subheader("📋 取得データ一覧")
    display_cols = [col for col in ['date', 'hall_name', 'unit', 'machine_name', 'diff_balls'] if col in df_filtered.columns]
    st.dataframe(df_filtered[display_cols].sort_values('date', ascending=False), use_container_width=True)

except Exception as e:
    st.error(f"データの読み込み中にエラーが発生しました: {e}")
