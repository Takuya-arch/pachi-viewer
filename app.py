import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("ワンダーランド西新 - パチンコデータ分析ビューア")

# データベースから全データを安全に読み込む関数
def load_all_data():
    try:
        conn = sqlite3.connect("pachi_data.db")
        df = pd.read_sql("SELECT date, unit, machine_name, diff_balls FROM slump_data ORDER BY date DESC, unit ASC", conn)
        conn.close()
        return df
    except Exception:
        # テーブルがまだ無い場合やエラー時は空のDataFrameを返す
        return pd.DataFrame()

df_all = load_all_data()

if df_all.empty:
    st.info("💡 現在、データベースにデータがありません。\n\n今夜の自動データ収集（タスクスケジューラ）が実行されると、ここにデータやグラフが表示されます！")
else:
    tab1, tab2 = st.tabs(["📊 個別グラフ詳細", "📋 全台一覧（横スクロール確認）"])

    with tab1:
        st.subheader("台ごとの詳細スランプグラフ")
        units_with_names = df_all[['unit', 'machine_name']].drop_duplicates().values
        unit_options = [f"{row[0]}番台 : {row[1]}" for row in units_with_names]
        
        selected_option = st.selectbox("確認したい台を選択してください", unit_options)
        selected_unit = selected_option.split("番台")[0]

        days_choice = st.radio("表示期間", ["直近 7日間", "直近 30日間"], horizontal=True)
        days_num = 7 if "7日間" in days_choice else 30

        df_unit = df_all[df_all['unit'] == selected_unit].sort_values('date', ascending=True).tail(days_num)

        if df_unit.empty:
            st.info("データがありません。")
        else:
            machine_title = df_unit['machine_name'].iloc[0]
            
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(df_unit['date'], df_unit['diff_balls'], marker='o', color='purple', linewidth=2)
            ax.set_title(f"{selected_unit}番台 ({machine_title})", fontsize=12)
            ax.set_xlabel("日付")
            ax.set_ylabel("差玉数")
            plt.xticks(rotation=45)
            ax.grid(True)
            fig.tight_layout()

            st.pyplot(fig)

    with tab2:
        st.subheader("全台データ一覧表")
        st.dataframe(
            df_all,
            use_container_width=True,
            hide_index=True,
            column_config={
                "date": "日付",
                "unit": "台番号",
                "machine_name": "機種名",
                "diff_balls": st.column_config.NumberColumn("差玉数", format="%d 玉")
            }
        )
