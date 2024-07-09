# Import necessary libraries
from urllib.parse import urlparse, parse_qs

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

from pytube import YouTube
from pytube.exceptions import VideoUnavailable

from openai import OpenAI
from dotenv import load_dotenv

import os

# Load environment variables from the .env file
load_dotenv()

# Get the OPENROUTER_API_KEY from the .env file
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Models from LM Studio :
# You can uncomment to select model or add your own model. Make sure to comment out the other line.
# model="MaziyarPanahi/Mistral-7B-Instruct-v0.3-GGUF",
# model="LM Studio Community/Meta-Llama-3-8B-Instruct-GGUF",

# Models from OpenRouter :
# You can change model here.
model = "google/gemma-2-9b-it:free"

# Client for LM Studio
# You can uncomment to use LM Studio or add your own tool/service. Make sure to comment out the other line.
# client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

# Client for OpenRouter
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)


def get_video_id(video_url: str) -> str:
    """
    Retrieves the video ID from a given YouTube URL.

    Args:
        video_url (str): The URL of the YouTube video.

    Returns:
        str: The video ID if found, otherwise None.

    URL Examples:
     - http://youtu.be/video_id
     - http://www.youtube.com/watch?v=video_id&feature=feedu
     - http://www.youtube.com/embed/video_id
     - http://www.youtube.com/v/video_id?version=3&hl=en_US
     - https://www.youtube.com/shorts/video_id

    """
    try:
        # Parse the URL to extract its components
        query = urlparse(video_url)

        # Check if the hostname is "youtu.be"
        if query.hostname == "youtu.be":
            # Return the path (which contains the video ID) minus the first character
            return query.path[1:]

        # Check if the hostname is "www.youtube.com" or "youtube.com"
        if query.hostname in ("www.youtube.com", "youtube.com"):
            # Check if the path is "/watch"
            if query.path == "/watch":
                # Parse the query string to extract the video ID
                p = parse_qs(query.query)
                return p["v"][0]

            # Check if the path starts with "/embed/"
            elif query.path.startswith("/embed/"):
                # Return the third part of the path (which contains the video ID)
                return query.path.split("/")[2]

            # Check if the path starts with "/v/"
            elif query.path.startswith("/v/"):
                # Return the third part of the path (which contains the video ID)
                return query.path.split("/")[2]

            # Check if the path starts with "/shorts/"
            elif query.path.startswith("/shorts/"):
                # Return the third part of the path (which contains the video ID)
                return query.path.split("/")[2]

    except Exception as e:
        print(f"An error occurred: {e}")

    # If none of the above conditions are met, return None
    return None


def get_transcript(video_url: str) -> str:
    """
    Retrieves the transcript from the given video URL.

    Args:
        video_url (str): The URL of the YouTube video.

    Returns:
        str: The transcript of the video.
    """
    try:
        # Get the video ID from the URL
        video_id = get_video_id(video_url)

        # Check if the video ID is valid
        if video_id is None:
            raise ValueError("Invalid YouTube URL")

        # Retrieve the transcripts for the video
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Find the English transcript
        transcript = transcript_list.find_transcript(["en"])
        if transcript:
            # Fetch the transcript text
            transcript_text = transcript.fetch()

            # Format the transcript text using a TextFormatter
            formatter = TextFormatter()
            formatted_transcript = formatter.format_transcript(transcript_text).replace(
                "\n", " "
            )

            return formatted_transcript
        else:
            raise ValueError("No English transcript found")

    except Exception as e:
        # Handle any exceptions that occur during the process
        print(f"Error: {str(e)}")


def embed_youtube_video(video_url):
    """
    Generates an HTML iframe element for embedding a YouTube video.

    Args:
        video_url (str): The URL of the YouTube video.

    Returns:
        str: The generated HTML iframe element.
    """
    # Get the video ID from the URL
    video_id = get_video_id(video_url)

    # Generate the HTML iframe element
    iframe = f"""
    <div style="display: flex; justify-content: center;">
        <iframe 
            width="60%" 
            height="400" 
            src="https://www.youtube.com/embed/{video_id}" 
            frameborder="0" 
            allowfullscreen
            title="YouTube video player"
        >
        </iframe>
    </div>
    """
    # Return the generated HTML iframe element
    return iframe


def get_video_title(video_url: str) -> str:
    """
    Retrieves the title from the given video URL.

    Args:
        video_url (str): The URL of the YouTube video.

    Returns:
        str: The title of the video.
    """
    try:
        # Create a YouTube object with the given video URL
        youtube_video = YouTube(video_url)

        # Get the title of the video
        video_title = youtube_video.title

        return video_title

    except VideoUnavailable:
        # Return an error message if the video is not available
        print("Video not available")

    except Exception as e:
        # Log and return an error message for any other exceptions
        print(f"Error occurred: {str(e)}")


def summarize_video(video_url: str):
    """
    Summarizes a YouTube video transcript.

    Args:
        video_url (str): The URL of the YouTube video.

    Yields:
        str: A summary of the YouTube video transcript.
    """
    try:
        # Get the transcript and title of the video
        transcript = get_transcript(video_url)
        video_title = get_video_title(video_url)

        # Create a message for the chat completion API
        message = [
            {
                "role": "system",
                "content": """Summarize the main points and their comprehensive explanations from the YouTube video transcript, 
                presenting them under appropriate headings. Use various emojis to symbolize different sections also use markdown 
                formatting, and format the content as a cohesive paragraph under each heading. Ensure the summary is clear, 
                detailed, and informative. Avoid using phrases that directly reference 'the script provides' to maintain a direct 
                and objective tone.""",
            },
            {
                "role": "user",
                "content": f"Video Title : {video_title}, Video Transcript : {transcript}",
            },
        ]

        # Create the chat completion API response
        response = client.chat.completions.create(
            model=model,
            messages=message,
            temperature=0.7,
            stream=True,
        )

        text = ""

        for chunk in response:
            if chunk.choices[0].finish_reason != "stop":
                text += chunk.choices[0].delta.content
                yield text
    except Exception as e:
        print(f"An error occurred: {str(e)}")


def chat(user_input, history, video_url):
    """
    This function generates a conversation based on user input,
    video transcript, and previous conversations.

    Args:
        user_input (str): The current user input.
        history (list of tuples): A list of tuples containing the human and assistant messages in the conversation.
        video_url (str): The URL of the video for which the transcript is needed.

    Returns:
        A generator that yields the chat conversation.

    Raises:
        ValueError: If the user input is empty or None.
    """

    # Get the video title and transcript
    transcript = get_transcript(video_url)
    video_title = get_video_title(video_url)

    if user_input is None or user_input == "":
        raise ValueError("User input cannot be empty")

    # Initialize the OpenAI format for the conversation history
    history_openai_format = []
    history_openai_format.append(
        {
            "role": "system",
            "content": f"""Your task is to answer questions about a video transcript. 
    Extract information from the provided script only and provide relevant answers within its scope. 
    Please refrain from making any inferences or using external knowledge.
    Here is the video title and video transcript text:
    
    Video Title : {video_title}, Video Transcript Text : {transcript}
    
    If asked to perform tasks unrelated to the video transcript, 
    please politely decline""",
        }
    )

    # Add previous conversations to the history OpenAI format
    for human, assistant in history:
        history_openai_format.append({"role": "user", "content": human})
        history_openai_format.append({"role": "assistant", "content": assistant})

    # Add the current user input to the conversation history
    history_openai_format.append({"role": "user", "content": user_input})

    # Generate the chat completion using OpenAI
    completion = client.chat.completions.create(
        model=model,
        messages=history_openai_format,
        temperature=0.7,
        stream=True,
    )

    new_message = ""

    for chunk in completion:
        if chunk.choices[0].delta.content:
            new_message += chunk.choices[0].delta.content
            yield new_message
