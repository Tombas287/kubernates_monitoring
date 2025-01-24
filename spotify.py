from langchain.prompts import PromptTemplate
from langchain.agents import initialize_agent, AgentType, Tool
from langchain.tools.base import BaseTool
from langchain_community.tools import DuckDuckGoSearchRun
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.callbacks.streamlit import StreamlitCallbackHandler
import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables for your Spotify API credentials
load_dotenv()

# Initialize Spotify API client
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET")
))

# Initialize the LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    api_key=os.getenv("GENAI_API_KEY"),
    temperature=0.5
)

# Initialize DuckDuckGo Search tool
search_artist = DuckDuckGoSearchRun()

# Define the Spotify tool to fetch top songs and artist image
class SpotifyTopSongsTool(BaseTool):
    name: str = "spotify_top_songs"
    description: str = "Fetches the top 5 songs of the artist from Spotify and their profile image."

    def _run(self, artist_name: str) -> dict:
        # Search for the artist on Spotify
        results = sp.search(q=artist_name, type='artist', limit=1)
        if not results['artists']['items']:
            return {"error": "Artist not found on Spotify"}

        artist_data = results['artists']['items'][0]
        artist_id = artist_data['id']
        artist_image = artist_data['images'][0]['url'] if artist_data['images'] else None

        # Fetch the top 5 tracks for the artist
        top_tracks = sp.artist_top_tracks(artist_id)['tracks'][:5]
        song_list = [{"name": track['name'], "url": track['external_urls']['spotify']} for track in top_tracks]

        return {"image": artist_image, "songs": song_list}

# Define tools list
tools = [
    Tool(
        name="Spotify Top Songs",
        func=SpotifyTopSongsTool()._run,
        description="Fetches top 5 songs of the artist from Spotify along with their profile image."
    ),
    Tool(
        name="Artist Summary",
        func=search_artist.run,
        description="Fetches a detailed summary of the artist, including their birth, major awards, "
        "famous works, recent updates about their achievements and contributions, and "
        "links to their social media profiles (Instagram, Twitter, Facebook) if available."


    )
]

# Define Prompt Template
prompt_template = PromptTemplate(
    input_variables=["singer"],
    template=(
        "Give me a list of 5 romantic songs by {singer}. "
        "Include a brief introduction about the singer. "
        "Present the song list in a table with the following columns: "
        "'Song Name' and 'youtube URL'."
    )
)

# Initialize the agent with verbose flow tracking
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent_type=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# Streamlit layout configuration
st.set_page_config(layout="wide", page_title="Music Assistant")
st.title("Music Assistant")

# Input and button in the sidebar
user_input = st.sidebar.text_input("Enter the name of the artist you want to search for:")
submit = st.sidebar.button("Submit")

# When user clicks submit, process the input
if user_input and submit:
    with st.spinner("Processing your request..."):
        try:
            # Use the prompt template to construct the task for the agent
            query = prompt_template.format(singer=user_input)

            # Initialize the Streamlit callback handler for live updates
            callback_handler = StreamlitCallbackHandler(parent_container=st.container())
            agent.run(query, callbacks=[callback_handler])

            # Fetch artist's top songs and image using Spotify tool
            spotify_tool = SpotifyTopSongsTool()
            spotify_data = spotify_tool._run(user_input)  # Directly use the Spotify tool
            artist_image = spotify_data.get("image", "NA")
            song_list = spotify_data.get("songs", "NA")

            # Fetch artist summary using the agent
            artist_summary = search_artist.run(user_input)

            # Display the artist's profile image and summary
            st.subheader("Artist Profile")
            if artist_image:
                st.image(artist_image, width=300, caption=f"{user_input}'s Spotify Profile")
            st.write(artist_summary or "No summary available.")

            # Display the final song list in a table
            st.subheader("Top Songs")
            if song_list:
                table_rows = "| Song Name | Spotify URL |\n|-----------|-------------|\n"
                for song in song_list:
                    table_rows += f"| {song['name']} | [Listen Here]({song['url']}) |\n"
                    # Render the table with clickable links
                st.markdown(table_rows, unsafe_allow_html=True)
            else:
                st.error("No songs found for the artist.")

        except Exception as e:
            st.error(f"Error processing the request: {e}")
