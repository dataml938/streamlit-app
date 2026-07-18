import pandas as pd
import plotly.express as px
import streamlit as st

APP_TITLE = "Superstore Satış Analitikası"
DATA_PATH = "dataset.csv"
DATA_ENCODING = "latin1"
VALID_CREDENTIALS = {"datacube": "datacube123"}
TOP_N_PRODUCTS = 10
PRIMARY_COLOR = "#4F46E5"
NEGATIVE_COLOR = "#EF4444"
POSITIVE_COLOR = "#10B981"
RAW_DATA_PREVIEW_ROWS = 50

st.set_page_config(page_title=APP_TITLE, page_icon="📊", layout="wide")


@st.cache_data(show_spinner="Data yüklənir...")
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, encoding=DATA_ENCODING)
    df["Order Date"] = pd.to_datetime(df["Order Date"], format="%m/%d/%Y")
    df["Ship Date"] = pd.to_datetime(df["Ship Date"], format="%m/%d/%Y")
    df["Order Month"] = df["Order Date"].dt.to_period("M").dt.to_timestamp()
    df["Profit Margin"] = df["Profit"] / df["Sales"]
    return df


def render_sidebar_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("🔎 Filtrlər")

    min_date, max_date = df["Order Date"].min().date(), df["Order Date"].max().date()
    date_range = st.sidebar.date_input(
        "Tarix aralığı", value=(min_date, max_date), min_value=min_date, max_value=max_date
    )

    regions = st.sidebar.multiselect("Region", sorted(df["Region"].unique()), default=sorted(df["Region"].unique()))
    categories = st.sidebar.multiselect(
        "Kateqoriya", sorted(df["Category"].unique()), default=sorted(df["Category"].unique())
    )
    segments = st.sidebar.multiselect(
        "Müştəri seqmenti", sorted(df["Segment"].unique()), default=sorted(df["Segment"].unique())
    )
    ship_modes = st.sidebar.multiselect(
        "Çatdırılma növü", sorted(df["Ship Mode"].unique()), default=sorted(df["Ship Mode"].unique())
    )

    filtered_df = df.copy()
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[
            (filtered_df["Order Date"].dt.date >= start_date) & (filtered_df["Order Date"].dt.date <= end_date)
        ]

    filtered_df = filtered_df[
        filtered_df["Region"].isin(regions)
        & filtered_df["Category"].isin(categories)
        & filtered_df["Segment"].isin(segments)
        & filtered_df["Ship Mode"].isin(ship_modes)
    ]

    st.sidebar.caption(f"{len(filtered_df):,} / {len(df):,} sətir seçilib")
    return filtered_df


def render_kpi_cards(df: pd.DataFrame) -> None:
    total_sales = df["Sales"].sum()
    total_profit = df["Profit"].sum()
    total_orders = df["Order ID"].nunique()
    avg_order_value = total_sales / total_orders if total_orders else 0.0
    profit_margin = total_profit / total_sales if total_sales else 0.0
    total_quantity = int(df["Quantity"].sum())

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Ümumi satış", f"${total_sales:,.0f}")
    col2.metric("Ümumi mənfəət", f"${total_profit:,.0f}")
    col3.metric("Sifariş sayı", f"{total_orders:,}")
    col4.metric("Orta sifariş dəyəri", f"${avg_order_value:,.0f}")
    col5.metric("Mənfəət marjası", f"{profit_margin * 100:.1f}%")
    col6.metric("Satılan ədəd", f"{total_quantity:,}")


def build_sales_trend_chart(df: pd.DataFrame):
    monthly = df.groupby("Order Month", as_index=False).agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
    fig = px.line(
        monthly, x="Order Month", y=["Sales", "Profit"], markers=True,
        title="Aylıq satış və mənfəət trendi", color_discrete_sequence=[PRIMARY_COLOR, POSITIVE_COLOR],
    )
    fig.update_layout(xaxis_title="", yaxis_title="Məbləğ ($)", legend_title="")
    return fig


def build_category_sales_chart(df: pd.DataFrame):
    grouped = df.groupby("Category", as_index=False)["Sales"].sum()
    fig = px.pie(grouped, names="Category", values="Sales", hole=0.5, title="Kateqoriyaya görə satış payı")
    fig.update_traces(textinfo="percent+label")
    return fig


def build_region_sales_chart(df: pd.DataFrame):
    grouped = df.groupby("Region", as_index=False)["Sales"].sum().sort_values("Sales")
    fig = px.bar(
        grouped, x="Sales", y="Region", orientation="h", title="Regiona görə satış",
        color_discrete_sequence=[PRIMARY_COLOR],
    )
    fig.update_layout(xaxis_title="Satış ($)", yaxis_title="")
    return fig


def build_subcategory_profit_chart(df: pd.DataFrame):
    grouped = df.groupby("Sub-Category", as_index=False)["Profit"].sum().sort_values("Profit")
    fig = px.bar(grouped, x="Profit", y="Sub-Category", orientation="h", title="Alt kateqoriyaya görə mənfəət")
    fig.update_traces(marker_color=[NEGATIVE_COLOR if v < 0 else POSITIVE_COLOR for v in grouped["Profit"]])
    fig.update_layout(xaxis_title="Mənfəət ($)", yaxis_title="")
    return fig


def build_top_products_chart(df: pd.DataFrame, top_n: int = TOP_N_PRODUCTS):
    grouped = (
        df.groupby("Product Name", as_index=False)["Sales"].sum()
        .sort_values("Sales", ascending=False).head(top_n).sort_values("Sales")
    )
    fig = px.bar(
        grouped, x="Sales", y="Product Name", orientation="h", title=f"Ən çox satılan {top_n} məhsul",
        color_discrete_sequence=[PRIMARY_COLOR],
    )
    fig.update_layout(xaxis_title="Satış ($)", yaxis_title="")
    return fig


def build_segment_sales_chart(df: pd.DataFrame):
    grouped = df.groupby("Segment", as_index=False)["Sales"].sum()
    fig = px.bar(grouped, x="Segment", y="Sales", color="Segment", title="Seqmentə görə satış")
    fig.update_layout(xaxis_title="", yaxis_title="Satış ($)", showlegend=False)
    return fig


def build_discount_profit_scatter(df: pd.DataFrame):
    fig = px.scatter(
        df, x="Discount", y="Profit", color="Category", opacity=0.6,
        title="Endirim və mənfəət əlaqəsi",
    )
    fig.update_layout(xaxis_title="Endirim", yaxis_title="Mənfəət ($)", xaxis_tickformat=".0%")
    return fig


def render_insights(df: pd.DataFrame) -> None:
    st.subheader("💡 Analitik yekunlar")

    category_sales = df.groupby("Category")["Sales"].sum()
    top_category = category_sales.idxmax()
    st.markdown(
        f"- Ən çox satış **{top_category}** kateqoriyasındandır "
        f"(ümumi satışın {category_sales.max() / category_sales.sum():.1%}-i)."
    )

    subcategory_profit = df.groupby("Sub-Category")["Profit"].sum()
    if subcategory_profit.min() < 0:
        st.markdown(
            f"- **{subcategory_profit.idxmin()}** alt kateqoriyası zərərlə işləyir "
            f"(${abs(subcategory_profit.min()):,.0f} zərər)."
        )

    region_margin = df.groupby("Region").apply(lambda g: g["Profit"].sum() / g["Sales"].sum())
    st.markdown(
        f"- Ən yüksək mənfəət marjası **{region_margin.idxmax()}** regionundadır "
        f"({region_margin.max() * 100:.1f}%)."
    )

    discount_profit_corr = df["Discount"].corr(df["Profit"])
    if discount_profit_corr < -0.2:
        st.markdown(f"- Endirim artdıqca mənfəət azalır (korrelyasiya: {discount_profit_corr:.2f}).")


def render_data_quality_summary(df: pd.DataFrame) -> None:
    col1, col2, col3 = st.columns(3)
    col1.metric("Sətir sayı", f"{len(df):,}")
    col2.metric("Sütun sayı", f"{df.shape[1]:,}")
    col3.metric("Təkrarlanan sətir", f"{df.duplicated().sum():,}")

    missing_values = df.isnull().sum()
    missing_values = missing_values[missing_values > 0]
    if missing_values.empty:
        st.success("Boş (missing) dəyər aşkar edilmədi.")
    else:
        st.dataframe(missing_values.rename("Boş dəyər sayı"), use_container_width=True)


def convert_df_to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def render_raw_data_tab(df: pd.DataFrame) -> None:
    with st.expander("📋 Data keyfiyyəti xülasəsi"):
        render_data_quality_summary(df)

    show_all_rows = st.checkbox("Bütün filtrlənmiş sətirləri göstər")
    preview_df = df if show_all_rows else df.head(RAW_DATA_PREVIEW_ROWS)
    st.dataframe(preview_df, use_container_width=True, hide_index=True)
    if not show_all_rows:
        st.caption(f"İlk {RAW_DATA_PREVIEW_ROWS} sətir göstərilir. Hamısını görmək üçün yuxarıdakı qutunu işarələyin.")

    st.download_button(
        "⬇️ CSV kimi endir", data=convert_df_to_csv(df),
        file_name="filtrlenmis_data.csv", mime="text/csv", use_container_width=True,
    )


def render_dashboard(df: pd.DataFrame) -> None:
    st.title(f"📊 {APP_TITLE}")
    st.caption("Satış performansı üzrə interaktiv Data Analytics paneli")

    if df.empty:
        st.warning("⚠️ Seçilmiş filtrlərə uyğun heç bir məlumat tapılmadı. Filtrləri dəyişin.")
        st.stop()

    render_kpi_cards(df)
    st.divider()

    tab_overview, tab_analysis, tab_raw_data = st.tabs(["Ümumi baxış", "Ətraflı analiz", "Xam data"])

    with tab_overview:
        st.plotly_chart(build_sales_trend_chart(df), use_container_width=True)
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(build_category_sales_chart(df), use_container_width=True)
        with col2:
            st.plotly_chart(build_region_sales_chart(df), use_container_width=True)
        render_insights(df)

    with tab_analysis:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(build_subcategory_profit_chart(df), use_container_width=True)
        with col2:
            st.plotly_chart(build_top_products_chart(df), use_container_width=True)
        col3, col4 = st.columns(2)
        with col3:
            st.plotly_chart(build_segment_sales_chart(df), use_container_width=True)
        with col4:
            st.plotly_chart(build_discount_profit_scatter(df), use_container_width=True)

    with tab_raw_data:
        render_raw_data_tab(df)


if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""

if not st.session_state.authenticated:
    st.title(f"📊 {APP_TITLE}")
    st.caption("Dashboard-a daxil olmaq üçün hesabınızı təsdiqləyin")

    _, center_col, _ = st.columns([1, 1, 1])
    with center_col:
        with st.form("login_form"):
            username = st.text_input("İstifadəçi adı")
            password = st.text_input("Şifrə", type="password")
            submitted = st.form_submit_button("Daxil ol", use_container_width=True)

        if submitted:
            if VALID_CREDENTIALS.get(username) == password:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("İstifadəçi adı və ya şifrə yanlışdır.")

        st.caption("Demo giriş — İstifadəçi adı: **datacube**, Şifrə: **datacube123**")

else:
    st.sidebar.title(f"📊 {APP_TITLE}")
    st.sidebar.caption(f"Xoş gəldiniz, **{st.session_state.username}**")

    df = load_data(DATA_PATH)
    filtered_df = render_sidebar_filters(df)

    st.sidebar.divider()
    if st.sidebar.button("🚪 Çıxış", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.rerun()

    render_dashboard(filtered_df)