import folium
from folium.plugins import HeatMap
import streamlit as st
import pandas as pd
import branca.colormap as cm
from matplotlib import rc
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go

# 한글 폰트 설정
rc('font', family='NanumGothic')
plt.rcParams['axes.unicode_minus'] = False

# ----------------------------
# 데이터 불러오기 및 전처리
# ----------------------------

# 교통사고 다발 지역 데이터 불러오기
df = pd.read_csv('교통사고 데이터/전국교통사고다발지역표준데이터.csv', encoding='euc-kr')
drop_list = ['데이터기준일자', '제공기관코드', '제공기관명']
df = df.drop(columns=drop_list)

# 사고건수 기준으로 데이터 내림차순 정렬
df_sorted = df.sort_values(by='사고건수', ascending=False)

# 사고다발 지역의 위도와 경도를 추출하고, 사고건수를 사용하여 가중치로 사용
heat_data = []
for index, row in df.iterrows():
    heat_data.append([row['위도'], row['경도'], row['사고건수']])

# 지도 생성
m = folium.Map(location=[df['위도'].mean(), df['경도'].mean()], zoom_start=7)

# 색상 스케일 설정
min_count = df['사고건수'].min()
max_count = df['사고건수'].max()
colormap = cm.LinearColormap(colors=['blue', 'lime', 'yellow', 'red'], vmin=min_count, vmax=max_count)

# 히트맵 생성
HeatMap(heat_data, radius=15, blur=25, max_zoom=1).add_to(m)

# 지도에 색상바 추가
colormap.caption = "사고건수"
m.add_child(colormap)

# 지도 HTML을 임시 파일로 저장
map_path = 'accident_heatmap.html'
m.save(map_path)

# ----------------------------
# Streamlit 앱 구성
# ----------------------------

# 웹 폰트 설정

st.title('초보운전, 언제가 가장 안전할까?')
st.markdown('### <span style="color:#4169e1">Q1. 전국에서 교통사고가 많이 발생하는 지역은 어디일까?</span>', unsafe_allow_html=True)
st.markdown('#### 1. 전국 교통사고 다발 지역 시각화 (2012-2021)')

# 전국 사고 다발 지역 지도 표시
with open(map_path, 'r', encoding='utf-8') as f:
    map_html = f.read()
st.components.v1.html(map_html, height=500)

# 전국 사고건수 기준 내림차순으로 정렬된 사고지역위치명 상위 20개 표시
st.markdown("##### ⦁ 사고 다발 지역 (전국 Top20)")

# 가운데 정렬을 위한 스타일 지정
def center_align(s):
    return ['text-align: center'] * len(s)

styled_table = df_sorted[['사고지역위치명', '사고건수']].head(20).style.set_table_styles(
    [{'selector': 'th', 
      'props': [('background-color', '#D3D3D3'), ('font-weight', 'bold'), ('text-align', 'center')]}]
).apply(center_align, axis=0)

# 스타일이 적용된 테이블 표시
st.table(styled_table)

# 시도별 사고 다발 지역 선택
sido_list = df['사고지역위치명'].apply(lambda x: x.split()[0]).unique()
selected_sido = st.selectbox("시도를 선택하세요", options=sido_list)

# 선택한 시도에 해당하는 데이터 필터링
df_sido = df[df['사고지역위치명'].str.contains(selected_sido)]

# 사고건수 기준으로 데이터 내림차순 정렬
df_sorted_sido = df_sido.sort_values(by='사고건수', ascending=False)

# 사고다발 지역의 위도와 경도를 추출하고, 사고건수를 사용하여 가중치로 사용
heat_data_sido = []
for index, row in df_sido.iterrows():
    heat_data_sido.append([row['위도'], row['경도'], row['사고건수']])

# 지도 생성
m_sido = folium.Map(location=[df_sido['위도'].mean(), df_sido['경도'].mean()], zoom_start=12)

# 색상 스케일 설정
min_count_sido = df_sido['사고건수'].min()
max_count_sido = df_sido['사고건수'].max()
colormap_sido = cm.LinearColormap(colors=['blue', 'lime', 'yellow', 'red'], vmin=min_count_sido, vmax=max_count_sido)

# 히트맵 생성
HeatMap(heat_data_sido, radius=15, blur=25, max_zoom=1).add_to(m_sido)

# 지도에 색상바 추가
colormap_sido.caption = "사고건수"
m_sido.add_child(colormap_sido)

# 지도 HTML을 임시 파일로 저장
map_sido_path = 'sido_accident_heatmap.html'
m_sido.save(map_sido_path)

# 선택된 시도에 대한 지도 표시
st.markdown(f'#### 2. {selected_sido}의 교통사고 다발 지역 시각화 (2012-2021)')
with open(map_sido_path, 'r', encoding='utf-8') as f:
    map_sido_html = f.read()
st.components.v1.html(map_sido_html, height=500)

# 선택된 시도의 사고건수 기준 내림차순으로 정렬된 사고지역위치명 상위 10개 표시
st.markdown(f"##### ⦁ {selected_sido} 내 사고 다발 지역 (Top10)")

# 가운데 정렬을 위한 스타일 지정
styled_table_sido = df_sorted_sido[['사고지역위치명', '사고건수']].head(10).style.set_table_styles(
    [{'selector': 'th', 
      'props': [('background-color', '#D3D3D3'), ('font-weight', 'bold'), ('text-align', 'center')]}]
).apply(center_align, axis=0)

# 스타일이 적용된 테이블 표시
st.table(styled_table_sido)

# ----------------------------
# 여러 연도의 데이터를 결합하여 요일, 시간대별 교통사고 추이 분석
# ----------------------------

# 사고 추이 분석 - 요일, 시간대
st.markdown('### <span style="color:#4169e1">Q2. 특정 기간의 교통사고 추이는 어떻게 변화했을까?</span>', unsafe_allow_html=True)

# ----------------------------
# 여러 연도의 데이터를 결합하여 특정 기간의 교통사고 추이 분석
# ----------------------------

# 여러 연도의 데이터를 결합하기 위해 파일 경로 목록을 만듭니다.
file_paths = [
    '교통사고 데이터/도로교통공단_일자별 시군구별 교통사고 건수(2016).csv',
    '교통사고 데이터/도로교통공단_일자별 시군구별 교통사고 건수(2017).csv',
    '교통사고 데이터/도로교통공단_일자별 시군구별 교통사고 건수(2018).csv',
    '교통사고 데이터/도로교통공단_일자별 시군구별 교통사고 건수(2019).csv',
    '교통사고 데이터/도로교통공단_일자별 시군구별 교통사고 건수(2020).csv',
    '교통사고 데이터/도로교통공단_일자별 시군구별 교통사고 건수(2021).csv',
    '교통사고 데이터/도로교통공단_일자별 시군구별 교통사고 건수(2022).csv',
    '교통사고 데이터/도로교통공단_일자별 시군구별 교통사고 건수(2023).csv'
]

# 데이터를 저장할 빈 리스트를 만듭니다.
df2_list = []

# 각 파일을 불러와서 리스트에 추가합니다.
for file_path in file_paths:
    year = int(file_path[-9:-5])  # 파일명에서 연도 추출
    df2 = pd.read_csv(file_path, encoding='euc-kr')
    df2['발생년도'] = year  # 발생년도 열 추가
    df2_list.append(df2)

# 모든 데이터를 하나의 데이터프레임으로 결합합니다.
df2_combined = pd.concat(df2_list, ignore_index=True)

# ----------------------------
# 어린이날 교통사고 추이 분석
# ----------------------------

# 어린이날 (5월 5일) 데이터 필터링
df_children_day = df2_combined[(df2_combined['발생월'] == 5) & (df2_combined['발생일'] == 5)]

# 연도별 사고 건수 및 사망자수, 중상자수, 경상자수 집계
children_day_stats = df_children_day.groupby('발생년도').sum()[['사고건수', '사망자수', '중상자수', '경상자수']].reset_index()

# 사고 추이 분석 - 어린이날
st.markdown('### <span style="color:#4169e1">Q3. 특정 기간의 교통사고 추이는 어떻게 변화했을까?</span>', unsafe_allow_html=True)

# 가설1 텍스트에 빨간색 밑줄 추가
st.markdown('##### [가설1] 고령화와 저출산의 영향으로 어린이 인구가 감소하면서, <span style="text-decoration: underline; text-decoration-color: red; text-underline-offset: 0.2em; text-decoration-thickness: 2px;">어린이날의 교통사고 발생 건수도 감소할 것이다.</span>', 
            unsafe_allow_html=True)

# Plotly 그래프 생성
fig = px.line(children_day_stats, x='발생년도', y=['사고건수', '사망자수', '중상자수', '경상자수'],
              labels={'value': '수치', 'variable': '항목', '발생년도': '연도'},
              markers=True,
              title='어린이날 교통사고 추이 (2016-2023)')

# x축 모든 연도 표시
fig.update_xaxes(tickmode='linear', dtick=1)

# Streamlit에서 Plotly 그래프 표시
st.plotly_chart(fig)

# ----------------------------
# 명절 기간 교통사고 추이 분석
# ----------------------------

# 가설2 텍스트에 빨간색 밑줄 추가
st.markdown('##### [가설2] 비대면 명절 문화의 확산 등 사회적 변화로 인해 <span style="text-decoration: underline; text-decoration-color: red; text-underline-offset: 0.2em; text-decoration-thickness: 2px;">명절 기간 동안의 유동인구가 감소하면서 교통사고 발생 건수도 줄어들 것이다.</span>', 
            unsafe_allow_html=True)

# 연도별 설날 연휴 날짜 딕셔너리
lunar_new_year_dates = {
    2016: [('02-07'), ('02-08'), ('02-09'), ('02-10')],
    2017: [('01-27'), ('01-28'), ('01-29'), ('01-30')],
    2018: [('02-15'), ('02-16'), ('02-17'), ('02-18')],
    2019: [('02-02'), ('02-03'), ('02-04'), ('02-05'), ('02-06')],
    2020: [('01-24'), ('01-25'), ('01-26'), ('01-27')],
    2021: [('02-11'), ('02-12'), ('02-13'), ('02-14')],
    2022: [('01-31'), ('02-01'), ('02-02')],
    2023: [('01-21'), ('01-22'), ('01-23'), ('01-24')]
}

# 연도별 추석 연휴 날짜 딕셔너리
chuseok_dates = {
    2016: [('09-14'), ('09-15'), ('09-16')],
    2017: [('10-03'), ('10-04'), ('10-05'), ('10-06')],
    2018: [('09-23'), ('09-24'), ('09-25'), ('09-26')],
    2019: [('09-12'), ('09-13'), ('09-14')],
    2020: [('09-30'), ('10-01'), ('10-02'), ('10-03')],
    2021: [('09-20'), ('09-21'), ('09-22')],
    2022: [('09-09'), ('09-10'), ('09-11'), ('09-12')],
    2023: [('09-28'), ('09-29'), ('09-30')]
}

def filter_holiday_data(df, holiday_dates):
    holiday_data_list = []
    for year, dates in holiday_dates.items():
        for date_str in dates:
            month, day = map(int, date_str.split('-'))
            filtered_data = df[
                (df['발생년도'] == year) &
                (df['발생월'] == month) &
                (df['발생일'] == day)
            ]
            holiday_data_list.append(filtered_data)
    return pd.concat(holiday_data_list, ignore_index=True)

# 설날 교통사고 데이터 필터링 및 집계
df_lunar_new_year = filter_holiday_data(df2_combined, lunar_new_year_dates)
lunar_new_year_stats = df_lunar_new_year.groupby('발생년도').sum()[['사고건수', '사망자수', '중상자수', '경상자수']].reset_index()
years_with_dates_lunar = [f"{year}\n({lunar_new_year_dates[year][0][0]}~{lunar_new_year_dates[year][-1][-1]})" for year in lunar_new_year_stats['발생년도']]

# 추석 교통사고 데이터 필터링 및 집계
df_chuseok = filter_holiday_data(df2_combined, chuseok_dates)
chuseok_stats = df_chuseok.groupby('발생년도').sum()[['사고건수', '사망자수', '중상자수', '경상자수']].reset_index()
years_with_dates_chuseok = [f"{year}\n({chuseok_dates[year][0][0]}~{chuseok_dates[year][-1][-1]})" for year in chuseok_stats['발생년도']]

# 설날 교통사고 추이 그래프 생성
fig_lunar = go.Figure()

for column in ['사고건수', '사망자수', '중상자수', '경상자수']:
    fig_lunar.add_trace(go.Scatter(x=lunar_new_year_stats['발생년도'], y=lunar_new_year_stats[column], mode='lines+markers', name=column))

fig_lunar.update_layout(
    title='설날 교통사고 추이 (2016-2023)',
    xaxis_title='연도 및 설날 기간',
    yaxis_title='수치',
    xaxis=dict(
        tickmode='linear',
        dtick=1,  # 모든 연도 표시
        tickangle=0,  # x축 레이블 수평으로 표시
        tickvals=lunar_new_year_stats['발생년도'],
        ticktext=years_with_dates_lunar
    )
)

# 추석 교통사고 추이 그래프 생성
fig_chuseok = go.Figure()

for column in ['사고건수', '사망자수', '중상자수', '경상자수']:
    fig_chuseok.add_trace(go.Scatter(x=chuseok_stats['발생년도'], y=chuseok_stats[column], mode='lines+markers', name=column))

fig_chuseok.update_layout(
    title='추석 교통사고 추이 (2016-2023)',
    xaxis_title='연도 및 추석 기간',
    yaxis_title='수치',
    xaxis=dict(
        tickmode='linear',
        dtick=1,  # 모든 연도 표시
        tickangle=0,  # x축 레이블 수평으로 표시
        tickvals=chuseok_stats['발생년도'],
        ticktext=years_with_dates_chuseok
    )
)

# Streamlit에서 Plotly 그래프 표시
st.plotly_chart(fig_lunar)
st.plotly_chart(fig_chuseok)
