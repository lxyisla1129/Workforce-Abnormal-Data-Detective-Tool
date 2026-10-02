import streamlit as st
import pandas as pd
from pathlib import Path
import altair as alt

st.set_page_config(
    page_title="Attendance Abnormal Report",
    layout="wide"
)

st.title("Attendance Abnormal Report")
st.caption("West Region Attendance Monitoring")

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "AMS_Attendance_Data.xlsx"

@st.cache_data
def load_data():
    df = pd.read_excel(DATA_FILE, engine="openpyxl")
    return df

# df = pd.read_excel(DATA_FILE)

# print("LATEST DATE IN FILE:", df["eday"].max())  # replace "date" with your actual date column


# Warehouse name mapping
warehouse_mapping = {
    "美国洛杉矶大件1号仓": "LAX1",
    "美国洛杉矶中小件2号仓": "LAX2",
    "出库组": "LAX2",
    "在库组": "LAX2",
    "美国洛杉矶中小件4号仓": "LAX4",
    "美国洛杉矶大件5号仓": "LAX5",
    "美国拉斯维加斯定制1号仓": "LAS1",
}


@st.cache_data(ttl=300)
def load_data():

    df = pd.read_excel(DATA_FILE, engine="openpyxl")

    # Convert date
    df["eday"] = pd.to_datetime(
        df["eday"],
        errors="coerce"
    )

    # ==========================================
    # DATA CLEAN
    # ==========================================
    df = df[
    df["scheduleDeptName"]
        .fillna("")
        .str.contains("洛杉矶|拉斯维加斯", na=False)
    |
    df["scheduleDeptName"]
        .fillna("")
        .isin(["出库组", "在库组"])
].copy()

    df["WarehouseName"] = (
    df["scheduleDeptName"]
    .map(warehouse_mapping)
    .fillna(df["scheduleDeptName"]))

    df["groupName"] = (
        df["kqAttGroupName"]
        .fillna("")
        .astype(str)
        .str[:2]
    )

    # Make sure hours are numeric
    df["planDuration"] = pd.to_numeric(
        df["planDuration"],
        errors="coerce"
    ).fillna(0)

    df["finalActualDurationHour"] = pd.to_numeric(
        df["finalActualDurationHour"],
        errors="coerce"
    ).fillna(0)

    df["HourGap"] = (
    df["finalActualDurationHour"]
    - df["planDuration"])

    abnormal_type_map = {
    "正常": "正常 Normal",
    "迟到": "迟到 Late Arrival",
    "早退": "早退 Early Leave",
    "缺卡": "缺卡 Missing Punch",
    "缺勤": "缺勤 Absence",
    "排空未出勤": "排空未出勤 Unscheduled & No Attendance",
    "排空出勤": "排空出勤 Unscheduled Attendance",
    "排休出勤": "排休出勤 Rest Day Attendance",
    "未多次打卡": "未多次打卡 Missing Multiple Punches",
}

    df["AbnormalTypeDisplay"] = (
        df["exTypeCodeDesc"]
        .map(abnormal_type_map)
        .fillna(df["exTypeCodeDesc"])
    )

    group_name_map = {
    "默认": "默认 Default",
    "入库": "入库 Inbound",
    "在库": "在库 Inventory",
    "出库": "出库 Outbound",
    "线下": "线下 Offline",
    "增值": "增值 VAS",
}

    df["GroupNameDisplay"] = (
        df["groupName"]
        .map(group_name_map)
        .fillna(df["groupName"])
    )

    return df


df = load_data()


# ==========================================
# SIDEBAR FILTERS
# ==========================================

st.sidebar.header("Filters")


# Date
available_dates = sorted(
    df["eday"].dropna().dt.date.unique(),
    reverse=True
)

selected_date = st.sidebar.selectbox(
    "Attendance Date",
    available_dates
)


# Warehouse
date_df = df[
    df["eday"].dt.date == selected_date
].copy()


warehouses = sorted(
    date_df["WarehouseName"]
    .dropna()
    .unique()
)

selected_warehouses = st.sidebar.multiselect(
    "Warehouse",
    warehouses,
    default=warehouses
)

filtered_df = date_df[
    date_df["WarehouseName"].isin(
        selected_warehouses
    )
].copy()

filtered_df["abnormalType"] = (
    df["exTypeCodeDesc"]
    .fillna("Unknown")
)

Normal_type= ["正常"]
filtered_df ["isAbnormal"] = (~filtered_df ["abnormalType"].isin(Normal_type))

abnormal_df = filtered_df[filtered_df["isAbnormal"]].copy()

# Dashboard

total_employees = filtered_df["userCode"].nunique()

normal_employees = filtered_df.loc[
    ~filtered_df["isAbnormal"],
    "userCode"
].nunique()

abnormal_employees = filtered_df.loc[
    filtered_df["isAbnormal"],
    "userCode"
].nunique()

abnormal_rate = (
    abnormal_employees / total_employees * 100
    if total_employees
    else 0
)

abnormal_df["AbnormalHours"] = (
    abnormal_df["HourGap"]
    .clip(upper=0)
    .abs()
)

total_abnormal_hours = (
    abnormal_df["AbnormalHours"].sum()
)

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    "Total Employees",
    f"{total_employees:,}"
)

col2.metric(
    "Normal Employees",
    f"{normal_employees:,}"
)

col3.metric(
    "Abnormal Employees",
    f"{abnormal_employees:,}"
)

col4.metric(
    "Abnormal Rate",
    f"{abnormal_rate:.2f}%"
)

col5.metric(
    "Abnormal Hour Gap",
    f"{total_abnormal_hours:,.1f} hrs"
)

st.divider()

st.subheader("Abnormal Hour Gap by Warehouse")

# Only count negative hour gaps as abnormal/lost hours
abnormal_df["abnormalHours"] = (
    abnormal_df["HourGap"]
    .clip(upper=0)
    .abs()
)

warehouse_hour_gap = (
    abnormal_df
    .groupby("WarehouseName")
    .agg(
        Abnormal_Employees=("userCode", "nunique"),
        Scheduled_Hours=("planDuration", "sum"),
        Actual_Hours=("finalActualDurationHour", "sum"),
        Abnormal_Hour_Gap=("abnormalHours", "sum")
    )
    .reset_index()
)

warehouse_hour_gap = warehouse_hour_gap.sort_values(
    "Abnormal_Hour_Gap",
    ascending=False
)

st.dataframe(
    warehouse_hour_gap.style.format({
        "Scheduled_Hours": "{:.1f}",
        "Actual_Hours": "{:.1f}",
        "Abnormal_Hour_Gap": "{:.1f}"
    }),
    use_container_width=True,
    hide_index=True
)

st.divider()

st.subheader("Abnormal Worker by Type by Warehouse")

module_by_wh = (
    abnormal_df
    .groupby(
        ["WarehouseName", "AbnormalTypeDisplay"]
    )["userCode"]
    .nunique()
    .reset_index(name="Employees")
)

module_by_wh = module_by_wh.sort_values(
    ["AbnormalTypeDisplay", "WarehouseName"]
)

module_by_wh["y_start"] = (
    module_by_wh
    .groupby("AbnormalTypeDisplay")["Employees"]
    .cumsum()
    - module_by_wh["Employees"]
)

module_by_wh["y_end"] = (
    module_by_wh["y_start"]
    + module_by_wh["Employees"]
)

# Middle of each stacked section
module_by_wh["y_mid"] = (
    module_by_wh["y_start"]
    + module_by_wh["Employees"] / 2
)

# ------------------------------------------
# STACKED BAR
# ------------------------------------------

bars = alt.Chart(module_by_wh).mark_bar().encode(

    x=alt.X(
        "AbnormalTypeDisplay:N",
        title="Abnormal Type"
    ),

    y=alt.Y(
        "y_start:Q",
        title="Employees"
    ),

    y2="y_end:Q",

    color=alt.Color(
        "WarehouseName:N",
        title="Warehouse"
    ),

    tooltip=[
        alt.Tooltip(
            "WarehouseName:N",
            title="Warehouse"
        ),
        alt.Tooltip(
            "AbnormalTypeDisplay:N",
            title="Abnormal Type"
        ),
        alt.Tooltip(
            "Employees:Q",
            title="Employees"
        )
    ]
)


# ------------------------------------------
# NUMBER LABEL
# ------------------------------------------

labels = alt.Chart(module_by_wh).mark_text(
    baseline="middle",
    align="center",
    fontSize=14,
    fontWeight="bold"
).encode(

    x=alt.X(
        "AbnormalTypeDisplay:N"
    ),

    y=alt.Y(
        "y_mid:Q"
    ),

    text=alt.Text(
        "Employees:Q",
        format=".0f"
    )
)


# ------------------------------------------
# COMBINE
# ------------------------------------------

chart = (
    bars + labels
).properties(
    height=450
)

st.altair_chart(
    chart,
    use_container_width=True
)

# st.bar_chart(
#     module_by_wh,
#     x="AbnormalTypeDisplay",
#     y="Employees",
#     color="WarehouseName"
# )

# col1, col2 = st.columns([2, 1])

# with col1:
# st.bar_chart(
#         module_summary,
#         x="AbnormalTypeDisplay",
#         y="Employees"
#     )

# # with col2:
# st.dataframe(
#         module_summary,
#         use_container_width=True,
#         hide_index=True
#     )


st.divider()

st.subheader("Abnormal Rate by Warehouse")

# Total unique employees in each warehouse
warehouse_total = (
    filtered_df
    .groupby("WarehouseName")["userCode"]
    .nunique()
)

# Unique abnormal employees by warehouse + abnormal type
warehouse_abnormal = (
    abnormal_df
    .groupby("WarehouseName")["userCode"]
    .nunique()
)

warehouse_summary = pd.DataFrame({
    "Total Employees": warehouse_total,
    "Abnormal Employees": warehouse_abnormal
}).fillna(0)

warehouse_summary["Abnormal Rate"] = (
    warehouse_summary["Abnormal Employees"]
    / warehouse_summary["Total Employees"]
    * 100
)

warehouse_summary = (
    warehouse_summary
    .reset_index()
    .sort_values(
        "Abnormal Rate",
        ascending=False
    )
)

# st.bar_chart(
#     warehouse_summary,
#     x="WarehouseName",
#     y="Abnormal Rate"
# )

# Total unique employees by warehouse
warehouse_total = (
    filtered_df
    .groupby("WarehouseName")["userCode"]
    .nunique()
    .rename("Total Employees")
    .reset_index()
)

# Abnormal employees by warehouse + abnormal type
warehouse_type = (
    abnormal_df
    .groupby(["WarehouseName", "AbnormalTypeDisplay"])["userCode"]
    .nunique()
    .rename("Abnormal Employees")
    .reset_index()
)

# Merge warehouse total into abnormal type table
warehouse_type = warehouse_type.merge(
    warehouse_total,
    on="WarehouseName",
    how="left"
)

# Calculate abnormal rate
warehouse_type["Abnormal %"] = (
    warehouse_type["Abnormal Employees"]
    / warehouse_type["Total Employees"]
    * 100
)

# Pivot
warehouse_pivot = warehouse_type.pivot_table(
    index="WarehouseName",
    columns="AbnormalTypeDisplay",
    values="Abnormal %",
    aggfunc="first",
    fill_value=0
)

# Display
def highlight_column_max(s):
    is_max = s == s.max()

    return [
        "background-color: #ffcccc; font-weight: bold"
        if v else ""
        for v in is_max
    ]


warehouse_styled = (
    warehouse_pivot.style
    .format("{:.2f}%")
    .apply(highlight_column_max, axis=0)
)

st.dataframe(
    warehouse_styled,
    use_container_width=True
)
# st.dataframe(
#     warehouse_pivot.style.format("{:.2f}%"),
#     use_container_width=True
# )

# ==========================================
# ABNORMAL MODULE % BY GROUP
# ==========================================

st.subheader("Abnormal Rate by Group")

group_total = (
    filtered_df
    .groupby(
        ["WarehouseName", "GroupNameDisplay"]
    )["userCode"]
    .nunique()
    .rename("Total Employees")
)

group_abnormal = (
    abnormal_df
    .groupby(
        [
            "WarehouseName",
            "GroupNameDisplay",
            "AbnormalTypeDisplay"
        ]
    )["userCode"]
    .nunique()
    .reset_index(name="Abnormal Employees")
)

group_abnormal = group_abnormal.merge(
    group_total.reset_index(),
    on=["WarehouseName", "GroupNameDisplay"],
    how="left"
)

group_abnormal["Abnormal %"] = (
    group_abnormal["Abnormal Employees"]
    / group_abnormal["Total Employees"]
    * 100
)

group_pivot = (
    group_abnormal
    .pivot_table(
        index=["WarehouseName", "GroupNameDisplay"],
        columns="AbnormalTypeDisplay",
        values="Abnormal %",
        fill_value=0
    )
)

group_styled = (
    group_pivot.style
    .format("{:.2f}%")
    .apply(highlight_column_max, axis=0)
)

st.dataframe(
    group_styled,
    use_container_width=True
)

# st.dataframe(
#     group_pivot.style.format("{:.2f}%"),
#     use_container_width=True
# )

st.divider()

st.subheader("Abnormal Employee Details")

selected_type = st.selectbox(
    "Abnormal Type",
    ["All"] + sorted(
        abnormal_df["AbnormalTypeDisplay"]
        .dropna()
        .unique()
        .tolist()
    )
)

detail_df = abnormal_df.copy()

if selected_type != "All":

    detail_df = detail_df[
        detail_df["AbnormalTypeDisplay"]
        == selected_type
    ]


display_columns = [
    "eday",
    "WarehouseName",
    "GroupNameDisplay",
    "userCode",
    "AbnormalTypeDisplay",
    "scheduledHours",
    "actualHours",
    "hourGap"
]

display_columns = [
    c for c in display_columns
    if c in detail_df.columns
]

st.dataframe(
    detail_df[display_columns],
    use_container_width=True,
    hide_index=True
)
