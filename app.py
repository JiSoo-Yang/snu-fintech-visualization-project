import folium
from folium.plugins import HeatMap
import streamlit as st
import pandas as pd
import branca.colormap as cm
from matplotlib import rc
import matplotlib.pyplot as plt
import plotly.express as px
import json
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

# 사고건수 기준으로 데이터 내림차순 정렬 (표에 반영)
df_sorted = df.sort_values(by='사고건수', ascending=False)

# '위치코드'의 앞 5자리 숫자로 그룹화하고 사고건수를 합산 (지도에 반영)
df['위치코드_시군구'] = df['위치코드'].astype(str).str[:5]  # 위치코드에서 첫 5자리 추출
df_grouped = df.groupby('위치코드_시군구', as_index=False)['사고건수'].sum()  # 사고건수 합산

# 법정구역 GeoJSON 파일 불러오기
with open('법정구역 GeoJSON 데이터_23년8월/법정구역_시군구.geojson', 'r', encoding='utf-8') as f:
    geojson = json.load(f)

# Choropleth 생성 함수 정의
def make_choropleth(df, geojson, location_code_column, value_column, color_theme):
    # Choropleth 생성
    choropleth = px.choropleth(df,
                               geojson=geojson,
                               locations=location_code_column,
                               featureidkey="properties.SIG_CD",
                               color=value_column,
                               color_continuous_scale=color_theme,
                               labels={value_column: '사고건수'},
                               template='simple_white'  # Use a clean template
                              )
    choropleth.update_geos(fitbounds="locations", visible=False)
    choropleth.update_layout(
        coloraxis_colorbar={
            'title': '누적 사고건수',
            'tickvals': [df[value_column].min(), df[value_column].max()],
            'ticktext': [f'{df[value_column].min()}', f'{df[value_column].max()}'],  # Display numeric values
        },
        margin=dict(l=0, r=0, t=0, b=0),
        height=500,
        geo=dict(
            bgcolor='rgba(0,0,0,0)'  # Transparent background
        )
    )
    return choropleth

# Choropleth 지도 생성
choropleth_map = make_choropleth(df_grouped, geojson, '위치코드_시군구', '사고건수', 'Blues')  # Use the "Blues" color scale

# ----------------------------
# Streamlit 앱 구성
# ----------------------------

st.title('초보운전, 언제가 가장 안전할까?')
st.markdown('### <span style="color:#4169e1">Q1. 전국에서 교통사고가 많이 발생하는 지역은 어디일까?</span>', unsafe_allow_html=True)
st.markdown('#### 1. 전국 교통사고 다발 지역 시각화 (2012-2021)')

# Choropleth 지도 표시
st.plotly_chart(choropleth_map)

# 가운데 정렬을 위한 스타일 지정
def center_align(s):
    return ['text-align: center'] * len(s)

# 첫 번째 표: 사고지역위치명을 기준으로 한 사고건수 Top 20
styled_table_location = df_sorted[['사고지역위치명', '사고건수']].head(20).style.set_table_styles(
    [{'selector': 'th', 
      'props': [('background-color', '#D3D3D3'), ('font-weight', 'bold'), ('text-align', 'center')]}]
).apply(center_align, axis=0)

# 전국 사고건수 기준 내림차순으로 정렬된 사고지역위치명 상위 20개 표시
st.markdown("##### ⦁ 사고지역위치명으로 합산한 사고 다발 지역 (전국 Top20)")
st.table(styled_table_location)

# 두 번째 표: '위치코드'의 앞 5자리 숫자로 그룹화한 후 사고건수를 합산한 것의 Top 20
df_grouped_sorted = df_grouped.sort_values(by='사고건수', ascending=False)
styled_table_code = df_grouped_sorted.head(20).style.set_table_styles(
    [{'selector': 'th', 
      'props': [('background-color', '#D3D3D3'), ('font-weight', 'bold'), ('text-align', 'center')]}]
).apply(center_align, axis=0)

# '위치코드' 앞 5자리 기준으로 그룹화한 후 사고건수 상위 20개 표시
st.markdown("##### ⦁ 시군구 기준으로 합산한 사고 다발 지역 (전국 Top20)")
st.table(styled_table_code)

# 시도별 사고 다발 지역 선택
sido_list = df['사고지역위치명'].apply(lambda x: x.split()[0]).unique()
selected_sido = st.selectbox("시도를 선택하세요", options=sido_list)

# 선택한 시도에 해당하는 데이터 필터링
df_sido = df[df['사고지역위치명'].str.contains(selected_sido)]

# 사고건수 기준으로 데이터 내림차순 정렬 (표에 반영)
df_sorted_sido = df_sido.sort_values(by='사고건수', ascending=False)

# '위치코드'의 앞 5자리 숫자로 그룹화하고 사고건수를 합산 (해당 시도의 지도에 반영)
df_sido['위치코드_시군구'] = df_sido['위치코드'].astype(str).str[:5]  # 위치코드에서 첫 5자리 추출
df_grouped_sido = df_sido.groupby('위치코드_시군구', as_index=False).agg({
    '사고건수': 'sum',
    '위도': 'mean',  # 중심 위치를 위한 위도 평균
    '경도': 'mean'   # 중심 위치를 위한 경도 평균
})

# 선택된 시도의 Choropleth 지도 생성
choropleth_map_sido = make_choropleth(df_grouped_sido, geojson, '위치코드_시군구', '사고건수', 'Reds')  # Use the "Reds" color scale

# 선택된 시도에 대한 지도 표시
st.markdown(f'#### 2. {selected_sido}의 교통사고 다발 지역 시각화 (2012-2021)')
st.plotly_chart(choropleth_map_sido)


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
# 요일, 시간대별 교통사고 추이 분석
# ----------------------------

st.markdown('### <span style="color:#4169e1">Q2. 운전하기에 적절한 요일, 시간대는 언제일까?</span>', unsafe_allow_html=True)

# # 두 개의 엑셀 파일을 읽어옵니다
# df1 = pd.read_excel('교통사고 데이터/요일별시간대별_사고건수(2014-2018).xls', header=2, index_col=0)
# df2 = pd.read_excel('교통사고 데이터/요일별시간대별_사고건수(2019-2023).xls', header=2, index_col=0)

# # 두 데이터프레임을 병합합니다
# df_combined = pd.concat([df1, df2], axis=1)

# # '합계' 열을 기준으로 데이터를 전처리합니다
# df_accidents = df_combined.loc['합계', :].T.reset_index()
# df_accidents.columns = ['시간대', '사고건수']

# # 다중 인덱스 문제 해결
# df_accidents = df_accidents.drop(columns='index', errors='ignore')

# # 시간대를 순서대로 정렬
# df_accidents['시간대'] = pd.Categorical(df_accidents['시간대'], categories=[
#     '00시-02시', '02시-04시', '04시-06시', '06시-08시', '08시-10시', '10시-12시', 
#     '12시-14시', '14시-16시', '16시-18시', '18시-20시', '20시-22시', '22시-24시'], ordered=True)
# df_accidents = df_accidents.sort_values('시간대')

# # 요일별 사고건수 합계
# df_days = df_combined.loc[df_combined.index.get_level_values(1) == '사고[건]'].reset_index(level=1, drop=True)

# # 요일별 시간대별 사고건수 히트맵
# fig_heatmap = px.imshow(df_days.values,
#                         labels=dict(x="시간대", y="요일", color="사고건수"),
#                         x=df_days.columns, y=df_days.index,
#                         color_continuous_scale='Reds')

# st.markdown('### <span style="color:#4169e1">Q2. 요일 및 시간대별 교통사고 현황</span>', unsafe_allow_html=True)

# # Plotly 그래프 생성 - 시간대별 사고건수
# fig_bar = px.bar(df_accidents, x='시간대', y='사고건수', title='시간대별 교통사고 건수',
#                  labels={'사고건수': '사고 건수', '시간대': '시간대'})

# # Plotly 그래프 생성 - 요일별 사고건수
# fig_day_bar = px.bar(df_days.sum(axis=1).reset_index(), x='사고요일', y=0, title='요일별 교통사고 건수',
#                      labels={0: '사고 건수', '사고요일': '요일'})

# # Streamlit에서 Plotly 그래프 표시
# st.plotly_chart(fig_heatmap)
# st.plotly_chart(fig_bar)
# st.plotly_chart(fig_day_bar)


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
df3_list = []

# 각 파일을 불러와서 리스트에 추가합니다.
for file_path in file_paths:
    year = int(file_path[-9:-5])  # 파일명에서 연도 추출
    df3 = pd.read_csv(file_path, encoding='euc-kr')
    df3['발생년도'] = year  # 발생년도 열 추가
    df3_list.append(df3)

# 모든 데이터를 하나의 데이터프레임으로 결합합니다.
df3_combined = pd.concat(df3_list, ignore_index=True)

# ----------------------------
# 어린이날 교통사고 추이 분석
# ----------------------------

# 어린이날 (5월 5일) 데이터 필터링
df_children_day = df3_combined[(df3_combined['발생월'] == 5) & (df3_combined['발생일'] == 5)]

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
df_lunar_new_year = filter_holiday_data(df3_combined, lunar_new_year_dates)
lunar_new_year_stats = df_lunar_new_year.groupby('발생년도').sum()[['사고건수', '사망자수', '중상자수', '경상자수']].reset_index()
years_with_dates_lunar = [f"{year}\n({lunar_new_year_dates[year][0][0]}~{lunar_new_year_dates[year][-1][-1]})" for year in lunar_new_year_stats['발생년도']]

# 추석 교통사고 데이터 필터링 및 집계
df_chuseok = filter_holiday_data(df3_combined, chuseok_dates)
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

# ----------------------------
# 월드컵 기간 교통사고 추이 분석
# ----------------------------

# 가설3 텍스트에 빨간색 밑줄 추가
st.markdown('##### [가설3] 월드컵 기간에는 유동인구가 증가하여 <span style="text-decoration: underline; text-decoration-color: red; text-underline-offset: 0.2em; text-decoration-thickness: 2px;">교통사고 발생 건수도 증가할 것이다.</span>', 
            unsafe_allow_html=True)

# 월드컵 기간 설정 (예시로 대한민국 경기 날짜 포함)
world_cup_dates_2018 = [
    ('06-14', '07-15')  # 2018 러시아 월드컵 전체 기간
]

world_cup_dates_2022 = [
    ('11-20', '12-18')  # 2022 카타르 월드컵 전체 기간
]

def filter_world_cup_data(df, world_cup_dates, year):
    world_cup_data_list = []
    for start_date, end_date in world_cup_dates:
        start_month, start_day = map(int, start_date.split('-'))
        end_month, end_day = map(int, end_date.split('-'))
        
        filtered_data = df[
            (df['발생년도'] == year) &
            ((df['발생월'] == start_month) & (df['발생일'] >= start_day) | (df['발생월'] == end_month) & (df['발생일'] <= end_day))
        ]
        world_cup_data_list.append(filtered_data)
    
    return pd.concat(world_cup_data_list, ignore_index=True)

# 2018년 데이터 필터링
df_wc_2018 = filter_world_cup_data(df3_combined, world_cup_dates_2018, 2018)

# 2022년 데이터 필터링
df_wc_2022 = filter_world_cup_data(df3_combined, world_cup_dates_2022, 2022)

# 연도별 사고 건수 집계
wc_2018_stats = df_wc_2018.groupby('발생년도').sum()[['사고건수']].reset_index()
wc_2022_stats = df_wc_2022.groupby('발생년도').sum()[['사고건수']].reset_index()

# 월드컵 기간 동안의 사고 건수를 추가
wc_2018_stats['기간'] = '2018 월드컵 기간'
wc_2022_stats['기간'] = '2022 월드컵 기간'

# 두 기간의 데이터 병합
wc_stats_combined = pd.concat([wc_2018_stats, wc_2022_stats], ignore_index=True)

# 월드컵 기간 동안의 사고 건수 시각화
fig_wc = px.bar(wc_stats_combined, x='기간', y='사고건수', title='월드컵 기간 동안의 교통사고 건수 비교',
                labels={'사고건수': '사고 건수', '기간': '기간'})

# Streamlit에서 그래프 표시
st.plotly_chart(fig_wc)


# 2018년과 2022년 데이터를 그룹화하여 월별 사고 건수를 계산
df_2018 = df3_combined[df3_combined['발생년도'] == 2018].groupby('발생월').sum()[['사고건수']].reset_index()
df_2022 = df3_combined[df3_combined['발생년도'] == 2022].groupby('발생월').sum()[['사고건수']].reset_index()

# 연도 정보 추가
df_2018['연도'] = '2018'
df_2022['연도'] = '2022'

# 2018년과 2022년 데이터를 결합
df_combined = pd.concat([df_2018, df_2022])

# 하나의 그래프에 2018년과 2022년 데이터를 표시
fig_combined = px.line(df_combined, x='발생월', y='사고건수', color='연도', 
                       title='2018년과 2022년 월드컵 기간 동안의 교통사고 건수 변화',
                       labels={'발생월': '월', '사고건수': '사고 건수', '연도': '연도'})

# 2018년 월드컵 기간 표시
fig_combined.add_scatter(x=[6, 7], y=df_2018[df_2018['발생월'].isin([6, 7])]['사고건수'], 
                         mode='lines+markers', name='2018 월드컵 기간', line=dict(dash='dot'))

# 2022년 월드컵 기간 표시
fig_combined.add_scatter(x=[11, 12], y=df_2022[df_2022['발생월'].isin([11, 12])]['사고건수'], 
                         mode='lines+markers', name='2022 월드컵 기간', line=dict(dash='dot'))

# Streamlit에서 그래프 표시
st.plotly_chart(fig_combined)

# 사고 추이 분석 - 미세먼지
st.markdown('### <span style="color:#4169e1">Q4. 미세먼지에 따른 교통사고건수 변화는?</span>', unsafe_allow_html=True)

# 사고 추이 분석 - 주가등락률
st.markdown('### <span style="color:#4169e1">Q5. 주가 등락률에 따른 교통사고건수 변화는?</span>', unsafe_allow_html=True)


