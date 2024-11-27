// Listen for messages from the content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    // If we received the video title, update the popup display
    if (message.videoTitle) {
        document.getElementById('title').textContent = message.videoTitle;
    }
});
