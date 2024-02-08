import streamlit as st
import pandas as pd

# Set page configuration to make it full width
st.set_page_config(layout="wide")

# Initialize session state for selected cluster
if 'selected_cluster_id' not in st.session_state:
    st.session_state.selected_cluster_id = None

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

def hero_number(label, value):
    container = st.container(border=True)
    with container:
        st.metric(label=label, value=value)
    
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
        
    
def review(site, rating, date, title, author, content):
    container = st.container(border=True)
    with container:
        c1,c2,c3 = st.columns([0.02,0.3,0.055])
        with c1:
            if site == 'Google':
                st.image('Google G Icon.png')
            #st.text(site)
        with c2:
            st.text(rating_display(rating))
        with c3:
            st.write(date)
        st.write(f'###### {title}')
        st.write(f'*{author}*')

        st.write(content)
       # st.write(f"📍 {entity_name}")
            
    

def main():
    st.title("Reviews Insights 💡")



    # Load the data
    data_path = 'example_clusters_titles_sentiment_1.csv'  # Updated path
    reviews_data_path = 'fake_reviews_2.csv'  # Updated path
    cluster_df = load_data(data_path)
    reviews_df = load_data(reviews_data_path)

    # Sort clusters by the number of reviews mentioning
    sorted_df = cluster_df.sort_values(
        by='NUM_REVIEWS_MENTIONING', ascending=False)

    hero_container = st.container(border=True)
    with hero_container:
        st.write("Review Insights summarize key highlights from your most recent reviews")
        st.caption("Last Generated: Jan 8th, 2024, 9:00 AM EST")
        c1, c2, c3, c4 = st.columns(4)
    with c1:
        hero_number(label='💬 New Reviews', value=4381)
    with c2:
        hero_number(label="⭐ Average Rating", value=4.2)
    with c3:
        hero_number(label="📈 Positive Themes", value=43)
    with c4:
        hero_number(label="📉 Negative Themes", value=30)
    
    # Create two columns for clusters and reviews
    col1, col2 = st.columns([0.4,0.6])

    with col1:
        st.write("### Themes")
        for _, row in sorted_df.iterrows():
            container = st.container(border=True)
            with container:
                display_title = f"{sentiment_icon(row['Sentiment'])} {row['Simplified_Title']}"
                st.write(f'##### {display_title}')
                st.write(str(row['NUM_REVIEWS_MENTIONING'])+ ' reviews')
                st.caption(row['CLUSTER_SUMMARY'])
                #st.button('View',key=row['CLUSTER_ID'], use_container_width=True)
                if st.button('View Details', key=row['CLUSTER_ID'], use_container_width=True):
                    select_cluster(row['CLUSTER_ID'])


            # Create a button for each cluster that updates the selected cluster ID in session state
            #button_label = f"{row['Simplified_Title']} {sentiment_icon(row['Sentiment'])} ({row['NUM_REVIEWS_MENTIONING']} reviews)"
            # st.markdown('<span id="button-after"></span>',
            #             unsafe_allow_html=True)
            # if st.button(button_label, key=row['CLUSTER_ID'], use_container_width=True):
            #     select_cluster(row['CLUSTER_ID'])

    with col2:
        st.write("### Details")
        if st.session_state.selected_cluster_id:
            # Display the selected cluster's summary and number of reviews
            selected_cluster = sorted_df[sorted_df['CLUSTER_ID']
                                         == st.session_state.selected_cluster_id]
            sentiment = f"{selected_cluster['Sentiment'].iloc[0]}"
            display_title = f" {selected_cluster['Simplified_Title'].iloc[0]}"

           # display_title = sentiment_icon(sentiment) + f" {selected_cluster['Simplified_Title'].iloc[0]}"
            st.write(f'#### {display_title}')
            st.write(str(selected_cluster['NUM_REVIEWS_MENTIONING'].iloc[0])+ " Reviews")

            st.caption(selected_cluster['CLUSTER_SUMMARY'].iloc[0])
            st.divider()

            # Filter reviews based on selected cluster ID and display them
            filtered_reviews = reviews_df[reviews_df['CLUSTER_ID']
                                          == st.session_state.selected_cluster_id]
            if not filtered_reviews.empty:
                st.write("##### Review Snippets")
                for _, row in filtered_reviews.iterrows():
                    review(
                        site='Google', 
                        rating = row['RATING'], 
                        title = 'Unpleasant Experience', 
                        author = row['REVIEW_AUTHOR'],
                        content= row['REVIEW_CONTENT'],
                        #entity_name = 'Kimberly Ann Arsi, DO',
                        date = row['REVIEW_DATE']
                    )
                    # st.write(
                    #     f"**{row['REVIEW_AUTHOR']}** on **{row['REVIEW_SITE']}** ({row['REVIEW_DATE']}) - Rating: {row['RATING']}")
                    # st.write(row['REVIEW_CONTENT'])
                    # st.write("---")
            else:
                st.write("No reviews available for this cluster.")


if __name__ == '__main__':
    main()
