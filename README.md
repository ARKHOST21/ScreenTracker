# Screen Tracker

Screen Tracker is an open-source application that captures screenshots at regular intervals, stores them in organized folders, and provides a user-friendly interface for managing and viewing them. This tool is ideal for monitoring screen activity or creating a visual log of your work.

## Features

- **Automated Screenshot Capture**: Takes screenshots at specified intervals.
- **Multi-Monitor Support**: Select which monitors to capture.
- **Dark Mode**: Toggle dark mode for a better viewing experience.
- **Screenshot Viewer**: View and navigate through captured screenshots.
- **Disk Space Info**: Check disk space usage.
- **Folder Cleanup**: Easily clean up old screenshot folders.
- **Multilingual Support**: Available in multiple languages.

## Screenshots

![Screen Tracker Main Interface](screenshots/main_interface.png)

## Installation

### Prerequisites

- Windows operating system
- Python 3.7 or later

### Running from Source

1. Clone the repository:
    ```sh
    git clone https://github.com/ARKHOST21/ScreenTracker.git
    ```
2. Navigate to the project directory:
    ```sh
    cd screen-tracker
    ```
3. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```
4. Run the application:
    ```sh
    python src/main.py
    ```

## Usage

1. **Set the Output Folder**: Click on "Set Output Folder" to choose where screenshots will be saved.
2. **Configure Settings**: Adjust the screenshot interval, format, and retention period.
3. **Start Capturing**: Click on "✔ Start" to begin capturing screenshots.
4. **View Screenshots**: Use the "View Screenshots" button to open the screenshot viewer.
5. **Manage Disk Space**: Click on "Disk Space Info" to see disk usage information.
6. **Clean Folders**: Use the "Clean Folders" button to delete old screenshot folders.

## Download the Portable Edition

For users who prefer a portable version, download the latest release from SourceForge:

[Download Portable Edition](https://sourceforge.net/projects/screentracker/files/releases/latest/download)

## Languages

Screen Tracker is available in the following languages:

- English
- Dutch
- Spanish
- Russian
- Italian
- German
- French
- Armenian
- Georgian
- Bulgarian
- Polish

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for more details.

## Support

If you find this project useful, consider supporting its development by [buying me a coffee](https://www.buymeacoffee.com/YuriKaramian).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Contact

- **Author**: Yuri K.
- **Company**: ArkHost
- **Email**: yuri@arkhost.com
- **Website**: [ArkHost](https://www.arkhost.com)

## Acknowledgments

Special thanks to all the contributors and the open-source community for their support.


### LICENSE

Make sure the `LICENSE` file in your project directory contains the following content for the MIT License:

MIT License

Copyright (c) 2024 Yuri Karamian

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### Final Project Structure

Ensure your project directory looks like this:

screen-tracker/
├── src/
│   ├── main.py
│   ├── icons/
│   │   ├── app_icon.ico
│   │   └── app_icon.png
│   ├── lang/
│   │   ├── english.json
│   │   ├── dutch.json
│   │   ├── spanish.json
│   │   ├── russian.json
│   │   ├── italian.json
│   │   ├── german.json
│   │   ├── french.json
│   │   ├── armenian.json
│   │   ├── georgian.json
│   │   ├── bulgarian.json
│   │   └── polish.json
│   └── requirements.txt
├── screenshots/
│   ├── main_interface.png
├── README.md
└── LICENSE

