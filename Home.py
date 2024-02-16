import streamlit as st
import pandas as pd
import snowflake.connector
import openai

DEFAULT_CLUSTER_COUNT = 20

##################### Snowflake #####################
#@st.cache_resource
def init_connection():
    return snowflake.connector.connect(
        **st.secrets["snowflake"], client_session_keep_alive=True
    )


#@st.cache_data(ttl=600)
def run_query(query, conn):
    with conn.cursor() as cur:
        cur.execute(query)
        columns = [i[0] for i in cur.description]
        return pd.DataFrame(cur.fetchall(), columns=columns)


####################################################

# Set page configuration to make it full width
st.set_page_config(layout="wide")

# Initialize session state for selected cluster
if 'selected_cluster_id' not in st.session_state:
    st.session_state.selected_cluster_id = None

if 'business_id' not in st.session_state:
    st.session_state.business_id = None
    
if 'theme_count' not in st.session_state:
    st.session_state.theme_count = DEFAULT_CLUSTER_COUNT

st.markdown("""
<style>.element-container:has(#button-after) + div button {
font-size: 100px;
 height: 50px;
 }</style>""", unsafe_allow_html=True)

# Function to load data


def load_data(filepath):
    return pd.read_csv(filepath)

# Function to display sentiment as an icon


def sentiment_icon(sentiment):
    if sentiment == "Positive":
        return "👍"
    elif sentiment == "Negative":
        return "👎"
    else:
        return "🤔"  # Neutral or undefined sentiment


# Function to update session state with selected cluster ID
def select_cluster(cluster_id):
    st.session_state.selected_cluster_id = cluster_id

# Function to update session state with selected business ID and trigger a re-run
def update_business_id(name_to_id):
    selected_name = st.session_state.selected_business_id
    selected_id = name_to_id[selected_name]
    st.session_state.business_id = selected_id
    st.experimental_rerun()

def update_theme_count(selected_count):
    st.session_state.theme_count = selected_count
    st.experimental_rerun()



def hero_number(label, value):
    container = st.container(border=True)
    with container:
        st.metric(label=label, value=value)
        
def hero_numbers(cluster_count, review_count, average_rating):
    hero_container = st.container(border=True)
    with hero_container:
        st.write(
            "Common themes from your most recent reviews")
        st.caption("Last Generated: Feb 12th, 2024, 9:00 AM EST")
        c1, c2, c3 = st.columns(3)
    with c1: 
        hero_number (label='💡 Themes', value = cluster_count)
    with c2:
        hero_number(label='💬 Reviews Included', value=review_count)
    with c3:
        hero_number(label="⭐ Average Rating", value=average_rating)
    # with c3:
    #     hero_number(label="📈 Positive Themes", value=43)
    # with c4:
    #     hero_number(label="📉 Negative Themes", value=30)


def rating_display(rating):

    if rating == 1:
        return '⭐'
    elif rating == 2:
        return '⭐⭐'
    elif rating == 3:
        return '⭐⭐⭐'
    elif rating == 4:
        return '⭐⭐⭐⭐'
    elif rating == 5:
        return '⭐⭐⭐⭐⭐'


def review(publisher_id, rating, date, title, author, content, content_segment):
    container = st.container(border=True)
    with container:
        c1, c2, c3 = st.columns([0.02, 0.3, 0.055])
        with c1:
            try:
                st.image(f'{publisher_id}.png')
            except:
                st.write(f'*{publisher_id}*')
        with c2:
            st.text(rating_display(rating))
        with c3:
            st.write(f'*{date}*')
        st.write(f'###### {title}')
        st.write(f'*{author}*')

        highlighted_content = content.replace(content_segment, f'<mark>{content_segment}</mark>')
        st.markdown(f'{highlighted_content}', unsafe_allow_html=True)

       # st.write(f"📍 {entity_name}")

with st.sidebar:
    conn = init_connection()
    unqiue_business_snowflake_query = f'''
        select distinct b.business_id, b.name
        from TEAM_DATA_SCIENCE.PUBLIC.CLUSTER_RUNS_REVIEWS cr
        join PROD_PLATFORM_GLOBAL.PUBLIC.BUSINESSES b on b.business_id=cr.business_id
        where 1
        AND IS_NOISE = FALSE
        ;
    '''
    
    business_df = run_query(unqiue_business_snowflake_query, conn)
    name_to_id = dict(zip(business_df['NAME'], business_df['BUSINESS_ID']))
    selected_name = st.selectbox('Customer:', business_df['NAME'], key='selected_business_id')

    # Number of themes option
    # theme_options = [15, 20, 25]
    # selected_theme_count = st.selectbox('Number of Themes:', theme_options, key='selected_theme_count')

    if st.button('Run Report'):
        update_business_id(name_to_id)
        #st.write(selected_theme_count)



def main():


    if st.session_state.business_id:
        cluster_count = DEFAULT_CLUSTER_COUNT
        st.title("Review Themes 💡")
    
    ## Write Sidebar component here

        # Code to re-run using the new business_id value
        conn = init_connection()
        cluster_snowflake_query = f'''
            select distinct CLUSTER_ID, CLUSTER_SUMMARY, REVIEW_SEGMENT, r.title, r.rating::FLOAT as "RATING", r.content, r.author_name, r.publisher_id, r.entity_id, r.publisher_timestamp
            from TEAM_DATA_SCIENCE.PUBLIC.CLUSTER_RUNS_REVIEWS cr
            join PROD_LISTINGS_LOCAL.REVIEWS.ENTITY_REVIEWS r on cr.review_id = r.review_id
            where cr.BUSINESS_ID = {st.session_state.business_id}
            AND RUN_ID = (SELECT MAX_BY(RUN_ID, RUN_TIMESTAMP) FROM TEAM_DATA_SCIENCE.PUBLIC.CLUSTER_RUNS_REVIEWS where business_id = {st.session_state.business_id})
            AND IS_NOISE = FALSE
            ;
        '''
        # Query for clusters and their reviews
        cluster_df = run_query(cluster_snowflake_query, conn)
        
        # Group clusters to get count and average rating of reviews    
        grouped = cluster_df.groupby(['CLUSTER_ID', 'CLUSTER_SUMMARY']).agg({'RATING': ['count', 'mean']})
        grouped.columns = ['NUM_REVIEWS', 'AVERAGE_RATING']
        grouped = grouped.reset_index()
        
        top_clusters = grouped.sort_values(by='NUM_REVIEWS', ascending=False).head(int(cluster_count))


        # Calculate total review count and weighted average rating for the top clusters
        total_reviews = top_clusters['NUM_REVIEWS'].sum()
        weighted_average_rating = (top_clusters['NUM_REVIEWS'] * top_clusters['AVERAGE_RATING']).sum() / total_reviews

        hero_numbers(cluster_count, total_reviews, round(weighted_average_rating, 2))


        # Create two columns for clusters and reviews
        col1, col2 = st.columns([0.4, 0.6])

        with col1:
            st.write("### Themes")
            control_bar = st.container()
            with control_bar:
                sort_options = {
                    'Number of Reviews (High to Low)': ('NUM_REVIEWS', False),
                    'Average Rating (High to Low)': ('AVERAGE_RATING', False),
                    'Average Rating (Low to High)': ('AVERAGE_RATING', True)
                }
                
                selected_sort = st.selectbox('Sort by:', list(sort_options.keys()), key='sort_by')
                sort_column, ascending = sort_options[selected_sort]

                # Sort the top clusters based on the selected sorting option
                sorted_df = top_clusters.sort_values(by=sort_column, ascending=ascending)
            for _, row in sorted_df.iterrows():
                container = st.container(border=True)
                with container:
                    st.caption(row['CLUSTER_SUMMARY'])
                    st.write(f"{row['NUM_REVIEWS']} Reviews")
                    st.write(f"{rating_display(round(row['AVERAGE_RATING']))} ({round(row['AVERAGE_RATING'], 2)})")
                    if st.button('View Reviews', key=row['CLUSTER_ID'], use_container_width=True):
                        select_cluster(row['CLUSTER_ID'])

        with col2:
            st.write("### Reviews")
            if st.session_state.selected_cluster_id:
            #     # Display the selected cluster's summary and number of reviews
            #     selected_cluster = sorted_df[sorted_df['CLUSTER_ID']
            #                                  == st.session_state.selected_cluster_id]
            #     sentiment = '🤔'
            #     #sentiment = f"{selected_cluster['Sentiment'].iloc[0]}"
            # #     display_title = f" {selected_cluster['Simplified_Title'].iloc[0]}"

            # #    # display_title = sentiment_icon(sentiment) + f" {selected_cluster['Simplified_Title'].iloc[0]}"
            # #     st.write(f'#### {display_title}')
            #     st.write(
            #         str(selected_cluster['NUM_REVIEWS'].iloc[0]) + " Reviews")

            #     st.caption(selected_cluster['CLUSTER_SUMMARY'].iloc[0])
            #     st.divider()

                # Filter reviews based on selected cluster ID and display them
                filtered_reviews = cluster_df[cluster_df['CLUSTER_ID'] == st.session_state.selected_cluster_id]   
                if not filtered_reviews.empty:
                    for _, row in filtered_reviews.iterrows():
                        review(
                            publisher_id=row['PUBLISHER_ID'],
                            rating=row['RATING'],
                            title=row['TITLE'],
                            author=row['AUTHOR_NAME'],
                            content=row['CONTENT'],
                            content_segment=row['REVIEW_SEGMENT'],
                            # entity_name = 'Kimberly Ann Arsi, DO',
                            date=str(row['PUBLISHER_TIMESTAMP'])[0:10]
                        )
                        # st.write(
                        #     f"**{row['REVIEW_AUTHOR']}** on **{row['REVIEW_SITE']}** ({row['REVIEW_DATE']}) - Rating: {row['RATING']}")
                        # st.write(row['REVIEW_CONTENT'])
                        # st.write("---")
                else:
                    st.write("Select a Theme to see reviews")


if __name__ == '__main__':
    main()
