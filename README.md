# Moonlight Upload

Moonlight Upload is a simple, unbloated, and Tor Friendly web application built with Flask that allows users to upload and share files. It features an administration panel for configuration, file management, and basic statistics.

Note: It was a old project that I never finished so the frontend is not 100% responsive, feel free to use the code for your projects...

## Features

- **File Upload:** Users can upload files through the main page.
- **File Deletion:** Users can delete files using a unique key generated during the upload.
- **Preview Images:** Optionally, users can provide preview images for their uploads.
- **Administration Panel:** A secure admin panel is available for configuration updates, viewing uploaded files, and monitoring statistics.
- **Stats Page:** Displays statistics such as the total number of uploads, preview images, total size, downloads, and views.

## Technologies Used

- **Flask:** Python Web framework for the backend.
- **Python 3.10+:** Python Programming Language.
- **HTML, CSS:** Front-end technologies for an interactive user experience.
- **PicoCSS:** Not bloated CSS framework and very lightweight. 
- **SQLite:** For the database.

## Administration 

The application uses Flask for the web framework, SQLAlchemy for database interactions, and Werkzeug for secure file handling.

### Configuration

- **Database:** SQLite is used to store upload information.
- **File Storage:** Uploaded files and previews are stored in the 'uploads' folder.
- **Allowed/Forbidden Extensions:** Certain file extensions are allowed or forbidden for upload.
- **File Size Limits:** Maximum sizes are set for both archive files and preview images.

### Database Models

- **Upload:** Represents uploaded files with details such as folder, filename, IP address, upload date, file size, key, preview, download count, and view count.
- **Message:** Stores a single content message, such as the main page message.
- **DownloadLog:** Logs download events, including the upload ID, IP address, and download time.

### File Handling

- **File Validation:** Checks if uploaded files have valid extensions and sizes.
- **Random Key Generation:** Generates random keys for secure file deletion.
- **Cleanup:** Deletes unused files and empty folders.

### Web Routes

- **Main Page (/):** Handles file uploads and displays relevant information.
- **Delete Page (/delete):** Initiates the file deletion process.
- **Vault Page (/vault):** Displays information about a specific upload.
- **Download Page (/download):** Allows users to download files.
- **Media Page (/media):** Serves video files.
- **Preview Page (/preview):** Serves preview images.
- **Admin Page (/admin):** Admin panel for configuration and file management.
- **Stats Page (/stats):** Displays statistics about uploads.
- **Static Pages (/about, /donation, /privacy, /tos):** Informative pages about the application.

### Error Handling

- Custom error pages for 404, 403, 405, and 500 errors with corresponding error images.

## Installation

1. Clone the repository: `#`
2. `cd moonlight-upload`
3. (optional) Create a python virtual environment. 
4. Install dependencies: `pip install -r requirements.txt`
5. Change the settings in the `moonlight/app.py` file.
6. Run the application (in development mode only): `python moonlight/app.py` or `python debug_app.py`

## Deploy

See this [guide](https://dev.to/brandonwallace/deploy-flask-the-easy-way-with-gunicorn-and-nginx-jgc) for deploying the application in a linux server using Nginx and Gunicorn.

Note: The `wsgi.py` file is stored in `/moonlight`

## Disclaimer

This project is for educational purposes only. Any actions and or activities related to the material contained within this project is solely your responsibility. I assume no liability and are not responsible for any misuse or damage caused by this program.

## Contact

Created by [Insomnia](https://github.com/currentlyonciawatchlist/) - feel free to contact me!