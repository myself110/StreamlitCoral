import streamlit as st
import os
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import time
import logging
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Fish Tank Monitor",
    page_icon="🐠",
    layout="wide"
)

# Custom CSS for compact single-window layout (no colored boxes)
st.markdown("""
<style>
/* Remove default Streamlit margins and spacing */
.main .block-container {
    padding-top: 0.25rem;
    padding-bottom: 0.25rem;
    padding-left: 0.25rem;
    padding-right: 0.25rem;
}

/* Ensure no scrolling */
body {
    overflow: hidden;
}
</style>
""", unsafe_allow_html=True)



# Function to find timelapse videos in Google Drive starting from root folder
def find_timelapse_videos():
    try:
        logger.info("🔍 Starting root folder video search...")
        
        # Configuration - Root folder ID that contains domain folders
        ROOT_FOLDER_ID = "0AHKUF31V4DyLUk9PVA"
        
        # Load service account credentials
        logger.info("📋 Loading service account credentials...")
        creds = service_account.Credentials.from_service_account_file(
            'service_account.json', 
            scopes=['https://www.googleapis.com/auth/drive']
        )
        logger.info(f"✅ Credentials loaded for: {creds.service_account_email}")
        
        # Build Drive service
        logger.info("🔧 Building Google Drive service...")
        service = build('drive', 'v3', credentials=creds)
        logger.info("✅ Google Drive service built successfully")
        
        # Test basic access first
        logger.info("🧪 Testing basic Drive API access...")
        test_query = "trashed=false"
        test_results = service.files().list(
            q=test_query, 
            pageSize=1,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        logger.info(f"✅ Basic API test successful - can access Drive API")
        
        # Step 1: Access the root folder and list domain folders
        logger.info(f"📁 Step 1: Accessing root folder: {ROOT_FOLDER_ID}")
        
        try:
            # Get root folder info
            root_info = service.files().get(
                fileId=ROOT_FOLDER_ID, 
                supportsAllDrives=True
            ).execute()
            logger.info(f"✅ Root folder accessible: {root_info['name']}")
        except HttpError as e:
            if e.resp.status == 404:
                logger.error(f"❌ Root folder not found: {ROOT_FOLDER_ID}")
                return [], service
            elif e.resp.status == 403:
                logger.error(f"❌ Access denied to root folder: {ROOT_FOLDER_ID}")
                return [], service
            else:
                raise e
        
        # List all domain folders within the root folder
        logger.info("🔍 Listing domain folders in root...")
        
        domain_query = f"'{ROOT_FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        domain_results = service.files().list(
            q=domain_query,
            pageSize=20,
            fields="files(id, name, parents, owners)",
            orderBy="name",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        
        domain_folders = domain_results.get('files', [])
        logger.info(f"📊 Found {len(domain_folders)} domain folders in root")
        
        if not domain_folders:
            logger.warning("❌ No domain folders found in root")
            return [], service
        
        # Log domain folders found
        for folder in domain_folders:
            logger.info(f"📁 Domain folder: {folder['name']} (ID: {folder['id']})")
        
        # Step 2: For each domain folder, look for camera folders, then timelapse folders INSIDE camera folders
        logger.info("📹 Step 2: Searching for camera folders, then timelapse folders INSIDE camera folders...")
        
        all_videos = []
        
        for domain in domain_folders:
            logger.info(f"🔍 Searching in domain: {domain['name']}")
            
            # Look for camera folders in this domain
            camera_query = f"'{domain['id']}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            camera_results = service.files().list(
                q=camera_query,
                fields="files(id, name, parents)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()
            
            camera_folders = camera_results.get('files', [])
            logger.info(f"📹 Found {len(camera_folders)} camera folders in {domain['name']}")
            
            # Step 3: For each camera folder, look for timelapse folder INSIDE it
            for camera in camera_folders:
                logger.info(f"🔍 Checking camera folder: {camera['name']}")
                
                # Look for timelapse folder INSIDE this camera folder (ONLY timelapse, not image)
                timelapse_query = f"'{camera['id']}' in parents and name='timelapse' and mimeType='application/vnd.google-apps.folder' and trashed=false"
                timelapse_results = service.files().list(
                    q=timelapse_query,
                    fields="files(id, name, parents)",
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True
                ).execute()
                
                timelapse_folders = timelapse_results.get('files', [])
                logger.info(f"⏰ Found {len(timelapse_folders)} timelapse folders in {domain['name']}/{camera['name']}")
                
                # Step 4: Find videos in timelapse folders ONLY - STOP at first video found
                for timelapse in timelapse_folders:
                    logger.info(f"🎬 Searching for videos in: {domain['name']}/{camera['name']}/{timelapse['name']}")
                    
                    # Search for video files within this timelapse folder ONLY
                    video_query = f"'{timelapse['id']}' in parents and (mimeType contains 'video/' or name contains '.mp4' or name contains '.avi' or name contains '.mov') and trashed=false"
                    video_results = service.files().list(
                        q=video_query,
                        pageSize=1,  # Only get 1 video - the first one found
                        fields="files(id, name, mimeType, size, webViewLink, owners, createdTime)",
                        orderBy="createdTime desc",  # Get newest video first
                        supportsAllDrives=True,
                        includeItemsFromAllDrives=True
                    ).execute()
                    
                    found_videos = video_results.get('files', [])
                    if found_videos:  # If we found a video, stop here
                        video = found_videos[0]  # Take the first video
                        video['folder_path'] = f"{domain['name']}/{camera['name']}/{timelapse['name']}"
                        video['domain'] = domain['name']
                        video['camera'] = camera['name']
                        video['timelapse_folder_id'] = timelapse['id']
                        all_videos.append(video)
                        logger.info(f"🎯 FIRST VIDEO FOUND: {video['name']} in {domain['name']}/{camera['name']}/{timelapse['name']}")
                        
                        # Stop searching - we found our first video!
                        logger.info("🎯 Stopping search - first video found!")
                        break  # Exit the timelapse loop
                
                # If we found a video in this camera, stop searching other cameras too
                if all_videos:
                    logger.info("🎯 Video found, stopping search in other cameras...")
                    break  # Exit the camera loop
        
        logger.info(f"🎯 Total videos found: {len(all_videos)}")
        
        # Log details of found videos
        for i, video in enumerate(all_videos):
            logger.info(f"📹 Video {i+1}: {video['name']} (ID: {video['id']}, Path: {video['folder_path']})")
        
        return all_videos, service
        
    except HttpError as e:
        error_msg = f"Google Drive HTTP Error {e.resp.status}: {e}"
        logger.error(error_msg)
        st.error(f"❌ {error_msg}")
        
        if e.resp.status == 403:
            st.error("🚫 **Permission Denied** - This usually means:")
            st.error("• Google Drive API is not enabled")
            st.error("• Service account lacks proper IAM roles")
            st.error("• Service account not shared with the folders")
        elif e.resp.status == 404:
            st.error("🔍 **Not Found** - This usually means:")
            st.error("• Folder structure doesn't exist")
            st.error("• Service account can't see the folders")
        
        return [], None
        
    except Exception as e:
        error_msg = f"Unexpected error accessing Google Drive: {e}"
        logger.error(error_msg)
        st.error(f"❌ {error_msg}")
        st.error("🔧 **Troubleshooting steps:**")
        st.error("• Check if service_account.json exists and is valid")
        st.error("• Verify Google Drive API is enabled in Google Cloud Console")
        st.error("• Ensure service account has proper permissions")
        st.error("• Verify folder structure: Domain → cam1 → timelapse")
        return [], None

# Function to get video stream URL
def get_video_stream_url(service, file_id):
    try:
        logger.info(f"🔗 Getting video stream URL for file ID: {file_id}")
        
        # Get file metadata with proper shared drive support
        file_metadata = service.files().get(
            fileId=file_id, 
            fields="id, name, mimeType, webViewLink, webContentLink",
            supportsAllDrives=True
        ).execute()
        logger.info(f"📄 File metadata retrieved: {file_metadata.get('name', 'Unknown')}")
        
        # Try multiple URL formats for better compatibility
        video_urls = []
        
        # Option 1: Direct preview URL (best for embedding)
        preview_url = f"https://drive.google.com/file/d/{file_id}/preview"
        video_urls.append(("Preview", preview_url))
        
        # Option 2: View URL (opens in Google Drive)
        view_url = f"https://drive.google.com/file/d/{file_id}/view"
        video_urls.append(("View", view_url))
        
        # Option 3: Use webViewLink if available
        if 'webViewLink' in file_metadata:
            web_view_url = file_metadata['webViewLink']
            video_urls.append(("WebView", web_view_url))
            logger.info(f"🔗 Found webViewLink: {web_view_url}")
        
        # Option 4: Direct download link (if accessible)
        if 'webContentLink' in file_metadata:
            download_url = file_metadata['webContentLink']
            video_urls.append(("Download", download_url))
            logger.info(f"🔗 Found webContentLink: {download_url}")
        
        # Return the preview URL as primary (best for iframe embedding)
        primary_url = preview_url
        logger.info(f"🎬 Generated primary video URL: {primary_url}")
        logger.info(f"📋 Available URL options: {len(video_urls)}")
        
        return primary_url
        
    except Exception as e:
        error_msg = f"Error getting video URL for file {file_id}: {e}"
        logger.error(error_msg)
        st.error(f"❌ {error_msg}")
        return None



# Initialize session state for data
if 'sensor_data' not in st.session_state:
    st.session_state.sensor_data = {
        'temperature': [],
        'light': [],
        'ph': [],
        'timestamps': []
    }
    
    # Generate initial data points to show graphs immediately
    base_time = datetime.now()
    for i in range(20):  # Generate 20 initial data points
        timestamp = base_time - timedelta(minutes=19-i)  # Spread over last 19 minutes
        
        # Generate realistic sensor data with some variation
        base_temp = 25.0 + np.sin(i * 0.3) * 2  # Add some wave pattern
        temp_variation = np.random.normal(0, 0.5)
        temperature = base_temp + temp_variation
        
        base_light = 800 + np.cos(i * 0.4) * 100  # Add some wave pattern
        light_variation = np.random.normal(0, 30)
        light = max(100, base_light + light_variation)
        
        base_ph = 7.2 + np.sin(i * 0.2) * 0.3  # Add some wave pattern
        ph_variation = np.random.normal(0, 0.05)
        ph = max(6.8, min(7.6, base_ph + ph_variation))
        
        # Add to session state
        st.session_state.sensor_data['temperature'].append(temperature)
        st.session_state.sensor_data['light'].append(light)
        st.session_state.sensor_data['ph'].append(ph)
        st.session_state.sensor_data['timestamps'].append(timestamp)

# Function to generate random sensor data
def generate_sensor_data():
    current_time = datetime.now()
    
    # Get current time components for more dynamic patterns
    seconds = current_time.second
    minutes = current_time.minute
    
    # Generate realistic sensor data with dynamic patterns
    # Temperature: varies with time and has seasonal-like patterns
    base_temp = 25.0 + np.sin(seconds * 0.1) * 1.5 + np.cos(minutes * 0.1) * 0.8
    temp_variation = np.random.normal(0, 0.3)
    temperature = base_temp + temp_variation
    
    # Light: simulates day/night cycle and artificial lighting
    time_factor = (seconds + minutes * 60) / 3600  # Hours since midnight
    base_light = 800 + np.sin(time_factor * 0.5) * 200 + np.cos(seconds * 0.05) * 50
    light_variation = np.random.normal(0, 25)
    light = max(100, base_light + light_variation)
    
    # pH: varies slowly with some random fluctuations
    base_ph = 7.2 + np.sin(minutes * 0.02) * 0.2 + np.sin(seconds * 0.01) * 0.1
    ph_variation = np.random.normal(0, 0.03)
    ph = max(6.8, min(7.6, base_ph + ph_variation))
    
    return temperature, light, ph, current_time

# Function to update sensor data
def update_sensor_data():
    temp, light, ph, timestamp = generate_sensor_data()
    
    # Add new data point
    st.session_state.sensor_data['temperature'].append(temp)
    st.session_state.sensor_data['light'].append(light)
    st.session_state.sensor_data['ph'].append(ph)
    st.session_state.sensor_data['timestamps'].append(timestamp)
    
    # Keep only last 50 data points for smooth animation
    max_points = 50
    if len(st.session_state.sensor_data['temperature']) > max_points:
        st.session_state.sensor_data['temperature'] = st.session_state.sensor_data['temperature'][-max_points:]
        st.session_state.sensor_data['light'] = st.session_state.sensor_data['light'][-max_points:]
        st.session_state.sensor_data['ph'] = st.session_state.sensor_data['ph'][-max_points:]
        st.session_state.sensor_data['timestamps'] = st.session_state.sensor_data['timestamps'][-max_points:]

# Update data every time the app reruns
update_sensor_data()

# Add auto-refresh functionality using session state
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()

# Check if it's time to add more data (every 5 seconds to avoid too frequent updates)
current_time = datetime.now()
time_diff = (current_time - st.session_state.last_refresh).total_seconds()

if time_diff >= 5:  # Add new data point every 5 seconds
    # Add multiple data points to make the animation more visible
    for _ in range(2):  # Add 2 new data points
        update_sensor_data()
    st.session_state.last_refresh = current_time



# TOP HALF: Two columns for Logging and Video (50% of screen)
col1, col2 = st.columns(2)

# Top-Left Section - Logging Fish Tank Information
with col1:
    st.markdown("### 📝 Fish Tank Logging")
    st.markdown("• Salinity")
    st.markdown("• Water Change (Date)")
    st.markdown("• Fish dead?")
    st.markdown("• Fish Tank Cleaned")

# Top-Right Section - Time Lapse Video Playing
with col2:
    st.markdown("### 🎬 Time Lapse Video")
    
    # Show Google Drive connection status
    drive_connected = False
    
    try:
        # Check if service account file exists
        if not os.path.exists('service_account.json'):
            logger.error("❌ service_account.json file not found")
            drive_connected = False
        else:
            logger.info("✅ service_account.json file exists")
        
        # Test connection
        logger.info("🔐 Testing Google Drive connection...")
        
        creds = service_account.Credentials.from_service_account_file(
            'service_account.json', 
            scopes=['https://www.googleapis.com/auth/drive']
        )
        logger.info(f"✅ Service account loaded: {creds.service_account_email}")
        
        service = build('drive', 'v3', credentials=creds)
        logger.info("✅ Google Drive service built")
        
        # Quick test query
        logger.info("🧪 Testing basic API access...")
        
        test_results = service.files().list(
            q="trashed=false", 
            pageSize=1,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        files_found = len(test_results.get('files', []))
        
        logger.info(f"✅ API access successful - found {files_found} accessible files")
        drive_connected = True
        
    except FileNotFoundError:
        error_msg = "service_account.json file not found"
        logger.error(f"❌ {error_msg}")
        drive_connected = False
        
    except HttpError as e:
        error_msg = f"Google Drive HTTP Error {e.resp.status}: {e}"
        logger.error(error_msg)
        drive_connected = False
        
    except Exception as e:
        error_msg = f"Google Drive connection failed: {e}"
        logger.error(error_msg)
        drive_connected = False
    
    # Find timelapse videos in Google Drive
    if drive_connected:
        videos, service = find_timelapse_videos()
        
        if videos:
            logger.info(f"🎯 Displaying FIRST video found: {videos[0]['name']}")
            
            # Display the first (and only) video found
            video = videos[0]
            logger.info(f"🎬 Playing video: {video['name']}")
            
            # Create video player using Google Drive link
            logger.info(f"🔗 Creating video URL for file ID: {video['id']}")
            video_url = get_video_stream_url(service, video['id'])
            
            if video_url:
                logger.info(f"✅ Video URL created successfully: {video_url}")
                
                # Try to embed the video for web playback
                try:
                    logger.info(f"🎥 Attempting to embed video with MIME type: {video['mimeType']}")
                    
                    # For MP4 files, we can try to embed directly
                    if 'mp4' in video['mimeType'].lower():
                        embed_url = video_url  # Use the preview URL from our function
                        logger.info(f"📺 Creating embed with URL: {embed_url}")
                        st.markdown(f"""
                        <iframe 
                            src="{embed_url}" 
                            width="100%" 
                            height="450" 
                            frameborder="0" 
                            allowfullscreen>
                        </iframe>
                        """, unsafe_allow_html=True)
                    else:
                        logger.info(f"⚠️ Non-MP4 video type: {video['mimeType']}")
                        
                except Exception as e:
                    error_msg = f"Error embedding video: {e}"
                    logger.error(error_msg)
            else:
                logger.error("❌ Failed to create video URL")
            
            # Show other available videos
            if len(videos) > 1:
                for i, other_video in enumerate(videos[1:4], 2):  # Show next 3
                    other_url = get_video_stream_url(service, other_video['id'])
                    logger.info(f"📎 Additional video {i}: {other_video['name']}")
                    
        else:
            logger.warning("⚠️ No videos found in timelapse folders")
            
            # Add a refresh button
            if st.button("🔄 Refresh Video Search"):
                logger.info("🔄 Manual refresh requested")
                st.rerun()
    else:
        logger.warning("📹 Google Drive not connected")
    
# BOTTOM HALF: Sensor Information & Graphs
st.markdown("### 📊 Sensor Information & Graphs")



# Create animated charts
if len(st.session_state.sensor_data['timestamps']) > 1:
    # Create DataFrame for plotting
    df = pd.DataFrame({
        'Time': st.session_state.sensor_data['timestamps'],
        'Temperature': st.session_state.sensor_data['temperature'],
        'Light': st.session_state.sensor_data['light'],
        'pH': st.session_state.sensor_data['ph']
    })
    
    # Create charts layout: All 3 charts in one row
    col_temp_chart, col_light_chart, col_ph_chart = st.columns(3)
    
    with col_temp_chart:
        st.markdown("**🌡️ Temperature**")
        fig_temp = px.line(df, x='Time', y='Temperature', 
                           title="",
                           color_discrete_sequence=['#ff6b6b'])
        fig_temp.update_layout(height=200, showlegend=False, margin=dict(l=0, r=0, t=15, b=0))
        fig_temp.update_traces(line=dict(width=3))
        st.plotly_chart(fig_temp, use_container_width=True)
    
    with col_light_chart:
        st.markdown("**💡 Light Level**")
        fig_light = px.line(df, x='Time', y='Light', 
                            title="",
                            color_discrete_sequence=['#ffd93d'])
        fig_light.update_layout(height=200, showlegend=False, margin=dict(l=0, r=0, t=15, b=0))
        fig_light.update_traces(line=dict(width=3))
        st.plotly_chart(fig_light, use_container_width=True)
    
    with col_ph_chart:
        st.markdown("**🧪 pH Level**")
        fig_ph = px.line(df, x='Time', y='pH', 
                         title="",
                         color_discrete_sequence=['#6bcf7f'])
        fig_ph.update_layout(height=200, showlegend=False, margin=dict(l=0, r=0, t=15, b=0))
        fig_ph.update_traces(line=dict(width=3))
        st.plotly_chart(fig_ph, use_container_width=True)

else:
    st.info("📊 Collecting sensor data... Charts will appear after a few data points.")
