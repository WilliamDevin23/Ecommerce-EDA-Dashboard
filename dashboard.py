import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import datetime
import seaborn as sns

#color palette
colors = ["#006600"] + ["#80ff80"]*4
colors2 = ["#990000"] + ["#ff8080"]*4

#create dataframe based on certain timeframe
def df_timeframe(df, timeframe='D') :
    tf_df = df.resample(rule=timeframe, on="order_date").agg({"order_id":"nunique",
                                                           "revenue":"sum"}).reset_index()
    tf_df.rename(columns={"order_id":"order_count"}, inplace=True)
    tf_df.sort_values("order_date", ascending=True, ignore_index=True, inplace=True)
    if timeframe == 'M' :
        tf_df["order_date"] = tf_df["order_date"].apply(lambda x: datetime.datetime.strptime(str(x), "%Y-%m-%d %H:%M:%S").strftime("%Y-%m"))
    return tf_df

#grouping dataframe by customer state
def customer_bystate(df) :
    cust_state = df.groupby("customer_state",
                            as_index=False).agg({"customer_unique_id":"nunique"}).sort_values("customer_unique_id",
                                                                                            ascending=False,
                                                                                            ignore_index=True)
    cust_state.rename(columns={"customer_unique_id":"customer_count"}, inplace=True)
    return cust_state

#grouping dataframe by customer city
def customer_bycity(df) :
    cust_city = df.groupby("customer_city", as_index=False).agg({"customer_unique_id":"nunique"}).sort_values("customer_unique_id", ascending=False, ignore_index=True)
    cust_city.rename(columns={"customer_unique_id":"customer_count"}, inplace=True)
    return cust_city

#grouping dataframe by seller state
def seller_bystate(df) :
    seller_state = df.groupby("seller_state", as_index=False).agg({"seller_id":"nunique"}).sort_values("seller_id", ascending=False, ignore_index=True)
    seller_state.rename(columns={"seller_id":"seller_count"}, inplace=True)
    return seller_state

#grouping dataframe by seller city
def seller_bycity(df) :
    seller_city = df.groupby("seller_city", as_index=False).agg({"seller_id":"nunique"}).sort_values("seller_id", ascending=False, ignore_index=True)
    seller_city.rename(columns={"seller_id":"seller_count"}, inplace=True)
    return seller_city

#grouping order by product category
def orderby_product(df):
    by_prod = df.groupby("product_category", as_index=False).agg({"order_id":"nunique"}).sort_values("order_id", ascending=False, ignore_index=True)
    by_prod.rename(columns={"order_id":"order_count"}, inplace=True)
    return by_prod

#grouping revenue by product category
def byprod_revenue(df):
    by_rev = df.groupby("product_category", as_index=False).agg({"revenue":"sum"}).sort_values("revenue", ascending=False, ignore_index=True)
    return by_rev

#create rfm dataframe
def rfm_df(df) :
    rfm = df.groupby("customer_unique_id", as_index=False).agg({"order_id":"nunique",
                                                                "order_date":"max",
                                                                "revenue":"sum"})
    rfm["recency"] = (rfm["order_date"].max() - rfm["order_date"]).dt.days
    rfm = rfm.rename(columns={"order_id":"frequency", "revenue":"monetary"})
    rfm.drop("order_date", axis=1, inplace=True)

    rfm = rfm.sort_values("customer_unique_id")
    rfm["customer_id_number"] = [i for i in range(len(rfm["customer_unique_id"].to_list()))]

    
    return rfm

#import dataframe
df = pd.read_csv("complete_ecommerce_data.csv")
df_review = pd.read_csv("ecommerce_review.csv")

#changing to datetime format
df_arr = [df, df_review]
for table in df_arr :
    table["order_date"] = pd.to_datetime(table["order_date"])

#get oldest and newest date
min_date = df["order_date"].min()
max_date = df["order_date"].max()

performance, rfm_tab, reviews, demography = st.tabs(["Sales Performance", "RFM", "Reviews (All Time)", "Demography"]) 
with performance :
#sidebar
    with st.sidebar:
        st.title("Filter the Data*")
        st.markdown("*Except for Reviews")
        ranges = st.date_input(
            label="Select Date Range",
            min_value=min_date, max_value=max_date,
            value=[min_date, max_date]
            )
        st.markdown("Select Timeframe for Sales Performance Report and Demography Report")
        timeframe = st.radio(label="Timeframe",
                            options=("Daily", "Monthly"),
                            horizontal=False)

#filtering from sidebar
    try :
        start_date, end_date = ranges
    except ValueError :
        st.error("You must pick two dates")
        st.stop()
    #filtering based on date range
    df_filter = df[(df["order_date"] >= str(start_date)) & (df["order_date"] <= str(end_date))]

    #filtering based on timeframe
    if timeframe == "Monthly" :
        tf_df = df_timeframe(df_filter, 'M')
    else :
        tf_df = df_timeframe(df_filter)
        
    #Make the dataframes for Product Performance
    prod_df = orderby_product(df_filter)
    rev_df = byprod_revenue(df_filter)

    #Writing Content
    st.title("E-Commerce Performance Dashboard :sparkles:")
    st.subheader("{} Order and Revenue".format(timeframe))

    #Make columns for most ordered product category and the its revenue
    c1, c2 = st.columns(2)
    with c1 :
        if df_filter.shape[0] > 0 :
            st.metric("Most Ordered Product Category :", value="{}".format(prod_df.loc[0, "product_category"]))
            st.metric("Orders from {} Category:".format(prod_df.loc[0, "product_category"]), value="{}".format(prod_df.loc[0, "order_count"]))
        else :
            st.metric("Most Ordered Product Category :", value="-")
            st.metric("No Order :", value="0")
    with c2 :
        if df_filter.shape[0] > 0 :
            st.metric("Product Category with Highest Revenue :", value=rev_df.loc[0, "product_category"])
            st.metric("The Revenue from {} :".format(rev_df.loc[0, "product_category"]), value="R$ {:,.2f}".format(rev_df.loc[0,"revenue"]))
        else :
            st.metric("Product Category with Highest Revenue :", value="-")
            st.metric("Revenue : ", value=" R$ 0")

    #Make columns for number of order and total revenue in specific date range
    c3, c4 = st.columns(2)
    with c3 :
        if df_filter.shape[0] > 0 :
            st.metric("Total Orders :", value="{}".format(tf_df["order_count"].sum()))
        else :
            st.metric("Total Orders :", value="0")
    with c4 :
        if df_filter.shape[0] > 0 :
            st.metric("Total Revenue on {0} / {1} :".format(start_date, end_date), value="R$ {:,.2f}".format(tf_df["revenue"].sum()))
        else :
            st.metric("Total Revenue on {0} / {1} :".format(start_date, end_date), value=" R$ 0")

    #Make Graphic for Order and Revenue
    if df_filter.shape[0] > 0 :
        #Order
        fig = plt.figure(figsize=(30,10))
        plt.title("{} E-Commerce Order Count".format(timeframe), fontsize=40, fontweight="bold")
        plt.plot("order_date", "order_count", data=tf_df, color="navy", marker=".", linewidth=1.5)
        plt.grid(color="darkgray", linestyle=":", linewidth=0.5)
        plt.xticks(fontsize=15, rotation=30)
        plt.ylim(ymin=0)
        plt.ylabel("Order Counts", fontsize=20)
        st.pyplot(fig)

        #Revenue
        fig = plt.figure(figsize=(30,10))
        plt.title("{} E-Commerce Revenue".format(timeframe), fontsize=40, fontweight="bold")
        plt.plot("order_date", "revenue", data=tf_df, color="navy", marker=".", linewidth=1.5)
        plt.grid(color="darkgray", linestyle=":", linewidth=0.5)
        plt.xticks(fontsize=15, rotation=30)

        if tf_df['revenue'].max() >= 1000000 :
            labels, locs = plt.yticks()
            plt.yticks(labels, (labels/1000000), fontsize=15)
            plt.ylabel("Revenue (in R$ millions)", fontsize=20)
        else :
            plt.ylabel("Revenue (in R$)", fontsize=20)
        plt.ylim(ymin=0)
        st.pyplot(fig)

        #Product Category Performance By Order Count
        st.subheader("Product Category Performance by Order Count")

        fig, ax = plt.subplots(1,2, figsize=(30,8))
        plt.subplots_adjust(top=0.8)
        sns.barplot(y="product_category",
                    x="order_count",
                    data=prod_df.sort_values("order_count",ascending=False).head(),
                    palette=colors, ax=ax[0])
        ax[0].set_title("Most Ordered Product Category",fontsize=20)
        ax[0].set_xlabel("Order Count",fontsize=20)
        ax[0].set_ylabel(None)
        ax[0].tick_params(labelsize=15)

        sns.barplot(y="product_category",
                    x="order_count",
                    data=prod_df.sort_values("order_count").head(),
                    palette=colors2, ax=ax[1])
        ax[1].set_title("Least Ordered Product Category",fontsize=20)
        ax[1].set_xlabel("Order Count",fontsize=20)
        ax[1].invert_xaxis()
        ax[1].yaxis.tick_right()
        ax[1].set_ylabel(None)
        ax[1].tick_params(labelsize=15)

        st.pyplot(fig)

        #Product Category Performance By Revenue
        st.subheader("Product Category Performance by Revenue")

        fig, ax = plt.subplots(1,2, figsize=(30,8))
        plt.subplots_adjust(top=0.8)
        sns.barplot(y="product_category",
                    x="revenue",
                    data=rev_df.sort_values("revenue",ascending=False).head(),
                    palette=colors, ax=ax[0])
        ax[0].set_title("Most Revenue by Product Category",fontsize=20)
        if rev_df["revenue"].max() >= 1000000 :
            ax[0].set_xlabel("Revenue ( in R$ Million)",fontsize=20)
            ax[0].set_xticks(ax[0].get_xticks())
            ax[0].set_xticklabels([i/1000000 for i in ax[0].get_xticks()])
        else :
            ax[0].set_xlabel("Revenue",fontsize=20)
        ax[0].set_ylabel(None)
        ax[0].tick_params(labelsize=15)

        sns.barplot(y="product_category",
                    x="revenue",
                    data=rev_df.sort_values("revenue").head(),
                    palette=colors2, ax=ax[1])
        ax[1].set_title("Least Revenue by Product Category",fontsize=20)
        if rev_df["revenue"].min() >= 1000000 :
            ax[1].set_xticks(ax[1].get_xticks())
            ax[1].set_xticklabels([i/1000000 for i in ax[1].get_xticks()])
            ax[1].set_xlabel("Revenue (in R$ Million)",fontsize=20)
        else :
            ax[1].set_xlabel("Revenue",fontsize=20)
        ax[1].invert_xaxis()
        ax[1].yaxis.tick_right()
        ax[1].set_ylabel(None)
        ax[1].tick_params(labelsize=15)

        st.pyplot(fig)
    else :
        st.error("No data to display")

with demography :
    if df_filter.shape[0] > 0 :
        #dataframe creation
        cust_state = customer_bystate(df_filter)
        cust_city = customer_bycity(df_filter)
        seller_state = seller_bystate(df_filter)
        seller_city = seller_bycity(df_filter)

        #Demographic
        #Seller City
        st.subheader("Seller Demography")

        fig, ax = plt.subplots(1,2, figsize=(30,8))
        plt.suptitle("Seller Demography by City", fontsize=40, fontweight="bold")
        plt.subplots_adjust(top=0.8)
        sns.barplot(y="seller_city",
                    x="seller_count",
                    data=seller_city.sort_values("seller_count",ascending=False).head(),
                    palette=colors, ax=ax[0])
        ax[0].set_title("Most City Where Sellers Are",fontsize=20)
        ax[0].set_xlabel("Seller Count",fontsize=20)
        ax[0].set_ylabel(None)
        ax[0].tick_params(labelsize=15)

        sns.barplot(y="seller_city",
                    x="seller_count",
                    data=seller_city.sort_values("seller_count").head(),
                    palette=colors2, ax=ax[1])
        ax[1].set_title("Least City Where Sellers Are",fontsize=20)
        ax[1].set_xlabel("Seller Count",fontsize=20)
        ax[1].invert_xaxis()
        ax[1].yaxis.tick_right()
        ax[1].set_ylabel(None)
        ax[1].tick_params(labelsize=15)

        st.pyplot(fig)

        #Seller State
        fig, ax = plt.subplots(1,2, figsize=(30,8))
        plt.suptitle("Seller Demography by State", fontsize=40, fontweight="bold")
        plt.subplots_adjust(top=0.8)
        sns.barplot(y="seller_state",
                    x="seller_count",
                    data=seller_state.sort_values("seller_count",ascending=False).head(),
                    palette=colors, ax=ax[0])
        ax[0].set_title("Most State Where Sellers Are",fontsize=20)
        ax[0].set_xlabel("Seller Count",fontsize=20)
        ax[0].set_ylabel(None)
        ax[0].tick_params(labelsize=15)

        sns.barplot(y="seller_state",
                    x="seller_count",
                    data=seller_state.sort_values("seller_count").head(),
                    palette=colors2, ax=ax[1])
        ax[1].set_title("Least State Where Sellers Are",fontsize=20)
        ax[1].set_xlabel("Seller Count",fontsize=20)
        ax[1].invert_xaxis()
        ax[1].yaxis.tick_right()
        ax[1].set_ylabel(None)
        ax[1].tick_params(labelsize=15)

        st.pyplot(fig)

        #Customer City
        st.subheader("Customer Demography")

        fig, ax = plt.subplots(1,2, figsize=(30,8))
        plt.suptitle("Customer Demography by City", fontsize=40, fontweight="bold")
        plt.subplots_adjust(top=0.8)
        sns.barplot(y="customer_city",
                    x="customer_count",
                    data=cust_city.sort_values("customer_count",ascending=False).head(),
                    palette=colors, ax=ax[0])
        ax[0].set_title("Most City Where Customers Are",fontsize=20)
        ax[0].set_xlabel("Customer Count",fontsize=20)
        ax[0].set_ylabel(None)
        ax[0].tick_params(labelsize=15)

        sns.barplot(y="customer_city",
                    x="customer_count",
                    data=cust_city.sort_values("customer_count").head(),
                    palette=colors2, ax=ax[1])
        ax[1].set_title("Least City Where Customers Are",fontsize=20)
        ax[1].set_xlabel("Customer Count",fontsize=20)
        ax[1].invert_xaxis()
        ax[1].yaxis.tick_right()
        ax[1].set_ylabel(None)
        ax[1].tick_params(labelsize=15)

        st.pyplot(fig)

        #Customer State
        fig, ax = plt.subplots(1,2, figsize=(30,8))
        plt.suptitle("Customer Demography by State", fontsize=40, fontweight="bold")
        plt.subplots_adjust(top=0.8)
        sns.barplot(y="customer_state",
                    x="customer_count",
                    data=cust_state.sort_values("customer_count",ascending=False).head(),
                    palette=colors, ax=ax[0])
        ax[0].set_title("Most State Where Customers Are",fontsize=20)
        ax[0].set_xlabel("Customer Count",fontsize=20)
        ax[0].set_ylabel(None)
        ax[0].tick_params(labelsize=15)

        sns.barplot(y="customer_state",
                    x="customer_count",
                    data=cust_state.sort_values("customer_count").head(),
                    palette=colors2, ax=ax[1])
        ax[1].set_title("Least State Where Customers Are",fontsize=20)
        ax[1].set_xlabel("Customer Count",fontsize=20)
        ax[1].invert_xaxis()
        ax[1].yaxis.tick_right()
        ax[1].set_ylabel(None)
        ax[1].tick_params(labelsize=15)

        st.pyplot(fig)
    else :
        st.error("No data to display")

#Review tab
with reviews :
    df_review_best = df_review.groupby("product_category", as_index=False).agg({"review_score":"mean"}).sort_values("review_score", ascending=False, ignore_index=True)
    df_review_worst = df_review.groupby("product_category", as_index=False).agg({"review_score":"mean"}).sort_values("review_score", ignore_index=True)
    cr1, cr2 = st.columns(2)
    with cr1 :
        st.metric("Product Category with Best Review :",
                    value=df_review_best.loc[0, "product_category"])
        st.metric("Best Review Score Mean :", value=df_review_best["review_score"].max())
    with cr2 :
        st.metric("Product Category with Worst Review :", 
                    value=df_review_worst.loc[0, "product_category"])
        st.metric("Worst Review Score Mean :", value=df_review_best["review_score"].min())
    
    fig, ax = plt.subplots(1,2, figsize=(30,10))
    plt.suptitle("Product Category Performance by Review", fontsize=40, fontweight="bold")
    sns.barplot(x="review_score",
                y="product_category",
                data=df_review_best.head(),
                palette=colors,
                ax=ax[0]
                )
    ax[0].set_title("Product Category with Best Review", fontsize=20)
    ax[0].set_xlabel("Review Score", fontsize=20)
    ax[0].tick_params(labelsize=15)
    ax[0].set_ylabel(None)

    sns.barplot(x="review_score",
                y="product_category",
                data=df_review_worst.head(),
                palette=colors2,
                ax=ax[1]
                )
    ax[1].set_title("Product Category with Worst Review", fontsize=20)
    ax[1].set_xlabel("Review Score", fontsize=20)
    ax[1].tick_params(labelsize=15)
    ax[1].set_ylabel(None)
    ax[1].invert_xaxis()
    ax[1].yaxis.tick_right()

    st.pyplot(fig)

#RFM
with rfm_tab:
    if df_filter.shape[0] > 0 :
        #filter rfm
        rfm = rfm_df(df_filter)

        # Make sorted dataframes
        sorted_recency = rfm.sort_values("recency",ascending=True)
        sorted_recency.reset_index(drop=True, inplace=True)

        sorted_frequency = rfm.sort_values("frequency",ascending=False)
        sorted_frequency.reset_index(drop=True, inplace=True)

        sorted_monetary = rfm.sort_values("monetary",ascending=False)
        sorted_monetary.reset_index(drop=True, inplace=True)

        rfm_dict = {"recency":sorted_recency, "frequency":sorted_frequency, "monetary":sorted_monetary}

        st.header("RFM Analysis")
        fig, ax = plt.subplots(1,3, figsize=(30,8))
        plt.suptitle("RFM Analysis Bar Plot", fontsize=40, fontweight="bold")
        plt.subplots_adjust(top=0.8)
        i = 0
        for metric, table in rfm_dict.items():
            sns.barplot(x=table.head().index,
                        y=metric,
                        data=table.head(),
                        palette=colors,
                        ax=ax[i])
            if metric == "recency" :
                ax[i].set_title("Recency (in Days)",fontsize=20, pad=10)
            else :
                ax[i].set_title(metric.title(),fontsize=20, pad=10)
            ax[i].set_xticklabels(table.head()["customer_id_number"])
            ax[i].set_xlabel("Customer ID Number",fontsize=20)
            ax[i].set_ylim(ymin=0)
            ax[i].tick_params(labelsize=12)
            ax[i].set_ylabel(None)
            i += 1
        st.pyplot(fig)
        st.markdown("Blank bar(s) on the recency barplot means that the 5 current transaction are made less than a day.")
    else :
        st.error("No data to display")

st.caption("Copyright (C) 2023 - William Devin")
